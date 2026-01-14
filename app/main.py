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
import threading
from fastapi import Response
from .db import connection_scope

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


# Variables para métricas simples
start_time = datetime.now(timezone.utc)
metrics = {
    'requests_total': 0,
    'errors_total': 0,
    'last_error': '',
}
metrics_lock = threading.Lock()



@app.get("/health")
def healthcheck():
    db_status = "ok"
    db_error = None
    try:
        with connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_status = "error"
        db_error = str(e)
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db_status": db_status,
        "db_error": db_error,
        "uptime_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "default_transporte": settings.default_transporte,
        "default_monedas": settings.default_monedas,
    }


# Middleware para contar peticiones y errores
@app.middleware("http")
async def metrics_middleware(request, call_next):
    with metrics_lock:
        metrics['requests_total'] += 1
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        with metrics_lock:
            metrics['errors_total'] += 1
            metrics['last_error'] = str(e)
        raise


@app.get("/metrics")
def metrics_endpoint():
    """Endpoint Prometheus-like para métricas básicas."""
    with metrics_lock:
        lines = [
            f"requests_total {metrics['requests_total']}",
            f"errors_total {metrics['errors_total']}",
            f"uptime_seconds {(datetime.now(timezone.utc) - start_time).total_seconds():.0f}",
        ]
        if metrics['last_error']:
            lines.append(f"last_error \"{metrics['last_error']}\"")
    return Response("\n".join(lines), media_type="text/plain")
