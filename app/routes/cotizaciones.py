from fastapi import APIRouter, Query, Depends
from typing import List
from app.db import connection_scope, fetch_all
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["cotizaciones"])


@router.get("/cotizaciones")
def list_cotizaciones(q: str = Query('', alias='q'), limit: int = 20, offset: int = 0, user=Depends(get_current_user)) -> List[dict]:
    """List or search cotizaciones. Requires authentication."""
    term = f"%{q}%"
    with connection_scope() as conn:
        cur = conn.cursor()
        sql = (
            "SELECT id, cliente, vendedor, numero_cliente, numero_vendedor, fecha_cotizacion, created_at "
            "FROM dbo.cotizaciones "
            "WHERE numero_cliente LIKE ? OR numero_vendedor LIKE ? OR cliente LIKE ? "
            "ORDER BY created_at DESC "
            "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        )
        rows = fetch_all(cur, sql, (term, term, term, offset, limit))
        return rows
