"""Agregar columna `password_case_sensitive` a dbo.Usuarios.
"""
import sys
import pyodbc
from app.config import settings


def main():
    conn = None
    try:
        conn = pyodbc.connect(settings.sqlserver_conn, autocommit=True)
        cur = conn.cursor()
        # Add column if not exists
        cur.execute("SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='Usuarios' AND COLUMN_NAME='password_case_sensitive'")
        if cur.fetchone():
            print('La columna password_case_sensitive ya existe en dbo.Usuarios.')
            return
        print('Creando columna password_case_sensitive en dbo.Usuarios...')
        cur.execute("ALTER TABLE dbo.Usuarios ADD password_case_sensitive BIT NOT NULL DEFAULT 0")
        print('Columna creada.')
    except Exception as e:
        print('ERROR en add_password_case_flag:', e)
        sys.exit(2)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
