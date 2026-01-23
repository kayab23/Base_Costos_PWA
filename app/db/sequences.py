from datetime import datetime
from app.db import connection_scope, fetch_one, fetch_all


def get_next_quote_numbers(cliente_codigo: str | None, vendedor_username: str | None) -> dict:
    """Atomically get and increment next sequence numbers for client and vendor.
    Returns dict with 'cliente_num' and 'vendedor_num'."""
    cliente_num = None
    vendedor_num = None
    with connection_scope() as conn:
        cur = conn.cursor()
        # client sequence
        if cliente_codigo:
            row = fetch_all(cur, "SELECT id, last_num FROM cotizacion_secuencias WHERE cliente_codigo = ?", (cliente_codigo,))
            if row:
                nextn = row[0]['last_num'] + 1
                cur.execute("UPDATE cotizacion_secuencias SET last_num = ?, updated_at = ? WHERE id = ?", (nextn, datetime.utcnow(), row[0]['id']))
                cliente_num = nextn
            else:
                cur.execute("INSERT INTO cotizacion_secuencias (cliente_codigo, last_num, updated_at) VALUES (?, ?, ?)", (cliente_codigo, 1, datetime.utcnow()))
                cliente_num = 1
        # vendor sequence
        if vendedor_username:
            row = fetch_all(cur, "SELECT id, last_num FROM cotizacion_secuencias WHERE vendedor_username = ?", (vendedor_username,))
            if row:
                nextn = row[0]['last_num'] + 1
                cur.execute("UPDATE cotizacion_secuencias SET last_num = ?, updated_at = ? WHERE id = ?", (nextn, datetime.utcnow(), row[0]['id']))
                vendedor_num = nextn
            else:
                cur.execute("INSERT INTO cotizacion_secuencias (vendedor_username, last_num, updated_at) VALUES (?, ?, ?)", (vendedor_username, 1, datetime.utcnow()))
                vendedor_num = 1
        conn.commit()
    return {'cliente_num': cliente_num, 'vendedor_num': vendedor_num}
