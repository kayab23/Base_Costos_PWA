import sys
import json
import pyodbc
from app.config import settings

if len(sys.argv) < 2:
    print('Usage: query_sku_specific.py <SKU>')
    sys.exit(1)
SKU = sys.argv[1]

try:
    conn = pyodbc.connect(settings.sqlserver_conn)
    cur = conn.cursor()

    def fetch(query, params=()):
        cur.execute(query, params)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return rows

    out = {}
    out['Productos'] = fetch("SELECT sku, descripcion, modelo, moneda_base, costo_base, fecha_actualizacion FROM dbo.Productos WHERE sku = ?", (SKU,))
    out['LandedCostCache'] = fetch("SELECT * FROM dbo.LandedCostCache WHERE sku = ? ORDER BY transporte", (SKU,))
    out['PreciosCalculados'] = fetch("SELECT * FROM dbo.PreciosCalculados WHERE sku = ? ORDER BY transporte", (SKU,))

    print(json.dumps(out, default=str, ensure_ascii=False, indent=2))

except Exception as e:
    print('ERROR:', str(e))
    sys.exit(2)

finally:
    try:
        cur.close()
    except:
        pass
    try:
        conn.close()
    except:
        pass
