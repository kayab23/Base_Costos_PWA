from PyPDF2 import PdfReader
import sys

path = sys.argv[1] if len(sys.argv)>1 else 'api_test_cotizacion.pdf'
reader = PdfReader(path)
all_text = ''
for i, page in enumerate(reader.pages):
    try:
        txt = page.extract_text() or ''
    except Exception:
        txt = ''
    all_text += f"\n--- PAGE {i+1} ---\n" + txt
print(all_text[:1200])
