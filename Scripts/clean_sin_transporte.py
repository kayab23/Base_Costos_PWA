"""
Eliminar filas con transporte='(SIN_TRANSPORTE)' si existen filas específicas (Aereo/Maritimo) para el mismo SKU.

Uso:
    & .venv\Scripts\python.exe Scripts\clean_sin_transporte.py
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

SELECT_SKUS_SQL = """
SELECT sku FROM dbo.PreciosCalculados WHERE transporte = '(SIN_TRANSPORTE)'
ORDER BY sku
"""

CHECK_OTHER_SQL = "SELECT COUNT(1) FROM dbo.PreciosCalculados WHERE sku = ? AND transporte <> '(SIN_TRANSPORTE)'"
DELETE_SQL = "DELETE FROM dbo.PreciosCalculados WHERE sku = ? AND transporte = '(SIN_TRANSPORTE)'"

def main():
    try:
        conn = pyodbc.connect(CONN)
    except Exception as e:
        print('ERROR conectando a BD:', e)
        return
    cur = conn.cursor()
    cur.execute(SELECT_SKUS_SQL)
    skus = [r[0] for r in cur.fetchall()]
    if not skus:
        print('No hay filas con (SIN_TRANSPORTE).')
        conn.close()
        return

    deleted_any = False
    for sku in skus:
        cur.execute(CHECK_OTHER_SQL, (sku,))
        cnt = cur.fetchone()[0]
        if cnt and cnt > 0:
            print(f"Eliminando fila (SIN_TRANSPORTE) para sku={sku} porque existen {cnt} filas con transporte definido.")
            cur.execute(DELETE_SQL, (sku,))
            deleted_any = True
        else:
            print(f"SKU {sku} solo tiene (SIN_TRANSPORTE) -> dejar para revisión manual.")

    if deleted_any:
        conn.commit()
        print('Cambios aplicados y confirmados.')
    else:
        print('No se eliminaron filas automáticas. Revisión manual requerida.')

    conn.close()

if __name__ == '__main__':
    main()
