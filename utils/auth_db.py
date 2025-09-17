# utils/auth_db.py

import bcrypt
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from config import DATABASE_URL

# Roles por defecto sugeridos
DEFAULT_ROLES = ["admin", "direccion", "preparador", "nutricion", "medico", "analista", "psicologo"]

_engine: Optional[Engine] = None

def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
    return _engine

# ============= Esquema de autenticación =============

def create_auth_schema_if_not_exists() -> None:
    """Crea las tablas de autenticación si no existen.
    - Usuarios en tabla 'dash_users'
    - Roles en tabla 'dash_roles'
    - Relación en 'dash_user_roles'
    """
    engine = get_engine()
    with engine.connect() as conn:
        # dash_users
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS dash_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                full_name VARCHAR(100),
                email VARCHAR(120),
                is_active TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ))
        # dash_roles
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS dash_roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                description VARCHAR(255)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ))
        # dash_user_roles
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS dash_user_roles (
                user_id INT NOT NULL,
                role_id INT NOT NULL,
                PRIMARY KEY (user_id, role_id),
                CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES dash_users(id) ON DELETE CASCADE,
                CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES dash_roles(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ))
        conn.commit()


def seed_roles(roles: List[str] = None) -> None:
    roles = roles or DEFAULT_ROLES
    engine = get_engine()
    with engine.connect() as conn:
        for r in roles:
            conn.execute(text(
                """
                INSERT INTO dash_roles (name, description)
                VALUES (:name, :desc)
                ON DUPLICATE KEY UPDATE name = name
                """
            ), {"name": r, "desc": f"Rol {r}"})
        conn.commit()


# ============= Helpers de usuarios y roles =============

def _hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def get_user_id(username: str) -> Optional[int]:
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id FROM dash_users WHERE username = :u"), {"u": username}).first()
        return int(res[0]) if res else None


def create_user(username: str, password: str, full_name: str = None, email: str = None, roles: List[str] = None) -> bool:
    """Crea un usuario con roles. Devuelve True si creado, False si ya existe."""
    roles = roles or []
    engine = get_engine()
    with engine.begin() as conn:
        # Existe ya?
        existing = conn.execute(text("SELECT id FROM dash_users WHERE username = :u"), {"u": username}).first()
        if existing:
            return False
        pwd_hash = _hash_password(password)
        conn.execute(text(
            """
            INSERT INTO dash_users (username, password_hash, full_name, email, is_active)
            VALUES (:u, :p, :f, :e, 1)
            """
        ), {"u": username, "p": pwd_hash, "f": full_name, "e": email})
        user_id = conn.execute(text("SELECT id FROM dash_users WHERE username = :u"), {"u": username}).scalar()
        # Asegurar roles existen
        for r in roles:
            conn.execute(text(
                """
                INSERT INTO dash_roles (name, description)
                VALUES (:name, :desc)
                ON DUPLICATE KEY UPDATE name = name
                """
            ), {"name": r, "desc": f"Rol {r}"})
            role_id = conn.execute(text("SELECT id FROM dash_roles WHERE name = :n"), {"n": r}).scalar()
            conn.execute(text(
                "INSERT IGNORE INTO dash_user_roles (user_id, role_id) VALUES (:uid, :rid)"
            ), {"uid": user_id, "rid": role_id})
        return True


def validate_user_db(username: str, password: str) -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT password_hash, is_active FROM dash_users WHERE username = :u"
        ), {"u": username}).first()
        if not row:
            return False
        pwd_hash, is_active = row[0], int(row[1])
        if not is_active:
            return False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), pwd_hash.encode("utf-8"))
        except Exception:
            return False


def get_user_roles(username: str) -> List[str]:
    engine = get_engine()
    with engine.connect() as conn:
        res = conn.execute(text(
            """
            SELECT r.name
            FROM dash_users u
            JOIN dash_user_roles ur ON u.id = ur.user_id
            JOIN dash_roles r ON r.id = ur.role_id
            WHERE u.username = :u
            """
        ), {"u": username}).fetchall()
        return [r[0] for r in res]


def list_roles() -> List[str]:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT name FROM dash_roles ORDER BY name"))
            return [r[0] for r in res]
    except SQLAlchemyError:
        return DEFAULT_ROLES
