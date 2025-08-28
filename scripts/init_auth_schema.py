# scripts/init_auth_schema.py

import os
import sys

# Asegura que el directorio raíz del proyecto esté en sys.path cuando se ejecuta el script directamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth_db import create_auth_schema_if_not_exists, seed_roles, create_user


def main():
    # Crear tablas si no existen
    create_auth_schema_if_not_exists()
    # Insertar roles base
    seed_roles()
    # Crear admin por defecto si no existe (usuario: admin / contraseña: admin)
    create_user("admin", "admin", full_name="Administrador", email=None, roles=["admin"])
    print("Esquema de autenticación inicializado. Usuario 'admin' creado (si no existía).")


if __name__ == "__main__":
    main()
