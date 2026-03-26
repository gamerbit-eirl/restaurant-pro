from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, status

from app.db.deps import get_db
from app.schemas.pedidos import (
    AbrirPedidoRequest,
    AgregarItemsResponse,
    CocinaPedidosResponse,
    ControlPedidoResponse,
    EnviarCocinaRequest,
    EnviarCocinaResponse,
    ItemIdRequest,
    PedidoItemAgregarRequest,
    PedidoItemOut,
    PedidoOut,
    ProductoOut,
)
from app.services.pedidos_service import (
    _item_to_out,
    abrir_pedido,
    agregar_item,
    control_pedido,
    eliminar_item,
    enviar_a_cocina,
    listar_productos,
    listar_cocina,
    marcar_entregado,
    marcar_listo,
)

router = APIRouter(tags=["Pedidos"])


@router.get("/productos", response_model=list[ProductoOut], status_code=status.HTTP_200_OK)
def listar_productos_endpoint(db: Session = Depends(get_db)) -> list[ProductoOut]:
    return listar_productos(db)


@router.post("/pedidos/abrir", response_model=PedidoOut, status_code=status.HTTP_200_OK)
def abrir_pedido_endpoint(payload: AbrirPedidoRequest, db: Session = Depends(get_db)) -> PedidoOut:
    pedido = abrir_pedido(db, mesa_id=payload.mesa_id)
    return PedidoOut(id=pedido.id, mesa_id=pedido.mesa_id, estado=pedido.estado)


@router.post("/pedido-items/agregar", response_model=AgregarItemsResponse, status_code=status.HTTP_201_CREATED)
def agregar_item_endpoint(payload: PedidoItemAgregarRequest, db: Session = Depends(get_db)) -> AgregarItemsResponse:
    items = agregar_item(
        db,
        pedido_id=payload.pedido_id,
        producto_id=payload.producto_id,
        cantidad=payload.cantidad,
        tipo_consumo=payload.tipo_consumo,
        entrada_producto_id=payload.entrada_producto_id,
    )
    return AgregarItemsResponse(
        pedido_id=payload.pedido_id,
        items_creados=[_item_to_out(item) for item in items],
    )


@router.post("/pedidos/enviar-cocina", response_model=EnviarCocinaResponse, status_code=status.HTTP_200_OK)
def enviar_cocina_endpoint(payload: EnviarCocinaRequest, db: Session = Depends(get_db)) -> EnviarCocinaResponse:
    total, ticket = enviar_a_cocina(db, pedido_id=payload.pedido_id)
    return EnviarCocinaResponse(pedido_id=payload.pedido_id, items_enviados=total, ticket_texto=ticket)


@router.get("/cocina/pedidos", response_model=CocinaPedidosResponse, status_code=status.HTTP_200_OK)
def cocina_pedidos_endpoint(db: Session = Depends(get_db)) -> CocinaPedidosResponse:
    return CocinaPedidosResponse(pedidos=listar_cocina(db))


@router.post("/pedido-items/marcar-listo", response_model=PedidoItemOut, status_code=status.HTTP_200_OK)
def marcar_listo_endpoint(payload: ItemIdRequest, db: Session = Depends(get_db)) -> PedidoItemOut:
    item = marcar_listo(db, pedido_item_id=payload.pedido_item_id)
    return _item_to_out(item)


@router.post("/pedido-items/entregar", response_model=PedidoItemOut, status_code=status.HTTP_200_OK)
def entregar_item_endpoint(payload: ItemIdRequest, db: Session = Depends(get_db)) -> PedidoItemOut:
    item = marcar_entregado(db, pedido_item_id=payload.pedido_item_id)
    return _item_to_out(item)


@router.post("/pedido-items/eliminar", response_model=PedidoItemOut, status_code=status.HTTP_200_OK)
def eliminar_item_endpoint(payload: ItemIdRequest, db: Session = Depends(get_db)) -> PedidoItemOut:
    return eliminar_item(db, pedido_item_id=payload.pedido_item_id)


@router.get("/pedidos/{pedido_id}/control", response_model=ControlPedidoResponse, status_code=status.HTTP_200_OK)
def control_pedido_endpoint(pedido_id: int, db: Session = Depends(get_db)) -> ControlPedidoResponse:
    return ControlPedidoResponse(**control_pedido(db, pedido_id=pedido_id))
