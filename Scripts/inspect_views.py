import pyodbc
from app.config import settings

VIEWS = ['Productos_view', 'PreciosCalculados_view', 'PreciosCalculados_vendedor']

conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
cur = conn.cursor()

for v in VIEWS:
    print('\n' + '='*60)
    print(f'VIEW: dbo.{v}')
    # definition from sys.sql_modules
    try:
        cur.execute("SELECT definition FROM sys.sql_modules m JOIN sys.views v ON m.object_id = v.object_id WHERE v.name = ?", (v,))
        row = cur.fetchone()
        if row and row[0]:
            print('\n-- Definition:')
            print(row[0])
        else:
            print('No definition found in sys.sql_modules for', v)
    except Exception as e:
        print('Error fetching definition for', v, e)
    # columns
    try:
        cur.execute("SELECT COLUMN_NAME, ORDINAL_POSITION, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=? ORDER BY ORDINAL_POSITION", (v,))
        cols = cur.fetchall()
        if not cols:
            print('\nNo columns found for view', v)
        else:
            print('\n-- Columns:')
            for c in cols:
                print(f"{c.COLUMN_NAME} (pos={c.ORDINAL_POSITION}) type={c.DATA_TYPE}")
    except Exception as e:
        print('Error fetching columns for', v, e)

conn.close()
