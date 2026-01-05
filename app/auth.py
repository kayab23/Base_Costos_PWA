"""Autenticación básica con usuario y contraseña."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .db import fetch_one, get_connection
from .security import verify_password

security = HTTPBasic()


def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    conn=Depends(get_connection),
):
    cursor = conn.cursor()
    user = fetch_one(
        cursor,
        """
        SELECT usuario_id, username, password_hash, rol, es_activo
        FROM dbo.Usuarios
        WHERE username = ?
        """,
        [credentials.username],
    )
    if not user or not user["es_activo"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    return {
        "usuario_id": user["usuario_id"],
        "username": user["username"],
        "rol": user["rol"],
    }
