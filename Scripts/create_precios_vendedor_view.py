"""Crear la vista dbo.PreciosCalculados_vendedor con las columnas solicitadas
y mostrar TOP 5 filas como verificación.

Columnas: sku, descripcion, Segmento_Hospitalario, transporte, precio_vendedor_min, precio_maximo
"""
import sys
import pyodbc
from app.config import settings


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
        cur = conn.cursor()

        # Verify base table exists
        cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='PreciosCalculados'")
        if not cur.fetchone():
            print('No existe dbo.PreciosCalculados. Abortando.')
            sys.exit(2)

        # Create or alter the view with the requested columns
        sql = (
            "CREATE OR ALTER VIEW dbo.PreciosCalculados_vendedor AS\n"
            "SELECT sku, descripcion, Segmento_Hospitalario, transporte, precio_vendedor_min, precio_maximo\n"
            "FROM dbo.PreciosCalculados;"
        )
        cur.execute(sql)
        print('Vista dbo.PreciosCalculados_vendedor creada/actualizada correctamente.')

        # Show TOP 5 rows for verification
        print('\nTOP 5 filas de dbo.PreciosCalculados_vendedor:')
        cur.execute('SELECT TOP 5 sku, descripcion, Segmento_Hospitalario, transporte, precio_vendedor_min, precio_maximo FROM dbo.PreciosCalculados_vendedor')
        rows = cur.fetchall()
        if not rows:
            print('La vista existe pero no devuelve filas.')
            return

        for r in rows:
            sku = getattr(r, 'sku') if hasattr(r, 'sku') else str(r[0])
            desc = getattr(r, 'descripcion') if getattr(r, 'descripcion') is not None else 'NULL'
            seg = getattr(r, 'Segmento_Hospitalario') if getattr(r, 'Segmento_Hospitalario') is not None else 'NULL'
            transporte = getattr(r, 'transporte') if getattr(r, 'transporte') is not None else 'NULL'
            pv = getattr(r, 'precio_vendedor_min') if getattr(r, 'precio_vendedor_min') is not None else 'NULL'
            pmax = getattr(r, 'precio_maximo') if getattr(r, 'precio_maximo') is not None else 'NULL'
            print(f"{sku} | {desc} | {seg} | {transporte} | {pv} | {pmax}")

    except Exception as e:
        print('ERROR creando/verificando vista:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
