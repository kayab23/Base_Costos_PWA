import requests

url = 'http://127.0.0.1:8000/auth/login'
cases = [
    ('fernando olvera rendon', 'anuar2309'),
    ('FERNANDO OLVERA RENDON', 'anuar2309'),
    ('Fernando Olvera Rendon', 'anuar2309'),
    ('fernando olvera rendon', 'AnUaR2309'),
]

for u, p in cases:
    r = requests.post(url, data={'username': u, 'password': p})
    try:
        data = r.json()
    except Exception:
        data = r.text
    print(u, p, '->', r.status_code, data)
