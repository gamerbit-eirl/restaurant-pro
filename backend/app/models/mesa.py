from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.connection import Base


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False, index=True)
    estado = Column(String(20), nullable=False, default="libre")

    pedidos = relationship("Pedido", back_populates="mesa")
