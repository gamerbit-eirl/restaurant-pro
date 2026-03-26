param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$Reload,
    [switch]$ForceRestart
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Restaurant Pro] $Message" -ForegroundColor Cyan
}

function Get-PortPids {
    param([int]$Port)
    $lines = netstat -ano | findstr ":$Port"
    if (-not $lines) { return @() }

    $pids = @()
    foreach ($line in $lines) {
        $trimmed = ($line -replace "\s+", " ").Trim()
        if (-not $trimmed) { continue }
        $parts = $trimmed.Split(" ")
        $last = $parts[-1]
        if ($last -match "^\d+$" -and [int]$last -gt 0) { $pids += [int]$last }
    }
    return $pids | Select-Object -Unique
}

function Stop-Port {
    param([int]$Port)
    $pids = Get-PortPids -Port $Port
    foreach ($procId in $pids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Step "Proceso $procId detenido en puerto $Port"
        }
        catch {
            Write-Host "[WARN] No se pudo detener PID $procId en puerto $Port" -ForegroundColor Yellow
        }
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$logsDir = Join-Path $repoRoot "logs"
New-Item -ItemType Directory -Force $logsDir | Out-Null

$backendOut = Join-Path $logsDir "backend-up.out.log"
$backendErr = Join-Path $logsDir "backend-up.err.log"
$frontendOut = Join-Path $logsDir "frontend-up.out.log"
$frontendErr = Join-Path $logsDir "frontend-up.err.log"

if ($ForceRestart.IsPresent) {
    Stop-Port -Port $BackendPort
    Stop-Port -Port $FrontendPort
}

$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$backendArgs = @("-m", "uvicorn", "app.main:app", "--host", $BackendHost, "--port", "$BackendPort")
if ($Reload.IsPresent) { $backendArgs += "--reload" }

Write-Step "Levantando backend en http://$BackendHost`:$BackendPort"
$backendCmd = "`"$pythonExe`" $($backendArgs -join ' ')"
$backendProc = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", $backendCmd) `
    -WorkingDirectory $backendDir -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru

Write-Step "Levantando frontend en http://127.0.0.1:$FrontendPort"
$frontendProc = Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm", "run", "dev", "--", "-p", "$FrontendPort") `
    -WorkingDirectory $frontendDir -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru

Write-Host ""
Write-Host "Backend:  http://$BackendHost`:$BackendPort" -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:$FrontendPort" -ForegroundColor Green
Write-Host "Logs:     $logsDir" -ForegroundColor Green
Write-Host ""
Write-Host "PIDs -> backend: $($backendProc.Id) | frontend: $($frontendProc.Id)" -ForegroundColor Yellow
Write-Host "Para detener: Stop-Process -Id $($backendProc.Id),$($frontendProc.Id)" -ForegroundColor Yellow
