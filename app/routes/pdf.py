"""
Rutas para generación y descarga de PDFs de política de entrega y datos bancarios.
"""


from fastapi import APIRouter, Response, status, Depends, HTTPException
from app.pdf.generar_pdf import generar_pdf_politica_entrega
from app.auth import get_current_user
import os
import io
from PyPDF2 import PdfMerger
from app.schemas import CotizacionVendedorPDF

router = APIRouter(prefix="/cotizacion", tags=["cotizacion"])

@router.post("/pdf", response_class=Response, status_code=status.HTTP_200_OK)
def generar_pdf_vendedor_endpoint(payload: CotizacionVendedorPDF, user=Depends(get_current_user)):
    """
    Recibe datos de cotización del vendedor (varios SKUs) y genera el PDF.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    datos = payload.dict()
    # Validación de descuentos según rol del solicitante (por seguridad)
    allowed_discount_by_role = {
        'Vendedor': 20,
        'Gerencia_Comercial': 25,
        'Subdireccion': 30,
        'Direccion': 35,
        'Gerencia': 40,
        'Admin': 100
    }
    role = user.get('rol') if isinstance(user, dict) else None
    allowed = allowed_discount_by_role.get(role, 0)
    # Recorrer items y verificar
    excedidos = []
    for it in datos.get('items', []):
        precio_max = it.get('precio_maximo_lista') or it.get('precio_maximo') or 0
        monto = it.get('monto_propuesto') or 0
        try:
            precio_max_f = float(precio_max)
            monto_f = float(monto)
        except Exception:
            precio_max_f = 0
            monto_f = 0
        if precio_max_f > 0:
            pct = max(0.0, (precio_max_f - monto_f) / precio_max_f * 100.0)
        else:
            pct = 0.0
        if pct > allowed:
            excedidos.append({'sku': it.get('sku'), 'pct': round(pct, 2), 'allowed': allowed})
    if excedidos:
        # Rechazar generación del PDF si hay descuentos no autorizados
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={'message': 'Descuentos no autorizados', 'items': excedidos})
    logging.info("Payload recibido para PDF: %s", datos)
    pdf_bytes = generar_pdf_politica_entrega(datos)

    # Rutas absolutas a los PDFs fijos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_politica = os.path.abspath(os.path.join(base_dir, '../pdf/Terminos_Condiciones_Vitaris.pdf'))
    pdf_banco = os.path.abspath(os.path.join(base_dir, '../pdf/Datos_Cuenta_Bancaria.pdf'))

    merger = PdfMerger()
    # 1. Cotización generada
    merger.append(io.BytesIO(pdf_bytes))
    # 2. Política de entrega
    if os.path.exists(pdf_politica):
        merger.append(pdf_politica)
    # 3. Datos bancarios
    if os.path.exists(pdf_banco):
        merger.append(pdf_banco)

    output_buffer = io.BytesIO()
    merger.write(output_buffer)
    merger.close()
    output_buffer.seek(0)
    return Response(content=output_buffer.read(), media_type="application/pdf")
