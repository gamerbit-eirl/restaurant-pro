from fastapi import FastAPI
from app.db.connection import engine, Base

# importar modelos
from app.models import mesa, producto, pedido, pedido_item

app = FastAPI(title="Restaurant Pro API")

# crear tablas
Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Restaurant Pro funcionando 🔥"}