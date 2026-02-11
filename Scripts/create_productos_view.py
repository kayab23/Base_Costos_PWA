"""Crear o actualizar la vista dbo.Productos_view con Segmento_Hospitalario
posicionado a la derecha de la columna `modelo`.
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

        cols = get_columns(cur, 'dbo', 'Productos')
        if not cols:
            print('No se encontró la tabla dbo.Productos o no tiene columnas.')
            sys.exit(2)

        # Ensure Segmento_Hospitalario is present in the physical table
        if 'Segmento_Hospitalario' not in cols:
            print('Advertencia: la columna Segmento_Hospitalario no existe en dbo.Productos. Crearla primero.')
            sys.exit(2)

        # Build ordered column list with Segmento_Hospitalario positioned after 'modelo'
        ordered = []
        inserted = False
        for c in cols:
            ordered.append(c)
            if c.lower() == 'modelo' and not inserted:
                # Ensure the new column follows modelo in the view
                if 'Segmento_Hospitalario' not in ordered:
                    ordered.append('Segmento_Hospitalario')
                inserted = True

        if not inserted and 'Segmento_Hospitalario' not in ordered:
            ordered.append('Segmento_Hospitalario')

        # Remove duplicates preserving order
        seen = set()
        final_cols = []
        for c in ordered:
            if c not in seen:
                seen.add(c)
                final_cols.append(c)

        select_list = ', '.join(final_cols)
        sql = f"CREATE OR ALTER VIEW dbo.Productos_view AS SELECT {select_list} FROM dbo.Productos;"
        cur.execute(sql)
        print('Vista dbo.Productos_view creada/actualizada correctamente.')
    except Exception as e:
        print('ERROR creando vista:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
