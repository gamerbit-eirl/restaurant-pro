from sqlalchemy import Column, Integer, String, Float
from app.db.connection import Base


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255))
    precio = Column(Float)

    categoria = Column(String(50))  # fondo, entrada, bebida
    area = Column(String(50))       # cocina, barra

    control_stock = Column(Integer, default=0)