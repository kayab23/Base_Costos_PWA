"""Herramienta sencilla para gestionar usuarios del API."""
from __future__ import annotations

import argparse
import os

import pyodbc

from app.security import hash_password
from cost_engine import DEFAULT_CONN_STR


def get_conn() -> pyodbc.Connection:
    conn_str = os.getenv("SQLSERVER_CONN", DEFAULT_CONN_STR)
    return pyodbc.connect(conn_str, autocommit=False)


def create_user(username: str, password: str, rol: str) -> None:
    password_hash = hash_password(password)
    conn = get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.Usuarios (username, password_hash, rol, es_activo)
            VALUES (?, ?, ?, 1)
            """,
            username,
            password_hash,
            rol,
        )
        conn.commit()
        print(f"Usuario '{username}' creado correctamente.")
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
