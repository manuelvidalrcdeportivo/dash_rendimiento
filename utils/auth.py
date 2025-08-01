import os
import bcrypt
from dotenv import load_dotenv

# Intenta cargar users.env si existe, pero no es obligatorio
USERS_ENV_PATH = os.path.join(os.path.dirname(__file__), '..', 'users.env')
if os.path.exists(USERS_ENV_PATH):
    load_dotenv(USERS_ENV_PATH, override=False)  # No sobreescribir variables ya existentes

def get_user_hash(username):
    """Devuelve el hash bcrypt del usuario o None si no existe."""
    key = f'USER_{username}'
    return os.getenv(key)

def validate_user(username, password):
    """Valida el usuario y contraseña usando bcrypt."""
    user_hash = get_user_hash(username)
    if not user_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), user_hash.encode('utf-8'))
    except Exception:
        return False
