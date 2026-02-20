import sys
import pyodbc
from app.config import settings

# Usage: .venv\Scripts\python.exe Scripts\update_product.py SKU "descripcion" "proveedor" "modelo" costo moneda

if len(sys.argv) < 7:
    print("Usage: update_product.py SKU descripcion proveedor modelo costo moneda")
    sys.exit(1)

sku = sys.argv[1]
descripcion = sys.argv[2]
proveedor = sys.argv[3]
modelo = sys.argv[4]
try:
    costo = float(sys.argv[5])
except Exception:
    costo = None
moneda = sys.argv[6]

conn = None
try:
    conn = pyodbc.connect(settings.sqlserver_conn, autocommit=False)
    cur = conn.cursor()

    # Ensure the costo_base column exists before making any updates to avoid
    # doing an UPDATE then rolling it back due to a failing ALTER TABLE.
    cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Productos' AND COLUMN_NAME='costo_base'")
    row = cur.fetchone()
    exists = row[0] if row else 0
    if not exists:
        cur.execute("ALTER TABLE dbo.Productos ADD costo_base DECIMAL(18,6) NULL")
        conn.commit()

    # Update Productos row(s)
    sql = """
    UPDATE dbo.Productos
    SET descripcion = ?, proveedor = ?, modelo = ?, moneda_base = ?, actualizado_en = GETDATE()
    WHERE sku = ?
    """
    cur.execute(sql, descripcion, proveedor, modelo, moneda, sku)

    if costo is not None:
        cur.execute("UPDATE dbo.Productos SET costo_base = ?, fecha_actualizacion = GETDATE() WHERE sku = ?", costo, sku)

    conn.commit()
    print(f"Producto {sku} actualizado: descripcion, proveedor, modelo, moneda, costo={costo}")
except Exception as e:
    print('ERROR:', e)
    if conn:
        try:
            conn.rollback()
        except:
            pass
    sys.exit(2)
finally:
    if conn:
        try:
            conn.close()
        except:
            pass
