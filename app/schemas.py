
from __future__ import annotations
# Esquema para cotización PDF del rol vendedor
from typing import Optional, List
from pydantic import BaseModel, Field


# Nuevo esquema para PDF multi-SKU
class CotizacionItemPDF(BaseModel):
    sku: str
    descripcion: Optional[str]
    cantidad: int
    # Compatibilidad: accept both old and new field names
    precio_maximo: Optional[float] = None
    precio_maximo_lista: Optional[float] = None
    precio_vendedor_min: float
    monto_propuesto: float
    logo_path: Optional[str] = None
    proveedor: Optional[str] = None
    origen: Optional[str] = None

class CotizacionVendedorPDF(BaseModel):
    items: list[CotizacionItemPDF]
    cliente: str
"""Modelos Pydantic para las respuestas y peticiones del API."""

from datetime import date, datetime
from typing import List, Optional



class UserInfo(BaseModel):
    usuario_id: int
    username: str
    rol: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str


class Producto(BaseModel):
    sku: str
    descripcion: Optional[str] = None
    proveedor: Optional[str] = None
    origen: Optional[str] = None
    segmento_hospitalario: Optional[str] = None
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
    """Schema para las listas de precios con nueva jerarquía de 4 niveles"""
    sku: str
    transporte: str
    landed_cost_mxn: Optional[float]
    precio_base_mxn: Optional[float]  # Mark-up base
    # Compatibilidad: mantener `precio_maximo` y exponer `precio_maximo_lista`
    precio_maximo: Optional[float]  # Mark-up × 2 (antiguo)
    precio_maximo_lista: Optional[float]  # Precio Máximo de Lista (nuevo nombre)
    # Precio mínimo de lista (nuevo campo, mapeado desde precio_vendedor_min)
    precio_minimo_lista: Optional[float]
    precio_vendedor_min: Optional[float]  # 20% descuento del Precio Máximo
    precio_gerente_com_min: Optional[float]  # 25% descuento del Precio Máximo
    precio_subdireccion_min: Optional[float]  # 30% descuento del Precio Máximo
    precio_direccion_min: Optional[float]  # 35% descuento del Precio Máximo
    markup_pct: Optional[float]
    fecha_calculo: Optional[datetime]
    # Campos adicionales para admin/gerencia
    costo_base_mxn: Optional[float]
    flete_pct: Optional[float]
    seguro_pct: Optional[float]
    arancel_pct: Optional[float]
    dta_pct: Optional[float]
    honorarios_aduanales_pct: Optional[float]
    categoria: Optional[str]


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
