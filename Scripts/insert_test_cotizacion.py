from app.db import connection_scope

with connection_scope() as conn:
    cur = conn.cursor()
    cur.execute("INSERT INTO dbo.cotizaciones (cliente, vendedor, numero_cliente, numero_vendedor, fecha_cotizacion, payload_json, created_at) VALUES (?, ?, ?, ?, GETDATE(), ?, GETDATE())",
                ('PRUEBA', 'vendedor1', 'PRUEBA/00001', 'vendedor1/00001', '{"test":true}'))
    conn.commit()
print('inserted')
