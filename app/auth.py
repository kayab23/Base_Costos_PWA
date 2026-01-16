"""Autenticación y autorización basada en HTTP Basic Auth.

Este módulo gestiona la autenticación de usuarios mediante:
- HTTP Basic Authentication (usuario y contraseña en header Authorization)
- Contraseñas hasheadas con bcrypt almacenadas en dbo.Usuarios
- Validación de usuario activo (es_activo = 1)
- Inyección de dependencia get_current_user para proteger endpoints

Flujo de autenticación:
1. Cliente envía credenciales en header: Authorization: Basic base64(user:pass)
2. get_current_user extrae credenciales y consulta BD
3. Verifica password con bcrypt y estado activo
4. Retorna datos del usuario (usuario_id, username, rol) para usar en endpoints
5. Si falla, retorna HTTP 401 Unauthorized

Roles soportados:
- admin: Acceso total al sistema
- Direccion: Nivel jerárquico más alto de autorización (35% descuento)
- Subdireccion: Segundo nivel de autorización (30% descuento)
- Gerencia_Comercial: Tercer nivel de autorización (25% descuento)
- Vendedor: Nivel base, solicita autorizaciones (20% descuento)
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security import OAuth2PasswordBearer

from .db import fetch_one, get_connection
from .security import verify_password
from .jwt_utils import create_access_token, decode_access_token


# OAuth2PasswordBearer para JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



# Nuevo get_current_user para JWT
async def get_current_user(token: str = Depends(oauth2_scheme), conn=Depends(get_connection)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    cursor = conn.cursor()
    user = fetch_one(
        cursor,
        """
        SELECT usuario_id, username, rol, es_activo
        FROM dbo.Usuarios
        WHERE usuario_id = ?
        """,
        [payload.get("usuario_id")],
    )
    if not user or not user["es_activo"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    return {
        "usuario_id": user["usuario_id"],
        "username": user["username"],
        "rol": user["rol"],
    }
