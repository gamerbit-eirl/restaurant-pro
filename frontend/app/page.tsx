"use client";

import { useEffect, useMemo, useState } from "react";

type ItemControl = {
  id: number;
  pedido_id: number;
  producto_id: number;
  producto_nombre: string;
  cantidad: number;
  precio_unitario: number;
  tipo_consumo: "local" | "llevar" | "delivery";
  area: "cocina" | "barra";
  estado_item: "pendiente" | "enviado_cocina" | "preparando" | "listo" | "entregado";
};

type ControlResponse = {
  pedido_id: number;
  pendientes: ItemControl[];
  listos_no_entregados: ItemControl[];
  entregados: ItemControl[];
};

type Producto = {
  id: number;
  nombre: string;
  precio: number;
  categoria: string | null;
  area: "cocina" | "barra";
  incluye_entrada: boolean;
};
type ProductoTab = "menu" | "segundo" | "carta" | "bebidas";

const SALONES = ["Salon", "Terraza", "Segundo Piso"] as const;
const MESAS = Array.from({ length: 20 }, (_, i) => ({ id: i + 1 }));

export default function Home() {
  const apiBase = useMemo(() => {
    if (process.env.NEXT_PUBLIC_API_URL) return process.env.NEXT_PUBLIC_API_URL;
    if (typeof window !== "undefined") {
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return "http://127.0.0.1:8000";
  }, []);

  const [salon, setSalon] = useState<(typeof SALONES)[number]>("Salon");
  const [selectedMesaId, setSelectedMesaId] = useState<number | null>(null);
  const [loadingMesaId, setLoadingMesaId] = useState<number | null>(null);
  const [loadingControl, setLoadingControl] = useState(false);
  const [sendingKitchen, setSendingKitchen] = useState(false);

  const [mensaje, setMensaje] = useState<string>("");
  const [error, setError] = useState<string>("");

  const [pedidoByMesa, setPedidoByMesa] = useState<Record<number, number>>({});
  const [control, setControl] = useState<ControlResponse | null>(null);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [showAgregar, setShowAgregar] = useState(false);
  const [savingItem, setSavingItem] = useState(false);
  const [tabProducto, setTabProducto] = useState<ProductoTab>("menu");
  const [formProductoId, setFormProductoId] = useState<number | null>(null);
  const [formEntradaId, setFormEntradaId] = useState<number | null>(null);
  const [formCantidad, setFormCantidad] = useState(1);
  const [formTipoConsumo, setFormTipoConsumo] = useState<"local" | "llevar" | "delivery">("local");

  const pedidoSeleccionadoId = selectedMesaId ? pedidoByMesa[selectedMesaId] ?? null : null;
  const itemsActuales = control
    ? [...control.pendientes, ...control.listos_no_entregados, ...control.entregados]
    : [];
  const total = itemsActuales.reduce((acc, item) => acc + item.precio_unitario * item.cantidad, 0);

  const filtrarProductosPorTab = (tab: ProductoTab): Producto[] => {
    if (tab === "menu") {
      return productos.filter(
        (p) => p.nombre.toLowerCase().includes("menu del dia") || p.incluye_entrada,
      );
    }
    if (tab === "segundo") {
      return productos.filter(
        (p) => p.categoria?.toLowerCase() === "fondo" && !p.nombre.toLowerCase().includes("menu del dia"),
      );
    }
    if (tab === "carta") {
      return productos.filter((p) => p.categoria?.toLowerCase() === "adicional");
    }
    return productos.filter((p) => p.area === "barra" || p.categoria?.toLowerCase() === "bebida");
  };

  const productosTab = filtrarProductosPorTab(tabProducto);
  const entradasMenu = productos.filter((p) => {
    const n = p.nombre.toLowerCase();
    return n.includes("sopa") || n.includes("huancaina") || n.includes("choclo") || n.includes("humita");
  });

  useEffect(() => {
    const cargarProductos = async () => {
      try {
        const resp = await fetch(`${apiBase}/productos`);
        const data = await resp.json();
        if (!resp.ok) {
          throw new Error(data?.detail ?? "No se pudo cargar productos");
        }
        setProductos(data);
        if (data.length > 0) setFormProductoId(data[0].id);
      } catch {
        setError("No se pudo cargar el catalogo de productos");
      }
    };

    cargarProductos();
  }, [apiBase]);

  useEffect(() => {
    if (productosTab.length > 0) {
      setFormProductoId(productosTab[0].id);
    } else {
      setFormProductoId(null);
    }
  }, [tabProducto, productos.length]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (entradasMenu.length > 0 && formEntradaId === null) {
      setFormEntradaId(entradasMenu[0].id);
    }
  }, [entradasMenu, formEntradaId]);

  const abrirPedido = async (mesaId: number) => {
    setLoadingMesaId(mesaId);
    setMensaje("");
    setError("");

    try {
      const resp = await fetch(`${apiBase}/pedidos/abrir`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mesa_id: mesaId }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data?.detail ?? "No se pudo abrir el pedido");
      }

      setPedidoByMesa((prev) => ({ ...prev, [mesaId]: data.id }));
      setSelectedMesaId(mesaId);
      setMensaje(`Mesa ${mesaId}: pedido #${data.id} activo`);
      await cargarControl(data.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de conexion con backend");
    } finally {
      setLoadingMesaId(null);
    }
  };

  const seleccionarMesa = async (mesaId: number) => {
    // Toggle: click again to deselect table.
    if (selectedMesaId === mesaId) {
      setPedidoByMesa((prev) => {
        const next = { ...prev };
        delete next[mesaId];
        return next;
      });
      setSelectedMesaId(null);
      setControl(null);
      setMensaje(`Mesa ${mesaId} deseleccionada`);
      setError("");
      return;
    }

    setSelectedMesaId(mesaId);
    setMensaje("");
    setError("");

    const pedidoExistente = pedidoByMesa[mesaId];
    if (pedidoExistente) {
      await cargarControl(pedidoExistente);
      return;
    }

    await abrirPedido(mesaId);
  };

  const cargarControl = async (pedidoId: number) => {
    setLoadingControl(true);
    try {
      const resp = await fetch(`${apiBase}/pedidos/${pedidoId}/control`);
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data?.detail ?? "No se pudo cargar el control del pedido");
      }
      setControl(data);
    } catch (e) {
      setControl(null);
      setError(e instanceof Error ? e.message : "Error cargando el control");
    } finally {
      setLoadingControl(false);
    }
  };

  const enviarACocina = async () => {
    if (!pedidoSeleccionadoId) return;
    setSendingKitchen(true);
    setMensaje("");
    setError("");
    try {
      const resp = await fetch(`${apiBase}/pedidos/enviar-cocina`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pedido_id: pedidoSeleccionadoId }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data?.detail ?? "No se pudo enviar a cocina");
      }
      setMensaje(`Enviado a cocina: ${data.items_enviados} item(s)`);
      await cargarControl(pedidoSeleccionadoId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error enviando a cocina");
    } finally {
      setSendingKitchen(false);
    }
  };

  const agregarProducto = async () => {
    if (!pedidoSeleccionadoId || !formProductoId) {
      setError("Selecciona una mesa con pedido y un producto");
      return;
    }
    if (tabProducto === "menu" && !formEntradaId) {
      setError("Para Menu debes seleccionar una entrada");
      return;
    }

    setSavingItem(true);
    setMensaje("");
    setError("");

    try {
      const resp = await fetch(`${apiBase}/pedido-items/agregar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pedido_id: pedidoSeleccionadoId,
          producto_id: formProductoId,
          cantidad: formCantidad,
          tipo_consumo: formTipoConsumo,
          entrada_producto_id: tabProducto === "menu" ? formEntradaId : null,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data?.detail ?? "No se pudo agregar el producto");
      }

      setMensaje(`Producto agregado (${data.items_creados?.length ?? 1} item(s))`);
      setShowAgregar(false);
      await cargarControl(pedidoSeleccionadoId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error agregando producto");
    } finally {
      setSavingItem(false);
    }
  };

  const eliminarProducto = async (itemId: number) => {
    if (!pedidoSeleccionadoId) return;
    setMensaje("");
    setError("");
    try {
      const resp = await fetch(`${apiBase}/pedido-items/eliminar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pedido_item_id: itemId }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data?.detail ?? "No se pudo retirar el item");
      }
      setMensaje(`Item retirado: ${data.producto_nombre}`);
      await cargarControl(pedidoSeleccionadoId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error retirando item");
    }
  };

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#1d2735_0%,#f0f2f5_140px,#eef1f6_100%)] px-3 py-3 md:px-6 md:py-5">
      <div className="mx-auto max-w-[1400px] overflow-hidden rounded-2xl border border-slate-300 bg-white/90 shadow-2xl shadow-slate-900/15 backdrop-blur">
        <header className="flex items-center justify-between border-b border-slate-300 bg-slate-100 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="rounded bg-amber-400 px-3 py-1 text-lg font-black tracking-wide text-slate-900">RPRO</div>
            <p className="text-sm font-semibold text-slate-700 md:text-base">Restaurant Pro | Mesas</p>
          </div>
          <div className="hidden text-sm font-medium text-slate-500 md:block">Turno activo</div>
        </header>

        <div className="grid min-h-[78vh] grid-cols-1 lg:grid-cols-[1fr_360px]">
          <section className="border-b border-slate-300 p-4 lg:border-b-0 lg:border-r">
            <div className="mb-4 flex flex-wrap gap-2">
              {SALONES.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setSalon(item)}
                  className={`rounded-md px-3 py-1.5 text-sm font-semibold transition ${
                    salon === item
                      ? "bg-slate-800 text-white shadow"
                      : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  {item}
                </button>
              ))}
            </div>

            {mensaje ? (
              <div className="mb-3 rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
                {mensaje}
              </div>
            ) : null}
            {error ? (
              <div className="mb-3 rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
                {error}
              </div>
            ) : null}

            <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-5">
              {MESAS.map((mesa) => {
                const ocupada = Boolean(pedidoByMesa[mesa.id]);
                const isSelected = mesa.id === selectedMesaId;
                return (
                  <button
                    key={mesa.id}
                    type="button"
                    onClick={() => seleccionarMesa(mesa.id)}
                    disabled={loadingMesaId !== null}
                    className={`rounded-xl border px-3 py-5 text-center font-bold text-white shadow-md transition ${
                      ocupada
                        ? "border-rose-600 bg-rose-500 hover:bg-rose-600"
                        : "border-emerald-600 bg-emerald-500 hover:bg-emerald-600"
                    } ${isSelected ? "ring-4 ring-cyan-200" : ""} ${loadingMesaId !== null ? "opacity-90" : ""}`}
                  >
                    <div className="text-2xl leading-none">{mesa.id}</div>
                    <div className="mt-1 text-xs font-semibold uppercase tracking-wide">
                      {loadingMesaId === mesa.id ? "Abriendo..." : ocupada ? "Ocupada" : "Libre"}
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          <aside className="bg-slate-50 p-4">
            <div className="mb-2 flex items-end justify-between">
              <h2 className="text-3xl font-bold text-slate-900">
                Mesa {selectedMesaId ?? "-"}
              </h2>
              <button
                type="button"
                disabled={!pedidoSeleccionadoId || loadingControl}
                onClick={() => pedidoSeleccionadoId && cargarControl(pedidoSeleccionadoId)}
                className="rounded bg-slate-200 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-300 disabled:opacity-60"
              >
                Refrescar
              </button>
            </div>

            <div className="mb-3">
              <button
                type="button"
                disabled={selectedMesaId === null}
                onClick={() => {
                  if (selectedMesaId !== null) {
                    setPedidoByMesa((prev) => {
                      const next = { ...prev };
                      delete next[selectedMesaId];
                      return next;
                    });
                    setSelectedMesaId(null);
                    setControl(null);
                    setMensaje("Mesa deseleccionada");
                    setError("");
                  }
                }}
                className="rounded bg-slate-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
              >
                Deseleccionar mesa
              </button>
            </div>

            <div className="mb-3 rounded-lg border border-slate-300 bg-white p-3">
              <p className="text-sm text-slate-600">
                Pedido:{" "}
                <span className="font-semibold text-slate-900">
                  {pedidoSeleccionadoId ? `#${pedidoSeleccionadoId}` : "Sin abrir"}
                </span>
              </p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
                <span className="rounded bg-amber-100 px-2 py-1 text-amber-700">
                  Pendientes: {control?.pendientes.length ?? 0}
                </span>
                <span className="rounded bg-sky-100 px-2 py-1 text-sky-700">
                  Listos: {control?.listos_no_entregados.length ?? 0}
                </span>
                <span className="rounded bg-emerald-100 px-2 py-1 text-emerald-700">
                  Entregados: {control?.entregados.length ?? 0}
                </span>
              </div>
            </div>

            <div className="max-h-[340px] overflow-auto rounded-lg border border-slate-300 bg-white">
              <div className="border-b border-slate-200 px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                Items del pedido
              </div>
              {loadingControl ? (
                <p className="px-3 py-4 text-sm text-slate-500">Cargando control...</p>
              ) : itemsActuales.length === 0 ? (
                <p className="px-3 py-4 text-sm text-slate-500">Todavia no hay items en este pedido.</p>
              ) : (
                <ul className="divide-y divide-slate-200">
                  {itemsActuales.map((item) => (
                    <li key={item.id} className="px-3 py-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold text-slate-800">{item.producto_nombre}</p>
                          <p className="text-xs text-slate-500">
                            x{item.cantidad} | S/ {item.precio_unitario.toFixed(2)} | {item.area} | {item.estado_item}
                          </p>
                        </div>
                        {item.estado_item === "pendiente" ? (
                          <button
                            type="button"
                            onClick={() => eliminarProducto(item.id)}
                            className="rounded bg-rose-100 px-2 py-1 text-[11px] font-semibold text-rose-700 hover:bg-rose-200"
                          >
                            Retirar
                          </button>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mt-4 rounded-lg border border-slate-300 bg-white p-3">
              <div className="mb-3 flex items-center justify-between text-xl font-bold text-slate-900">
                <span>Total</span>
                <span>S/ {total.toFixed(2)}</span>
              </div>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => setShowAgregar((prev) => !prev)}
                  disabled={!pedidoSeleccionadoId}
                  className="w-full rounded-md bg-orange-500 px-4 py-2.5 text-left font-semibold text-white shadow hover:bg-orange-600"
                >
                  + Agregar producto
                </button>
                {showAgregar ? (
                  <div className="space-y-2 rounded-md border border-orange-200 bg-orange-50 p-3">
                    <div className="grid grid-cols-4 gap-1 rounded bg-amber-100 p-1 text-[11px] font-bold text-slate-700">
                      <button
                        type="button"
                        onClick={() => setTabProducto("menu")}
                        className={`rounded px-1 py-1 ${tabProducto === "menu" ? "bg-white text-slate-900" : ""}`}
                      >
                        Menu
                      </button>
                      <button
                        type="button"
                        onClick={() => setTabProducto("segundo")}
                        className={`rounded px-1 py-1 ${tabProducto === "segundo" ? "bg-white text-slate-900" : ""}`}
                      >
                        Segundo
                      </button>
                      <button
                        type="button"
                        onClick={() => setTabProducto("carta")}
                        className={`rounded px-1 py-1 ${tabProducto === "carta" ? "bg-white text-slate-900" : ""}`}
                      >
                        Carta
                      </button>
                      <button
                        type="button"
                        onClick={() => setTabProducto("bebidas")}
                        className={`rounded px-1 py-1 ${tabProducto === "bebidas" ? "bg-white text-slate-900" : ""}`}
                      >
                        Bebidas
                      </button>
                    </div>
                    <label className="block text-xs font-semibold text-slate-700">
                      Producto
                      <select
                        className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
                        value={formProductoId ?? ""}
                        onChange={(e) => setFormProductoId(Number(e.target.value))}
                      >
                        {productosTab.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.nombre} | S/ {p.precio.toFixed(2)}
                          </option>
                        ))}
                      </select>
                    </label>
                    {tabProducto === "menu" ? (
                      <label className="block text-xs font-semibold text-slate-700">
                        Entrada (obligatoria para menu)
                        <select
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
                          value={formEntradaId ?? ""}
                          onChange={(e) => setFormEntradaId(Number(e.target.value))}
                        >
                          {entradasMenu.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.nombre}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                    <div className="grid grid-cols-2 gap-2">
                      <label className="block text-xs font-semibold text-slate-700">
                        Cantidad
                        <input
                          type="number"
                          min={1}
                          value={formCantidad}
                          onChange={(e) => setFormCantidad(Math.max(1, Number(e.target.value) || 1))}
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
                        />
                      </label>
                      <label className="block text-xs font-semibold text-slate-700">
                        Consumo
                        <select
                          className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
                          value={formTipoConsumo}
                          onChange={(e) => setFormTipoConsumo(e.target.value as "local" | "llevar" | "delivery")}
                        >
                          <option value="local">Local</option>
                          <option value="llevar">Llevar</option>
                          <option value="delivery">Delivery</option>
                        </select>
                      </label>
                    </div>
                    <button
                      type="button"
                      onClick={agregarProducto}
                      disabled={savingItem}
                      className="w-full rounded bg-orange-600 px-3 py-2 text-sm font-semibold text-white hover:bg-orange-700 disabled:opacity-60"
                    >
                      {savingItem ? "Agregando..." : "Confirmar agregado"}
                    </button>
                  </div>
                ) : null}
                <button
                  type="button"
                  onClick={enviarACocina}
                  disabled={!pedidoSeleccionadoId || sendingKitchen}
                  className="w-full rounded-md bg-emerald-500 px-4 py-2.5 text-left font-semibold text-white shadow hover:bg-emerald-600 disabled:opacity-60"
                >
                  {sendingKitchen ? "Enviando..." : "Enviar a cocina"}
                </button>
                <button
                  type="button"
                  className="w-full rounded-md bg-slate-800 px-4 py-2.5 text-left font-semibold text-white shadow hover:bg-slate-900"
                >
                  Cobrar
                </button>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}
