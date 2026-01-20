"""
Módulo para generación de PDFs de política de entrega y datos bancarios.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# Función principal para generar PDF de política de entrega y datos bancarios
def generar_pdf_politica_entrega(datos: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Logo (opcional, si se provee ruta en el primer item)
    y = height - 60
    logo_path = None
    if 'items' in datos and datos['items']:
        logo_path = datos['items'][0].get('logo_path')
    if logo_path:
        try:
            c.drawImage(logo_path, 40, y, width=120, height=60)
            y -= 70
        except Exception:
            y -= 10
    else:
        y -= 10

    # Encabezado principal
    c.setFont("Helvetica-Bold", 22)
    c.setFillColorRGB(0.13, 0.45, 0.29)
    c.drawString(40, y, "Cotización Oficial")
    c.setFillColorRGB(0, 0, 0)
    y -= 35

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Cliente: {datos.get('cliente', '-').upper()}")
    y -= 25

    # Tabla de SKUs cotizados
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Productos Cotizados:")
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    headers = ["SKU", "Cantidad", "Monto Propuesto", "Total"]
    col_widths = [80, 60, 110, 110]
    x = 40
    for i, h in enumerate(headers):
        c.drawString(x, y, h)
        x += col_widths[i]
    y -= 14
    c.setFont("Helvetica", 10)
    total_global = 0
    for item in datos.get('items', []):
        if y < 80:
            c.showPage()
            y = height - 60
        x = 40
        cantidad = int(item.get('cantidad', 1) or 1)
        monto_propuesto = float(item.get('monto_propuesto', 0) or 0)
        total = monto_propuesto * cantidad
        total_global += total
        row = [
            item.get('sku', '-'),
            str(cantidad),
            f"${monto_propuesto:,.2f}",
            f"${total:,.2f}"
        ]
        for i, val in enumerate(row):
            c.drawString(x, y, str(val))
            x += col_widths[i]
        y -= 14

    # Total global
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.13, 0.45, 0.29)
    c.drawString(40, y, f"MONTO TOTAL PROPUESTO: ${total_global:,.2f}")
    c.setFillColorRGB(0, 0, 0)
    y -= 30

    # Descripciones detalladas de cada producto cotizado
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Detalles de productos cotizados:")
    y -= 18
    c.setFont("Helvetica", 10)
    for item in datos.get('items', []):
        if y < 80:
            c.showPage()
            y = height - 60
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, f"{item.get('sku', '-')}{'(' + str(item.get('cantidad', 1)) + ')' if item.get('cantidad', 1) > 1 else ''}")
        y -= 14
        c.setFont("Helvetica", 10)
        descripcion = item.get('descripcion') if 'descripcion' in item else '-'
        proveedor = item.get('proveedor') if 'proveedor' in item else '-'
        origen = item.get('origen') if 'origen' in item else '-'
        # Normalizar proveedor y origen para mostrar '-' si están vacíos, null o solo espacios
        proveedor = proveedor if isinstance(proveedor, str) and proveedor.strip() else '-'
        origen = origen if isinstance(origen, str) and origen.strip() else '-'
        # Descripción con salto de línea si es muy larga
        desc_text = f"Descripción: {descripcion if descripcion not in [None, ''] else '-'}"
        max_width = 80
        desc_lines = []
        while len(desc_text) > max_width:
            split_at = desc_text.rfind(' ', 0, max_width)
            if split_at == -1:
                split_at = max_width
            desc_lines.append(desc_text[:split_at])
            desc_text = desc_text[split_at:].lstrip()
        desc_lines.append(desc_text)
        for line in desc_lines:
            c.drawString(60, y, line)
            y -= 12
        c.drawString(60, y, f"Proveedor: {proveedor}")
        y -= 12
        c.drawString(60, y, f"Origen: {origen}")
        y -= 16

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(40, y, "Esta cotización es válida únicamente para el cliente y productos especificados.")
    y -= 15
    c.drawString(40, y, "Incluye términos y condiciones y datos bancarios en las siguientes páginas.")

    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(40, 40, "Documento generado automáticamente por el sistema de cotización Vitaris.")
    c.setFillColorRGB(0, 0, 0)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
