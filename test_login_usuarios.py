import requests

USUARIOS = [
    {"username": "admin", "password": "Admin123!", "rol": "admin"},
    {"username": "direccion1", "password": "Direcc123!", "rol": "Direccion"},
    {"username": "subdir1", "password": "Subdir123!", "rol": "Subdireccion"},
    {"username": "gercom1", "password": "GerCom123!", "rol": "Gerencia_Comercial"},
    {"username": "vendedor1", "password": "Vend123!", "rol": "Vendedor"},
]

API_URL = "http://127.0.0.1:8000/auth/login"

print("Validando login de usuarios contra:", API_URL)

for user in USUARIOS:
    data = {
        "username": user["username"],
        "password": user["password"]
    }
    try:
        response = requests.post(API_URL, data=data)
        if response.status_code == 200 and "access_token" in response.json():
            print(f"✔️  Usuario '{user['username']}' login OK | Rol: {user['rol']} | Token: {response.json()['access_token'][:16]}...")
        else:
            print(f"❌ Usuario '{user['username']}' login FALLÓ | Rol: {user['rol']} | Status: {response.status_code} | Detalle: {response.text}")
    except Exception as e:
        print(f"❌ Usuario '{user['username']}' error de conexión: {e}")
