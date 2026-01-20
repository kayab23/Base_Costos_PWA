"""
"""
from __future__ import annotations


from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from .jwt_utils import create_access_token, decode_access_token


# OAuth2PasswordBearer para JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")




# Nuevo get_current_user para JWT
from fastapi.security import OAuth2PasswordBearer
from .db import fetch_one, get_connection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

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
