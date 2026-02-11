from app.db import connection_scope

create_sql = '''
CREATE TABLE cotizaciones (
  id INT IDENTITY PRIMARY KEY,
  cliente VARCHAR(255) NULL,
  vendedor VARCHAR(255) NULL,
  numero_cliente VARCHAR(100) NULL,
  numero_vendedor VARCHAR(100) NULL,
  fecha_cotizacion DATETIME NULL,
  payload_json NVARCHAR(MAX) NULL,
  created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_cotizaciones_numcliente ON cotizaciones(numero_cliente);
CREATE INDEX idx_cotizaciones_numvendedor ON cotizaciones(numero_vendedor);
'''

with connection_scope() as conn:
    cur = conn.cursor()
    # Check if table exists
    cur.execute("SELECT OBJECT_ID('dbo.cotizaciones','U')")
    obj = cur.fetchone()[0]
    if obj:
        print('cotizaciones table already exists (OBJECT_ID=', obj, ')')
    else:
        print('Creating cotizaciones table...')
        cur.execute(create_sql)
        conn.commit()
        print('Created table cotizaciones')
