import pyodbc
from app.config import settings

conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
cur = conn.cursor()

for t in ('clientes','vendedores'):
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"{t}: {cnt}")

cur.close()
conn.close()
