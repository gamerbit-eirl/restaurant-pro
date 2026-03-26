from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Mesa, Pedido, PedidoItem, Producto
from app.schemas.pedidos import CocinaPedidoItemOut, PedidoItemOut, ProductoOut


def _decimal_to_float(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def _item_to_out(item: PedidoItem) -> PedidoItemOut:
    return PedidoItemOut(
        id=item.id,
        pedido_id=item.pedido_id,
        producto_id=item.producto_id,
        producto_nombre=item.producto.nombre if item.producto else "",
        cantidad=item.cantidad,
        precio_unitario=_decimal_to_float(item.precio_unitario),
        tipo_consumo=item.tipo_consumo,
        area=item.area,
        estado_item=item.estado_item,
    )


def _producto_to_out(producto: Producto) -> ProductoOut:
    return ProductoOut(
        id=producto.id,
        nombre=producto.nombre,
        precio=_decimal_to_float(producto.precio),
        categoria=producto.categoria,
        area=producto.area,
        incluye_entrada=producto.incluye_entrada,
    )


def listar_productos(db: Session) -> list[ProductoOut]:
    productos = db.scalars(select(Producto).order_by(Producto.nombre.asc())).all()
    return [_producto_to_out(producto) for producto in productos]


def abrir_pedido(db: Session, mesa_id: int) -> Pedido:
    mesa = db.get(Mesa, mesa_id)
    if not mesa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mesa no existe")

    pedido_abierto = db.scalar(
        select(Pedido)
        .where(Pedido.mesa_id == mesa_id, Pedido.estado == "abierto")
        .order_by(Pedido.id.desc())
    )
    if pedido_abierto:
        return pedido_abierto

    pedido = Pedido(mesa_id=mesa_id, mesa_activa=mesa_id, estado="abierto")
    db.add(pedido)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        pedido_existente = db.scalar(
            select(Pedido)
            .where(Pedido.mesa_id == mesa_id, Pedido.estado == "abierto")
            .order_by(Pedido.id.desc())
        )
        if pedido_existente:
            return pedido_existente
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La mesa ya tiene un pedido activo",
        )

    db.refresh(pedido)
    return pedido


def agregar_item(
    db: Session,
    pedido_id: int,
    producto_id: int,
    cantidad: int,
    tipo_consumo: str,
    entrada_producto_id: int | None = None,
) -> list[PedidoItem]:
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no existe")
    if pedido.estado != "abierto":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pedido cerrado")

    producto = db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no existe")

    creados: list[PedidoItem] = []

    principal = PedidoItem(
        pedido_id=pedido_id,
        producto_id=producto.id,
        cantidad=cantidad,
        precio_unitario=producto.precio,
        tipo_consumo=tipo_consumo,
        area=producto.area,
        estado_item="pendiente",
    )
    db.add(principal)
    creados.append(principal)

    entrada_id = entrada_producto_id or producto.entrada_producto_id
    if (producto.incluye_entrada or entrada_producto_id is not None) and entrada_id:
        entrada = db.get(Producto, entrada_id)
        if entrada:
            entrada_item = PedidoItem(
                pedido_id=pedido_id,
                producto_id=entrada.id,
                cantidad=cantidad,
                precio_unitario=entrada.precio,
                tipo_consumo=tipo_consumo,
                area=entrada.area,
                estado_item="pendiente",
            )
            db.add(entrada_item)
            creados.append(entrada_item)

    db.commit()
    for item in creados:
        db.refresh(item)
        _ = item.producto
    return creados


def generar_ticket_texto(pedido: Pedido, items: list[PedidoItem]) -> str:
    mesa = pedido.mesa.numero if pedido.mesa else pedido.mesa_id

    grupos: dict[str, dict[str, list[str]]] = {
        "cocina": {"local": [], "llevar": [], "delivery": []},
        "barra": {"local": [], "llevar": [], "delivery": []},
    }

    for item in items:
        nombre = item.producto.nombre if item.producto else f"Producto #{item.producto_id}"
        etiqueta = f"- {nombre} x{item.cantidad}"
        grupos[item.area][item.tipo_consumo].append(etiqueta)

    lineas = [f"Mesa {mesa}", "----------------"]

    for area in ("cocina", "barra"):
        if any(grupos[area][tc] for tc in ("local", "llevar", "delivery")):
            lineas.append(area.upper() + ":")
            for tipo in ("local", "llevar", "delivery"):
                if grupos[area][tipo]:
                    lineas.append(tipo.upper() + ":")
                    lineas.extend(grupos[area][tipo])
            lineas.append("")

    lineas.append("----------------")
    lineas.append(f"Hora: {datetime.now().strftime('%H:%M')}")
    return "\n".join(lineas).strip()


