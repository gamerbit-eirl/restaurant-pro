param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [int]$MesaId = 1,
    [int]$ProductoId = 1,
    [ValidateSet("local", "llevar", "delivery")]
    [string]$TipoConsumo = "local",
    [switch]$Reload,
    [switch]$SkipFlowTests,
    [switch]$NoKeepRunning
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Restaurant Pro] $Message" -ForegroundColor Cyan
}

function Wait-HttpReady {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 60,
        [string]$Name = "service"
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
                Write-Step "$Name listo en $Url"
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 700
        }
    }

    throw "Timeout esperando $Name en $Url"
}

function Assert-JsonProperty {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [Parameter(Mandatory = $true)][string]$Property,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if (-not ($Object.PSObject.Properties.Name -contains $Property)) {
        throw "Respuesta invalida en ${Context}: falta propiedad '$Property'"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$logsDir = Join-Path $repoRoot "logs"
New-Item -ItemType Directory -Force $logsDir | Out-Null

$backendOut = Join-Path $logsDir "backend-dev.out.log"
$backendErr = Join-Path $logsDir "backend-dev.err.log"
$frontendOut = Join-Path $logsDir "frontend-dev.out.log"
$frontendErr = Join-Path $logsDir "frontend-dev.err.log"

$backendProc = $null
$frontendProc = $null

try {
    Write-Step "Levantando backend FastAPI en $BackendHost`:$BackendPort"
    $backendArgs = @("-m", "uvicorn", "app.main:app", "--host", $BackendHost, "--port", "$BackendPort")
    if ($Reload.IsPresent) {
        $backendArgs += "--reload"
    }
    $backendProc = Start-Process -FilePath "python" -ArgumentList $backendArgs `
        -WorkingDirectory $backendDir -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru

    Write-Step "Levantando frontend Next.js en puerto $FrontendPort"
    $frontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList @(
        "/c", "npm", "run", "dev", "--", "-p", "$FrontendPort"
    ) -WorkingDirectory $frontendDir -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru

    Wait-HttpReady -Url "http://$BackendHost`:$BackendPort/" -TimeoutSeconds 90 -Name "backend"
    Wait-HttpReady -Url "http://127.0.0.1:$FrontendPort/" -TimeoutSeconds 120 -Name "frontend"

    Write-Step "Smoke test backend"
    $backendRoot = Invoke-RestMethod -Method Get -Uri "http://$BackendHost`:$BackendPort/"
    Assert-JsonProperty -Object $backendRoot -Property "message" -Context "GET /"
    Write-Step "GET / OK -> $($backendRoot.message)"

    Write-Step "Smoke test frontend"
    $frontRoot = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort/" -UseBasicParsing
    if ($frontRoot.StatusCode -lt 200 -or $frontRoot.StatusCode -ge 400) {
        throw "Frontend devolvio estado inesperado: $($frontRoot.StatusCode)"
    }
    Write-Step "Frontend OK con estado $($frontRoot.StatusCode)"

    if (-not $SkipFlowTests.IsPresent) {
        Write-Step "Flow test POS: abrir pedido -> agregar item -> enviar cocina -> cocina/pedidos"

        $abrirResp = Invoke-RestMethod -Method Post `
            -Uri "http://$BackendHost`:$BackendPort/pedidos/abrir" `
            -ContentType "application/json" `
            -Body (@{ mesa_id = $MesaId } | ConvertTo-Json)

        Assert-JsonProperty -Object $abrirResp -Property "id" -Context "POST /pedidos/abrir"
        $pedidoId = [int]$abrirResp.id
        Write-Step "Pedido activo: $pedidoId (mesa $MesaId)"

        $agregarResp = Invoke-RestMethod -Method Post `
            -Uri "http://$BackendHost`:$BackendPort/pedido-items/agregar" `
            -ContentType "application/json" `
            -Body (@{
                pedido_id = $pedidoId
                producto_id = $ProductoId
                cantidad = 1
                tipo_consumo = $TipoConsumo
            } | ConvertTo-Json)

        Assert-JsonProperty -Object $agregarResp -Property "items_creados" -Context "POST /pedido-items/agregar"
        if (-not $agregarResp.items_creados -or $agregarResp.items_creados.Count -lt 1) {
            throw "No se crearon items en /pedido-items/agregar"
        }

        $enviarResp = Invoke-RestMethod -Method Post `
            -Uri "http://$BackendHost`:$BackendPort/pedidos/enviar-cocina" `
            -ContentType "application/json" `
            -Body (@{ pedido_id = $pedidoId } | ConvertTo-Json)

        Assert-JsonProperty -Object $enviarResp -Property "items_enviados" -Context "POST /pedidos/enviar-cocina"
        Write-Step "Items enviados a cocina: $($enviarResp.items_enviados)"

        $kdsResp = Invoke-RestMethod -Method Get -Uri "http://$BackendHost`:$BackendPort/cocina/pedidos"
        Assert-JsonProperty -Object $kdsResp -Property "pedidos" -Context "GET /cocina/pedidos"
        Write-Step "Pedidos visibles en cocina: $($kdsResp.pedidos.Count)"

        $firstKitchenItem = $null
        foreach ($p in $kdsResp.pedidos) {
            if ($p.items -and $p.items.Count -gt 0) {
                $firstKitchenItem = $p.items[0]
                break
            }
        }

        if ($null -ne $firstKitchenItem) {
            $itemId = [int]$firstKitchenItem.item_id

            $listoResp = Invoke-RestMethod -Method Post `
                -Uri "http://$BackendHost`:$BackendPort/pedido-items/marcar-listo" `
                -ContentType "application/json" `
                -Body (@{ pedido_item_id = $itemId } | ConvertTo-Json)

            if ($listoResp.estado_item -ne "listo") {
                throw "El item $itemId no paso a estado 'listo'"
            }

            $entregarResp = Invoke-RestMethod -Method Post `
                -Uri "http://$BackendHost`:$BackendPort/pedido-items/entregar" `
                -ContentType "application/json" `
                -Body (@{ pedido_item_id = $itemId } | ConvertTo-Json)

            if ($entregarResp.estado_item -ne "entregado") {
                throw "El item $itemId no paso a estado 'entregado'"
            }

            Write-Step "Control de entrega OK en item $itemId"
        }
        else {
            Write-Step "No se encontro item en cocina para probar marcar-listo/entregar"
        }
    }

    Write-Host ""
    Write-Host "Backend:  http://$BackendHost`:$BackendPort" -ForegroundColor Green
    Write-Host "Frontend: http://127.0.0.1:$FrontendPort" -ForegroundColor Green
    Write-Host "Logs:     $logsDir" -ForegroundColor Green

    if ($NoKeepRunning.IsPresent) {
        Write-Step "NoKeepRunning activo: cerrando servicios"
        return
    }

    Write-Step "Servicios activos. Presiona Ctrl+C para terminar."
    while ($true) {
        if ($backendProc.HasExited) {
            throw "Backend se detuvo inesperadamente. Revisa $backendErr"
        }
        if ($frontendProc.HasExited) {
            throw "Frontend se detuvo inesperadamente. Revisa $frontendErr"
        }
        Start-Sleep -Seconds 2
    }
}
catch {
    Write-Host "" -ForegroundColor Red
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Revisa logs en: $logsDir" -ForegroundColor Yellow
    throw
}
finally {
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force
    }
    if ($frontendProc -and -not $frontendProc.HasExited) {
        Stop-Process -Id $frontendProc.Id -Force
    }
}
