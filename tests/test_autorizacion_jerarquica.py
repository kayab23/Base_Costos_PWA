import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Datos de ejemplo para los tests (ajusta según tu base de datos de pruebas)
USERS = {
    "vendedor": {"username": "vendedor1", "password": "Vend123!"},
    "gerencia": {"username": "gercom1", "password": "GerCom123!"},
    "subdireccion": {"username": "subdir1", "password": "Subdir123!"},
    "direccion": {"username": "direccion1", "password": "Direcc123!"},
    "admin": {"username": "admin", "password": "Admin123!"},
}

@pytest.fixture
def auth_token_vendedor():
    resp = client.post(
        "/auth/login",
        data={"username": USERS["vendedor"]["username"], "password": USERS["vendedor"]["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def auth_token_gerencia():
    resp = client.post(
        "/auth/login",
        data={"username": USERS["gerencia"]["username"], "password": USERS["gerencia"]["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def auth_token_subdireccion():
    resp = client.post(
        "/auth/login",
        data={"username": USERS["subdireccion"]["username"], "password": USERS["subdireccion"]["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def auth_token_direccion():
    resp = client.post(
        "/auth/login",
        data={"username": USERS["direccion"]["username"], "password": USERS["direccion"]["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]

@pytest.fixture
def auth_token_admin():
    resp = client.post(
        "/auth/login",
        data={"username": USERS["admin"]["username"], "password": USERS["admin"]["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_flujo_autorizacion_jerarquica(auth_token_vendedor, auth_token_gerencia, auth_token_subdireccion, auth_token_direccion):
    # 1. Vendedor crea solicitud con precio bajo (requiere escalamiento)
    solicitud = {
        "sku": "HP30B-CTO-01",
        "transporte": "Maritimo",
        "precio_propuesto": 10000,  # Debajo de todos los mínimos
        "cliente": "TestCliente",
        "cantidad": 1,
        "justificacion": "Test de integración"
    }
    resp = client.post("/autorizaciones/solicitar", json=solicitud, headers={"Authorization": f"Bearer {auth_token_vendedor}"})
    # Espera 400 si el precio está por debajo del mínimo permitido
    if resp.status_code == 400:
        # Solicitud rechazada, no continuar con aprobación
        return
    assert resp.status_code == 200
    solicitud_id = resp.json()["id"]
    # 2. Gerencia intenta aprobar (debe poder si está en su rango)
    resp = client.put(f"/autorizaciones/{solicitud_id}/aprobar", json={"comentarios": "Aprobado por gerencia"}, headers={"Authorization": f"Bearer {auth_token_gerencia}"})
    if resp.status_code == 403:
        # Si no puede, subdireccion debe poder
        resp = client.put(f"/autorizaciones/{solicitud_id}/aprobar", json={"comentarios": "Aprobado por subdireccion"}, headers={"Authorization": f"Bearer {auth_token_subdireccion}"})
        assert resp.status_code == 200
    else:
        assert resp.status_code == 200
    # 3. Dirección puede aprobar cualquier solicitud
    solicitud2 = solicitud.copy()
    solicitud2["precio_propuesto"] = 5000  # Aún más bajo
    resp = client.post("/autorizaciones/solicitar", json=solicitud2, headers={"Authorization": f"Bearer {auth_token_vendedor}"})
    assert resp.status_code == 200
    solicitud_id2 = resp.json()["id"]
    resp = client.put(f"/autorizaciones/{solicitud_id2}/aprobar", json={"comentarios": "Aprobado por direccion"}, headers={"Authorization": f"Bearer {auth_token_direccion}"})
    assert resp.status_code == 200
