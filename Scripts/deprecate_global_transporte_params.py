"""
Marcar como no vigentes los parámetros globales 'Aereo' y 'Maritimo'
estableciendo `vigente_hasta = GETDATE()` para evitar que se usen como fallback.

Uso:
    & .venv\Scripts\python.exe Scripts\deprecate_global_transporte_params.py
"""
from __future__ import annotations
import os
import pyodbc

DEFAULT_CONN = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=.\\SQLEXPRESS;"
    "DATABASE=BD_Calculo_Costos;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
CONN = os.getenv('SQLSERVER_CONN', DEFAULT_CONN)

SQL = """
UPDATE dbo.ParametrosImportacion
SET vigente_hasta = GETDATE()
WHERE LTRIM(RTRIM(LOWER(concepto))) IN ('aereo','maritimo')
  AND vigente_hasta IS NULL
"""

def main():
    try:
        conn = pyodbc.connect(CONN)
    except Exception as e:
        print('ERROR conectando a BD:', e)
        return
    cur = conn.cursor()
    try:
        cur.execute(SQL)
        affected = cur.rowcount
        conn.commit()
        print(f'Filas actualizadas: {affected}')
    except Exception as e:
        print('ERROR ejecutando update:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
