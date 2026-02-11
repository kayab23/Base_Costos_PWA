"""Crea el usuario administrador `fernando olvera rendon` con la contraseña indicada.
"""
from manage_users import create_user


def main():
    username = "fernando olvera rendon"
    password = "anuar2309"
    rol = "admin"
    create_user(username, password, rol)


if __name__ == '__main__':
    main()
