from PyPDF2 import PdfReader

pdf_path = 'test_cotizacion.pdf'
reader = PdfReader(pdf_path)
all_text = ''
for i, page in enumerate(reader.pages):
    try:
        txt = page.extract_text() or ''
    except Exception:
        txt = ''
    all_text += f"\n--- PAGE {i+1} ---\n" + txt

checks = {
    'ABC-123': 'ABC-123' in all_text,
    'XYZ-789': 'XYZ-789' in all_text,
    'PRECIO_DE_LISTA': ('Precio de Lista' in all_text or 'Precio de lista' in all_text or 'Total Máximo' in all_text or 'Total Maximo' in all_text),
    'MONTO_TOTAL_PROPUESTO': 'MONTO TOTAL PROPUESTO' in all_text or 'MONTO TOTAL' in all_text,
    'IVA_16': 'IVA 16%' in all_text or 'IVA 16' in all_text,
    'DESCUENTO_PCT': 'Descuento %' in all_text or 'Descuento' in all_text,
    'DISCOUNT_10': '10.00%' in all_text or '10%' in all_text,
    'MONTO_LETRAS': ('pesos' in all_text.lower()) or ('mxn' in all_text.lower())
}

print('Extracción de texto de PDF (primeras 800 caracteres):\n')
print(all_text[:800])
print('\nResultados de validación:')
for k, v in checks.items():
    print(f'- {k}:', 'OK' if v else 'MISSING')

# Exit code 0 if all critical checks passed
critical = ['ABC-123', 'XYZ-789', 'PRECIO_DE_LISTA', 'MONTO_TOTAL_PROPUESTO', 'IVA_16', 'DESCUENTO_PCT', 'DISCOUNT_10', 'MONTO_LETRAS']
if all(checks[c] for c in critical):
    print('\nPDF validado correctamente.')
    raise SystemExit(0)
else:
    print('\nFaltan elementos en el PDF. Revise el contenido.')
    raise SystemExit(2)
