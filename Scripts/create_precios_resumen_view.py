"""Crear una vista resumen `dbo.PreciosResumen` que contenga:
- sku, descripcion, modelo, transporte
- precio_maximo (alias precio_maximo_lista)
- precio_vendedor_min (alias precio_minimo_lista)
- precio_gerente_com_min
- precio_subdireccion_min
- precio_direccion_min

El script valida la existencia de tablas y columnas y aplica `CREATE OR ALTER VIEW`.
"""
import sys
import pyodbc
from app.config import settings

REQUIRED_PRICE_COLS = [
    'precio_maximo',
    'precio_vendedor_min',
    'precio_gerente_com_min',
    'precio_subdireccion_min',
    'precio_direccion_min'
]


def has_table(cur, name):
    cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?", (name,))
    return bool(cur.fetchone())


def get_columns(cur, table):
    cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=? ORDER BY ORDINAL_POSITION", (table,))
    return [r[0] for r in cur.fetchall()]


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
        cur = conn.cursor()

        if not has_table(cur, 'PreciosCalculados'):
            print('ERROR: no existe la tabla dbo.PreciosCalculados')
            sys.exit(2)
        if not has_table(cur, 'Productos'):
            print('ERROR: no existe la tabla dbo.Productos')
            sys.exit(2)

        precio_cols = get_columns(cur, 'PreciosCalculados')
        prod_cols = get_columns(cur, 'Productos')

        missing = [c for c in REQUIRED_PRICE_COLS if c not in precio_cols and c.lower() not in [pc.lower() for pc in precio_cols]]
        if missing:
            print('ERROR: faltan columnas en PreciosCalculados:', missing)
            print('Columnas disponibles en PreciosCalculados:', precio_cols)
            sys.exit(2)

        # Build SQL: cast floats to DECIMAL(18,2) for consistency
        sql = (
            "CREATE OR ALTER VIEW dbo.PreciosResumen AS\n"
            "SELECT pr.sku, pr.descripcion, prod.modelo, pr.transporte,\n"
            "       CAST(pr.precio_maximo AS DECIMAL(18,2)) AS precio_maximo,\n"
            "       CAST(pr.precio_maximo AS DECIMAL(18,2)) AS precio_maximo_lista,\n"
            "       CAST(pr.precio_vendedor_min AS DECIMAL(18,2)) AS precio_vendedor_min,\n"
            "       CAST(pr.precio_vendedor_min AS DECIMAL(18,2)) AS precio_minimo_lista,\n"
            "       CAST(pr.precio_gerente_com_min AS DECIMAL(18,2)) AS precio_gerente_com_min,\n"
            "       CAST(pr.precio_subdireccion_min AS DECIMAL(18,2)) AS precio_subdireccion_min,\n"
            "       CAST(pr.precio_direccion_min AS DECIMAL(18,2)) AS precio_direccion_min\n"
            "FROM dbo.PreciosCalculados pr\n"
            "LEFT JOIN dbo.Productos prod ON pr.sku = prod.sku;"
        )

        cur.execute(sql)
        print('Vista dbo.PreciosResumen creada/actualizada correctamente.')

        # Show top 5 rows for quick verification
        print('\nTOP 5 filas de dbo.PreciosResumen:')
        cur.execute('SELECT TOP 5 sku, descripcion, modelo, transporte, precio_maximo, precio_vendedor_min, precio_gerente_com_min, precio_subdireccion_min, precio_direccion_min FROM dbo.PreciosResumen')
        rows = cur.fetchall()
        if not rows:
            print('La vista existe pero no devuelve filas.')
            return
        for r in rows:
            vals = [str(getattr(r, col) if hasattr(r, col) else r[i]) for i, col in enumerate(['sku','descripcion','modelo','transporte','precio_maximo','precio_vendedor_min','precio_gerente_com_min','precio_subdireccion_min','precio_direccion_min'])]
            print(' | '.join(vals))

    except Exception as e:
        print('ERROR creando dbo.PreciosResumen:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
