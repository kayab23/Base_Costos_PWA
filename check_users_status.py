"""
Script temporal para consultar hashes y estado de usuarios de prueba.
"""
import pyodbc
from app.config import settings

USERS = [
    'admin',
    'direccion1',
    'subdir1',
    'gercom1',
    'vendedor1',
]

def main():
    conn = pyodbc.connect(settings.sqlserver_conn)
    cursor = conn.cursor()
    print(f"{'username':<12} | {'es_activo':<9} | {'rol':<10} | {'password_hash'}")
    print('-'*80)
    for username in USERS:
        cursor.execute("""
            SELECT username, es_activo, rol, password_hash
            FROM dbo.Usuarios
            WHERE username = ?
        """, username)
        row = cursor.fetchone()
        if row:
            print(f"{row.username:<12} | {str(row.es_activo):<9} | {row.rol:<10} | {row.password_hash}")
        else:
            print(f"{username:<12} | NOT FOUND")
    conn.close()

if __name__ == "__main__":
    main()
