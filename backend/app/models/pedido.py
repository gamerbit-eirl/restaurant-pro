from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.connection import Base


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    mesa_id = Column(Integer, ForeignKey("mesas.id"), nullable=False, index=True)

    # DB-level guard: one active order per table.
    # Open orders store mesa_id here; closed orders set this to NULL.
    mesa_activa = Column(Integer, unique=True, nullable=True, index=True)

    estado = Column(String(20), nullable=False, default="abierto", index=True)
    fecha_apertura = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_cierre = Column(DateTime, nullable=True)

    mesa = relationship("Mesa", back_populates="pedidos")
    items = relationship(
        "PedidoItem",
        back_populates="pedido",
        cascade="all, delete-orphan",
        order_by="PedidoItem.id",
    )
