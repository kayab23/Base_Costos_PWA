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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .db import fetch_one, get_connection
from .security import verify_password

# Objeto de seguridad HTTP Basic para extraer credenciales del header
security = HTTPBasic()


def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    conn=Depends(get_connection),
):
    """Valida las credenciales del usuario y retorna sus datos.
    
    Esta función se usa como dependencia en endpoints protegidos.
    
    Args:
        credentials: Credenciales extraídas del header Authorization
        conn: Conexión a base de datos (inyectada automáticamente)
    
    Returns:
        dict: Datos del usuario autenticado con keys:
            - usuario_id: ID numérico en la tabla Usuarios
            - username: Nombre de usuario
            - rol: Rol jerárquico (Vendedor, Gerencia_Comercial, etc.)
    
    Raises:
        HTTPException 401: Si usuario no existe, está inactivo, o password incorrecto
    """
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
