"""
Script para actualizar contraseñas de usuarios según la jerarquía definida
"""
import sys
import pyodbc

from app.config import settings
from app.security import hash_password

def update_password(username: str, new_password: str):
    """Actualiza la contraseña de un usuario usando el mismo hash que el backend"""
    # Asegurar que la contraseña es un string simple y no una tupla ni bytes
    if not isinstance(new_password, str):
        new_password = str(new_password)
    # Debug: imprimir tipo y longitud
    print(f"Actualizando {username}: tipo={type(new_password)}, len={len(new_password)}")
    password_hash = hash_password(new_password)
    conn_str = settings.sqlserver_conn
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE dbo.Usuarios SET password_hash = ? WHERE username = ?",
            password_hash, username
        )
        conn.commit()
        print(f"✅ Contraseña actualizada para {username}")

def main():
    """Actualiza todas las contraseñas según la tabla de jerarquía"""
    usuarios = [
        ('admin', 'Admin123!'),
        ('direccion1', 'Direcc123!'),
        ('subdir1', 'Subdir123!'),
        ('gercom1', 'GerCom123!'),
        ('vendedor1', 'Vend123!')
    ]
    
    print("Actualizando contraseñas según jerarquía...")
    print("-" * 50)
    
    for username, password in usuarios:
        try:
            update_password(username, password)
        except Exception as e:
            print(f"❌ Error actualizando {username}: {e}")
    
    print("-" * 50)
    print("✅ Proceso completado")
    print("\nJerarquía de usuarios:")
    print("  1. Admin (admin) - Ve todos los costos")
    print("  2. Dirección (direccion1) - 35% descuento")
    print("  3. Subdirección (subdir1) - 30% descuento")
    print("  4. Gerencia Comercial (gercom1) - 25% descuento")
    print("  5. Vendedor (vendedor1) - 20% descuento")

if __name__ == '__main__':
    main()
