"""Actualizar la vista dbo.PreciosCalculados_vendedor para incluir `modelo`.

La vista se crea como JOIN entre `PreciosCalculados` (alias pr) y `Productos` (alias prod)
por `sku`. Se usa LEFT JOIN para no perder filas de precios que no tengan producto.
"""
import sys
import pyodbc
from app.config import settings


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
        cur = conn.cursor()

        # Verificar existencia de tablas
        cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='PreciosCalculados'")
        if not cur.fetchone():
            print('No existe dbo.PreciosCalculados. Abortando.')
            sys.exit(2)
        cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='Productos'")
        if not cur.fetchone():
            print('No existe dbo.Productos. Abortando.')
            sys.exit(2)

        sql = (
            "CREATE OR ALTER VIEW dbo.PreciosCalculados_vendedor AS\n"
            "SELECT pr.sku, pr.descripcion, pr.Segmento_Hospitalario, prod.modelo, pr.transporte, pr.precio_vendedor_min, pr.precio_maximo\n"
            "FROM dbo.PreciosCalculados pr\n"
            "LEFT JOIN dbo.Productos prod ON pr.sku = prod.sku;"
        )

        cur.execute(sql)
        print('Vista dbo.PreciosCalculados_vendedor actualizada correctamente (modelo agregado).')

        # Mostrar TOP 5 rows para verificación
        print('\nTOP 5 filas de dbo.PreciosCalculados_vendedor:')
        cur.execute('SELECT TOP 5 sku, descripcion, Segmento_Hospitalario, modelo, transporte, precio_vendedor_min, precio_maximo FROM dbo.PreciosCalculados_vendedor')
        rows = cur.fetchall()
        if not rows:
            print('La vista existe pero no devuelve filas.')
            return
        for r in rows:
            sku = getattr(r, 'sku') if hasattr(r, 'sku') else str(r[0])
            desc = getattr(r, 'descripcion') if getattr(r, 'descripcion') is not None else 'NULL'
            seg = getattr(r, 'Segmento_Hospitalario') if getattr(r, 'Segmento_Hospitalario') is not None else 'NULL'
            modelo = getattr(r, 'modelo') if getattr(r, 'modelo') is not None else 'NULL'
            transporte = getattr(r, 'transporte') if getattr(r, 'transporte') is not None else 'NULL'
            pv = getattr(r, 'precio_vendedor_min') if getattr(r, 'precio_vendedor_min') is not None else 'NULL'
            pmax = getattr(r, 'precio_maximo') if getattr(r, 'precio_maximo') is not None else 'NULL'
            print(f"{sku} | {desc} | {seg} | {modelo} | {transporte} | {pv} | {pmax}")

    except Exception as e:
        print('ERROR actualizando vista:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
