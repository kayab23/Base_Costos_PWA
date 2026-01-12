"""Punto de entrada para FastAPI."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import catalog, pricing, auth

app = FastAPI(title=settings.api_title, version=settings.api_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(pricing.router)

start_time = datetime.now(timezone.utc)


@app.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "uptime_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "default_transporte": settings.default_transporte,
        "default_monedas": settings.default_monedas,
    }
