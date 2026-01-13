"""Punto de entrada principal para la API FastAPI del Sistema de Cálculo de Costos.

Este módulo inicializa la aplicación FastAPI y configura:
- CORS para permitir peticiones desde el frontend
- Routers para autenticación, catálogos, pricing y autorizaciones
- Endpoint de health check para monitoreo

La aplicación expone endpoints REST para:
- Gestión de usuarios y autenticación
- Consulta de productos y parámetros
- Cálculo y consulta de precios (Landed Cost, Listas de Precios)
- Gestión de solicitudes de autorización de descuentos
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import catalog, pricing, auth, autorizaciones

# Inicializar aplicación FastAPI con configuración desde settings
app = FastAPI(title=settings.api_title, version=settings.api_version)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Registrar routers de cada módulo funcional
app.include_router(auth.router)  # Autenticación y gestión de usuarios
app.include_router(catalog.router)  # Catálogos de productos y parámetros
app.include_router(pricing.router)  # Cálculos de precios y listas
app.include_router(autorizaciones.router)  # Solicitudes de autorización de descuentos

start_time = datetime.now(timezone.utc)


@app.get("/health")
def healthcheck():
    return {
        "status": "ok",
        "uptime_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "default_transporte": settings.default_transporte,
        "default_monedas": settings.default_monedas,
    }
