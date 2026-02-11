"""Agregar columna `Segmento_Hospitalario` a dbo.PreciosCalculados y rellenar desde dbo.Productos.
"""
import sys
import pyodbc
from app.config import settings


def column_exists(cursor, table_name: str, column_name: str) -> bool:
    sql = (
        "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? AND COLUMN_NAME = ?"
    )
    cursor.execute(sql, table_name, column_name)
    return cursor.fetchone() is not None


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
        cur = conn.cursor()

        # Check table exists
        cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='PreciosCalculados'")
        if not cur.fetchone():
            print('No existe la tabla dbo.PreciosCalculados. Abortando.')
            sys.exit(2)

        # Add Segmento_Hospitalario if missing
        if not column_exists(cur, 'PreciosCalculados', 'Segmento_Hospitalario'):
            print('Creando columna `Segmento_Hospitalario` en dbo.PreciosCalculados...')
            cur.execute("ALTER TABLE dbo.PreciosCalculados ADD Segmento_Hospitalario NVARCHAR(100) NULL")
        else:
            print('La columna `Segmento_Hospitalario` ya existe en dbo.PreciosCalculados.')

        # Backfill Segmento_Hospitalario from dbo.Productos
        print('Rellenando Segmento_Hospitalario desde dbo.Productos (JOIN por sku)...')
        update_sql = (
            "UPDATE pc SET Segmento_Hospitalario = p.Segmento_Hospitalario "
            "FROM dbo.PreciosCalculados pc "
            "LEFT JOIN dbo.Productos p ON pc.sku = p.sku "
            "WHERE (pc.Segmento_Hospitalario IS NULL OR LTRIM(RTRIM(pc.Segmento_Hospitalario)) = '') AND p.Segmento_Hospitalario IS NOT NULL"
        )
        cur.execute(update_sql)
        rows = cur.rowcount
        print(f'Filas actualizadas con Segmento_Hospitalario: {rows}')

        print('Operación completada.')
    except Exception as e:
        print('ERROR en add_segmento_to_precios:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
