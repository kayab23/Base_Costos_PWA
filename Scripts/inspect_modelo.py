import pyodbc
from app.config import settings

conn = pyodbc.connect(settings.sqlserver_conn)
cur = conn.cursor()
cur.execute("SELECT TOP 20 sku, descripcion, modelo FROM dbo.Productos WHERE modelo IS NOT NULL AND LTRIM(RTRIM(modelo)) <> ''")
rows = cur.fetchall()
for r in rows:
    print(r.sku, '|', r.descripcion[:60], '|', r.modelo)
print('--- count non-null ---')
cur.execute("SELECT COUNT(1) FROM dbo.Productos WHERE modelo IS NOT NULL AND LTRIM(RTRIM(modelo)) <> ''")
print(cur.fetchone()[0])
cur.close()
conn.close()