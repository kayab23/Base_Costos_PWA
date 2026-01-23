from fastapi import APIRouter, Query, Depends
from typing import List
from app.db import connection_scope, fetch_all
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["clientes"])


@router.get("/clientes")
def list_clientes(q: str = Query('', alias='q'), limit: int = 10, offset: int = 0, user=Depends(get_current_user)) -> List[dict]:
    with connection_scope() as conn:
        cur = conn.cursor()
        term = f"%{q}%"
        sql = "SELECT id, codigo, nombre, rfc, telefono, email FROM clientes WHERE nombre LIKE ? OR codigo LIKE ? ORDER BY nombre OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        rows = fetch_all(cur, sql, (term, term, offset, limit))
        return rows


@router.get("/clientes/{cliente_id}")
def get_cliente(cliente_id: int, user=Depends(get_current_user)):
    with connection_scope() as conn:
        cur = conn.cursor()
        row = fetch_all(cur, "SELECT id, codigo, nombre, rfc, direccion, contacto, telefono, email FROM clientes WHERE id = ?", (cliente_id,))
        return row[0] if row else None