def enviar_a_cocina(db: Session, pedido_id: int) -> tuple[int, str]:
    pedido = db.scalar(
        select(Pedido)
        .where(Pedido.id == pedido_id)
        .options(joinedload(Pedido.mesa), joinedload(Pedido.items).joinedload(PedidoItem.producto))
    )
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no existe")

    pendientes = [item for item in pedido.items if item.estado_item == "pendiente"]
    if not pendientes:
        return 0, ""

    ahora = datetime.utcnow()
    for item in pendientes:
        item.estado_item = "enviado_cocina"
        item.hora_envio_cocina = ahora

    db.commit()
    for item in pendientes:
        db.refresh(item)
        _ = item.producto

    return len(pendientes), generar_ticket_texto(pedido, pendientes)


def listar_cocina(db: Session) -> list[dict]:
    items = db.scalars(
        select(PedidoItem)
        .where(PedidoItem.estado_item.in_(("enviado_cocina", "preparando")))
        .options(
            joinedload(PedidoItem.producto),
            joinedload(PedidoItem.pedido).joinedload(Pedido.mesa),
        )
        .order_by(PedidoItem.pedido_id, PedidoItem.id)
    ).all()

    agrupado: dict[int, list[PedidoItem]] = defaultdict(list)
    for item in items:
        agrupado[item.pedido_id].append(item)

    salida: list[dict] = []
    for pedido_id, grupo_items in agrupado.items():
        pedido = grupo_items[0].pedido
        items_por_area_tipo: dict[str, dict[str, list[CocinaPedidoItemOut]]] = {
            "cocina": {"local": [], "llevar": [], "delivery": []},
            "barra": {"local": [], "llevar": [], "delivery": []},
        }

        items_out: list[CocinaPedidoItemOut] = []
        for item in grupo_items:
            item_out = CocinaPedidoItemOut(
                item_id=item.id,
                producto=item.producto.nombre if item.producto else "",
                cantidad=item.cantidad,
                tipo_consumo=item.tipo_consumo,
                area=item.area,
                estado_item=item.estado_item,
            )
            items_out.append(item_out)
            items_por_area_tipo[item.area][item.tipo_consumo].append(item_out)

        salida.append(
            {
                "pedido_id": pedido_id,
                "mesa_id": pedido.mesa_id,
                "items": items_out,
                "items_por_area_tipo": items_por_area_tipo,
                "ticket_texto": generar_ticket_texto(pedido, grupo_items),
            }
        )

    return salida


def marcar_listo(db: Session, pedido_item_id: int) -> PedidoItem:
    item = db.scalar(
        select(PedidoItem)
        .where(PedidoItem.id == pedido_item_id)
        .options(joinedload(PedidoItem.producto))
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no existe")
    if item.estado_item != "enviado_cocina":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo items enviados a cocina pueden marcarse como listos",
        )

    item.estado_item = "listo"
    item.hora_listo = datetime.utcnow()
    db.commit()
    db.refresh(item)
    _ = item.producto
    return item


def marcar_entregado(db: Session, pedido_item_id: int) -> PedidoItem:
    item = db.scalar(
        select(PedidoItem)
        .where(PedidoItem.id == pedido_item_id)
        .options(joinedload(PedidoItem.producto))
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no existe")
    if item.estado_item != "listo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo items listos pueden entregarse",
        )

    item.estado_item = "entregado"
    item.hora_entrega = datetime.utcnow()
    db.commit()
    db.refresh(item)
    _ = item.producto
    return item


def eliminar_item(db: Session, pedido_item_id: int) -> PedidoItemOut:
    item = db.scalar(
        select(PedidoItem)
        .where(PedidoItem.id == pedido_item_id)
        .options(joinedload(PedidoItem.producto))
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no existe")
    if item.estado_item != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden retirar items pendientes",
        )

    out = _item_to_out(item)
    db.delete(item)
    db.commit()
    return out


def control_pedido(db: Session, pedido_id: int) -> dict[str, list[PedidoItemOut] | int]:
    pedido = db.scalar(
        select(Pedido)
        .where(Pedido.id == pedido_id)
        .options(joinedload(Pedido.items).joinedload(PedidoItem.producto))
    )
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no existe")

    pendientes = [_item_to_out(i) for i in pedido.items if i.estado_item == "pendiente"]
    listos_no_entregados = [_item_to_out(i) for i in pedido.items if i.estado_item == "listo"]
    entregados = [_item_to_out(i) for i in pedido.items if i.estado_item == "entregado"]

    return {
        "pedido_id": pedido.id,
        "pendientes": pendientes,
        "listos_no_entregados": listos_no_entregados,
        "entregados": entregados,
    }
