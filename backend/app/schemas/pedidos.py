from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TipoConsumo = Literal["local", "llevar", "delivery"]
EstadoItem = Literal["pendiente", "enviado_cocina", "preparando", "listo", "entregado"]
AreaPreparacion = Literal["cocina", "barra"]


class AbrirPedidoRequest(BaseModel):
    mesa_id: int = Field(gt=0)


class PedidoItemAgregarRequest(BaseModel):
    pedido_id: int = Field(gt=0)
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0)
    tipo_consumo: TipoConsumo
    entrada_producto_id: int | None = Field(default=None, gt=0)


class EnviarCocinaRequest(BaseModel):
    pedido_id: int = Field(gt=0)


class ItemIdRequest(BaseModel):
    pedido_item_id: int = Field(gt=0)


class PedidoItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    producto_id: int
    producto_nombre: str
    cantidad: int
    precio_unitario: float
    tipo_consumo: TipoConsumo
    area: AreaPreparacion
    estado_item: EstadoItem


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mesa_id: int
    estado: str


class ProductoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    precio: float
    categoria: str | None
    area: AreaPreparacion
    incluye_entrada: bool


class AgregarItemsResponse(BaseModel):
    pedido_id: int
    items_creados: list[PedidoItemOut]


class EnviarCocinaResponse(BaseModel):
    pedido_id: int
    items_enviados: int
    ticket_texto: str


class CocinaPedidoItemOut(BaseModel):
    item_id: int
    producto: str
    cantidad: int
    tipo_consumo: TipoConsumo
    area: AreaPreparacion
    estado_item: EstadoItem


class CocinaPedidoOut(BaseModel):
    pedido_id: int
    mesa_id: int
    items: list[CocinaPedidoItemOut]
    items_por_area_tipo: dict[str, dict[str, list[CocinaPedidoItemOut]]]
    ticket_texto: str


class CocinaPedidosResponse(BaseModel):
    pedidos: list[CocinaPedidoOut]


class ControlPedidoResponse(BaseModel):
    pedido_id: int
    pendientes: list[PedidoItemOut]
    listos_no_entregados: list[PedidoItemOut]
    entregados: list[PedidoItemOut]
