"""Modelos Pydantic para las respuestas y peticiones del API."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    usuario_id: int
    username: str
    rol: str


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
    dta_pct: Optional[float]
    honorarios_aduanales_pct: Optional[float]
    gastos_aduana_mxn: Optional[float]
    landed_cost_mxn: Optional[float]
    mark_up: Optional[float]
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
    calculado_en: Optional[datetime]


class RecalculateRequest(BaseModel):
    transporte: str = Field(default="Maritimo")
    monedas: List[str] | None = None


class RecalculateResponse(BaseModel):
    landed_rows: int
    price_rows: int


class ListaPrecio(BaseModel):
    """Schema para las listas de precios con rangos por jerarquía"""
    sku: str
    transporte: str
    landed_cost_mxn: Optional[float]
    precio_base_mxn: Optional[float]  # Mark-up 10%
    precio_vendedor_max: Optional[float]  # 90% sobre Mark-up
    precio_vendedor_min: Optional[float]  # 65% sobre Mark-up
    precio_gerencia_com_max: Optional[float]  # 65% sobre Mark-up
    precio_gerencia_com_min: Optional[float]  # 40% sobre Mark-up
    precio_gerencia_max: Optional[float]  # 40% sobre Mark-up
    precio_gerencia_min: Optional[float]  # 10% sobre Mark-up (= precio_base_mxn)
    markup_pct: Optional[float]
    fecha_calculo: Optional[datetime]
    # Campos adicionales para admin/gerencia
    costo_base_mxn: Optional[float]
    flete_pct: Optional[float]
    seguro_pct: Optional[float]
    arancel_pct: Optional[float]
    dta_pct: Optional[float]
    honorarios_aduanales_pct: Optional[float]


class SolicitudAutorizacionCreate(BaseModel):
    """Schema para crear solicitud de autorización"""
    sku: str
    transporte: str
    precio_propuesto: float
    cliente: Optional[str] = None
    cantidad: Optional[int] = None
    justificacion: str


class SolicitudAutorizacionResponse(BaseModel):
    """Schema para aprobar/rechazar solicitud"""
    comentarios: Optional[str] = None


class SolicitudAutorizacion(BaseModel):
    """Schema para solicitud de autorización"""
    id: int
    sku: str
    transporte: str
    solicitante_id: int
    solicitante: Optional[str]
    nivel_solicitante: str
    precio_propuesto: float
    precio_minimo_actual: float
    descuento_adicional_pct: float
    cliente: Optional[str]
    cantidad: Optional[int]
    justificacion: str
    estado: str
    autorizador_id: Optional[int]
    autorizador: Optional[str]
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime]
    comentarios_autorizador: Optional[str]
