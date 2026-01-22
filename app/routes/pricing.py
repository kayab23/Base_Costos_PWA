"""Rutas API para consulta de cálculos de pricing y generación de listas de precios.

Endpoints:
- GET /pricing/landed: Consulta Landed Cost calculados por SKU/transporte
- GET /pricing/lista: Consulta precios de venta por SKU/cliente
- GET /pricing/listas: Consulta precios con campos específicos por rol del usuario
- POST /pricing/recalcular: Ejecuta recálculo completo de precios para un transporte

Control de acceso por rol:
- Vendedor: Solo ve Precio Máximo y su Precio Mínimo (sin costos)
- Gerencia Comercial, Subdirección, Dirección, Admin: Ven todos los costos y precios
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from .. import schemas
from ..auth import get_current_user
from ..config import settings
from ..db import fetch_all, get_connection
from cost_engine import run_calculations

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.get("/landed", response_model=list[schemas.LandedCost])
def list_landed_cost(
    sku: str | None = Query(default=None, description="Filtra por SKU exacto"),
    transporte: str | None = Query(default=None, description="Filtra por Transporte (Maritimo/Aereo)"),
    conn=Depends(get_connection),
    user=Depends(get_current_user),
):
    cursor = conn.cursor()
    query = """
        SELECT sku, transporte, origen, moneda_base, costo_base, tc_mxn, costo_base_mxn,
               flete_pct, seguro_pct, arancel_pct, dta_pct, honorarios_aduanales_pct,
               gastos_aduana_mxn, landed_cost_mxn, mark_up, calculado_en
        FROM dbo.LandedCostCache
        WHERE 1=1
    """
    params: list[str] = []
    if sku:
        query += " AND sku = ?"
        params.append(sku)
    if transporte:
        query += " AND transporte = ?"
        params.append(transporte)
    query += " ORDER BY sku"
    return fetch_all(cursor, query, params)


@router.get("/lista", response_model=list[schemas.PrecioVenta])
def list_precios(
    sku: str | None = Query(default=None, description="Filtra por SKU"),
    tipo_cliente: str | None = Query(default=None, description="Filtra por cliente"),
    conn=Depends(get_connection),
    user=Depends(get_current_user),
):
    cursor = conn.cursor()
    query = """
        SELECT sku, tipo_cliente, moneda_precio, tc_mxn, landed_cost_mxn, margen_pct,
               precio_venta_mxn, precio_venta_moneda, precio_min_mxn, notas,
               calculado_en
        FROM dbo.ListaPrecios
        WHERE 1=1
    """
    params: list[str] = []
    if sku:
        query += " AND sku = ?"
        params.append(sku)
    if tipo_cliente:
        query += " AND tipo_cliente = ?"
        params.append(tipo_cliente)
    query += " ORDER BY sku, tipo_cliente"
    return fetch_all(cursor, query, params)


@router.post("/recalculate", response_model=schemas.RecalculateResponse)
def recalculate_pricing(
    payload: schemas.RecalculateRequest,
    conn=Depends(get_connection),
    user=Depends(get_current_user),
):
    transporte = payload.transporte or settings.default_transporte
    monedas = payload.monedas or settings.default_monedas
    summary = run_calculations(transporte, monedas, conn)
    return summary


@router.get("/listas", response_model=list[schemas.ListaPrecio])
def get_listas_precios(
    sku: str | None = Query(default=None, description="Filtra por SKU"),
    transporte: str | None = Query(default=None, description="Filtra por Transporte (Maritimo/Aereo)"),
    conn=Depends(get_connection),
    user=Depends(get_current_user),
):
    """
    Obtiene las listas de precios calculadas con nueva jerarquía de 4 niveles:
    - Precio Máximo: Mark-up × 2
    - Vendedor: 20% descuento del Precio Máximo
    - Gerente Comercial: 25% descuento del Precio Máximo
    - Subdirección: 30% descuento del Precio Máximo
    - Dirección: 35% descuento del Precio Máximo
    """
    cursor = conn.cursor()
    query = """
        SELECT p.sku, p.transporte, p.landed_cost_mxn, p.precio_base_mxn,
               p.precio_maximo, p.precio_vendedor_min,
               p.precio_gerente_com_min, p.precio_subdireccion_min,
               p.precio_direccion_min,
               p.markup_pct, p.fecha_calculo,
               p.costo_base_mxn, p.flete_pct, p.seguro_pct, 
               p.arancel_pct, p.dta_pct, p.honorarios_aduanales_pct, p.categoria
        FROM dbo.PreciosCalculados p
        WHERE 1=1
    """
    params: list[str] = []
    if sku:
        query += " AND p.sku = ?"
        params.append(sku)
    if transporte:
        query += " AND p.transporte = ?"
        params.append(transporte)
    query += " ORDER BY p.sku, p.transporte"
    resultados = fetch_all(cursor, query, params)
    # Si el usuario es Vendedor, ocultar campos de costos
    if user["rol"] == "Vendedor":
        for r in resultados:
            r["costo_base_mxn"] = None
            r["flete_pct"] = None
            r["seguro_pct"] = None
            r["arancel_pct"] = None
            r["dta_pct"] = None
            r["honorarios_aduanales_pct"] = None
            r["landed_cost_mxn"] = None
    # Map legacy field names to new "lista" names for compatibility
    for r in resultados:
        # precio_maximo_lista is the new name for precio_maximo
        try:
            r['precio_maximo_lista'] = r.get('precio_maximo') if r.get('precio_maximo') is not None else None
        except Exception:
            r['precio_maximo_lista'] = None
        # precio_minimo_lista maps to precio_vendedor_min (seller minimum)
        try:
            r['precio_minimo_lista'] = r.get('precio_vendedor_min') if r.get('precio_vendedor_min') is not None else None
        except Exception:
            r['precio_minimo_lista'] = None
    return resultados
