"""
Módulo para generación de PDFs de política de entrega y datos bancarios.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from decimal import Decimal

# Try to use num2words if available for amount-in-words; otherwise fallback
try:
    from num2words import num2words
    def number_to_words_es(amount: float) -> str:
        # num2words handles floats with to='currency' poorly; convert to integer pesos and cents
        try:
            pesos = int(Decimal(amount))
            cents = int((Decimal(str(amount)) - Decimal(pesos)) * 100)
        except Exception:
            return str(amount)
        if cents:
            return f"{num2words(pesos, lang='es').capitalize()} pesos {num2words(cents, lang='es')} centavos"
        return f"{num2words(pesos, lang='es').capitalize()} pesos"
except Exception:
    def number_to_words_es(amount: float) -> str:
        # Fallback: return formatted number as text
        try:
            return f"{amount:,.2f} MXN"
        except Exception:
            return str(amount)

# Función principal para generar PDF de política de entrega y datos bancarios
def generar_pdf_politica_entrega(datos: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Logo Vitaris (siempre usar el logo oficial)
    y = height - 60
    logo_path = 'app/pdf/logo.png'  # Ruta relativa al backend, asegúrate de que exista
    try:
        c.drawImage(logo_path, 40, y, width=120, height=60, mask='auto')
        y -= 70
    except Exception:
        y -= 10

    # Encabezado principal con color azul institucional (como en los otros PDF)
    c.setFont("Helvetica-Bold", 22)
    c.setFillColorRGB(0.09, 0.29, 0.55)  # Azul institucional (aprox #185b8c)
    c.drawString(40, y, "Cotización Oficial")
    c.setFillColorRGB(0, 0, 0)
    y -= 35

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Cliente: {datos.get('cliente', '-').upper()}")
    # Mostrar número de cotización y fecha (si existen en payload)
    numero_cliente = datos.get('numero_cotizacion_cliente')
    numero_vendedor = datos.get('numero_cotizacion_vendedor')
    fecha_cot = datos.get('fecha_cotizacion')
    if not fecha_cot:
        from datetime import datetime
        fecha_cot = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    y -= 18
    c.setFont('Helvetica', 9)
    if numero_cliente or numero_vendedor:
        num_text = ' '.join([p for p in [f"N° Cliente: {numero_cliente}" if numero_cliente else None,
                                        f"N° Vendedor: {numero_vendedor}" if numero_vendedor else None] if p])
        c.drawString(40, y, num_text)
        y -= 14
    c.drawString(40, y, f"Fecha: {fecha_cot}")
    y += 4
    y -= 25

    # Tabla de SKUs cotizados con fondo blanco, encabezados azules y líneas divisorias suaves
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Productos Cotizados:")
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    # Mostrar Precio de Lista (unidad) y debajo el Total Máximo en la misma celda
    headers = ["SKU", "Cantidad", "Precio de Lista", "Monto Propuesto", "IVA 16%", "Descuento %", "Total"]
    # Ajustar anchos para mejorar legibilidad y evitar que los encabezados se solapen
    # Usable width = 612 (letter) - 40 left margin - 40 right margin = 532
    # Aumentamos SKU y Cantidad, reducimos ligeramente Precio de Lista y movemos espacio a IVA/Descuento
    col_widths = [120, 50, 120, 80, 50, 60, 52]
    x_start = 40
    x = x_start
    # Encabezados (texto azul, fondo blanco)
    header_box_h = 18
    header_font_size = 8
    for i, h in enumerate(headers):
        c.setFillColorRGB(1, 1, 1)
        c.rect(x, y-2, col_widths[i], header_box_h, fill=1, stroke=0)
        c.setFillColorRGB(0.09, 0.29, 0.55)  # Azul institucional
        c.setFont('Helvetica-Bold', header_font_size)
        # Align headers: center all headers horizontally and vertically inside header box
        # Compute header text Y so it is vertically centered inside the header box
        # rect is drawn at (x, y-2) with height header_box_h, so center = y-2 + header_box_h/2
        header_text_y = (y - 2) + (header_box_h / 2) - (header_font_size / 4)
        center_x = x + (col_widths[i] / 2)
        c.drawCentredString(center_x, header_text_y, h)
        x += col_widths[i]
    y -= header_box_h
    c.setFont("Helvetica", 10)
    total_global = 0
    row_height = 18
    for item in datos.get('items', []):
        if y < 80:
            c.showPage()
            y = height - 60
            x = x_start
        x = x_start
        cantidad = int(item.get('cantidad', 1) or 1)
        monto_propuesto = float(item.get('monto_propuesto', 0) or 0)
        # Determine precio_maximo_lista with fallbacks
        precio_maximo_lista = None
        if item.get('precio_maximo_lista'):
            precio_maximo_lista = float(item.get('precio_maximo_lista'))
        elif item.get('precio_maximo'):
            precio_maximo_lista = float(item.get('precio_maximo'))
        else:
            precio_maximo_lista = 0.0

        # Calcular montos totales considerando la cantidad
        monto_propuesto_total = monto_propuesto * cantidad
        iva_total = monto_propuesto_total * 0.16
        total = monto_propuesto_total + iva_total
        total_global += total

        # Calcular descuento relativo al precio de lista total (precio por unidad * cantidad)
        try:
            precio_lista_total = precio_maximo_lista * cantidad if precio_maximo_lista is not None else 0.0
            if precio_lista_total > 0:
                descuento_pct = max(0.0, 100.0 * (1.0 - (monto_propuesto_total / precio_lista_total)))
            else:
                descuento_pct = 0.0
        except Exception:
            descuento_pct = 0.0

        # Mostrar Precio de Lista: usar el valor del Total Máximo (redondeado a pesos)
        precio_lista_total_rounded = round(precio_lista_total)
        precio_lista_total_fmt = f"${precio_lista_total_rounded:,.0f}"
        row = [
            item.get('sku', '-'),
            str(cantidad),
            precio_lista_total_fmt,
            f"${monto_propuesto_total:,.2f}",
            f"${iva_total:,.2f}",
            f"{descuento_pct:.2f}%",
            f"${total:,.2f}"
        ]
        for i, val in enumerate(row):
            c.setFillColorRGB(1, 1, 1)
            c.rect(x, y-4, col_widths[i], row_height, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            try:
                # baseline Y centered within row
                text_y = y - (row_height / 2) + 3
                # Use smaller font for values
                if i == 3:
                    c.setFont('Helvetica-Bold', 9)
                else:
                    c.setFont('Helvetica', 9)
                text = str(val)
                # Center all cell values horizontally
                center_x = x + (col_widths[i] / 2)
                c.drawCentredString(center_x, text_y, text)
            except Exception:
                c.setFont('Helvetica', 9)
                c.drawString(x+6, y, str(val))
            finally:
                x += col_widths[i]
        y -= row_height
        # Línea divisoria
        c.setStrokeColorRGB(0.85, 0.85, 0.85)
        c.setLineWidth(0.5)
        c.line(x_start, y+12, x_start+sum(col_widths), y+12)

    # Total global
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.09, 0.29, 0.55)
    c.drawString(40, y, f"MONTO TOTAL PROPUESTO: ${total_global:,.2f}")
    c.setFillColorRGB(0, 0, 0)
    y -= 30

    # Monto total en letras
    try:
        monto_letras = number_to_words_es(total_global)
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"({monto_letras})")
        y -= 20
    except Exception:
        pass

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
    # Marca de versión para identificar la plantilla usada en la generación
    try:
        from datetime import datetime
        ver_text = f"Plantilla PDF: v2 — Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawRightString(width - 40, 28, ver_text)
        c.setFillColorRGB(0, 0, 0)
    except Exception:
        pass

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
