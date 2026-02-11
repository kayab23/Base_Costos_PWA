import requests
import json
import sys

# Configurable timeout (seconds) for HTTP requests to avoid hanging
HTTP_TIMEOUT = 10

url = 'http://127.0.0.1:8000/cotizacion/pdf'
login_url = 'http://127.0.0.1:8000/auth/login'
payload = {
    'cliente': 'IMSS CENTRO',
    'items': [
        {
            'sku': '1199-00055-01',
            'cantidad': 2,
            'precio_maximo_lista': 5580.86,
            'monto_propuesto': 5000.0,
            'precio_vendedor_min': 10000.0,
            'precio_minimo_lista': 10000.0,
            'descripcion': 'Heater only - test',
            'proveedor': 'Medcaptain',
            'origen': 'Importado'
        }
    ]
}
print('Logging in to get token...')
try:
    login = requests.post(
        login_url,
        data={'username': 'vendedor1', 'password': 'Vend123!'},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=HTTP_TIMEOUT,
    )
except Exception as e:
    print('Login request error:', repr(e))
    sys.exit(2)

if login.status_code != 200:
    print('Login failed:', login.status_code, login.text)
    sys.exit(1)

token = login.json().get('access_token')
if not token:
    print('Login succeeded but no token returned:', login.text)
    sys.exit(1)
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
print('Posting to', url)
try:
    resp = requests.post(url, data=json.dumps(payload), headers=headers, timeout=HTTP_TIMEOUT)
except Exception as e:
    print('Request to /cotizacion/pdf failed:', repr(e))
    sys.exit(3)
print('Status:', resp.status_code)
if resp.status_code == 200:
    out = 'api_test_cotizacion.pdf'
    with open(out, 'wb') as f:
        f.write(resp.content)
    print('Saved:', out)
    # Extract and print first part of text for verification
    try:
        from PyPDF2 import PdfReader
        r = PdfReader(out)
        txt = ''
        for i, p in enumerate(r.pages):
            try:
                txt += p.extract_text() or ''
            except Exception:
                pass
        print('\nPDF extract preview:\n')
        print(txt[:800])
    except Exception as e:
        print('Could not extract PDF text:', e)
else:
    try:
        print('Response:', resp.json())
    except Exception:
        print('Response text:', resp.text)
