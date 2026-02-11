"""Herramienta sencilla para gestionar usuarios del API."""
from __future__ import annotations

import argparse
import os

import pyodbc

from app.security import hash_password
from app.config import settings


def get_conn() -> pyodbc.Connection:
    conn_str = os.getenv("SQLSERVER_CONN", settings.sqlserver_conn)
    return pyodbc.connect(conn_str, autocommit=False)


def create_user(username: str, password: str, rol: str) -> None:
    """Crea un usuario en dbo.Usuarios.

    Reglas de normalización:
    - El `username` se almacena tal cual, pero las comparaciones de login usan LOWER() para
      permitir login case-insensitive.
    - Si la contraseña contiene letras mayúsculas y minúsculas y además contiene dígitos
      (alfanumérica y alternada), se marca `password_case_sensitive = 1` y se almacena el hash
      de la contraseña tal cual. En caso contrario, se almacenará el hash de la versión
      en minúsculas de la contraseña y `password_case_sensitive = 0`, permitiendo login
      independientemente de mayúsculas/minúsculas.
    """
    # Detectar si la contraseña debe ser case-sensitive
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    case_sensitive = 1 if (has_upper and has_lower and has_digit) else 0

    store_password = password if case_sensitive else password.lower()
    password_hash = hash_password(store_password)

    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.Usuarios (username, password_hash, rol, es_activo, password_case_sensitive)
            VALUES (?, ?, ?, 1, ?)
            """,
            username,
            password_hash,
            rol,
            case_sensitive,
        )
        conn.commit()
        print(f"Usuario '{username}' creado correctamente (case_sensitive={case_sensitive}).")
    except pyodbc.IntegrityError as exc:
        conn.rollback()
        raise SystemExit(f"Error: no se pudo crear el usuario. Detalle: {exc}")
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gestión básica de usuarios")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Crea un nuevo usuario")
    create_parser.add_argument("--username", required=True)
    create_parser.add_argument("--password", required=True)
    create_parser.add_argument("--rol", default="operador")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "create":
        create_user(args.username, args.password, args.rol)


if __name__ == "__main__":
    main()
