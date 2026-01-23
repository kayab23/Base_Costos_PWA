"""Package-level DB helpers for app.db package.

This exposes `connection_scope`, `fetch_all`, and `fetch_one` so
submodules like `app.db.sequences` can import them as `from app.db import ...`.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Optional, Sequence

import pyodbc

from app.config import settings


def _connect() -> pyodbc.Connection:
    return pyodbc.connect(settings.sqlserver_conn, autocommit=False)


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


__all__ = [
    "connection_scope",
    "get_connection",
    "fetch_all",
    "fetch_one",
]
