from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.db.connection import Base

AREA_ENUM = Enum("cocina", "barra", name="area_enum", native_enum=False)


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    categoria = Column(String(50), nullable=True)
    area = Column(AREA_ENUM, nullable=False, default="cocina")
    control_stock = Column(Boolean, nullable=False, default=False)

    incluye_entrada = Column(Boolean, nullable=False, default=False)
    entrada_producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)

    entrada_producto = relationship("Producto", remote_side=[id], uselist=False)
    items = relationship("PedidoItem", back_populates="producto")
