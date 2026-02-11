import pyodbc
from app.config import settings

conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
cur = conn.cursor()

tables = ['clientes', 'vendedores', 'cotizacion_secuencias']
for t in tables:
    cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (t,))
    row = cur.fetchone()
    print(f"{t}: {'FOUND' if row else 'MISSING'}")

cur.close()
conn.close()
