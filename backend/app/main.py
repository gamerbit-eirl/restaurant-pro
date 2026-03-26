from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.api import pedidos_router
from app.db.connection import Base, engine

# Ensure metadata is loaded before create_all.
from app.models import Mesa, Pedido, PedidoItem, Producto  # noqa: F401

app = FastAPI(title="Restaurant Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(pedidos_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Restaurant Pro funcionando"}
