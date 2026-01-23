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
    # Page layout parameters
    left_margin = 40
    right_margin = 40
    top_margin = 60
    bottom_margin = 60
    usable_width = width - left_margin - right_margin

    # Helper to draw page header (logo + title + client block)
    def draw_page_header(cnv, page_y, datos, include_client_block=True):
        # Compact header: move logo to top-right and reduce header height to free space
        header_band_h = 80
        top_y = height - top_margin
        band_bottom = top_y - header_band_h
        logo_path = 'app/pdf/logo.png'
        logo_w = 120
        logo_h = 48
        try:
            # place logo aligned to the right and as high as possible without leaving the page
            logo_x = width - right_margin - logo_w
            # minimal inset from top edge (6 pts)
            logo_y = height - logo_h - 6
            cnv.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')
        except Exception:
            pass
        # Title: align left and place as high as possible within the header band
        cnv.setFont("Helvetica-Bold", 20)
        cnv.setFillColorRGB(0.09, 0.29, 0.55)
        title_x = left_margin
        # small offset from the top edge but inside page
        title_y = top_y - 6
        cnv.drawString(title_x, title_y, "Cotización Oficial")
        cnv.setFillColorRGB(0, 0, 0)
        # Client block placed below title inside header band, start a little above band bottom
        cb_y = band_bottom + 26
        if include_client_block:
            cnv.setFont("Helvetica-Bold", 12)
            cliente_txt = datos.get('cliente', '-')
            cnv.drawString(left_margin, cb_y, f"Cliente: {cliente_txt}")
            cb_y -= 14
            cnv.setFont('Helvetica', 9)
            numero_cliente = datos.get('numero_cotizacion_cliente')
            numero_vendedor = datos.get('numero_cotizacion_vendedor')
            # Draw each identifier on its own line for clarity
            if numero_cliente:
                cnv.drawString(left_margin, cb_y, f"Número de cotización (Cliente): {numero_cliente}")
                cb_y -= 12
            if numero_vendedor:
                cnv.drawString(left_margin, cb_y, f"Número de cotización (Vendedor): {numero_vendedor}")
                cb_y -= 12
            fecha_cot = datos.get('fecha_cotizacion')
            if not fecha_cot:
                from datetime import datetime
                fecha_cot = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
            cnv.drawString(left_margin, cb_y, f"Fecha: {fecha_cot}")
            cb_y -= 8
        # Return the Y position just below the client block (or header band) to start body content.
        # Prefer the current client-block Y to avoid overlapping when client lines extend down.
        try:
            return min(cb_y - 12, band_bottom - 8)
        except Exception:
            return band_bottom - 8

    # Start first page and draw header
    y = draw_page_header(c, height, datos, include_client_block=True)

    # Tabla de SKUs cotizados: usar todo el ancho utilizable y alinear números a la derecha
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, y, "Productos Cotizados:")
    y -= 16
    # Column fractions (sum ~1.0)
    fractions = [0.28, 0.08, 0.14, 0.14, 0.12, 0.09, 0.15]
    col_widths = [int(usable_width * f) for f in fractions]
    # Adjust last to fill rounding gaps
    extra = usable_width - sum(col_widths)
    if extra > 0:
        col_widths[-1] += extra

    headers = ["SKU", "Cantidad", "P. Lista", "Monto Prop.", "IVA 16%", "Desc. %", "Total"]
    x_start = left_margin
    x = x_start
    header_box_h = 20
    header_font_size = 8

    def draw_table_header(cx, cy):
        x = x_start
        cx.setFont('Helvetica-Bold', header_font_size)
        for i, h in enumerate(headers):
            # light blue header background
            cx.setFillColorRGB(0.94, 0.96, 0.99)
            cx.rect(x, cy - 4, col_widths[i], header_box_h, fill=1, stroke=0)
            cx.setFillColorRGB(0.09, 0.29, 0.55)
            # center header label
            text_y = (cy - 4) + header_box_h / 2 - (header_font_size / 4)
            cx.drawCentredString(x + (col_widths[i] / 2), text_y, h)
            x += col_widths[i]

    draw_table_header(c, y)
    y -= header_box_h
    c.setFont('Helvetica', 9)
    total_global = 0.0
    row_padding = 6
    row_min_h = 18

    # Reserve a footer/block space for totals and details to avoid cutting
    def space_needed_for_footer_and_details(items_count):
        # estimate lines for totals + amount in words + header for details + per-item detail lines
        base = 120
        per_item = 44
        try:
            return base + (items_count * per_item)
        except Exception:
            return base

    def format_money(v):
        try:
            return f"${round(float(v)):,.0f}"
        except Exception:
            return "$0"

    for item in datos.get('items', []):
        # compute numeric values
        cantidad = int(item.get('cantidad', 1) or 1)
        monto_propuesto = float(item.get('monto_propuesto', 0) or 0)
        precio_maximo_lista = 0.0
        if item.get('precio_maximo_lista'):
            precio_maximo_lista = float(item.get('precio_maximo_lista'))
        elif item.get('precio_maximo'):
            precio_maximo_lista = float(item.get('precio_maximo'))
        monto_propuesto_total = monto_propuesto * cantidad
        iva_total = monto_propuesto_total * 0.16
        total = monto_propuesto_total + iva_total
        total_global += total
        precio_lista_total = precio_maximo_lista * cantidad
        descuento_pct = 0.0
        if precio_lista_total > 0:
            descuento_pct = max(0.0, 100.0 * (1.0 - (monto_propuesto_total / precio_lista_total)))

        # Prepare cell texts
        sku_text = str(item.get('sku', '-'))
        cantidad_text = str(cantidad)
        precio_lista_text = format_money(precio_lista_total)
        monto_propuesto_text = f"${monto_propuesto_total:,.2f}"
        iva_text = f"${iva_total:,.2f}"
        descuento_text = f"{descuento_pct:.2f}%"
        total_text = f"${total:,.2f}"

        # estimate row height (wrap SKU if too long)
        max_sku_chars = int(col_widths[0] / 6)
        sku_lines = []
        if len(sku_text) > max_sku_chars:
            # naive wrap
            i = 0
            while i < len(sku_text):
                sku_lines.append(sku_text[i:i+max_sku_chars])
                i += max_sku_chars
        else:
            sku_lines = [sku_text]
        row_h = max(row_min_h, (len(sku_lines) * 12) + row_padding)

        # Check space
        needed = row_h + space_needed_for_footer_and_details(max(1, len(datos.get('items', []))))
        if y < bottom_margin + row_h:
            c.showPage()
            y = draw_page_header(c, height, datos, include_client_block=False)
            draw_table_header(c, y)
            y -= header_box_h

        x = x_start
        # SKU cell (centered under header)
        c.setFillColorRGB(1, 1, 1)
        c.rect(x, y - row_h + 4, col_widths[0], row_h, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        text_y = y - 10
        sku_center_x = x + (col_widths[0] / 2)
        for line in sku_lines:
            c.drawCentredString(sku_center_x, text_y, line)
            text_y -= 12
        x += col_widths[0]

        # Cantidad (center)
        c.drawCentredString(x + col_widths[1]/2, y - (row_h/2) + 4, cantidad_text)
        x += col_widths[1]

        # Precio de Lista (centered under header)
        c.drawCentredString(x + (col_widths[2] / 2), y - (row_h/2) + 4, precio_lista_text)
        x += col_widths[2]

        # Monto Propuesto (centered, bold)
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(x + (col_widths[3] / 2), y - (row_h/2) + 4, monto_propuesto_text)
        c.setFont('Helvetica', 9)
        x += col_widths[3]

        # IVA (centered)
        c.drawCentredString(x + (col_widths[4] / 2), y - (row_h/2) + 4, iva_text)
        x += col_widths[4]

        # Descuento (centered)
        c.drawCentredString(x + (col_widths[5] / 2), y - (row_h/2) + 4, descuento_text)
        x += col_widths[5]

        # Total (centered)
        c.drawCentredString(x + (col_widths[6] / 2), y - (row_h/2) + 4, total_text)

        # divider
        c.setStrokeColorRGB(0.85, 0.85, 0.85)
        c.setLineWidth(0.5)
        c.line(x_start, y - row_h + 2, x_start + usable_width, y - row_h + 2)

        y -= row_h

    # Total global (left aligned to match table rows)
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.setFillColorRGB(0.09, 0.29, 0.55)
    total_label = f"MONTO TOTAL PROPUESTO: ${total_global:,.2f}"
    c.drawString(left_margin, y, total_label)
    c.setFillColorRGB(0, 0, 0)
    y -= 30

    # Monto total en letras (alineado a la izquierda bajo el total) y añadir M/N
    try:
        monto_letras = number_to_words_es(total_global)
        monto_text = f"({str(monto_letras).capitalize()} M/N)"
        c.setFont("Helvetica", 10)
        c.drawString(left_margin, y, monto_text)
        y -= 20
    except Exception:
        pass

    # Descripciones detalladas de cada producto cotizado
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_margin, y, "Detalles de productos cotizados:")
    y -= 18
    c.setFont("Helvetica", 10)
    for item in datos.get('items', []):
        if y < bottom_margin + 80:
            c.showPage()
            y = draw_page_header(c, height, datos, include_client_block=False)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y, f"{item.get('sku', '-')}{'(' + str(item.get('cantidad', 1)) + ')' if item.get('cantidad', 1) > 1 else ''}")
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
            c.drawString(left_margin + 20, y, line)
            y -= 12
        c.drawString(left_margin + 20, y, f"Proveedor: {proveedor}")
        y -= 12
        c.drawString(left_margin + 20, y, f"Origen: {origen}")
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
