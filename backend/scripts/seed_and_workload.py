from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text

from app.db.connection import SessionLocal
from app.models import Mesa, Pedido, PedidoItem, Producto
from app.services.pedidos_service import agregar_item, enviar_a_cocina, marcar_entregado, marcar_listo


@dataclass(frozen=True)
class ProductoSeed:
    nombre: str
    precio: Decimal
    categoria: str
    area: str
    control_stock: bool
    incluye_entrada: bool = False
    entrada_ref: str | None = None


SEED_PRODUCTOS = [
    # Entradas base
    ProductoSeed("Entrada del dia", Decimal("0.00"), "entrada", "cocina", False),
    ProductoSeed("Torta de choclo (entrada)", Decimal("0.00"), "entrada", "cocina", False),
    # Menu del dia (con entrada automatica)
    ProductoSeed("Chanfainita (menu del dia)", Decimal("10.00"), "fondo", "cocina", False, True, "Entrada del dia"),
    ProductoSeed("Cau-cau (menu del dia)", Decimal("10.00"), "fondo", "cocina", False, True, "Entrada del dia"),
    ProductoSeed("Bistec a lo pobre (menu del dia)", Decimal("12.00"), "fondo", "cocina", False, True, "Entrada del dia"),
    ProductoSeed("Tortilla de raya (menu del dia)", Decimal("12.00"), "fondo", "cocina", False, True, "Entrada del dia"),
    ProductoSeed("Seco de res (menu del dia)", Decimal("15.00"), "fondo", "cocina", False, True, "Entrada del dia"),
    # Adicionales (sin entrada)
    ProductoSeed("Papa rellena", Decimal("6.00"), "adicional", "cocina", False, False, None),
    ProductoSeed("Papa a la huancaina", Decimal("7.00"), "adicional", "cocina", False, False, None),
    ProductoSeed("Torta de choclo (adicional)", Decimal("7.00"), "adicional", "cocina", False, False, None),
    ProductoSeed("Ceviche (adicional)", Decimal("18.00"), "adicional", "cocina", False, False, None),
    # Barra para probar separacion KDS
    ProductoSeed("Inka Cola personal", Decimal("4.50"), "bebida", "barra", True, False, None),
    ProductoSeed("Chicha morada", Decimal("5.00"), "bebida", "barra", True, False, None),
]


def upsert_mesas(total_mesas: int) -> None:
    with SessionLocal() as db:
        existentes = {m.numero: m for m in db.scalars(select(Mesa)).all()}
        nuevos = 0
        for numero in range(1, total_mesas + 1):
            if numero not in existentes:
                db.add(Mesa(numero=numero, estado="libre"))
                nuevos += 1
        db.commit()
        print(f"Mesas listas: {total_mesas} (nuevas={nuevos})")


