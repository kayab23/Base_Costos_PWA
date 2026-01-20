"""
Rutas para generación y descarga de PDFs de política de entrega y datos bancarios.
"""


from fastapi import APIRouter, Response, status
from app.pdf.generar_pdf import generar_pdf_politica_entrega
import os
import io
from PyPDF2 import PdfMerger
from app.schemas import CotizacionVendedorPDF

router = APIRouter(prefix="/cotizacion", tags=["cotizacion"])

@router.post("/pdf", response_class=Response, status_code=status.HTTP_200_OK)
def generar_pdf_vendedor_endpoint(payload: CotizacionVendedorPDF):
    """
    Recibe datos de cotización del vendedor (varios SKUs) y genera el PDF.
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    datos = payload.dict()
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
