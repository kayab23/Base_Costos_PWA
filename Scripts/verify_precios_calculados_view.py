"""Verificar existencia y contenido de dbo.PreciosCalculados_view.
Imprime columnas de la vista y TOP 5 filas.
"""
import sys
import pyodbc
from app.config import settings


def view_exists(cursor, view_name: str) -> bool:
    sql = (
        "SELECT 1 FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME = ?"
    )
    cursor.execute(sql, view_name)
    return cursor.fetchone() is not None


def get_view_columns(cursor, view_name: str) -> list:
    sql = (
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION"
    )
    cursor.execute(sql, view_name)
    return [r[0] for r in cursor.fetchall()]


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn)
        cur = conn.cursor()

        if not view_exists(cur, 'PreciosCalculados_view'):
            print('La vista dbo.PreciosCalculados_view NO existe.')
            sys.exit(2)

        cols = get_view_columns(cur, 'PreciosCalculados_view')
        print('Columnas en dbo.PreciosCalculados_view:')
        print(', '.join(cols))

        print('\nTOP 5 filas de dbo.PreciosCalculados_view:')
        cur.execute('SELECT TOP 5 * FROM dbo.PreciosCalculados_view')
        rows = cur.fetchall()
        if not rows:
            print('La vista existe pero no devuelve filas.')
            return

        # Print rows as comma-separated values (truncated)
        for r in rows:
            vals = [str(getattr(r, col)) if getattr(r, col) is not None else 'NULL' for col in cols]
            print(' | '.join(vals))

    except Exception as e:
        print('ERROR verificando vista:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
