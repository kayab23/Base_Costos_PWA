"""Rutas de autenticación."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from .. import schemas

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=schemas.UserInfo)
def get_me(user=Depends(get_current_user)):
    """Obtiene información del usuario autenticado."""
    return user
