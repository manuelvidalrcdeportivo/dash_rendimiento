import os
import bcrypt
from dotenv import load_dotenv

USERS_ENV_PATH = os.path.join(os.path.dirname(__file__), '..', 'test_users.env')

# Carga el archivo test_users.env
load_dotenv(USERS_ENV_PATH, override=True)

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
