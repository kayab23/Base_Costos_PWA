"""Rutas de autenticación."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from slowapi.util import get_remote_address
from slowapi import Limiter

from ..auth import get_current_user
from ..db import fetch_one, get_connection
from ..security import verify_password
from ..jwt_utils import create_access_token, create_refresh_token
from fastapi import HTTPException, status, Depends
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas

from fastapi import Request
router = APIRouter(prefix="/auth", tags=["Auth"])
from fastapi import Request
from fastapi import Depends as FastAPIDepends


# Nuevo endpoint /auth/login para JWT
from app.limiter import limiter

@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), conn=Depends(get_connection)):
    import logging
    logger = logging.getLogger("auth_debug")
    cursor = conn.cursor()
    logger.info(f"Intento de login: username={form_data.username}")
    # Buscar usuario por username normalizado (case-insensitive)
    user = fetch_one(
        cursor,
        """
        SELECT usuario_id, username, password_hash, rol, es_activo, ISNULL(password_case_sensitive, 0) AS password_case_sensitive
        FROM dbo.Usuarios
        WHERE LOWER(LTRIM(RTRIM(username))) = LOWER(LTRIM(RTRIM(?)))
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
        # Si el usuario marcó su contraseña como case-sensitive, verificar exactamente.
        if user.get("password_case_sensitive"):
            valid = verify_password(form_data.password, user["password_hash"])
        else:
            # Intentar verificar con la entrada tal cual o con la versión en minúsculas
            valid = verify_password(form_data.password, user["password_hash"]) or verify_password(form_data.password.lower(), user["password_hash"])
    except Exception as e:
        logger.error(f"Error en verify_password: {e}")
        valid = False
    logger.info(f"Resultado verify_password: {valid}")
    if not valid:
        logger.warning(f"Credenciales inválidas para usuario: {form_data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    token_data = {
        "usuario_id": user["usuario_id"],
        "username": user["username"],
        "rol": user["rol"]
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    logger.info(f"Login exitoso para usuario: {form_data.username}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# Endpoint para refrescar access token usando refresh token
from ..jwt_utils import decode_refresh_token, create_access_token, create_refresh_token
from fastapi import Body

@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(data: schemas.TokenRefreshRequest = Body(...)):
    payload = decode_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado")
    # Generar nuevos tokens
    token_data = {
        "usuario_id": payload["usuario_id"],
        "username": payload["username"],
        "rol": payload["rol"]
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserInfo)
async def get_me(user=Depends(get_current_user)):
    """Obtiene información del usuario autenticado."""
    return user
