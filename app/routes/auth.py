"""Rutas de autenticación."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..db import fetch_one, get_connection
from ..security import verify_password
from ..jwt_utils import create_access_token
from fastapi import HTTPException, status, Depends
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas

router = APIRouter(prefix="/auth", tags=["Auth"])


# Nuevo endpoint /auth/login para JWT
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn=Depends(get_connection)):
    import logging
    logger = logging.getLogger("auth_debug")
    cursor = conn.cursor()
    logger.info(f"Intento de login: username={form_data.username}")
    user = fetch_one(
        cursor,
        """
        SELECT usuario_id, username, password_hash, rol, es_activo
        FROM dbo.Usuarios
        WHERE username = ?
        """,
        [form_data.username],
    )
    if not user:
        logger.warning(f"Usuario no encontrado: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    if not user["es_activo"]:
        logger.warning(f"Usuario inactivo: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    logger.info(f"Hash en BD: {user['password_hash']}")
    try:
        valid = verify_password(form_data.password, user["password_hash"])
    except Exception as e:
        logger.error(f"Error en verify_password: {e}")
        valid = False
    logger.info(f"Resultado verify_password: {valid}")
    if not valid:
        logger.warning(f"Credenciales inválidas para usuario: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    token = create_access_token({
        "usuario_id": user["usuario_id"],
        "username": user["username"],
        "rol": user["rol"]
    })
    logger.info(f"Login exitoso para usuario: {form_data.username}")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserInfo)
async def get_me(user=Depends(get_current_user)):
    """Obtiene información del usuario autenticado."""
    return user
