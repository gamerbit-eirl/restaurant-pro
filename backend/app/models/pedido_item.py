from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from datetime import datetime
from app.db.connection import Base


class PedidoItem(Base):
    __tablename__ = "pedido_items"

    id = Column(Integer, primary_key=True, index=True)

    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    cantidad = Column(Integer)
    precio_unitario = Column(Float)

    # 🔥 clave de tu sistema
    tipo_consumo = Column(String(20))  # local, llevar, delivery

    # 🔥 flujo cocina
    estado_item = Column(String(20), default="pendiente")
    # pendiente, enviado_cocina, preparando, listo

    hora_envio_cocina = Column(DateTime, nullable=True)
    hora_listo = Column(DateTime, nullable=True)