from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import Optional
from app.db import connection_scope, fetch_all
from app.auth import get_current_user
import json

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"]) 


def _format_currency(v: float) -> str:
    return f"${v:,.2f}" if v is not None else "-"


@router.get("/metrics")
def metrics(periodDays: int = Query(30, alias='periodDays'), vendedor: Optional[str] = Query('all')):
    """Aggregate simple KPIs from dbo.cotizaciones for the requested period.
    This implementation parses stored JSON payloads and computes totals client-side.
    """
    cutoff = datetime.utcnow() - timedelta(days=periodDays)
    with connection_scope() as conn:
        cur = conn.cursor()
        sql = (
            "SELECT id, cliente, vendedor, numero_cliente, numero_vendedor, fecha_cotizacion, payload_json, created_at "
            "FROM dbo.cotizaciones "
            "WHERE created_at >= ? "
        )
        params = [cutoff]
        if vendedor and vendedor != 'all':
            sql += " AND vendedor = ? "
            params.append(vendedor)
        sql += " ORDER BY created_at DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()

    total_sales = 0.0
    quote_count = 0
    sales_by_day = {}
    client_agg = {}
    recent_quotes = []
    discounts = []

    for r in rows:
        # cursor description: (id, cliente, vendedor, numero_cliente, numero_vendedor, fecha_cotizacion, payload_json, created_at)
        try:
            payload = json.loads(r[6]) if r[6] else {}
        except Exception:
            payload = {}
        items = payload.get('items', []) if isinstance(payload, dict) else []
        quote_total = 0.0
        item_discounts = []
        for it in items:
            try:
                cantidad = float(it.get('cantidad', 1))
            except Exception:
                cantidad = 1.0
            try:
                monto = float(it.get('monto_propuesto', 0) or 0)
            except Exception:
                monto = 0.0
            try:
                precio_lista = float(it.get('precio_maximo_lista') or it.get('precio_maximo') or 0) or 0.0
            except Exception:
                precio_lista = 0.0
            line_total = monto * cantidad
            quote_total += line_total
            if precio_lista > 0:
                discount_pct = max(0.0, (1.0 - (monto / precio_lista)) * 100.0)
                item_discounts.append(discount_pct)
        total_sales += quote_total
        quote_count += 1
        # sales by day
        fecha = r[5] if r[5] else r[7]
        try:
            fecha_dt = fecha if isinstance(fecha, datetime) else datetime.fromisoformat(str(fecha))
        except Exception:
            fecha_dt = datetime.utcnow()
        day = fecha_dt.date().isoformat()
        sales_by_day.setdefault(day, 0.0)
        sales_by_day[day] += quote_total
        # client aggregation
        client_name = r[1] or 'Desconocido'
        client_agg.setdefault(client_name, 0.0)
        client_agg[client_name] += quote_total
        # recent quotes
        recent_quotes.append({
            'id': r[0],
            'folio': (r[3] or r[4] or ''),
            'fecha': fecha_dt.strftime('%Y-%m-%d %H:%M'),
            'cliente': client_name,
            'vendedor': r[2] or '',
            'valor': quote_total,
            'valor_formatted': _format_currency(quote_total),
            'estado': payload.get('estado', 'N/A') if isinstance(payload, dict) else 'N/A'
        })
        if item_discounts:
            discounts.extend(item_discounts)

    # Prepare structured response
    sales_by_day_list = [{'date': d, 'amount': a} for d, a in sorted(sales_by_day.items())]
    top_clients = [{'name': k, 'amount': v} for k, v in sorted(client_agg.items(), key=lambda x: x[1], reverse=True)[:10]]
    avg_discount = (sum(discounts) / len(discounts)) if discounts else None

    resp = {
        'period_days': periodDays,
        'total_sales': total_sales,
        'total_sales_formatted': _format_currency(total_sales),
        'quote_count': quote_count,
        'sales_by_day': sales_by_day_list,
        'top_clients': top_clients,
        'avg_discount_percent': round(avg_discount, 2) if avg_discount is not None else None,
        'avg_discount_percent_formatted': (f"{avg_discount:.2f}%" if avg_discount is not None else None),
        'recent_quotes': recent_quotes[:20]
    }
    return resp
