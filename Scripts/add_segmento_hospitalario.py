"""Agregar columna Segmento_Hospitalario a dbo.Productos.

Uso:
  .venv\Scripts\python.exe Scripts\add_segmento_hospitalario.py [--backfill]

Si se pasa `--backfill` actualizará todas las filas existentes donde el valor es NULL a 'Infusión'.
El script verifica si la columna ya exista antes de alterar la tabla.
"""
import argparse
import sys
import pyodbc
from app.config import settings


def column_exists(cursor, table_name: str, column_name: str) -> bool:
    sql = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? AND COLUMN_NAME = ?"
    cursor.execute(sql, table_name, column_name)
    return cursor.fetchone()[0] > 0


def add_column(cursor) -> None:
    # Add nullable column first to avoid locking issues. We'll add a default constraint for future inserts.
    cursor.execute("ALTER TABLE dbo.Productos ADD Segmento_Hospitalario NVARCHAR(100) NULL")
    # Add a default constraint so new rows default to 'Infusión'
    try:
        cursor.execute(
            "ALTER TABLE dbo.Productos ADD CONSTRAINT DF_Productos_SegmentoHospitalario DEFAULT ('Infusión') FOR Segmento_Hospitalario"
        )
    except Exception:
        # If constraint exists or cannot be added, ignore (idempotent intent)
        pass


def backfill(cursor) -> int:
    # Set 'Infusión' where currently NULL
    cursor.execute("UPDATE dbo.Productos SET Segmento_Hospitalario = ? WHERE Segmento_Hospitalario IS NULL", 'Infusión')
    return cursor.rowcount


def main():
    parser = argparse.ArgumentParser(description='Agregar Segmento_Hospitalario a dbo.Productos')
    parser.add_argument('--backfill', action='store_true', help="Rellenar filas existentes con 'Infusión' cuando sean NULL")
    args = parser.parse_args()

    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=False)
        cur = conn.cursor()

        if column_exists(cur, 'Productos', 'Segmento_Hospitalario'):
            print('La columna Segmento_Hospitalario ya existe en dbo.Productos.')
        else:
            print('Creando columna Segmento_Hospitalario en dbo.Productos...')
            add_column(cur)
            conn.commit()
            print('Columna creada y constraint de default añadido (si fue posible).')

        if args.backfill:
            print("Backfilling filas existentes a 'Infusión' donde Segmento_Hospitalario IS NULL...")
            updated = backfill(cur)
            conn.commit()
            print(f'Filas actualizadas: {updated}')

        print('Operación completada.')
    except Exception as e:
        print('ERROR:', e)
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