def _column_exists(db, table_name: str, column_name: str) -> bool:
    value = db.scalar(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return bool(value)


def ensure_schema_compatible() -> None:
    with SessionLocal() as db:
        statements: list[str] = []

        if not _column_exists(db, "productos", "incluye_entrada"):
            statements.append("ALTER TABLE productos ADD COLUMN incluye_entrada TINYINT(1) NOT NULL DEFAULT 0")
        if not _column_exists(db, "productos", "entrada_producto_id"):
            statements.append("ALTER TABLE productos ADD COLUMN entrada_producto_id INT NULL")
        if not _column_exists(db, "productos", "area"):
            statements.append("ALTER TABLE productos ADD COLUMN area VARCHAR(20) NOT NULL DEFAULT 'cocina'")
        if not _column_exists(db, "productos", "control_stock"):
            statements.append("ALTER TABLE productos ADD COLUMN control_stock TINYINT(1) NOT NULL DEFAULT 0")

        if not _column_exists(db, "pedidos", "mesa_activa"):
            statements.append("ALTER TABLE pedidos ADD COLUMN mesa_activa INT NULL UNIQUE")

        if not _column_exists(db, "pedido_items", "area"):
            statements.append("ALTER TABLE pedido_items ADD COLUMN area VARCHAR(20) NOT NULL DEFAULT 'cocina'")
        if not _column_exists(db, "pedido_items", "hora_entrega"):
            statements.append("ALTER TABLE pedido_items ADD COLUMN hora_entrega DATETIME NULL")
        if not _column_exists(db, "pedido_items", "creado_en"):
            statements.append(
                "ALTER TABLE pedido_items ADD COLUMN creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
            )

        # Keep types aligned with current models when possible.
        statements.extend(
            [
                "ALTER TABLE productos MODIFY COLUMN precio DECIMAL(10,2) NOT NULL",
                "ALTER TABLE pedido_items MODIFY COLUMN precio_unitario DECIMAL(10,2) NOT NULL",
                "ALTER TABLE pedido_items MODIFY COLUMN tipo_consumo VARCHAR(20) NOT NULL",
                "ALTER TABLE pedido_items MODIFY COLUMN estado_item VARCHAR(20) NOT NULL DEFAULT 'pendiente'",
            ]
        )

        for stmt in statements:
            try:
                db.execute(text(stmt))
            except Exception:
                # Continue to maximize compatibility across existing local schemas.
                pass

        db.commit()


def upsert_productos() -> dict[str, int]:
    with SessionLocal() as db:
        by_name = {p.nombre: p for p in db.scalars(select(Producto)).all()}

        for seed in SEED_PRODUCTOS:
            prod = by_name.get(seed.nombre)
            if not prod:
                prod = Producto(
                    nombre=seed.nombre,
                    precio=seed.precio,
                    categoria=seed.categoria,
                    area=seed.area,
                    control_stock=seed.control_stock,
                    incluye_entrada=seed.incluye_entrada,
                )
                db.add(prod)
                db.flush()
                by_name[seed.nombre] = prod
            else:
                prod.precio = seed.precio
                prod.categoria = seed.categoria
                prod.area = seed.area
                prod.control_stock = seed.control_stock
                prod.incluye_entrada = seed.incluye_entrada

        for seed in SEED_PRODUCTOS:
            if seed.entrada_ref:
                prod = by_name[seed.nombre]
                entrada = by_name[seed.entrada_ref]
                prod.entrada_producto_id = entrada.id

        db.commit()
        return {name: prod.id for name, prod in by_name.items()}


def _cerrar_pedido(db, pedido: Pedido, fecha_base: datetime) -> None:
    pedido.estado = "cerrado"
    pedido.fecha_cierre = fecha_base + timedelta(minutes=random.randint(10, 90))
    pedido.mesa_activa = None


def generar_carga(ordenes: int, min_items: int, max_items: int) -> None:
    with SessionLocal() as db:
        mesas = db.scalars(select(Mesa)).all()
        if not mesas:
            raise RuntimeError("No hay mesas. Ejecuta seed primero.")

        productos = db.scalars(select(Producto)).all()
        if not productos:
            raise RuntimeError("No hay productos. Ejecuta seed primero.")

        tipos_consumo = ["local", "llevar", "delivery"]
        creados = 0
        items_totales = 0
        enviados = 0
        listos = 0
        entregados = 0

        for _ in range(ordenes):
            mesa = random.choice(mesas)
            pedido = Pedido(
                mesa_id=mesa.id,
                mesa_activa=mesa.id,
                estado="abierto",
                fecha_apertura=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            )
            db.add(pedido)
            db.commit()
            db.refresh(pedido)

            n_items = random.randint(min_items, max_items)
            items_ids: list[int] = []
            for _ in range(n_items):
                prod = random.choice(productos)
                cantidad = random.randint(1, 3)
                tipo = random.choice(tipos_consumo)
                creados_items = agregar_item(db, pedido.id, prod.id, cantidad, tipo)
                for item in creados_items:
                    items_ids.append(item.id)
                items_totales += len(creados_items)

            total_enviados, _ = enviar_a_cocina(db, pedido.id)
            enviados += total_enviados

            for item_id in items_ids:
                item = db.get(PedidoItem, item_id)
                if not item:
                    continue
                if item.estado_item == "enviado_cocina":
                    if random.random() < 0.85:
                        marcar_listo(db, item_id)
                        listos += 1
                        if random.random() < 0.80:
                            marcar_entregado(db, item_id)
                            entregados += 1

            _cerrar_pedido(db, pedido, pedido.fecha_apertura)
            db.commit()
            creados += 1

        pendientes = db.scalar(
            select(func.count()).select_from(PedidoItem).where(PedidoItem.estado_item == "pendiente")
        )
        listos_no_entregados = db.scalar(
            select(func.count()).select_from(PedidoItem).where(PedidoItem.estado_item == "listo")
        )

    print("Carga de trabajo completada")
    print(f"Pedidos creados: {creados}")
    print(f"Items totales creados: {items_totales}")
    print(f"Items enviados cocina: {enviados}")
    print(f"Items listos: {listos}")
    print(f"Items entregados: {entregados}")
    print(f"Items pendientes (control): {pendientes}")
    print(f"Items listos no entregados (control): {listos_no_entregados}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed y carga de trabajo para Restaurant Pro")
    parser.add_argument("--mesas", type=int, default=20, help="Cantidad de mesas a crear/asegurar")
    parser.add_argument("--ordenes", type=int, default=300, help="Cantidad de pedidos para carga")
    parser.add_argument("--min-items", type=int, default=2, help="Items minimos por pedido")
    parser.add_argument("--max-items", type=int, default=6, help="Items maximos por pedido")
    parser.add_argument("--solo-seed", action="store_true", help="Solo carga catalogo y mesas")
    args = parser.parse_args()

    if args.min_items < 1 or args.max_items < args.min_items:
        raise SystemExit("Rango de items invalido")

    print("Alineando esquema de base de datos...")
    ensure_schema_compatible()
    print("Preparando datos base (mesas + catalogo)...")
    upsert_mesas(args.mesas)
    ids = upsert_productos()
    print(f"Catalogo listo: {len(ids)} productos")

    if args.solo_seed:
        print("Seed completado (sin carga de trabajo).")
        return

    print("Generando carga de trabajo...")
    generar_carga(args.ordenes, args.min_items, args.max_items)


if __name__ == "__main__":
    main()
