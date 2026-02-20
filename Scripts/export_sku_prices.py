r"""Exportador de SKUs y precios a Excel.

Genera un archivo Excel con las columnas:
- sku
- descripcion
- costo_base_mxn (desde dbo.PreciosCalculados / dbo.LandedCostCache)
- vendedor_min_maritimo
- maximo_maritimo
- vendedor_min_aereo
- maximo_aereo

Uso:
  .venv\Scripts\python.exe Scripts\export_sku_prices.py [output.xlsx]

Si no se proporciona output, se crea `outputs/sku_prices_YYYYMMDD_HHMMSS.xlsx`.

El script consulta `dbo.PreciosCalculados` y `dbo.Productos`.
"""
from pathlib import Path
import sys
import pyodbc
import datetime
from openpyxl import Workbook
from app.config import settings

DEFAULT_OUT_DIR = Path('outputs')
SKU_COLS = [
    'sku',
    'descripcion',
    'modelo',
    'costo_base_mxn',
    'vendedor_min_maritimo',
    'maximo_maritimo',
    'vendedor_min_aereo',
    'maximo_aereo',
]

SQL = """
SELECT p.sku, p.descripcion, p.modelo, pc.transporte, 
    pc.costo_base_mxn, pc.precio_vendedor_min, pc.precio_maximo
FROM dbo.PreciosCalculados pc
LEFT JOIN dbo.Productos p ON p.sku = pc.sku
WHERE pc.transporte IN ('Maritimo','Aereo')
ORDER BY p.sku, pc.transporte
"""


def get_conn():
    conn_str = getattr(settings, 'sqlserver_conn', None) or None
    if not conn_str:
        # Fallback to environment handled inside pyodbc if present
        conn = pyodbc.connect()
    else:
        conn = pyodbc.connect(conn_str)
    return conn


def fetch_data(conn):
    cur = conn.cursor()
    cur.execute(SQL)
    rows = cur.fetchall()
    cols = [c[0].lower() for c in cur.description]
    results = [dict(zip(cols, r)) for r in rows]
    cur.close()
    return results


def aggregate(rows):
    out = {}
    for r in rows:
        sku = (r.get('sku') or '').strip()
        if not sku:
            continue
        rec = out.setdefault(sku, {
            'sku': sku,
            'descripcion': r.get('descripcion') or '',
            'costo_base_mxn': None,
            'vendedor_min_maritimo': None,
            'maximo_maritimo': None,
            'vendedor_min_aereo': None,
            'maximo_aereo': None,
        })
        trans = (r.get('transporte') or '').strip()
        try:
            costo = float(r.get('costo_base_mxn')) if r.get('costo_base_mxn') is not None else None
        except Exception:
            costo = None
        try:
            vendedor_min = float(r.get('precio_vendedor_min')) if r.get('precio_vendedor_min') is not None else None
        except Exception:
            vendedor_min = None
        try:
            maximo = float(r.get('precio_maximo')) if r.get('precio_maximo') is not None else None
        except Exception:
            maximo = None
        if costo is not None:
            rec['costo_base_mxn'] = costo
        # modelo: si no existe en la columna, intentar extraer desde la descripcion
        modelo_val = (r.get('modelo') or '').strip() if r.get('modelo') is not None else ''
        if modelo_val:
            rec['modelo'] = modelo_val
        else:
            # heurística simple: buscar patrones comunes en la descripción
            desc = (r.get('descripcion') or '')
            import re
            m = re.search(r"Model[:\s-]*([A-Z0-9\-_/\.]+)", desc, re.IGNORECASE)
            if not m:
                m = re.search(r"\b([A-Z]{1,3}[\- ]?\d{2,4}[A-Z0-9\-]*)\b", desc)
            if m:
                rec['modelo'] = m.group(1).strip()
        if trans.lower() == 'maritimo':
            rec['vendedor_min_maritimo'] = vendedor_min
            rec['maximo_maritimo'] = maximo
        elif trans.lower() == 'aereo':
            rec['vendedor_min_aereo'] = vendedor_min
            rec['maximo_aereo'] = maximo
    return list(out.values())


def write_excel(rows, outpath: Path):
    wb = Workbook()
    ws = wb.active
    assert ws is not None, "Worksheet not created"
    ws.title = 'SKU_Precios'
    # ensure header row
    ws.append(SKU_COLS)
    for r in rows:
        ws.append([
            r.get('sku'),
            r.get('descripcion'),
            r.get('modelo'),
            r.get('costo_base_mxn'),
            r.get('vendedor_min_maritimo'),
            r.get('maximo_maritimo'),
            r.get('vendedor_min_aereo'),
            r.get('maximo_aereo'),
        ])
    outpath.parent.mkdir(parents=True, exist_ok=True)
    wb.save(outpath)


def main(argv):
    out = None
    if len(argv) >= 2:
        out = Path(argv[1])
    else:
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        out = DEFAULT_OUT_DIR / f'sku_prices_{ts}.xlsx'

    conn = get_conn()
    try:
        rows = fetch_data(conn)
        agg = aggregate(rows)
        write_excel(agg, out)
        print(f'Wrote {len(agg)} SKUs to {out}')
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(main(sys.argv))
