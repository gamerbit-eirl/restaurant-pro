from sqlalchemy import Column, Integer, String
from app.db.connection import Base


class Mesa(Base):
    __tablename__ = "mesas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)
    estado = Column(String(20), default="libre")  # libre, ocupada