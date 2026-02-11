from app.db import connection_scope
import random

CLIENTS = [
    (f"C{1000+i}", f"Cliente {i}", f"RFC{i:04d}", f"Calle {i}", f"Contacto {i}", f"55{1000+i}", f"cliente{i}@example.com")
    for i in range(1, 16)
]

VENDORS = [
    (f"vend{i}", f"Vendedor {i}", "Vendedor", f"vend{i}@example.com", f"55{2000+i}")
    for i in range(1, 6)
]

def seed():
    with connection_scope() as conn:
        cur = conn.cursor()
        for codigo, nombre, rfc, direccion, contacto, telefono, email in CLIENTS:
            try:
                cur.execute("INSERT INTO clientes (codigo, nombre, rfc, direccion, contacto, telefono, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (codigo, nombre, rfc, direccion, contacto, telefono, email))
            except Exception:
                pass
        for username, nombre_completo, rol, email, telefono in VENDORS:
            try:
                cur.execute("INSERT INTO vendedores (username, nombre_completo, rol, email, telefono) VALUES (?, ?, ?, ?, ?)",
                            (username, nombre_completo, rol, email, telefono))
            except Exception:
                pass
        conn.commit()

if __name__ == '__main__':
    seed()
    print('Seed completed')
