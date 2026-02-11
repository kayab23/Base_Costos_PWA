from app.db import connection_scope, fetch_all

with connection_scope() as conn:
    cur = conn.cursor()
    rows = fetch_all(cur, "SELECT TOP 5 id, cliente, vendedor, numero_cliente, numero_vendedor, fecha_cotizacion, created_at FROM dbo.cotizaciones ORDER BY created_at DESC")
    print('found', len(rows), 'rows')
    for r in rows:
        print(r)
