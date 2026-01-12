"""Rutas de autenticación."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])


class UserInfo(BaseModel):
    usuario_id: int
    username: str
    rol: str


@router.get("/me", response_model=UserInfo)
def get_me(user=Depends(get_current_user)):
    """Obtiene información del usuario autenticado."""
    return user
