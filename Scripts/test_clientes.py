import requests, json

LOGIN = 'http://127.0.0.1:8000/auth/login'
API = 'http://127.0.0.1:8000/api/clientes?q=IMSS'

s = requests.Session()
login = s.post(LOGIN, data={'username':'vendedor1','password':'Vend123!'}, headers={'Content-Type':'application/x-www-form-urlencoded'}, timeout=5)
print('login status', login.status_code)
if not login.ok:
    print('login fail', login.text)
    raise SystemExit(1)

token = login.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}
r = s.get(API, headers=headers, timeout=5)
print('/api/clientes status', r.status_code)
try:
    print(json.dumps(r.json()[:5], ensure_ascii=False, indent=2))
except Exception as e:
    print('could not parse json:', e)
    print('text:', r.text)
