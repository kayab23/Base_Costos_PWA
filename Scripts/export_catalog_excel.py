r"""
Exporta un catálogo de SKUs con landed cost y mark-up a un archivo Excel.
Genera: outputs/catalog_landed_markup_YYYYMMDD_HHMMSS.xlsx

Columnas: sku, descripcion, modelo, costo_base, transporte, landed_cost_mxn, mark_up

Uso:
    & .venv\Scripts\python.exe Scripts\export_catalog_excel.py
"""
from __future__ import annotations
import os
import pyodbc
import pandas as pd
from datetime import datetime

DEFAULT_CONN = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=BD_Calculo_Costos;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
CONN = os.getenv('SQLSERVER_CONN', DEFAULT_CONN)

SQL = """
WITH latest_lc AS (
    SELECT sku, transporte, landed_cost_mxn, mark_up, calculado_en,
           ROW_NUMBER() OVER (PARTITION BY sku, transporte ORDER BY calculado_en DESC) AS rn
    FROM dbo.LandedCostCache
)
SELECT p.sku, p.descripcion, COALESCE(p.modelo, '') AS modelo, p.costo_base,
       ll.transporte, ll.landed_cost_mxn, ll.mark_up
FROM dbo.Productos p
LEFT JOIN latest_lc ll ON p.sku = ll.sku AND ll.rn = 1
ORDER BY p.sku, ll.transporte
"""

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
os.makedirs(OUT_DIR, exist_ok=True)

def fetch_to_df(conn_str: str) -> pd.DataFrame:
    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    cur.execute(SQL)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    conn.close()
    # Convert pyodbc rows to list of dicts for pandas
    dict_rows = [dict(zip(cols, r)) for r in rows]
    df = pd.DataFrame.from_records(dict_rows, columns=cols)
    return df


def main():
    try:
        df = fetch_to_df(CONN)
    except Exception as e:
        print('ERROR: no se pudo consultar la BD:', e)
        return
    if df.empty:
        print('No se encontraron filas. Generando Excel vacío con cabecera.')
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(OUT_DIR, f'catalog_landed_markup_{ts}.xlsx')
    try:
        df.to_excel(out_path, index=False, engine='openpyxl')
        print('Excel generado:', out_path)
    except Exception as e:
        print('ERROR al generar Excel:', e)

if __name__ == '__main__':
    main()
