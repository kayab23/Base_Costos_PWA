"""Agregar columna `descripcion` a dbo.PreciosCalculados y rellenar desde dbo.Productos.
Uso: ejecutar en el entorno del proyecto (usa `settings.sqlserver_conn`).
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

        # Add descripcion if missing
        if not column_exists(cur, 'PreciosCalculados', 'descripcion'):
            print('Creando columna `descripcion` en dbo.PreciosCalculados...')
            cur.execute("ALTER TABLE dbo.PreciosCalculados ADD descripcion NVARCHAR(500) NULL")
        else:
            print('La columna `descripcion` ya existe en dbo.PreciosCalculados.')

        # Backfill descripcion from dbo.Productos to ALL matching PreciosCalculados rows
        # (asegura que cada fila por transporte reciba la descripcion correspondiente)
        print('Rellenando descripcion desde dbo.Productos para todas las filas coincidentes (por sku y transporte)...')
        update_sql = (
            "UPDATE pc SET descripcion = p.descripcion "
            "FROM dbo.PreciosCalculados pc "
            "INNER JOIN dbo.Productos p ON pc.sku = p.sku "
            "WHERE p.descripcion IS NOT NULL"
        )
        cur.execute(update_sql)
        rows = cur.rowcount
        print(f'Filas actualizadas con descripcion: {rows}')

        # Check Segmento_Hospitalario presence in PreciosCalculados
        if not column_exists(cur, 'PreciosCalculados', 'Segmento_Hospitalario'):
            print('Advertencia: `Segmento_Hospitalario` no existe en PreciosCalculados. Puede crearla si lo desea.')
        else:
            print('`Segmento_Hospitalario` existe en PreciosCalculados.')

        print('Operación completada.')
    except Exception as e:
        print('ERROR en add_descripcion_to_precios:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
