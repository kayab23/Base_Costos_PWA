import pyodbc
from app.config import settings
from pathlib import Path

SQL_FILE = Path('sql/create_clientes_vendedores.sql')
if not SQL_FILE.exists():
    print('SQL file not found:', SQL_FILE)
    raise SystemExit(1)

conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
with open(SQL_FILE, 'r', encoding='utf-8') as f:
    sql = f.read()

# Split on GO or semicolon per batch (simple approach)
commands = [s.strip() for s in sql.replace('\r', '\n').split('\n\n') if s.strip()]
cur = conn.cursor()
for cmd in commands:
    try:
        cur.execute(cmd)
    except Exception as e:
        print('Command failed:', e)
print('SQL script executed. Verify tables exist.')
cur.close()
conn.close()
