from PyPDF2 import PdfReader
import sys

generated = 'test_cotizacion.pdf'
attached = r'C:\Users\FernandoOlveraRendon\Downloads\cotizacion_multiSKU (40).pdf'

def extract_text(path, max_chars=2000):
    try:
        r = PdfReader(path)
    except Exception as e:
        return f'ERROR opening {path}: {e}'
    all_text = ''
    for i, p in enumerate(r.pages):
        try:
            txt = p.extract_text() or ''
        except Exception:
            txt = ''
        all_text += f"\n--- PAGE {i+1} ---\n" + txt
    return all_text

print('Extrayendo generada:', generated)
gen = extract_text(generated)
print(gen[:1200])
print('\n--- Attached PDF ---')
att = extract_text(attached)
print(att[:1200])

# Simple presence checks
keys = ['Precio de Lista', 'Total Máximo', 'MONTO TOTAL PROPUESTO', 'IVA 16%', 'Descuento %', '1199-00052-02']
print('\nChecks:')
for k in keys:
    print(f"- {k}: gen={'YES' if k in gen else 'NO'}, attached={'YES' if k in att else 'NO'}")

# Exit with 0
sys.exit(0)
