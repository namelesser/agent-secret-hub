from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import init_db
from app.routes import device, secret, sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Agent Secret Hub", version="0.1.0", lifespan=lifespan)

app.include_router(device.router)
app.include_router(secret.router)
app.include_router(sync.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

