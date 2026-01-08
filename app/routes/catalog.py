"""Rutas para exponer catálogos base."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from .. import schemas
from ..auth import get_current_user
from ..db import fetch_all, get_connection

router = APIRouter(prefix="/catalog", tags=["Catalogos"])


@router.get("/productos", response_model=list[schemas.Producto])
def list_productos(conn=Depends(get_connection), user=Depends(get_current_user)):
    cursor = conn.cursor()
    rows = fetch_all(
        cursor,
        """
        SELECT sku, descripcion, proveedor, origen, categoria, unidad, moneda_base, 
               costo_base, fecha_actualizacion, activo
        FROM dbo.Productos
        ORDER BY sku
        """,
    )
    return rows


# Endpoint /costos eliminado - los costos ahora están en /productos (tabla Productos.costo_base)


@router.get("/parametros", response_model=list[schemas.ParametroImportacion])
def list_parametros(conn=Depends(get_connection), user=Depends(get_current_user)):
    cursor = conn.cursor()
    rows = fetch_all(
        cursor,
        """
        SELECT concepto, tipo, valor, descripcion, notas
        FROM dbo.ParametrosImportacion
        WHERE vigente_hasta IS NULL
        ORDER BY concepto
        """,
    )
    return rows


@router.get("/tipos-cambio", response_model=list[schemas.TipoCambio])
def list_tipos_cambio(conn=Depends(get_connection), user=Depends(get_current_user)):
    cursor = conn.cursor()
    rows = fetch_all(
        cursor,
        """
        SELECT moneda, fecha, tipo_cambio_mxn, fuente
        FROM dbo.TiposCambio
        ORDER BY moneda, fecha DESC
        """,
    )
    return rows


@router.get("/margenes", response_model=list[schemas.PoliticaMargen])
def list_margenes(conn=Depends(get_connection), user=Depends(get_current_user)):
    cursor = conn.cursor()
    rows = fetch_all(
        cursor,
        """
        SELECT tipo_cliente, margen, notas
        FROM dbo.PoliticasMargen
        WHERE vigente_hasta IS NULL
        ORDER BY tipo_cliente
        """,
    )
    return rows
