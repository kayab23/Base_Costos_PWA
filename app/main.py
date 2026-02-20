
"""
Punto de entrada principal para la API FastAPI del Sistema de Cálculo de Costos.

Este módulo inicializa la aplicación FastAPI, configura CORS, registra routers y expone endpoints
para autenticación, catálogos, pricing, autorizaciones y monitoreo.
"""
from __future__ import annotations

from datetime import datetime, timezone
import threading
from fastapi import Response, FastAPI
from slowapi import _rate_limit_exceeded_handler
from app.limiter import limiter
from slowapi.errors import RateLimitExceeded
from typing import Any, cast
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .routes import catalog, pricing, auth, autorizaciones, pdf, clientes, vendedores, cotizaciones, dashboard
from .logger import logger
from .db import connection_scope

# Inicializar aplicación FastAPI con configuración desde settings
app = FastAPI(title=settings.api_title, version=settings.api_version)
app.state.limiter = limiter
# slowapi handler has a typing signature that pyright/mypy may not accept directly
# cast to Any to satisfy the static checker while preserving runtime behavior
app.add_exception_handler(RateLimitExceeded, cast(Any, _rate_limit_exceeded_handler))

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Servir archivos estáticos del frontend (dashboard, index, assets)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Registrar routers de cada módulo funcional
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(pricing.router)
app.include_router(autorizaciones.router)
app.include_router(pdf.router)
app.include_router(clientes.router)
app.include_router(vendedores.router)
app.include_router(cotizaciones.router)
app.include_router(dashboard.router)

# Variables para métricas simples (única definición)
start_time = datetime.now(timezone.utc)
metrics = {
    'requests_total': 0,
    'errors_total': 0,
    'last_error': '',
}
metrics_lock = threading.Lock()


@app.get("/health")
def healthcheck():
    """
    Endpoint de health check para monitoreo externo.
    Verifica conexión a la base de datos y retorna estado general.
    Returns:
        dict: Estado de la app, DB, uptime y parámetros por defecto.
    """
    import logging
    db_status = "ok"
    db_error = None
    logging.warning(f"[DEBUG-HEALTH] Iniciando healthcheck. Cadena de conexión: {settings.sqlserver_conn}")
    try:
        with connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        logging.warning("[DEBUG-HEALTH] Conexión a BD exitosa.")
    except Exception as e:
        db_status = "error"
        db_error = str(e)
        logging.error(f"[DEBUG-HEALTH] Error de conexión a BD: {db_error}")
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db_status": db_status,
        "db_error": db_error,
        "uptime_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
        "default_transporte": settings.default_transporte,
        "default_monedas": settings.default_monedas,
    }
# Middleware para métricas y debug de headers/auth
@app.middleware("http")
async def debug_and_metrics_middleware(request, call_next):
    """
    Middleware que cuenta peticiones, errores y loguea headers sensibles.
    Incrementa el contador de peticiones y errores, y registra headers de autenticación.
    """
    with metrics_lock:
        metrics['requests_total'] += 1  # Suma una petición
    # Loguea path y headers de autenticación/cookie
    logger.warning(f"[DEBUG-MIDDLEWARE] path={request.url.path} headers={{'authorization': request.headers.get('authorization', None), 'cookie': request.headers.get('cookie', None)}}")
    try:
        response = await call_next(request)  # Llama al siguiente handler
        return response
    except Exception as e:
        with metrics_lock:
            metrics['errors_total'] += 1  # Suma un error
            metrics['last_error'] = str(e)  # Guarda el último error
        raise  # Propaga el error


@app.get("/metrics")
def metrics_endpoint():
    """
    Endpoint Prometheus-like para métricas básicas de la app.
    Retorna el total de peticiones, errores, uptime y último error.
    Returns:
        Response: Texto plano con métricas para Prometheus.
    """
    with metrics_lock:
        lines = [
            f"requests_total {metrics['requests_total']}",
            f"errors_total {metrics['errors_total']}",
            f"uptime_seconds {(datetime.now(timezone.utc) - start_time).total_seconds():.0f}",
        ]
        if metrics['last_error']:
            # Añadir como métrica de texto para debugging
            lines.append(f'last_error "{metrics["last_error"]}"')
    return Response("\n".join(lines), media_type="text/plain")
