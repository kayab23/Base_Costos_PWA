"""Utilidades para manejar conexiones a SQL Server."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Optional, Sequence

import pyodbc

from .config import settings


def _connect() -> pyodbc.Connection:
    return pyodbc.connect(settings.sqlserver_conn, autocommit=False)


def connect() -> pyodbc.Connection:
    """Conexión directa (no context-manager). Use `with connect() as conn:` para
    obtener una conexión gestionada.
    """
    return _connect()


@contextmanager
def connection_scope() -> Iterable[pyodbc.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def get_connection() -> Iterable[pyodbc.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(cursor: pyodbc.Cursor, query: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    cursor.execute(query, params or ())
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def fetch_one(
    cursor: pyodbc.Cursor,
    query: str,
    params: Sequence[Any] | None = None,
) -> Optional[dict[str, Any]]:
    cursor.execute(query, params or ())
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
