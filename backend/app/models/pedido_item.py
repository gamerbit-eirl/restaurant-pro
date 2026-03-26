from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.connection import Base

TIPO_CONSUMO_ENUM = Enum(
    "local",
    "llevar",
    "delivery",
    name="tipo_consumo_enum",
    native_enum=False,
)

ESTADO_ITEM_ENUM = Enum(
    "pendiente",
    "enviado_cocina",
    "preparando",
    "listo",
    "entregado",
    name="estado_item_enum",
    native_enum=False,
)

AREA_ENUM = Enum("cocina", "barra", name="area_item_enum", native_enum=False)


class PedidoItem(Base):
    __tablename__ = "pedido_items"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)

    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)

    tipo_consumo = Column(TIPO_CONSUMO_ENUM, nullable=False)
    area = Column(AREA_ENUM, nullable=False)
    estado_item = Column(ESTADO_ITEM_ENUM, nullable=False, default="pendiente", index=True)

    hora_envio_cocina = Column(DateTime, nullable=True)
    hora_listo = Column(DateTime, nullable=True)
    hora_entrega = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items")
