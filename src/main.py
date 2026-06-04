import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.adapters.seed import seed_database
from src.infrastructure.api.auth_router import router as auth_router
from src.infrastructure.api.middleware import RequestLoggingMiddleware
from src.infrastructure.api.orders_router import router as orders_router
from src.infrastructure.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title=settings.app_title,
    version="1.0.0",
    description="Servicio de órdenes — Proyecto final Python Complete",
)

# Middleware El último agregado se ejecuta primero
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Routers
app.include_router(auth_router)
app.include_router(orders_router)


@app.on_event("startup")
def on_startup():
    seed_database()


@app.get("/")
def root():
    return {
        "message": f"{settings.app_title} funcionando",
        "docs": "/docs",
    }
