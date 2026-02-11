from app.db import connection_scope
import json

sku = 'MV01B-CTO-01'
try:
    with connection_scope() as conn:
        cur = conn.cursor()
        # Inspect columns present in dbo.Productos
        cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='Productos' ORDER BY ORDINAL_POSITION")
        cols = [r[0] for r in cur.fetchall()]
        print('COLUMNS:', cols)
        # Query the producto by SKU using available columns
        sel_cols = [c for c in ['sku','costo_base','moneda_base','fecha_actualizacion'] if c in cols]
        sql = f"SELECT {', '.join(sel_cols)} FROM dbo.Productos WHERE sku = ?"
        cur.execute(sql, (sku,))
        rows = cur.fetchall()
        if not rows:
            print('NOT_FOUND')
        else:
            for r in rows:
                out = {}
                for i,col in enumerate(sel_cols):
                    val = r[i]
                    if val is None:
                        out[col] = None
                    elif 'costo' in col:
                        out[col] = float(val)
                    elif 'fecha' in col or isinstance(val, (bytes,)):
                        out[col] = str(val)
                    else:
                        out[col] = val
                print(json.dumps(out, ensure_ascii=False))
except Exception as e:
    print('ERROR')
    import traceback
    traceback.print_exc()
    raise
