"""Crear o actualizar la vista dbo.PreciosCalculados_view con `descripcion` a la
derecha de `sku` y `Segmento_Hospitalario` a la derecha de `descripcion`.
"""
import sys
import pyodbc
from app.config import settings


def get_columns(cursor, table_schema: str, table_name: str) -> list:
    sql = (
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? "
        "ORDER BY ORDINAL_POSITION"
    )
    cursor.execute(sql, table_schema, table_name)
    return [row[0] for row in cursor.fetchall()]


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
        cur = conn.cursor()

        cols = get_columns(cur, 'dbo', 'PreciosCalculados')
        if not cols:
            print('No se encontró la tabla dbo.PreciosCalculados o no tiene columnas.')
            sys.exit(2)

        # Validate required physical columns
        if 'descripcion' not in [c.lower() for c in cols]:
            print('Advertencia: la columna `descripcion` no existe en dbo.PreciosCalculados. Crearla primero.')
            sys.exit(2)
        if 'Segmento_Hospitalario' not in cols:
            print('Advertencia: la columna `Segmento_Hospitalario` no existe en dbo.PreciosCalculados. Crearla primero.')
            sys.exit(2)

        # Build ordered column list with descripcion after sku and Segmento_Hospitalario after descripcion
        lower_cols = [c.lower() for c in cols]
        final = []

        # Ensure sku first
        if 'sku' in lower_cols:
            final.append('sku')

        # Insert descripcion next (use actual case from cols)
        if 'descripcion' in lower_cols:
            # find original casing
            d = next(c for c in cols if c.lower() == 'descripcion')
            final.append(d)

        # Insert Segmento_Hospitalario next (original casing)
        if 'Segmento_Hospitalario' in cols:
            final.append('Segmento_Hospitalario')

        # Append remaining columns in their existing order, skipping already added
        for c in cols:
            if c not in final:
                final.append(c)

        select_list = ', '.join(final)
        sql = f"CREATE OR ALTER VIEW dbo.PreciosCalculados_view AS SELECT {select_list} FROM dbo.PreciosCalculados;"
        cur.execute(sql)
        print('Vista dbo.PreciosCalculados_view creada/actualizada correctamente.')
    except Exception as e:
        print('ERROR creando vista PreciosCalculados_view:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
