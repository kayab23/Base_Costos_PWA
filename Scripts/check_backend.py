import requests

try:
    r = requests.get('http://127.0.0.1:8000', timeout=5)
    print('Status', r.status_code)
    print(r.text[:400])
except Exception as e:
    print('ERROR', e)
