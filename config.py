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
            return default
        raise RuntimeError(f"Error de configuración: falta la variable de entorno {key}")
    return val

# Base de datos principal
DB_USER     = _get("DB_USER")
DB_PASSWORD = _get("DB_PASSWORD")
DB_HOST     = _get("DB_HOST")
DB_PORT     = _get("DB_PORT", "3306")
DB_NAME     = _get("DB_NAME", "vald")  # Valor por defecto 'vald' si no está en .env
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Base de datos secundaria: 'soccersystem' (permite host/puerto/credenciales distintas)
SOCCER_DB_NAME     = _get("SOCCER_DB_NAME", "soccersystem")
SOCCER_DB_HOST     = _get("SOCCER_DB_HOST", DB_HOST)
SOCCER_DB_PORT     = _get("SOCCER_DB_PORT", DB_PORT)
SOCCER_DB_USER     = _get("SOCCER_DB_USER", DB_USER)
SOCCER_DB_PASSWORD = _get("SOCCER_DB_PASSWORD", DB_PASSWORD)
SOCCER_DATABASE_URL = (
    f"mysql+pymysql://{SOCCER_DB_USER}:{SOCCER_DB_PASSWORD}@{SOCCER_DB_HOST}:{SOCCER_DB_PORT}/{SOCCER_DB_NAME}"
)

