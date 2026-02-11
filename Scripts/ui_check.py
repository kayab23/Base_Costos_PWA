from playwright.sync_api import sync_playwright
from PyPDF2 import PdfReader
import json

URL = 'http://localhost:5173'

# Sample mirrors the attachment: per-unit precio_maximo_lista such that Total Máximo = 82,679.52
SAMPLE = [
    {
        "sku": "1199-00052-02",
        "cantidad": 2,
        "precio_maximo": 41339.76,
        "precio_maximo_lista": 41339.76,
        "precio_vendedor_min": 2000.0,
        "precio_minimo_lista": 2000.0,
        # monto_propuesto reported by seller is per-unit 35000. We'll let the frontend treat it as unit price and the PDF generator will multiply by cantidad
        "monto_propuesto": 35000.0,
        "logo_path": None,
        "proveedor": "Proveedor X",
        "origen": "México"
    }
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL)

    def handle_pricing(route, request):
        route.fulfill(status=200, body=json.dumps(SAMPLE), headers={"Content-Type": "application/json"})

    page.route('**/pricing/listas**', handle_pricing)

    # Ensure frontend thinks we're logged in (set state and show cards without performing real login)
    page.evaluate("() => { localStorage.setItem('authToken','FAKE-TOKEN'); localStorage.setItem('userRole','Vendedor'); window.state = window.state || {}; window.state.auth = 'FAKE-TOKEN'; window.state.userRole = 'Vendedor'; document.querySelectorAll('.card').forEach(c => c.style.display = ''); }")
    page.reload()
    # Wait briefly for UI to re-render (element may be present but hidden)
    page.wait_for_selector('#user-role', state='attached', timeout=15000)

    # Wait for inputs to be ready, then fill SKU and quantity
    page.wait_for_selector('.sku-input', state='attached', timeout=10000)
    # Fill SKU and quantity and trigger consult
    # Set inputs via JS (may be hidden) and invoke loadLanded directly
    page.evaluate("() => { document.querySelector('.sku-input').value = '1199-00052-02'; document.querySelector('.cantidad-input').value = '2'; document.getElementById('input-cliente').value = 'ACME S.A. DE C.V.'; if (typeof loadLanded === 'function') loadLanded(); }")
    # small wait to allow frontend to process the mocked response
    page.wait_for_timeout(800)

    try:
        # give more time for table population
        page.wait_for_selector('table#landed-table tbody tr:has-text("1199-00052-02")', timeout=20000)
        print('Fila 1199-00052-02 encontrada en tabla')
    except Exception as e:
        print('No se encontró fila 1199-00052-02:', e)
        browser.close()
        raise SystemExit(2)

    # Click global PDF and wait for response
    with page.expect_response(lambda r: '/cotizacion/pdf' in r.url and r.status == 200, timeout=40000) as resp_info:
        page.click('#pdf-cotizar-btn-global')
    response = resp_info.value
    body = response.body()
    out_path = 'ui_test_cotizacion.pdf'
    with open(out_path, 'wb') as f:
        f.write(body)
    print('PDF descargado:', out_path)

    browser.close()

    # Validate PDF contents
    reader = PdfReader(out_path)
    all_text = ''
    for p in reader.pages:
        try:
            txt = p.extract_text() or ''
        except Exception:
            txt = ''
        all_text += txt + '\n'

    checks = {
        'SKU_PRESENT': '1199-00052-02' in all_text,
        'TOTAL_MAXIMO': ('Total Máximo' in all_text or 'Precio de Lista' in all_text),
        'MONTO_TOTAL_PROPUESTO': 'MONTO TOTAL PROPUESTO: $81,200.00' in all_text or 'MONTO TOTAL PROPUESTO: $81,200' in all_text,
        'TOTAL_VALUE': '$81,200.00' in all_text or '$81200.00' in all_text
    }

    print('\nExtracción PDF (primeras 800 chars):\n')
    print(all_text[:800])
    print('\nResultados:')
    for k, v in checks.items():
        print(f'- {k}:', 'OK' if v else 'MISSING')

    if all(checks.values()):
        print('\nE2E UI check OK')
        raise SystemExit(0)
    else:
        print('\nE2E UI check FALLÓ')
        raise SystemExit(3)
