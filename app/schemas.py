"""Modelos Pydantic para las respuestas y peticiones del API."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Producto(BaseModel):
    sku: str
    descripcion: Optional[str] = None
    proveedor: Optional[str] = None
    origen: Optional[str] = None
    categoria: Optional[str] = None
    unidad: Optional[str] = None
    moneda_base: Optional[str] = None
    costo_base: Optional[float] = None
    fecha_actualizacion: Optional[date] = None
    activo: Optional[bool] = None


class CostoBase(BaseModel):
    sku: str
    costo_base: Optional[float] = None
    moneda: Optional[str] = None
    fecha_actualizacion: Optional[date] = None
    proveedor: Optional[str] = None
    notas: Optional[str] = None


class ParametroImportacion(BaseModel):
    concepto: str
    tipo: str
    valor: float
    descripcion: Optional[str] = None
    notas: Optional[str] = None


class TipoCambio(BaseModel):
    moneda: str
    fecha: date
    tipo_cambio_mxn: float
    fuente: Optional[str] = None


class PoliticaMargen(BaseModel):
    tipo_cliente: str
    margen: float
    notas: Optional[str] = None


class LandedCost(BaseModel):
    sku: str
    transporte: str
    origen: Optional[str]
    moneda_base: Optional[str]
    costo_base: Optional[float]
    tc_mxn: Optional[float]
    costo_base_mxn: Optional[float]
    flete_pct: Optional[float]
    seguro_pct: Optional[float]
    arancel_pct: Optional[float]
    gastos_aduana_mxn: Optional[float]
    landed_cost_mxn: Optional[float]
    mark_up: Optional[float]
    version_id: Optional[int]
    calculado_en: Optional[datetime]


class PrecioVenta(BaseModel):
    sku: str
    tipo_cliente: str
    moneda_precio: str
    tc_mxn: Optional[float]
    landed_cost_mxn: Optional[float]
    margen_pct: Optional[float]
    precio_venta_mxn: Optional[float]
    precio_venta_moneda: Optional[float]
    precio_min_mxn: Optional[float]
    notas: Optional[str]
    version_id: Optional[int]
    calculado_en: Optional[datetime]


class RecalculateRequest(BaseModel):
    transporte: str = Field(default="Maritimo")
    monedas: List[str] | None = None


class RecalculateResponse(BaseModel):
    landed_rows: int
    price_rows: int
    version_id: Optional[int]
