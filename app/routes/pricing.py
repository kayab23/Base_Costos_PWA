"""Rutas para cálculos y resultados de pricing."""
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
    Obtiene las listas de precios calculadas con rangos por jerarquía:
    - Vendedor: 90% a 65% sobre Mark-up
    - Gerencia Comercial: 65% a 40% sobre Mark-up
    - Gerencia: 40% a 10% sobre Mark-up
    """
    cursor = conn.cursor()
    query = """
        SELECT p.sku, p.transporte, p.landed_cost_mxn, p.precio_base_mxn,
               p.precio_vendedor_max, p.precio_vendedor_min,
               p.precio_gerencia_com_max, p.precio_gerencia_com_min,
               p.precio_gerencia_max, p.precio_gerencia_min,
               p.markup_pct, p.fecha_calculo,
               l.costo_base_mxn, l.flete_pct, l.seguro_pct, l.arancel_pct,
               l.dta_pct, l.honorarios_aduanales_pct
        FROM dbo.PreciosCalculados p
        LEFT JOIN dbo.LandedCostCache l ON p.sku = l.sku AND p.transporte = l.transporte
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
    return fetch_all(cursor, query, params)
