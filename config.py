# config.py
import os
from dotenv import load_dotenv, find_dotenv

# Carga el .env sin loguear nada
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

# Helper para obtener variables (con valores por defecto opcionales)
def _get(key: str, default=None) -> str:
    val = os.getenv(key)
    if not val:
        if default is not None:
            print(f"Advertencia: La variable {key} no está definida, usando valor por defecto")
            return default
        raise RuntimeError(f"Error de configuración: falta la variable de entorno {key}")
    return val

# Base de datos principal
DB_USER     = _get("DB_USER")
DB_PASSWORD = _get("DB_PASSWORD")
DB_HOST     = _get("DB_HOST")
DB_NAME     = _get("DB_NAME", "vald")  # Valor por defecto 'vald' si no está en .env
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

