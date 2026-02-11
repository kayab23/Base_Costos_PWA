"""
Imprime el contenido de la tabla `ParametrosImportacion` para revisión.

Uso:
    & .venv\Scripts\python.exe Scripts\inspect_parametros.py
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

COLS_SQL = """
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'ParametrosImportacion'
ORDER BY ORDINAL_POSITION
"""

SQL = "SELECT * FROM dbo.ParametrosImportacion"

UPSERTS = [
    ('aereo_equipo', '%', 0.10),
    ('maritimo_equipo', '%', 0.05),
    ('aereo_insumo', '%', 0.10),
    ('maritimo_insumo', '%', 0.05),
]

UPSERT_SQL = """
IF EXISTS (SELECT 1 FROM dbo.ParametrosImportacion WHERE LTRIM(RTRIM(LOWER(concepto))) = LOWER(?) )
    UPDATE dbo.ParametrosImportacion SET tipo = ?, valor = ?, vigente_hasta = NULL WHERE LTRIM(RTRIM(LOWER(concepto))) = LOWER(?)
ELSE
    INSERT INTO dbo.ParametrosImportacion (concepto, tipo, valor, vigente_hasta) VALUES (?, ?, ?, NULL)
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
        rows = cur.fetchall()
    except Exception as e:
        print('ERROR ejecutando consulta:', e)
        conn.close()
        return

    if not rows:
        print('No hay filas en ParametrosImportacion')
    else:
        # obtener columnas
        try:
            cur.execute(COLS_SQL)
            cols = [c[0] for c in cur.fetchall()]
        except Exception:
            cols = []
        print('Columnas detectadas:', ', '.join(cols) if cols else '[desconocidas]')
        print('Filas actuales:')
        for r in rows:
            print('|'.join(str(x) if x is not None else 'NULL' for x in r))

    # Si se invoca con la variable de entorno APPLY_FLETE=1, aplicar upserts
    if os.getenv('APPLY_FLETE', '') == '1':
        print('\nAplicando upserts de flete por categoria...')
        for concepto, tipo, valor in UPSERTS:
            try:
                cur.execute(UPSERT_SQL, (concepto, tipo, valor, concepto, concepto, tipo, valor))
                print(f'  Upsert {concepto} = {valor}')
            except Exception as e:
                print('  ERROR upsert', concepto, e)
        conn.commit()
        print('Upserts aplicados.')

    conn.close()

if __name__ == '__main__':
    main()
