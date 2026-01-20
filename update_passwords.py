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

#!/usr/bin/env python3
"""
Script para actualizar contraseñas de usuarios según la jerarquía definida.
Este script recorre una lista de usuarios y actualiza sus contraseñas en la base de datos,
utilizando el mismo algoritmo de hash que el backend para asegurar compatibilidad.
"""

import sys  # Importa el módulo sys (no usado directamente, pero útil para futuras extensiones)
import pyodbc  # Cliente ODBC para conexión a SQL Server

from app.config import settings  # Importa la configuración de conexión a la base de datos
from app.security import hash_password  # Función para hashear contraseñas igual que el backend

def update_password(username: str, new_password: str):
    """
    Actualiza la contraseña de un usuario en la base de datos.
    Utiliza el mismo hash que el backend para asegurar compatibilidad.
    Args:
        username (str): Nombre de usuario a actualizar.
        new_password (str): Nueva contraseña en texto plano.
    """
    # Asegura que la contraseña es un string (por si viene como bytes o tupla)
    if not isinstance(new_password, str):
        new_password = str(new_password)
    # Imprime el tipo y longitud de la contraseña para debug
    print(f"Actualizando {username}: tipo={type(new_password)}, len={len(new_password)}")
    # Hashea la contraseña usando la función del backend
    password_hash = hash_password(new_password)
    # Obtiene la cadena de conexión desde la configuración
    conn_str = settings.sqlserver_conn
    # Abre la conexión a la base de datos usando pyodbc
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()  # Crea un cursor para ejecutar comandos SQL
        # Ejecuta el UPDATE para cambiar el hash de la contraseña
        cursor.execute(
            "UPDATE dbo.Usuarios SET password_hash = ? WHERE username = ?",
            password_hash, username
        )
        conn.commit()  # Confirma los cambios en la base de datos
        print(f"✅ Contraseña actualizada para {username}")  # Mensaje de éxito

def main():
    """
    Actualiza todas las contraseñas de los usuarios definidos en la jerarquía.
    Recorre la lista de usuarios y llama a update_password para cada uno.
    """
    # Lista de usuarios y contraseñas según la jerarquía definida
    usuarios = [
        ('admin', 'Admin123!'),  # Administrador general
        ('direccion1', 'Direcc123!'),  # Usuario de Dirección
        ('subdir1', 'Subdir123!'),  # Usuario de Subdirección
        ('gercom1', 'GerCom123!'),  # Usuario de Gerencia Comercial
        ('vendedor1', 'Vend123!')  # Usuario Vendedor
    ]

    print("Actualizando contraseñas según jerarquía...")
    print("-" * 50)

    # Recorre cada usuario y actualiza su contraseña
    for username, password in usuarios:
        try:
            update_password(username, password)
        except Exception as e:
            print(f"❌ Error actualizando {username}: {e}")  # Muestra error si ocurre

    print("-" * 50)
    print("✅ Proceso completado")
    print("\nJerarquía de usuarios:")
    print("  1. Admin (admin) - Ve todos los costos")
    print("  2. Dirección (direccion1) - 35% descuento")
    print("  3. Subdirección (subdir1) - 30% descuento")
    print("  4. Gerencia Comercial (gercom1) - 25% descuento")
    print("  5. Vendedor (vendedor1) - 20% descuento")

# Punto de entrada del script
if __name__ == '__main__':
    main()
