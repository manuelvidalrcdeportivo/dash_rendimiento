#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para inicializar la tabla de umbrales en la base de datos
con los valores predeterminados para cada variable y día.
"""

from utils.db_manager import get_db_connection
import pandas as pd
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def crear_tabla_umbrales():
    """
    Crea la tabla 'umbrales' si no existe y la inicializa con los valores por defecto.
    """
    try:
        logger.info("Iniciando la creación e inicialización de la tabla de umbrales...")
        engine = get_db_connection()
        
        if engine is None:
            logger.error("Error: No se pudo establecer conexión con la base de datos")
            return False
        
        # Verificar si la tabla ya existe
        try:
            existe_tabla = pd.read_sql("SHOW TABLES LIKE 'umbrales'", engine)
            if not existe_tabla.empty:
                respuesta = input("La tabla 'umbrales' ya existe. ¿Desea eliminarla y recrearla? (s/n): ")
                if respuesta.lower() == 's':
                    logger.info("Eliminando tabla existente...")
                    with engine.connect() as conn:
                        conn.execute("DROP TABLE umbrales")
                        conn.commit()
                else:
                    logger.info("Operación cancelada por el usuario.")
                    return False
        except Exception as e:
            logger.warning(f"Error al verificar existencia de tabla: {e}")
            pass  # Continuamos con la creación
        
        # Crear la tabla
        logger.info("Creando tabla 'umbrales'...")
        with engine.connect() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS umbrales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                variable VARCHAR(100) NOT NULL,
                dia VARCHAR(10) NOT NULL,
                max_value FLOAT NOT NULL,
                min_value FLOAT NOT NULL,
                UNIQUE KEY (variable, dia)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            conn.commit()
        
        # Datos para inicializar
        datos = [
            # Average Distance (Session) (m)
            {"variable": "Average Distance (Session) (m)", "dia": "MD-4", "max_value": 6535, "min_value": 3383},
            {"variable": "Average Distance (Session) (m)", "dia": "MD-3", "max_value": 7237, "min_value": 4853},
            {"variable": "Average Distance (Session) (m)", "dia": "MD-2", "max_value": 4465, "min_value": 1700},
            {"variable": "Average Distance (Session) (m)", "dia": "MD-1", "max_value": 5150, "min_value": 2645},
            
            # HSR Distance (m)
            {"variable": "HSR Distance (m)", "dia": "MD-4", "max_value": 232, "min_value": 38},
            {"variable": "HSR Distance (m)", "dia": "MD-3", "max_value": 483, "min_value": 128},
            {"variable": "HSR Distance (m)", "dia": "MD-2", "max_value": 100, "min_value": 16},
            {"variable": "HSR Distance (m)", "dia": "MD-1", "max_value": 121, "min_value": 15},
            
            # Velocity Band Band 6 Distance (Session) (m)
            {"variable": "Velocity Band Band 6 Distance (Session) (m)", "dia": "MD-4", "max_value": 33, "min_value": 0},
            {"variable": "Velocity Band Band 6 Distance (Session) (m)", "dia": "MD-3", "max_value": 110, "min_value": 10},
            {"variable": "Velocity Band Band 6 Distance (Session) (m)", "dia": "MD-2", "max_value": 3, "min_value": 0},
            {"variable": "Velocity Band Band 6 Distance (Session) (m)", "dia": "MD-1", "max_value": 10, "min_value": 0},
            
            # Average Player Load
            {"variable": "Average Player Load", "dia": "MD-4", "max_value": 6506, "min_value": 2759},
            {"variable": "Average Player Load", "dia": "MD-3", "max_value": 246, "min_value": 89},
            {"variable": "Average Player Load", "dia": "MD-2", "max_value": 452, "min_value": 169},
            {"variable": "Average Player Load", "dia": "MD-1", "max_value": 135, "min_value": 61},
        ]
        
        # Convertir a DataFrame
        df = pd.DataFrame(datos)
        
        # Insertar datos
        logger.info(f"Insertando {len(datos)} registros de umbrales...")
        df.to_sql('umbrales', engine, if_exists='append', index=False)
        
        # Verificar inserción
        total = pd.read_sql("SELECT COUNT(*) as total FROM umbrales", engine)
        logger.info(f"Total de registros en tabla umbrales: {total.iloc[0]['total']}")
        
        logger.info("Inicialización de tabla de umbrales completada con éxito.")
        return True
        
    except Exception as e:
        logger.error(f"Error al inicializar tabla de umbrales: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    crear_tabla_umbrales()
