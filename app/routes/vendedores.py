from fastapi import APIRouter, Query
from typing import List
from app.db import connection_scope, fetch_all

router = APIRouter(prefix="/api", tags=["vendedores"])


@router.get("/vendedores")
def list_vendedores(q: str = Query('', alias='q'), limit: int = 10, offset: int = 0) -> List[dict]:
    with connection_scope() as conn:
        cur = conn.cursor()
        term = f"%{q}%"
        sql = "SELECT id, username, nombre_completo, email, rol FROM vendedores WHERE nombre_completo LIKE ? OR username LIKE ? ORDER BY nombre_completo OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        rows = fetch_all(cur, sql, (term, term, offset, limit))
        return rows


@router.get("/vendedores/{vendedor_id}")
def get_vendedor(vendedor_id: int):
    with connection_scope() as conn:
        cur = conn.cursor()
        row = fetch_all(cur, "SELECT id, username, nombre_completo, email, rol, telefono FROM vendedores WHERE id = ?", (vendedor_id,))
        return row[0] if row else None
