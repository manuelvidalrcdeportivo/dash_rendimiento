# scripts/create_user.py

import os
import sys
import argparse

# Asegura que el directorio raíz del proyecto esté en sys.path cuando se ejecuta el script directamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth_db import create_user, list_roles


def parse_args():
    parser = argparse.ArgumentParser(description="Crear usuario para el dashboard con roles")
    parser.add_argument("username", type=str, help="Nombre de usuario")
    parser.add_argument("password", type=str, help="Contraseña")
    parser.add_argument("--full-name", type=str, default=None, help="Nombre completo")
    parser.add_argument("--email", type=str, default=None, help="Correo electrónico")
    parser.add_argument(
        "--roles",
        type=str,
        default="",
        help="Roles separados por coma (disponibles: %s)" % ", ".join(list_roles()),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    ok = create_user(args.username, args.password, args.full_name, args.email, roles)
    if ok:
        print(f"Usuario '{args.username}' creado con roles: {', '.join(roles) if roles else 'sin roles'}")
    else:
        print(f"El usuario '{args.username}' ya existe.")


if __name__ == "__main__":
    main()
