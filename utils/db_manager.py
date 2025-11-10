# utils/db_manager.py

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv
import sys
import traceback
from datetime import datetime, timedelta

# Cargar variables de entorno para las credenciales de la base de datos
load_dotenv()

# Función para obtener la conexión a la base de datos
def get_db_connection():
    """
    Crea y retorna una conexión a la base de datos usando SQLAlchemy.
    """
    # Configuración de credenciales desde el archivo .env
    DB_CONFIG = {
        'user': os.getenv('DB_USER'),  # Usuario desde .env
        'password': os.getenv('DB_PASSWORD'),  # Contraseña desde .env
        'host': os.getenv('DB_HOST'),  # Host desde .env
        'database': os.getenv('DB_NAME')  # Base de datos desde .env
    }
    
    # Crear la URL de conexión
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    
    try:
        # Crear y devolver el motor de SQLAlchemy
        
        engine = create_engine(db_url)
        
        # Probar la conexión
        connection = engine.connect()
        
        
        # Mostrar las tablas disponibles
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        
        connection.close()
        return engine
    except Exception as e:
        
        return None

# Funciones específicas para consultar los datos necesarios para la sección Jugadores

def get_all_athletes():
    """
    Obtiene la lista de todos los atletas (jugadores) de la base de datos.
    
    Returns:
        DataFrame con id, first_name, last_name de todos los atletas.
    """
    try:
        engine = get_db_connection()
        if engine is None:
            
            return pd.DataFrame(columns=['id', 'first_name', 'last_name'])
        
        # Verificar las tablas disponibles antes de la consulta
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        
        # Verificar si la tabla 'athletes' existe
        if 'athletes' not in tables:
            
            # Posibles tablas que contienen jugadores (athlete/player/jugador)
            return pd.DataFrame(columns=['id', 'first_name', 'last_name'])
        
        # Verificar las columnas de la tabla 'athletes'
        columns = [c['name'] for c in inspector.get_columns('athletes')]
        
        
        query = """
        SELECT id, first_name, last_name, position_name
        FROM athletes 
        ORDER BY first_name, last_name
        """
        
        # Ejecutar consulta y obtener resultados
        
        df = pd.read_sql(query, engine)
        
        # Imprimir resultados para depuración
        
        if not df.empty:
            pass
        else:
            pass
        # Añadir columna para el nombre completo (para mostrar en UI)
        df['full_name'] = df['first_name'] + ' ' + df['last_name']
        # Si position_name no existe, añadir columna vacía
        if 'position_name' not in df.columns:
            df['position_name'] = None
        return df
        
    except Exception as e:
        
        import traceback
        traceback.print_exc()
        # Devolver un DataFrame vacío en caso de error
        return pd.DataFrame(columns=['id', 'first_name', 'last_name', 'full_name'])

def get_athlete_activities(athlete_id):
    """
    Obtiene todas las actividades en las que ha participado un atleta.
    
    Args:
        athlete_id: ID del atleta/jugador
    
    Returns:
        DataFrame con id, activity_id de las actividades en las que participó el atleta.
    """
    try:
        
        engine = get_db_connection()
        if engine is None:
            
            return pd.DataFrame(columns=['id', 'activity_id'])
            
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'simple_activity_participation' not in inspector.get_table_names():
            
            return pd.DataFrame(columns=['id', 'activity_id'])
            
        # Verificar las columnas de la tabla
        columns = [c['name'] for c in inspector.get_columns('simple_activity_participation')]
        
        
        # Verificar si athlete_id está en las columnas
        if 'athlete_id' not in columns:
            
            posibles_columnas = [c for c in columns if 'athlete' in c.lower() or 'player' in c.lower()]
            
            return pd.DataFrame(columns=['id', 'activity_id'])
        
        query = """
        SELECT id, activity_id 
        FROM simple_activity_participation 
        WHERE athlete_id = %s
        ORDER BY activity_id DESC
        """
        
        
        
        # Ejecutar consulta con parámetros (MySQL/MariaDB usa %s y tuple)
        df = pd.read_sql(query, engine, params=(athlete_id,))
        
        
        if not df.empty:
            pass
        else:
            pass
        
        return df
        
    except Exception as e:
        
        import traceback
        traceback.print_exc()
        # Devolver un DataFrame vacío en caso de error
        return pd.DataFrame(columns=['id', 'activity_id'])

def get_activity_metric(activity_id, athlete_id, parameter_name='total_distance'):
    """
    Obtiene el valor de un parámetro específico para una combinación de actividad y atleta.
    
    Args:
        activity_id: ID de la actividad
        athlete_id: ID del atleta/jugador
        parameter_name: Nombre del parámetro a consultar
    
    Returns:
        Valor del parámetro o None si no se encuentra.
    
    Nota: El id de participación ya no se utiliza para consultar métricas.
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return None
        
        query = """
        SELECT parameter_value 
        FROM activity_athlete_metrics 
        WHERE activity_id = %s AND athlete_id = %s AND parameter_name = %s
        """
        
        
        
        # Ejecutar consulta con parámetros
        result = pd.read_sql(query, engine, params=(activity_id, athlete_id, parameter_name))
        
        # Verificar si se encontró algún resultado
        if not result.empty:
            
            return result.iloc[0]['parameter_value']
        else:
            
            return None
            
    except Exception as e:
        
        import traceback
        traceback.print_exc()
        return None

# --------------------------------------
# NUEVAS FUNCIONES PARA FILTRO POR FECHA
# --------------------------------------
def get_activities_by_date_range(start_timestamp, end_timestamp):
    """
    Devuelve las actividades cuyo start_time está entre dos timestamps UNIX.
    Args:
        start_timestamp (int): timestamp UNIX inicio
        end_timestamp (int): timestamp UNIX fin
    Returns:
        DataFrame con actividades filtradas (solo columnas esenciales para optimizar)
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        # Optimización: Solo seleccionar columnas necesarias en lugar de SELECT *
        query = '''
            SELECT id, start_time, name, tag_list_json
            FROM activities
            WHERE start_time >= %s AND start_time <= %s
            ORDER BY start_time ASC
        '''
        df = pd.read_sql(query, engine, params=(start_timestamp, end_timestamp))
        return df
    except Exception as e:
        
        return pd.DataFrame()

def get_participants_for_activities(activity_ids, include_participation_tags=False):
    """
    Devuelve los jugadores participantes en una lista de actividades.
    Args:
        activity_ids (list): lista de activity_id
        include_participation_tags (bool): Si True, incluye columna participation_type
    Returns:
        DataFrame con columnas: activity_id, athlete_id [, participation_type]
        participation_type puede ser: 'Full', 'Part', 'Rehab', o None
    """
    try:
        engine = get_db_connection()
        if engine is None or not activity_ids:
            cols = ["activity_id", "athlete_id"]
            if include_participation_tags:
                cols.append("participation_type")
            return pd.DataFrame(columns=cols)
        
        if include_participation_tags:
            query = '''
                SELECT activity_id, athlete_id, tags_json FROM activity_athletes
                WHERE activity_id IN %s
            '''
        else:
            query = '''
                SELECT activity_id, athlete_id FROM activity_athletes
                WHERE activity_id IN %s
            '''
        df = pd.read_sql(query, engine, params=(tuple(activity_ids),))
        
        # Si se solicitan tags de participación, parsear tags_json
        if include_participation_tags and not df.empty and 'tags_json' in df.columns:
            df['participation_type'] = df['tags_json'].apply(_extract_participation_tag)
            df = df.drop(columns=['tags_json'])
        
        return df
    except Exception as e:
        print(f"Error getting participants: {e}")
        cols = ["activity_id", "athlete_id"]
        if include_participation_tags:
            cols.append("participation_type")
        return pd.DataFrame(columns=cols)

def _extract_participation_tag(tags_json_str):
    """
    Extrae el tag de participación del JSON de tags.
    Busca tags con tag_type_name == 'Participation'
    Retorna: 'Full', 'Part', 'Rehab', o None
    """
    import json
    
    if pd.isna(tags_json_str) or tags_json_str == '' or tags_json_str is None:
        return None  # Sin tag = consideramos Full por defecto
    
    try:
        tags = json.loads(tags_json_str)
        for tag in tags:
            if tag.get('tag_type_name') == 'Participation' or tag.get('tag_type_id') == '09fd58ee-3477-11ef-8148-06e64249fcaf':
                return tag.get('name')  # 'Full', 'Part', 'Rehab'
        return None  # Sin tag de participación = Full por defecto
    except:
        return None

# Cache para días de referencia (evitar consultas repetidas)
_DIAS_REF_CACHE = None

def add_grupo_dia_column(actividades_df):
    """
    Añade una columna 'grupo_dia' al DataFrame de actividades, SOLO usando los tags de tipo 'DayCode' (tag_type_id == '09bdd0ac-3477-11ef-8148-06e64249fcaf').
    Ignora los demás tag_type_id (GPS, Injected, etc).
    Normaliza las etiquetas 'Game -X' a 'MD-X' para unificar nomenclatura.
    """
    import json
    import re
    global _DIAS_REF_CACHE
    DAYCODE_TAG_TYPE_ID = '09bdd0ac-3477-11ef-8148-06e64249fcaf'
    try:
        engine = get_db_connection()
        if engine is None or actividades_df.empty or 'tag_list_json' not in actividades_df.columns:
            actividades_df['grupo_dia'] = 'Sin clasificar'
            return actividades_df
        
        # Optimización: Cachear días de referencia para no consultar cada vez
        if _DIAS_REF_CACHE is None:
            tags_df = pd.read_sql(f"SELECT DISTINCT name FROM activity_tags WHERE tag_type_id = '{DAYCODE_TAG_TYPE_ID}'", engine)
            _DIAS_REF_CACHE = set(tags_df['name'].dropna().tolist())
        
        dias_ref = _DIAS_REF_CACHE
        # Función para extraer el grupo_dia de tag_list_json SOLO si tag_type_id es el de DayCode
        def extraer_grupo_dia(tag_json_str):
            try:
                tags = json.loads(tag_json_str)
                for tag in tags:
                    if tag.get('tag_type_id') == DAYCODE_TAG_TYPE_ID and tag.get('name') in dias_ref:
                        return tag['name']
                return 'Sin clasificar'
            except Exception:
                return 'Sin clasificar'
                
        # Aplicar la extracción
        actividades_df['grupo_dia'] = actividades_df['tag_list_json'].apply(extraer_grupo_dia)
        
        # Función para normalizar los valores de grupo_dia (Game -X -> MD-X)
        def normalizar_grupo_dia(valor):
            # Caso base: ya es Sin clasificar
            if valor == 'Sin clasificar':
                return valor
                
            # Normalizar 'Game -X' a 'MD-X'
            game_pattern = r'Game\s+-\s*(\d+)'
            match = re.search(game_pattern, valor)
            if match:
                numero = match.group(1)
                return f'MD-{numero}'  # Formato unificado sin espacios
                
            # Normalizar 'MD -X' a 'MD-X' (eliminar espacio)
            md_pattern = r'MD\s+-\s*(\d+)'
            match = re.search(md_pattern, valor)
            if match:
                numero = match.group(1)
                return f'MD-{numero}'  # Formato unificado sin espacios
                
            # Para otros valores como MD o Game (sin número)
            if valor == 'Game':
                return 'MD'
                
            # Para otros formatos no reconocidos, mantener el valor original
            return valor
        
        # Aplicar la normalización
        actividades_df['grupo_dia'] = actividades_df['grupo_dia'].apply(normalizar_grupo_dia)
        
        return actividades_df
    except Exception as e:
        
        actividades_df['grupo_dia'] = 'Sin clasificar'
        return actividades_df

def get_metrics_for_activities_and_athletes(activity_ids, athlete_ids, parameter_name):
    """
    Devuelve las métricas para cada combinación de actividad y atleta.
    Args:
        activity_ids (list): lista de activity_id
        athlete_ids (list): lista de athlete_id
        parameter_name (str): métrica a consultar
    Returns:
        DataFrame con columnas: activity_id, athlete_id, parameter_value
    """
    try:
        engine = get_db_connection()
        if engine is None or not activity_ids or not athlete_ids:
            return pd.DataFrame(columns=["activity_id", "athlete_id", "parameter_value"])
        
        # Optimización: Usar índices y filtrar primero por parameter_name (más selectivo)
        # Convertir a CAST para asegurar tipo numérico en parameter_value
        query = '''
            SELECT activity_id, athlete_id, CAST(parameter_value AS DECIMAL(10,2)) as parameter_value
            FROM activity_athlete_metrics
            WHERE parameter_name = %s 
            AND activity_id IN %s 
            AND athlete_id IN %s
        '''
        df = pd.read_sql(query, engine, params=(parameter_name, tuple(activity_ids), tuple(athlete_ids)))
        return df
    except Exception as e:
        
        return pd.DataFrame(columns=["activity_id", "athlete_id", "parameter_value"])

def get_field_time_for_activities(activity_ids, athlete_ids):
    """
    Obtiene el field_time (tiempo en campo) para jugadores en actividades específicas.
    Args:
        activity_ids (list): lista de activity_id
        athlete_ids (list): lista de athlete_id
    Returns:
        DataFrame con columnas: activity_id, athlete_id, field_time (en segundos)
    """
    try:
        engine = get_db_connection()
        if engine is None or not activity_ids or not athlete_ids:
            return pd.DataFrame(columns=["activity_id", "athlete_id", "field_time"])
        
        query = '''
            SELECT 
                activity_id, 
                athlete_id, 
                CAST(parameter_value AS DECIMAL(10,2)) as field_time
            FROM activity_athlete_metrics
            WHERE parameter_name = 'field_time'
            AND activity_id IN %s 
            AND athlete_id IN %s
            AND parameter_value IS NOT NULL
            AND parameter_value != ''
        '''
        df = pd.read_sql(query, engine, params=(tuple(activity_ids), tuple(athlete_ids)))
        return df
    except Exception as e:
        print(f"Error getting field_time: {e}")
        return pd.DataFrame(columns=["activity_id", "athlete_id", "field_time"])

# Función para obtener los parámetros disponibles
def get_available_parameters():
    """
    Devuelve la lista de parámetros disponibles para seleccionar.
    Incluye distancia total y otras métricas de rendimiento.
    
    Returns:
        Lista de parámetros disponibles con su valor interno y etiqueta para mostrar.
    """
    return [
        {'value': 'total_distance', 'label': 'Distancia Total (m)'},
        {'value': 'distancia_21_kmh', 'label': 'Distancia +21km/h (m)'},
        {'value': 'distancia_24_kmh', 'label': 'Distancia +24km/h (m)'},
        {'value': 'acc_dec_total', 'label': 'Aceleraciones/Deceleraciones +3'},
        {'value': 'ritmo_medio', 'label': 'Ritmo Medio (m/min)'}
    ]
    
def get_variable_thresholds(variable_name):
    """
    Obtiene los umbrales (mínimo y máximo) para una variable específica por día del microciclo.
    
    Args:
        variable_name: Nombre de la variable para la que se desean los umbrales
        
    Returns:
        DataFrame con columnas: dia, min_value, max_value para cada día del microciclo
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame(columns=['dia', 'min_value', 'max_value'])
        
        # Mapeo de variables internas a nombres en la tabla de umbrales
        variable_mappings = {
            'total_distance': 'Average Distance (Session) (m)',
            'distancia_21_kmh': 'HSR Distance (m)',
            'distancia_24_kmh': 'Velocity Band Band 6 Distance (Session) (m)',
            'acc_dec_total': 'Aceleraciones',  # Sin umbrales en BD
            'ritmo_medio': 'Ritmo Medio'  # Sin umbrales en BD
        }
        
        # Obtener el nombre correcto para la consulta
        db_variable_name = variable_mappings.get(variable_name, variable_name)
        
        # Consultar umbrales para esta variable
        query = f"""SELECT dia, max_value, min_value 
                   FROM umbrales 
                   WHERE variable = '{db_variable_name}'
                   ORDER BY FIELD(dia, 'MD-4', 'MD-3', 'MD-2', 'MD-1', 'MD')"""
        
        df = pd.read_sql(query, engine)
        return df
        
    except Exception as e:
        # Solo imprimir errores críticos
        print(f"Error al obtener umbrales: {e}")
        # Devolver un DataFrame vacío en caso de error
        return pd.DataFrame(columns=['dia', 'min_value', 'max_value'])

# --------------------------------------
# FUNCIONES PARA LALIGA DATABASE
# --------------------------------------

def get_laliga_db_connection():
    """
    Crea y retorna una conexión a la base de datos LaLiga.
    """
    # Asegurar que las variables de entorno están cargadas
    load_dotenv()
    
    # Configuración de credenciales desde el archivo .env
    DB_CONFIG = {
        'user': os.getenv('LALIGA_DB_USER', os.getenv('DB_USER')),
        'password': os.getenv('LALIGA_DB_PASSWORD', os.getenv('DB_PASSWORD')),
        'host': os.getenv('LALIGA_DB_HOST', os.getenv('DB_HOST')),
        'database': os.getenv('LALIGA_DB_NAME', 'laliga')  # laliga por defecto
    }
    
    # Validar que tenemos las credenciales necesarias
    if not all(DB_CONFIG.values()):
        print(f"Error: Faltan credenciales de BD LaLiga. Config: {DB_CONFIG}")
        return None
    
    # Crear la URL de conexión
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    
    try:
        engine = create_engine(db_url)
        # Probar la conexión
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        print(f"Error conectando a LaLiga: {e}")
        print(f"URL de conexión (sin credenciales): mysql+pymysql://*:*@{DB_CONFIG['host']}/{DB_CONFIG['database']}")
        return None

def get_indicadores_rendimiento_laliga(team_name="RC Deportivo"):
    """
    Obtiene los indicadores de rendimiento desde la base de datos LaLiga para un equipo específico.
    Transforma los datos al formato estándar (metrica, valor, ranking).
    
    Args:
        team_name (str): Nombre del equipo (por defecto "RC Deportivo")
    
    Returns:
        DataFrame con columnas: metrica, valor, ranking
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return pd.DataFrame(columns=['metrica', 'valor', 'ranking'])
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'indicadores_rendimiento' not in inspector.get_table_names():
            return pd.DataFrame(columns=['metrica', 'valor', 'ranking'])
        
        # Consulta para obtener datos del equipo en formato estándar
        query = """
        SELECT 
            metric_name as metrica,
            CONCAT(metric_value, 
                   CASE 
                       WHEN metric_unit IS NOT NULL AND metric_unit != 'Unknown' 
                       THEN CONCAT(' ', metric_unit)
                       ELSE ''
                   END) as valor,
            ranking_position as ranking
        FROM indicadores_rendimiento 
        WHERE team_name = %s
        ORDER BY metric_category, metric_name
        """
        
        df = pd.read_sql(query, engine, params=(team_name,))
        
        if not df.empty:
            # Limpieza de datos
            df['ranking'] = pd.to_numeric(df['ranking'], errors='coerce').astype('Int64')
            df = df.dropna(subset=['metrica', 'ranking'])
        
        return df
        
    except Exception as e:
        pass
        return pd.DataFrame(columns=['metrica', 'valor', 'ranking'])

def get_available_teams_laliga():
    """
    Obtiene la lista de equipos disponibles en la tabla indicadores_rendimiento de LaLiga.
    
    Returns:
        list: Lista de nombres de equipos únicos
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return []
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'indicadores_rendimiento' not in inspector.get_table_names():
            return []
        
        query = "SELECT DISTINCT team_name FROM indicadores_rendimiento ORDER BY team_name"
        df = pd.read_sql(query, engine)
        teams = df['team_name'].tolist()
        print(f"Equipos disponibles: {teams}")
        return teams
        
    except Exception as e:
        print(f"Error obteniendo equipos disponibles: {e}")
        return []

def get_available_metrics_laliga(team_name="RC Deportivo"):
    """
    Obtiene las métricas disponibles para un equipo específico en LaLiga.
    
    Args:
        team_name (str): Nombre del equipo
    
    Returns:
        list: Lista de métricas disponibles para el equipo
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return []
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'indicadores_rendimiento' not in inspector.get_table_names():
            return []
        
        # Obtener los nombres de métricas únicos para el equipo
        query = """
        SELECT DISTINCT metric_name 
        FROM indicadores_rendimiento 
        WHERE team_name = %s 
        ORDER BY metric_name
        """
        df = pd.read_sql(query, engine, params=(team_name,))
        metrics = df['metric_name'].tolist()
        
        print(f"Métricas disponibles para {team_name}: {len(metrics)} métricas")
        return metrics
        
    except Exception as e:
        print(f"Error obteniendo métricas disponibles: {e}")
        return []

def get_metrics_by_category_laliga(team_name="RC Deportivo"):
    """
    Obtiene las métricas agrupadas por categoría para un equipo específico.
    
    Args:
        team_name (str): Nombre del equipo
    
    Returns:
        dict: Diccionario con categorías como claves y listas de métricas como valores
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        query = """
        SELECT 
            metric_category,
            metric_name,
            ranking_position
        FROM indicadores_rendimiento 
        WHERE team_name = %s 
        ORDER BY metric_category, metric_name
        """
        df = pd.read_sql(query, engine, params=(team_name,))
        
        if df.empty:
            return {}
        
        # Agrupar por categoría
        categories = {}
        for category in df['metric_category'].unique():
            category_metrics = df[df['metric_category'] == category]['metric_name'].tolist()
            categories[category] = category_metrics
        
        return categories
        
    except Exception as e:
        print(f"Error obteniendo métricas por categoría: {e}")
        return {}

def get_all_teams_ranking_by_metric_laliga(metric_name):
    """
    Obtiene el ranking de todos los equipos para una métrica específica.
    
    Args:
        metric_name (str): Nombre de la métrica
    
    Returns:
        dict: Diccionario con ranking_position como clave y team_name como valor
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        query = """
        SELECT 
            team_name,
            ranking_position,
            metric_value
        FROM indicadores_rendimiento 
        WHERE metric_name = %s 
        ORDER BY ranking_position
        """
        df = pd.read_sql(query, engine, params=(metric_name,))
        
        if df.empty:
            return {}
        
        # Crear diccionario ranking -> equipo
        ranking_dict = {}
        for _, row in df.iterrows():
            ranking_dict[int(row['ranking_position'])] = {
                'team': row['team_name'],
                'value': row['metric_value']
            }
        
        return ranking_dict
        
    except Exception as e:
        print(f"Error obteniendo ranking por métrica: {e}")
        return {}

def get_all_teams_rankings_laliga(metric_names):
    """
    Obtiene el ranking de todos los equipos para múltiples métricas.
    
    Args:
        metric_names (list): Lista de nombres de métricas
    
    Returns:
        dict: Diccionario anidado {metric_name: {ranking: {team, value}}}
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        # Crear placeholders para la consulta IN
        placeholders = ','.join(['%s'] * len(metric_names))
        query = f"""
        SELECT 
            metric_name,
            team_name,
            ranking_position,
            metric_value
        FROM indicadores_rendimiento 
        WHERE metric_name IN ({placeholders})
        ORDER BY metric_name, ranking_position
        """
        
        df = pd.read_sql(query, engine, params=tuple(metric_names))
        
        if df.empty:
            return {}
        
        # Crear diccionario anidado
        rankings_dict = {}
        for _, row in df.iterrows():
            metric = row['metric_name']
            ranking = int(row['ranking_position'])
            
            if metric not in rankings_dict:
                rankings_dict[metric] = {}
            
            rankings_dict[metric][ranking] = {
                'team': row['team_name'],
                'value': row['metric_value']
            }
        
        return rankings_dict
        
    except Exception as e:
        print(f"Error obteniendo rankings múltiples: {e}")
        return {}

def get_metric_info_from_name(metric_name, team_name="RC Deportivo"):
    """
    Obtiene el metric_id, metric_category y season_id para una métrica específica desde indicadores_rendimiento.
    
    Args:
        metric_name (str): Nombre de la métrica (ej: "Iniciativa de Juego (Puntos)")
        team_name (str): Nombre del equipo
    
    Returns:
        tuple: (metric_id, metric_category, season_id) o (None, None, None) si no se encuentra
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return None, None, None
        
        query = """
        SELECT metric_id, metric_category, season_id
        FROM indicadores_rendimiento
        WHERE team_name = %s AND metric_name = %s
        LIMIT 1
        """
        
        df = pd.read_sql(query, engine, params=(team_name, metric_name))
        
        if not df.empty:
            return df.iloc[0]['metric_id'], df.iloc[0]['metric_category'], df.iloc[0]['season_id']
        
        return None, None, None
        
    except Exception as e:
        print(f"Error obteniendo info de métrica: {e}")
        return None, None, None


def get_match_opponents_by_matchday(team_name, season_id=1):
    """
    Obtiene los equipos rivales para cada jornada.
    
    Args:
        team_name (str): Nombre del equipo en laliga_teams (ej: "RC Deportivo")
        season_id (int): ID de la temporada
    
    Returns:
        dict: {match_day_number: opponent_name}
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        # Primero obtener los match_ids del equipo desde laliga_teams
        query_match_ids = """
        SELECT DISTINCT match_id 
        FROM laliga_teams 
        WHERE team_name = %s
        """
        df_match_ids = pd.read_sql(query_match_ids, engine, params=(team_name,))
        
        if df_match_ids.empty:
            return {}
        
        match_ids = df_match_ids['match_id'].tolist()
        
        # Obtener información de partidos desde laliga_matches
        placeholders = ','.join(['%s'] * len(match_ids))
        query_matches = f"""
        SELECT 
            match_day_number,
            home_team_name,
            away_team_name
        FROM laliga_matches
        WHERE match_id IN ({placeholders})
        AND season_id = %s
        ORDER BY match_day_number
        """
        
        df_matches = pd.read_sql(query_matches, engine, params=tuple(match_ids) + (season_id,))
        
        if df_matches.empty:
            return {}
        
        # Mapeo de nombres entre laliga_teams y laliga_matches
        team_name_mapping = {
            'RC Deportivo': 'Deportivo de La Coruña',
            # Agregar más mapeos si es necesario
        }
        
        team_name_in_matches = team_name_mapping.get(team_name, team_name)
        
        # Determinar el rival en cada jornada
        opponents = {}
        for _, row in df_matches.iterrows():
            matchday = int(row['match_day_number'])
            if row['home_team_name'] == team_name_in_matches:
                opponents[matchday] = row['away_team_name']
            else:
                opponents[matchday] = row['home_team_name']
        
        return opponents
        
    except Exception as e:
        print(f"Error obteniendo rivales por jornada: {e}")
        return {}


def get_match_results_by_matchday(team_name, season_id=1):
    """
    Obtiene los resultados (goles y resultado) para cada jornada desde match_context_analysis.
    
    Args:
        team_name (str): Nombre del equipo en laliga_teams (ej: "RC Deportivo")
        season_id (int): ID de la temporada
    
    Returns:
        dict: {match_day_number: {'goles_favor': int, 'goles_contra': int, 'resultado': str}}
              donde resultado puede ser 'Victoria', 'Empate', o 'Derrota'
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        query = """
        SELECT 
            match_day_number,
            goles_favor,
            goles_contra,
            resultado
        FROM match_context_analysis
        WHERE depor_team_name_teams = %s
        AND season_id = %s
        ORDER BY match_day_number
        """
        
        df_results = pd.read_sql(query, engine, params=(team_name, season_id))
        
        if df_results.empty:
            return {}
        
        # Crear diccionario con resultados por jornada
        results = {}
        for _, row in df_results.iterrows():
            matchday = int(row['match_day_number'])
            results[matchday] = {
                'goles_favor': int(row['goles_favor']) if pd.notna(row['goles_favor']) else 0,
                'goles_contra': int(row['goles_contra']) if pd.notna(row['goles_contra']) else 0,
                'resultado': row['resultado'] if pd.notna(row['resultado']) else 'Sin datos'
            }
        
        return results
        
    except Exception as e:
        print(f"Error obteniendo resultados por jornada: {e}")
        return {}


def get_metric_evolution_by_matchday(team_name, metric_id, metric_category, season_id=1):
    """
    Obtiene la evolución de una métrica específica para un equipo a lo largo de las jornadas.
    
    Args:
        team_name (str): Nombre del equipo
        metric_id (str): ID de la métrica a consultar
        metric_category (str): Categoría de la métrica
        season_id (int): ID de la temporada (por defecto 1)
    
    Returns:
        DataFrame con columnas: match_day_number, metric_value
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return pd.DataFrame(columns=['match_day_number', 'metric_value'])
        
        # Query optimizada: primero filtrar por laliga_teams (que tiene el nombre correcto)
        # y luego hacer JOIN con laliga_matches para obtener match_day_number
        query = """
        SELECT 
            m.match_day_number,
            t.metric_value
        FROM laliga_teams t
        INNER JOIN laliga_matches m ON t.match_id = m.match_id
        WHERE 
            t.team_name = %s
            AND t.metric_id = %s
            AND t.metric_category = %s
            AND m.season_id = %s
        ORDER BY m.match_day_number
        """
        
        df = pd.read_sql(
            query, 
            engine, 
            params=(team_name, metric_id, metric_category, season_id)
        )
        
        # Convertir a numéricos y limpiar
        if not df.empty:
            df['match_day_number'] = pd.to_numeric(df['match_day_number'], errors='coerce')
            df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
            df = df[['match_day_number', 'metric_value']].dropna()
        
        return df
        
    except Exception as e:
        print(f"Error obteniendo evolución de métrica: {e}")
        return pd.DataFrame(columns=['match_day_number', 'metric_value'])


def get_rankings_compuestos_laliga(team_name="RC Deportivo"):
    """
    Obtiene los rankings compuestos específicos (RankingEstilo, RankingOfensivo, etc.) 
    para un equipo desde la base de datos LaLiga.
    
    Args:
        team_name (str): Nombre del equipo (por defecto "RC Deportivo")
    
    Returns:
        dict: Diccionario con {metric_id: ranking_position} para los rankings compuestos
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'indicadores_rendimiento' not in inspector.get_table_names():
            return {}
        
        # Consulta para obtener exactamente los rankings que necesitamos
        # Para Rendimiento: RankingRendimiento, RankingOfensivo, RankingDefensivo, 
        #                   RankingFísico-Combatividad, RankingBalónParado
        # Para Estilo: RankingEstilo, RankingEstilo-IdentidadGeneral, 
        #              RankingEstilo-IdentidadOfensiva, RankingEstilo-IdentidadDefensiva
        query = """
        SELECT 
            metric_id,
            ranking_position
        FROM indicadores_rendimiento 
        WHERE team_name = %s 
        AND metric_id IN (
            'RankingRendimiento',
            'RankingOfensivo',
            'RankingDefensivo',
            'RankingFísico-Combatividad',
            'RankingBalónParado',
            'RankingEstilo',
            'RankingEstilo-IdentidadGeneral',
            'RankingEstilo-IdentidadOfensiva',
            'RankingEstilo-IdentidadDefensiva'
        )
        ORDER BY metric_id
        """
        
        df = pd.read_sql(query, engine, params=(team_name,))
        
        if not df.empty:
            # Convertir a diccionario
            rankings_dict = dict(zip(df['metric_id'], df['ranking_position']))
            return rankings_dict
        else:
            return {}
        
    except Exception as e:
        pass
        return {}

# --------------------------------------
# FUNCIONES PARA SOCCER SYSTEM (MÉDICO)
# --------------------------------------

def get_soccer_db_connection():
    """
    Crea y retorna una conexión a la base de datos soccersystem.
    """
    # Asegurar que las variables de entorno están cargadas
    load_dotenv()
    
    # Configuración de credenciales desde el archivo .env
    DB_CONFIG = {
        'user': os.getenv('SOCCER_DB_USER', os.getenv('DB_USER')),
        'password': os.getenv('SOCCER_DB_PASSWORD', os.getenv('DB_PASSWORD')),
        'host': os.getenv('SOCCER_DB_HOST', os.getenv('DB_HOST')),
        'database': os.getenv('SOCCER_DB_NAME', 'soccersystem')  # soccersystem
    }
    
    # Validar que tenemos las credenciales necesarias
    if not all(DB_CONFIG.values()):
        print(f"Error: Faltan credenciales de BD. Config: {DB_CONFIG}")
        return None
    
    # Crear la URL de conexión
    db_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    
    try:
        engine = create_engine(db_url)
        # Probar la conexión
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        print(f"Error conectando a soccersystem: {e}")
        print(f"URL de conexión (sin credenciales): mysql+pymysql://*:*@{DB_CONFIG['host']}/{DB_CONFIG['database']}")
        return None

def get_fechas_entrenamiento_disponibles():
    """
    Obtiene todas las fechas de entrenamiento disponibles ordenadas de más reciente a más antigua.
    
    Returns:
        list: Lista de fechas ordenadas descendentemente
    """
    try:
        print("Intentando obtener fechas de entrenamiento...")
        engine = get_soccer_db_connection()
        if engine is None:
            print("Error: No se pudo obtener conexión a la BD soccersystem")
            return []
        
        query = """
        SELECT DISTINCT fecha_entrenamiento 
        FROM medico_mejuto 
        ORDER BY fecha_entrenamiento DESC
        """
        
        print(f"Ejecutando query: {query}")
        df = pd.read_sql(query, engine)
        fechas = df['fecha_entrenamiento'].tolist()
        print(f"Fechas obtenidas: {len(fechas)} - Primeras 3: {fechas[:3] if fechas else 'Ninguna'}")
        return fechas
        
    except Exception as e:
        print(f"Error obteniendo fechas: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_evaluaciones_medicas(fecha_entrenamiento):
    """
    Obtiene todas las evaluaciones médicas para una fecha específica.
    """
    try:
        print(f"Obteniendo evaluaciones médicas para fecha: {fecha_entrenamiento}")
        # Obtener conexión
        engine = get_soccer_db_connection()
        if engine is None:
            print("Error: No se pudo obtener conexión a la BD soccersystem")
            return pd.DataFrame()
        
        query = """
        SELECT 
            COALESCE(m.nombre_pedrosa, mm.nombre_jugador) as nombre_jugador,
            mm.evaluacion,
            mm.comentarios_evaluacion,
            mm.observaciones
        FROM medico_mejuto mm
        LEFT JOIN mapeo_nombre_dni m ON mm.nombre_jugador COLLATE utf8mb4_unicode_ci = m.nombre_mejuto COLLATE utf8mb4_unicode_ci
        WHERE mm.fecha_entrenamiento = %s
        ORDER BY COALESCE(m.nombre_pedrosa, mm.nombre_jugador)
        """
        
        print(f"Ejecutando query con fecha: {fecha_entrenamiento}")
        df = pd.read_sql(query, engine, params=(fecha_entrenamiento,))
        print(f"Evaluaciones obtenidas: {len(df)} registros")
        
        # Rellenar valores nulos con cadena vacía
        df = df.fillna('')
        
        return df
    except Exception as e:
        print(f"Error obteniendo evaluaciones médicas: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def get_historico_evaluaciones_completo():
    """
    Obtiene todas las evaluaciones médicas históricas para análisis evolutivo con nombres unificados
    """
    try:
        # Obtener conexión
        engine = get_soccer_db_connection()
        if engine is None:
            return pd.DataFrame()
        
        query = """
        SELECT 
            mm.fecha_entrenamiento,
            COALESCE(m.nombre_pedrosa, mm.nombre_jugador) as nombre_jugador,
            mm.evaluacion,
            mm.comentarios_evaluacion,
            mm.observaciones
        FROM medico_mejuto mm
        LEFT JOIN mapeo_nombre_dni m ON mm.nombre_jugador COLLATE utf8mb4_unicode_ci = m.nombre_mejuto COLLATE utf8mb4_unicode_ci
        WHERE mm.evaluacion IS NOT NULL
        ORDER BY mm.fecha_entrenamiento DESC, COALESCE(m.nombre_pedrosa, mm.nombre_jugador) ASC
        """
        
        df = pd.read_sql_query(query, engine)
        engine.dispose()
        
        return df
    except Exception as e:
        print(f"Error obteniendo histórico de evaluaciones: {e}")
        return pd.DataFrame()

def get_estadisticas_por_jugador():
    """
    Calcula estadísticas de días por estado para cada jugador
    """
    try:
        df_historico = get_historico_evaluaciones_completo()
        if df_historico.empty:
            return pd.DataFrame()
        
        # Contar días por jugador y evaluación
        stats = df_historico.groupby(['nombre_jugador', 'evaluacion']).size().reset_index(name='dias')
        
        # Calcular total de días por jugador
        total_dias = df_historico.groupby('nombre_jugador').size().reset_index(name='total_dias')
        
        # Merge y calcular porcentajes
        stats = stats.merge(total_dias, on='nombre_jugador')
        stats['porcentaje'] = (stats['dias'] / stats['total_dias'] * 100).round(1)
        
        # Pivot para tener columnas por estado
        stats_pivot = stats.pivot(index='nombre_jugador', columns='evaluacion', values='porcentaje').fillna(0)
        
        # Asegurar que todas las columnas estén presentes
        for estado in ['Normal', 'Precaución', 'Fisio/RTP']:
            if estado not in stats_pivot.columns:
                stats_pivot[estado] = 0.0
        
        # Reordenar columnas
        stats_pivot = stats_pivot[['Normal', 'Precaución', 'Fisio/RTP']]
        stats_pivot = stats_pivot.reset_index()
        
        return stats_pivot
    except Exception as e:
        print(f"Error calculando estadísticas por jugador: {e}")
        return pd.DataFrame()

def get_evolucion_jugador(nombre_jugador):
    """
    Obtiene la evolución temporal de un jugador específico
    """
    try:
        df_historico = get_historico_evaluaciones_completo()
        if df_historico.empty:
            return pd.DataFrame()
        
        # Filtrar por jugador
        df_jugador = df_historico[df_historico['nombre_jugador'] == nombre_jugador].copy()
        
        if df_jugador.empty:
            return pd.DataFrame()
        
        # Mapear evaluaciones a valores numéricos para el gráfico
        evaluacion_map = {
            'Fisio/RTP': 1,
            'Precaución': 2, 
            'Normal': 3
        }
        
        df_jugador['valor_numerico'] = df_jugador['evaluacion'].map(evaluacion_map)
        
        # Ordenar por fecha
        df_jugador = df_jugador.sort_values('fecha_entrenamiento')
        
        return df_jugador
    except Exception as e:
        print(f"Error obteniendo evolución del jugador: {e}")
        return pd.DataFrame()

def get_lista_jugadores():
    """
    Obtiene la lista de jugadores únicos con evaluaciones
    """
    try:
        df_historico = get_historico_evaluaciones_completo()
        if df_historico.empty:
            return []
        
        jugadores = sorted(df_historico['nombre_jugador'].unique().tolist())
        return jugadores
    except Exception as e:
        print(f"Error obteniendo lista de jugadores: {e}")
        return []

# --------------------------------------
# FUNCIONES PARA TABLA INTERMEDIA DE MICROCICLOS
# --------------------------------------

def get_microciclos_from_processed_table():
    """
    Obtiene la lista de microciclos desde la tabla preprocesada.
    Mucho más rápido que get_microciclos() ya que no procesa actividades en tiempo real.
    
    Returns:
        Lista de diccionarios con:
        - id: microciclo_id
        - label: etiqueta para mostrar
        - start_date: fecha de inicio
        - end_date: fecha de fin
        - partido_nombre: nombre del partido
        - is_current: True si es semana actual
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return []
        
        query = '''
            SELECT 
                microciclo_id,
                microciclo_nombre,
                MIN(fecha_inicio) as fecha_inicio,
                MAX(fecha_fin) as fecha_fin,
                partido_nombre,
                MAX(fecha_partido) as fecha_partido,
                MAX(is_current_week) as is_current_week
            FROM microciclos_metricas_procesadas
            GROUP BY microciclo_id, microciclo_nombre, partido_nombre
            ORDER BY MIN(fecha_inicio) DESC
        '''
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return []
        
        microciclos = []
        for _, row in df.iterrows():
            # Formatear fechas para label
            fecha_inicio_str = pd.to_datetime(row['fecha_inicio']).strftime('%d/%m/%Y')
            fecha_fin_str = pd.to_datetime(row['fecha_fin']).strftime('%d/%m/%Y')
            
            microciclo = {
                'id': row['microciclo_id'],
                'label': f"{row['microciclo_nombre']} ({fecha_inicio_str} - {fecha_fin_str})",
                'start_date': pd.to_datetime(row['fecha_inicio']).strftime('%Y-%m-%d'),
                'end_date': pd.to_datetime(row['fecha_fin']).strftime('%Y-%m-%d %H:%M:%S'),
                'partido_nombre': row['partido_nombre'],
                'is_current': bool(row.get('is_current_week', False))
            }
            
            microciclos.append(microciclo)
        
        return microciclos
        
    except Exception as e:
        print(f"Error obteniendo microciclos desde tabla procesada: {e}")
        import traceback
        traceback.print_exc()
        # Fallback a función antigua
        return get_microciclos()


def get_microciclo_data_processed(microciclo_id, metric_name, athlete_ids=None, 
                                   exclude_part_rehab=True, exclude_goalkeepers=True):
    """
    Obtiene datos de un microciclo desde la tabla preprocesada.
    
    Args:
        microciclo_id (str): ID del microciclo (ej: 'mc_2024-11-10_vs_Oviedo')
        metric_name (str): Nombre de la métrica (ej: 'total_distance')
        athlete_ids (list): Lista de IDs de atletas a incluir (None = todos)
        exclude_part_rehab (bool): Excluir participaciones Part/Rehab
        exclude_goalkeepers (bool): Excluir porteros
    
    Returns:
        DataFrame con columnas: activity_tag, athlete_id, athlete_name, athlete_position,
                                participation_type, <metric_name>
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        
        # Mapeo de nombres de métricas del dashboard a columnas de la tabla
        metric_mapping = {
            'total_distance': 'total_distance',
            'distancia_+21_km/h_(m)': 'distancia_21_kmh',
            'distancia_+24_km/h_(m)': 'distancia_24_kmh',
            'distancia+28_(km/h)': 'distancia_28_kmh',
            'gen2_acceleration_band7plus_total_effort_count': 'aceleraciones',
            'average_player_load': 'player_load',
            'player_load': 'player_load',
            'max_vel': 'max_vel',
            'field_time': 'field_time'
        }
        
        # Obtener nombre de columna en la tabla
        column_name = metric_mapping.get(metric_name, metric_name)
        
        # Construir query base (siempre incluir field_time para estandarización)
        query = f'''
            SELECT 
                activity_tag,
                activity_date,
                activity_name,
                athlete_id,
                athlete_name,
                athlete_position,
                participation_type,
                {column_name} as metric_value,
                field_time
            FROM microciclos_metricas_procesadas
            WHERE microciclo_id = %s
        '''
        
        params = [microciclo_id]
        
        # Filtros opcionales
        if exclude_part_rehab:
            query += " AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))"
        
        if exclude_goalkeepers:
            query += " AND athlete_position != 'Goal Keeper'"
        
        if athlete_ids:
            placeholders = ','.join(['%s'] * len(athlete_ids))
            query += f" AND athlete_id IN ({placeholders})"
            params.extend(athlete_ids)
        
        query += " ORDER BY activity_date ASC, athlete_name ASC"
        
        df = pd.read_sql(query, engine, params=tuple(params))
        
        # FILTRO ADICIONAL: Los compensatorios (MD+X) SIEMPRE deben filtrar Part/Rehab
        # independientemente del parámetro exclude_part_rehab
        if not df.empty and 'activity_tag' in df.columns:
            import re
            # Identificar compensatorios
            df['es_compensatorio'] = df['activity_tag'].apply(
                lambda x: bool(re.match(r'^MD\+\d+$', str(x)))
            )
            
            # Filtrar compensatorios: solo participation_type Full (NULL o no Part/Rehab)
            df_filtrado = df[
                (~df['es_compensatorio']) |
                (
                    df['es_compensatorio'] & 
                    (df['participation_type'].isna() | 
                     ~df['participation_type'].isin(['Part', 'Rehab']))
                )
            ].copy()
            
            # Eliminar columna temporal
            df = df_filtrado.drop(columns=['es_compensatorio'])
        
        return df
        
    except Exception as e:
        print(f"Error obteniendo datos del microciclo procesado: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_athletes_from_microciclo(microciclo_id):
    """
    Obtiene la lista de atletas que participaron en un microciclo.
    
    Args:
        microciclo_id (str): ID del microciclo
    
    Returns:
        DataFrame con: athlete_id, athlete_name, athlete_position, 
                      has_part_rehab (True si tiene alguna actividad Part/Rehab)
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        
        query = '''
            SELECT DISTINCT
                athlete_id,
                athlete_name,
                athlete_position,
                MAX(CASE 
                    WHEN participation_type IN ('Part', 'Rehab') THEN 1 
                    ELSE 0 
                END) as has_part_rehab
            FROM microciclos_metricas_procesadas
            WHERE microciclo_id = %s
            GROUP BY athlete_id, athlete_name, athlete_position
            ORDER BY athlete_name ASC
        '''
        
        df = pd.read_sql(query, engine, params=(microciclo_id,))
        df['has_part_rehab'] = df['has_part_rehab'].astype(bool)
        
        return df
        
    except Exception as e:
        print(f"Error obteniendo atletas del microciclo: {e}")
        return pd.DataFrame()


def get_microciclo_metrics_summary(microciclo_id, metric_name, athlete_ids=None,
                                   exclude_part_rehab=True, exclude_goalkeepers=True):
    """
    Obtiene resumen de métricas agrupadas por día (activity_tag) para un microciclo.
    Útil para gráficos de barras por día.
    
    Args:
        microciclo_id (str): ID del microciclo
        metric_name (str): Nombre de la métrica
        athlete_ids (list): Lista de IDs de atletas a incluir
        exclude_part_rehab (bool): Excluir Part/Rehab
        exclude_goalkeepers (bool): Excluir porteros
    
    Returns:
        DataFrame con: activity_tag, avg_metric, sum_metric, count_athletes
    """
    print(f"\n📊 get_microciclo_metrics_summary LLAMADA:")
    print(f"  Microciclo: {microciclo_id}")
    print(f"  Métrica: {metric_name}")
    print(f"  Jugadores: {len(athlete_ids) if athlete_ids else 'TODOS'}")
    print(f"  Exclude Part/Rehab: {exclude_part_rehab}")
    
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        
        # Mapeo de métricas
        metric_mapping = {
            'total_distance': 'total_distance',
            'distancia_+21_km/h_(m)': 'distancia_21_kmh',
            'distancia_+24_km/h_(m)': 'distancia_24_kmh',
            'distancia+28_(km/h)': 'distancia_28_kmh',
            'gen2_acceleration_band7plus_total_effort_count': 'aceleraciones',
            'average_player_load': 'player_load',
            'player_load': 'player_load',
            'max_vel': 'max_vel',
            'field_time': 'field_time'
        }
        
        column_name = metric_mapping.get(metric_name, metric_name)
        
        # Query con agregaciones
        query = f'''
            SELECT 
                activity_tag,
                activity_date,
                AVG({column_name}) as avg_metric,
                SUM({column_name}) as sum_metric,
                COUNT(DISTINCT athlete_id) as count_athletes
            FROM microciclos_metricas_procesadas
            WHERE microciclo_id = %s
        '''
        
        params = [microciclo_id]
        
        if exclude_part_rehab:
            query += " AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))"
        
        # COMPENSATORIOS (MD+X): SIEMPRE filtrar Part/Rehab independientemente del parámetro
        # Solo aplicar a compensatorios con patrón MD+número
        query += " AND (activity_tag NOT REGEXP '^MD\\\\+[0-9]+$' OR (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab')))"
        
        if exclude_goalkeepers:
            query += " AND athlete_position != 'Goal Keeper'"
        
        if athlete_ids:
            placeholders = ','.join(['%s'] * len(athlete_ids))
            # NO filtrar MD por jugadores (debe usar TODOS), solo filtrar entrenamientos
            query += f" AND (activity_tag = 'MD' OR athlete_id IN ({placeholders}))"
            params.extend(athlete_ids)
            print(f"  🔍 Filtrando: {len(athlete_ids)} jugadores para entrenamientos, MD usa TODOS")
        
        query += " GROUP BY activity_tag, activity_date ORDER BY activity_date ASC"
        
        df = pd.read_sql(query, engine, params=tuple(params))
        
        if not df.empty:
            print(f"  ✅ Resumen obtenido:")
            for _, row in df.iterrows():
                print(f"    {row['activity_tag']}: {row['count_athletes']} jugadores, avg={row['avg_metric']:.1f}")
        
        return df
        
    except Exception as e:
        print(f"Error obteniendo resumen de métricas: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_ultimos_4_mds_promedios(metric_name, fecha_partido_actual, exclude_part_rehab=True, exclude_goalkeepers=True):
    """
    Obtiene los promedios de los últimos 4 MDs (incluyendo el actual).
    CRÍTICO: Filtra jugadores +70 mins y estandariza a 94'.
    
    Args:
        metric_name: Nombre de la métrica
        fecha_partido_actual: Fecha del partido actual para buscar hacia atrás
        exclude_part_rehab: Excluir Part/Rehab
        exclude_goalkeepers: Excluir porteros
        
    Returns:
        DataFrame con: fecha_partido, microciclo_id, promedio_estandarizado
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        
        # Mapeo de métricas
        metric_mapping = {
            'total_distance': 'total_distance',
            'distancia_+21_km/h_(m)': 'distancia_21_kmh',
            'distancia_+24_km/h_(m)': 'distancia_24_kmh',
            'distancia+28_(km/h)': 'distancia_28_kmh',
            'gen2_acceleration_band7plus_total_effort_count': 'aceleraciones',
            'average_player_load': 'player_load',
            'player_load': 'player_load',
            'max_vel': 'max_vel'
        }
        
        column_name = metric_mapping.get(metric_name, metric_name)
        
        # Query para obtener últimos 4 MDs con filtrado +70 mins y estandarización
        query = f'''
            SELECT 
                activity_date as fecha_partido,
                microciclo_id,
                microciclo_nombre,
                AVG({column_name} * (5640.0 / field_time)) as promedio_estandarizado
            FROM microciclos_metricas_procesadas
            WHERE activity_tag = 'MD'
              AND field_time >= 4200
              AND {column_name} IS NOT NULL
              AND activity_date <= %s
        '''
        
        params = [fecha_partido_actual]
        
        if exclude_part_rehab:
            query += " AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))"
        
        if exclude_goalkeepers:
            query += " AND athlete_position != 'Goal Keeper'"
        
        query += '''
            GROUP BY activity_date, microciclo_id, microciclo_nombre
            ORDER BY activity_date DESC
            LIMIT 4
        '''
        
        df = pd.read_sql(query, engine, params=tuple(params))
        return df
        
    except Exception as e:
        print(f"Error obteniendo últimos 4 MDs: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_microciclo_athlete_totals(microciclo_id, metric_name, exclude_part_rehab=True, exclude_goalkeepers=True):
    """
    Obtiene totales acumulados por atleta para un microciclo.
    Útil para comparar carga total entre jugadores.
    
    Args:
        microciclo_id (str): ID del microciclo
        metric_name (str): Nombre de la métrica
        exclude_part_rehab (bool): Excluir Part/Rehab
        exclude_goalkeepers (bool): Excluir porteros
    
    Returns:
        DataFrame con: athlete_name, total_metric, avg_metric, num_sessions
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        
        metric_mapping = {
            'total_distance': 'total_distance',
            'distancia_+21_km/h_(m)': 'distancia_21_kmh',
            'distancia_+24_km/h_(m)': 'distancia_24_kmh',
            'distancia+28_(km/h)': 'distancia_28_kmh',
            'gen2_acceleration_band7plus_total_effort_count': 'aceleraciones',
            'average_player_load': 'player_load',
            'player_load': 'player_load',
            'max_vel': 'max_vel',
            'field_time': 'field_time'
        }
        
        column_name = metric_mapping.get(metric_name, metric_name)
        
        query = f'''
            SELECT 
                athlete_id,
                athlete_name,
                athlete_position,
                SUM({column_name}) as total_metric,
                AVG({column_name}) as avg_metric,
                COUNT(DISTINCT activity_id) as num_sessions
            FROM microciclos_metricas_procesadas
            WHERE microciclo_id = %s
        '''
        
        params = [microciclo_id]
        
        if exclude_part_rehab:
            query += " AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))"
        
        if exclude_goalkeepers:
            query += " AND athlete_position != 'Goal Keeper'"
        
        query += " GROUP BY athlete_id, athlete_name, athlete_position ORDER BY total_metric DESC"
        
        df = pd.read_sql(query, engine, params=tuple(params))
        
        return df
        
    except Exception as e:
        print(f"Error obteniendo totales por atleta: {e}")
        return pd.DataFrame()


def get_full_section_ranking(ranking_id: str):
    """
    Obtiene el ranking completo de todos los equipos para una sección específica.
    
    Args:
        ranking_id: ID del ranking (ej: 'RankingEstilo', 'RankingOfensivo', etc.)
    
    Returns:
        Lista de diccionarios con team_name, ranking_position, section_name
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return get_full_section_ranking_fallback(ranking_id)
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'indicadores_rendimiento' not in inspector.get_table_names():
            return get_full_section_ranking_fallback(ranking_id)
        
        # Consultar el ranking completo para la sección específica
        query = """
        SELECT team_name, ranking_position, metric_id
        FROM indicadores_rendimiento 
        WHERE metric_id = %s 
        ORDER BY ranking_position ASC
        """
        
        df = pd.read_sql(query, engine, params=(ranking_id,))
        
        if df.empty:
            print(f"No se encontraron datos para {ranking_id}")
            return get_full_section_ranking_fallback(ranking_id)
        
        # Mapear metric_id a nombre de sección
        id_to_section = {
            'RankingEstilo': 'ESTILO',
            'RankingOfensivo': 'RENDIMIENTO OFENSIVO',
            'RankingDefensivo': 'RENDIMIENTO DEFENSIVO', 
            'RankingFísico': 'RENDIMIENTO FÍSICO',
            'RankingBalónParado': 'BALÓN PARADO',
            'RankingGlobal': 'RENDIMIENTO GLOBAL'
        }
        
        section_name = id_to_section.get(ranking_id, ranking_id)
        
        ranking_data = []
        for _, row in df.iterrows():
            ranking_data.append({
                'team_name': row['team_name'],
                'ranking_position': int(row['ranking_position']),
                'section_name': section_name
            })
        
        print(f"✅ Obtenido ranking completo para {ranking_id}: {len(ranking_data)} equipos")
        return ranking_data
        
    except Exception as e:
        print(f"Error en get_full_section_ranking: {e}")
        return get_full_section_ranking_fallback(ranking_id)


def get_full_section_ranking_fallback(ranking_id: str):
    """Datos de fallback para el ranking completo de una sección"""
    
    # Simulamos datos de ejemplo para La Liga (22 equipos)
    teams = [
        "FC Barcelona", "Real Madrid", "Atlético Madrid", "RC Deportivo", 
        "Real Sociedad", "Athletic Club", "Valencia CF", "Sevilla FC",
        "Real Betis", "Villarreal CF", "Getafe CF", "Osasuna",
        "Celta Vigo", "Las Palmas", "Rayo Vallecano", "Alavés",
        "Mallorca", "Girona FC", "Leganes", "Espanyol",
        "Valladolid", "Almería"
    ]
    
    id_to_section = {
        'RankingEstilo': 'ESTILO',
        'RankingOfensivo': 'RENDIMIENTO OFENSIVO',
        'RankingDefensivo': 'RENDIMIENTO DEFENSIVO', 
        'RankingFísico': 'RENDIMIENTO FÍSICO',
        'RankingBalónParado': 'BALÓN PARADO',
        'RankingGlobal': 'RENDIMIENTO GLOBAL'
    }
    
    section_name = id_to_section.get(ranking_id, ranking_id)
    
    ranking_data = []
    for i, team in enumerate(teams, 1):
        ranking_data.append({
            'team_name': team,
            'ranking_position': i,
            'section_name': section_name
        })
    
    print(f"⚠️ Usando datos fallback para {ranking_id}")
    return ranking_data


# --------------------------------------
# FUNCIONES PARA CONTEXTOS DE PARTIDOS
# --------------------------------------

def get_match_context_analysis(team_name="RC Deportivo", competition_id=None, season_id=None):
    """
    Obtiene el análisis de contextos de partidos desde la tabla match_context_analysis.
    
    Args:
        team_name (str): Nombre del equipo en laliga_teams (por defecto "RC Deportivo")
        competition_id (str): ID de la competición (opcional)
        season_id (str): ID de la temporada (opcional)
    
    Returns:
        DataFrame con todos los campos de match_context_analysis
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            print("Error: No se pudo conectar a la BD LaLiga")
            return pd.DataFrame()
        
        # Verificar si la tabla existe
        inspector = inspect(engine)
        if 'match_context_analysis' not in inspector.get_table_names():
            print("Error: Tabla match_context_analysis no existe")
            return pd.DataFrame()
        
        # Construir query con filtros opcionales
        query = """
        SELECT 
            match_id,
            season_id,
            season_name,
            competition_id,
            competition_name,
            match_date,
            match_day_number,
            depor_team_name_matches,
            depor_team_name_teams,
            opponent_name,
            condicion,
            goles_favor,
            goles_contra,
            resultado,
            resultado_tipo,
            pct_ganando,
            pct_empatando,
            pct_perdiendo,
            contexto_preferente,
            contexto_tipo,
            etiqueta_contexto,
            interpretacion,
            process_date,
            last_updated
        FROM match_context_analysis
        WHERE depor_team_name_teams = %s
        """
        
        params = [team_name]
        
        if competition_id:
            query += " AND competition_id = %s"
            params.append(competition_id)
        
        if season_id:
            query += " AND season_id = %s"
            params.append(season_id)
        
        query += " ORDER BY match_date ASC, match_day_number ASC"
        
        df = pd.read_sql(query, engine, params=tuple(params))
        
        print(f"✅ Obtenidos {len(df)} partidos con análisis de contexto")
        return df
        
    except Exception as e:
        print(f"Error obteniendo análisis de contextos: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_matches_by_context_matrix(team_name="RC Deportivo", competition_id=None, season_id=None):
    """
    Obtiene los partidos organizados en una matriz 2x2 según resultado_tipo y contexto_tipo.
    
    Args:
        team_name (str): Nombre del equipo
        competition_id (str): ID de la competición (opcional)
        season_id (str): ID de la temporada (opcional)
    
    Returns:
        dict: Diccionario con estructura {
            'Positivo': {'Favorable': [...], 'Desfavorable': [...]},
            'Negativo': {'Favorable': [...], 'Desfavorable': [...]}
        }
    """
    try:
        df = get_match_context_analysis(team_name, competition_id, season_id)
        
        if df.empty:
            return {
                'Positivo': {'Favorable': [], 'Desfavorable': []},
                'Negativo': {'Favorable': [], 'Desfavorable': []}
            }
        
        # Organizar en matriz
        matrix = {
            'Positivo': {'Favorable': [], 'Desfavorable': []},
            'Negativo': {'Favorable': [], 'Desfavorable': []}
        }
        
        for _, row in df.iterrows():
            resultado_tipo = row['resultado_tipo']
            contexto_tipo = row['contexto_tipo']
            
            match_info = {
                'match_id': row['match_id'],
                'match_date': row['match_date'],
                'match_day_number': row['match_day_number'],
                'opponent_name': row['opponent_name'],
                'condicion': row['condicion'],
                'goles_favor': row['goles_favor'],
                'goles_contra': row['goles_contra'],
                'resultado': row['resultado'],
                'resultado_tipo': row['resultado_tipo'],
                'contexto_tipo': row['contexto_tipo'],
                'contexto_preferente': row['contexto_preferente'],
                'etiqueta_contexto': row['etiqueta_contexto'],
                'interpretacion': row['interpretacion'],
                'pct_ganando': row['pct_ganando'],
                'pct_empatando': row['pct_empatando'],
                'pct_perdiendo': row['pct_perdiendo']
            }
            
            matrix[resultado_tipo][contexto_tipo].append(match_info)
        
        return matrix
        
    except Exception as e:
        print(f"Error organizando matriz de contextos: {e}")
        import traceback
        traceback.print_exc()
        return {
            'Positivo': {'Favorable': [], 'Desfavorable': []},
            'Negativo': {'Favorable': [], 'Desfavorable': []}
        }


def get_context_statistics(team_name="RC Deportivo", competition_id=None, season_id=None):
    """
    Obtiene estadísticas agregadas de los contextos de partidos.
    
    Args:
        team_name (str): Nombre del equipo
        competition_id (str): ID de la competición (opcional)
        season_id (str): ID de la temporada (opcional)
    
    Returns:
        dict: Estadísticas de distribución de partidos por contexto
    """
    try:
        df = get_match_context_analysis(team_name, competition_id, season_id)
        
        if df.empty:
            return {}
        
        stats = {
            'total_partidos': len(df),
            'por_resultado_tipo': df['resultado_tipo'].value_counts().to_dict(),
            'por_contexto_tipo': df['contexto_tipo'].value_counts().to_dict(),
            'por_contexto_preferente': df['contexto_preferente'].value_counts().to_dict(),
            'por_condicion': df['condicion'].value_counts().to_dict(),
            'matriz_resultado_contexto': df.groupby(['resultado_tipo', 'contexto_tipo']).size().to_dict()
        }
        
        return stats
        
    except Exception as e:
        print(f"Error calculando estadísticas de contexto: {e}")
        return {}


def get_league_standings(competition_id=None, season_id=None, team_name="RC Deportivo"):
    """
    Obtiene la clasificación de la liga con opción de vista resumida centrada en un equipo.
    
    Args:
        competition_id (str): ID de la competición (opcional)
        season_id (str): ID de la temporada (opcional)
        team_name (str): Nombre del equipo para centrar la vista
    
    Returns:
        dict: {
            'full_standings': DataFrame con toda la clasificación,
            'team_position': posición del equipo,
            'context_standings': DataFrame con 5 arriba y 5 abajo del equipo
        }
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            print("Error: No se pudo conectar a la BD LaLiga")
            return {}
        
        # Query base
        query = """
        SELECT 
            competition_id, competition_name, season_id, season_name,
            team_id, team_name,
            position, position_previous, position_change,
            matches_played, matches_won, matches_drawn, matches_lost, points,
            matches_played_home, matches_won_home, matches_drawn_home, matches_lost_home, points_home,
            matches_played_away, matches_won_away, matches_drawn_away, matches_lost_away, points_away,
            goals_for, goals_against, goal_difference,
            goals_for_home, goals_against_home, goal_difference_home,
            goals_for_away, goals_against_away, goal_difference_away,
            avg_goals_for, avg_goals_against, avg_points,
            current_streak, current_streak_count, unbeaten_streak, winless_streak,
            clean_sheets, failed_to_score,
            last_5_matches, last_5_points,
            biggest_win, biggest_win_margin, biggest_loss, biggest_loss_margin,
            last_match_date, last_match_result, last_updated
        FROM league_standings
        WHERE 1=1
        """
        
        params = []
        
        if competition_id:
            query += " AND competition_id = %s"
            params.append(competition_id)
        
        if season_id:
            query += " AND season_id = %s"
            params.append(season_id)
        
        query += " ORDER BY position ASC"
        
        df = pd.read_sql(query, engine, params=tuple(params) if params else None)
        
        if df.empty:
            return {}
        
        # Encontrar posición del equipo
        team_row = df[df['team_name'] == team_name]
        
        if team_row.empty:
            # Si no se encuentra el equipo, devolver toda la tabla
            return {
                'full_standings': df,
                'team_position': None,
                'context_standings': df.head(11)  # Primeros 11 equipos
            }
        
        team_position = int(team_row.iloc[0]['position'])
        
        # Crear vista de contexto: 5 arriba y 5 abajo
        start_pos = max(1, team_position - 5)
        end_pos = min(len(df), team_position + 5)
        
        context_df = df[(df['position'] >= start_pos) & (df['position'] <= end_pos)]
        
        print(f"✅ Clasificación obtenida: {len(df)} equipos, {team_name} en posición {team_position}")
        
        return {
            'full_standings': df,
            'team_position': team_position,
            'context_standings': context_df
        }
        
    except Exception as e:
        print(f"Error obteniendo clasificación: {e}")
        import traceback
        traceback.print_exc()
        return {}


def get_match_reports_links(match_id):
    """
    Obtiene los links de informes (postpartido y evolutivo) de un partido.
    
    Args:
        match_id (int): ID del partido
    
    Returns:
        dict: {'postpartido_link': str, 'evolutivo_link': str}
    """
    try:
        engine = get_laliga_db_connection()
        if engine is None:
            return {}
        
        query = """
        SELECT match_id, postpartido_link, evolutivo_link
        FROM laliga_matches
        WHERE match_id = %s
        """
        
        df = pd.read_sql(query, engine, params=(match_id,))
        
        if df.empty:
            return {'postpartido_link': None, 'evolutivo_link': None}
        
        return {
            'postpartido_link': df.iloc[0]['postpartido_link'],
            'evolutivo_link': df.iloc[0]['evolutivo_link']
        }
        
    except Exception as e:
        print(f"Error obteniendo links de informes: {e}")
        return {'postpartido_link': None, 'evolutivo_link': None}


def get_results_trend_statistics(team_name="RC Deportivo", competition_id=None, season_id=None, last_n=None):
    """
    Obtiene estadísticas de tendencia de resultados para visualizaciones.
    
    Args:
        team_name (str): Nombre del equipo
        competition_id (str): ID de la competición (opcional)
        season_id (str): ID de la temporada (opcional)
        last_n (int): Número de últimos partidos a considerar (None = todos)
    
    Returns:
        dict: Estadísticas completas de tendencia
    """
    try:
        df = get_match_context_analysis(team_name, competition_id, season_id)
        
        if df.empty:
            return {}
        
        # Ordenar por fecha
        df = df.sort_values('match_date', ascending=True)
        
        # Limitar a últimos N partidos si se especifica
        if last_n:
            df = df.tail(last_n)
        
        # Calcular puntos (Victoria=3, Empate=1, Derrota=0)
        df['puntos'] = df['resultado'].map({'Victoria': 3, 'Empate': 1, 'Derrota': 0})
        
        # Estadísticas por resultado
        resultado_counts = df['resultado'].value_counts().to_dict()
        
        # Estadísticas por condición
        condicion_stats = {}
        for condicion in ['Local', 'Visitante']:
            df_cond = df[df['condicion'] == condicion]
            if not df_cond.empty:
                condicion_stats[condicion] = {
                    'total': len(df_cond),
                    'victorias': len(df_cond[df_cond['resultado'] == 'Victoria']),
                    'empates': len(df_cond[df_cond['resultado'] == 'Empate']),
                    'derrotas': len(df_cond[df_cond['resultado'] == 'Derrota']),
                    'puntos': df_cond['puntos'].sum(),
                    'goles_favor': df_cond['goles_favor'].sum(),
                    'goles_contra': df_cond['goles_contra'].sum()
                }
        
        # Racha actual
        racha_actual = []
        for _, row in df.tail(5).iterrows():
            if row['resultado'] == 'Victoria':
                racha_actual.append('V')
            elif row['resultado'] == 'Empate':
                racha_actual.append('E')
            else:
                racha_actual.append('D')
        
        # Últimos partidos para timeline
        ultimos_partidos = []
        for _, row in df.tail(10).iterrows():
            ultimos_partidos.append({
                'match_id': row['match_id'],
                'match_date': row['match_date'],
                'match_day_number': row['match_day_number'],
                'opponent_name': row['opponent_name'],
                'condicion': row['condicion'],
                'goles_favor': row['goles_favor'],
                'goles_contra': row['goles_contra'],
                'resultado': row['resultado'],
                'resultado_tipo': row['resultado_tipo'],
                'contexto_tipo': row['contexto_tipo'],
                'puntos': row['puntos']
            })
        
        stats = {
            'total_partidos': len(df),
            'puntos_totales': df['puntos'].sum(),
            'goles_favor': df['goles_favor'].sum(),
            'goles_contra': df['goles_contra'].sum(),
            'diferencia_goles': df['goles_favor'].sum() - df['goles_contra'].sum(),
            'victorias': resultado_counts.get('Victoria', 0),
            'empates': resultado_counts.get('Empate', 0),
            'derrotas': resultado_counts.get('Derrota', 0),
            'por_condicion': condicion_stats,
            'racha_actual': racha_actual,
            'ultimos_partidos': ultimos_partidos,
            'puntos_ultimos_5': df.tail(5)['puntos'].sum() if len(df) >= 5 else df['puntos'].sum(),
            'resultado_tipo_counts': df['resultado_tipo'].value_counts().to_dict(),
            'contexto_tipo_counts': df['contexto_tipo'].value_counts().to_dict()
        }
        
        return stats
        
    except Exception as e:
        print(f"Error calculando estadísticas de tendencia: {e}")
        import traceback
        traceback.print_exc()
        return {}

# --------------------------------------
# FUNCIONES PARA MICROCICLOS
# --------------------------------------
def get_microciclos():
    """
    Obtiene todos los microciclos estructurados por partidos MD.
    Un microciclo es el periodo entre un MD y el siguiente MD (o hasta hoy si es la semana actual).
    
    Returns:
        Lista de diccionarios con:
        - id: identificador único del microciclo
        - label: etiqueta para mostrar "Semana + nombre_partido (fecha_inicio - fecha_fin)"
        - start_date: fecha de inicio del microciclo (formato YYYY-MM-DD)
        - end_date: fecha de fin del microciclo (formato YYYY-MM-DD)
        - partido_nombre: nombre del partido que cierra el microciclo
        - is_current: True si es la semana actual (sin MD de cierre)
    """
    from datetime import datetime, timedelta
    import json
    
    try:
        engine = get_db_connection()
        if engine is None:
            return []
        
        # Calcular timestamp de hace 6 meses para limitar la búsqueda
        hace_6_meses = int((datetime.now() - timedelta(days=180)).timestamp())
        
        # Obtener solo actividades de los últimos 6 meses (OPTIMIZACIÓN)
        query = f'''
            SELECT id, start_time, name, tag_list_json
            FROM activities
            WHERE start_time >= {hace_6_meses}
            ORDER BY start_time ASC
        '''
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return []
        
        # Añadir columna grupo_dia para identificar MDs
        df = add_grupo_dia_column(df)
        
        # Filtrar solo actividades MD (partidos)
        df_md = df[df['grupo_dia'] == 'MD'].copy()
        
        if df_md.empty:
            return []
        
        microciclos = []
        
        # Procesar cada partido MD como el objetivo del microciclo (preparación hacia ese partido)
        # El microciclo INCLUYE el MD anterior (que lo inicia) pero NO incluye el MD del título
        for idx, row in df_md.iterrows():
            md_timestamp = row['start_time']
            md_date = datetime.fromtimestamp(md_timestamp)
            partido_nombre = row['name'] if pd.notna(row['name']) else f"Partido {md_date.strftime('%d/%m/%Y')}"
            
            # Encontrar la fecha de inicio del microciclo (INCLUIR el MD anterior)
            if idx > 0:
                # Buscar el índice del MD anterior
                md_prev_idx = df_md.index[df_md.index < idx].max() if len(df_md.index[df_md.index < idx]) > 0 else None
                
                if md_prev_idx is not None:
                    # INCLUIR el MD anterior (ese partido inicia el microciclo)
                    prev_md_timestamp = df_md.loc[md_prev_idx, 'start_time']
                    start_timestamp = prev_md_timestamp
                else:
                    # Primer microciclo: tomar todas las actividades ANTES del primer MD
                    df_antes_md = df[df['start_time'] < md_timestamp]
                    if not df_antes_md.empty:
                        start_timestamp = df_antes_md['start_time'].min()
                    else:
                        start_timestamp = md_timestamp - 604800  # -7 días por defecto
            else:
                # Primer MD: buscar actividades previas (sin incluir el MD)
                df_antes_md = df[df['start_time'] < md_timestamp]
                if not df_antes_md.empty:
                    start_timestamp = df_antes_md['start_time'].min()
                else:
                    start_timestamp = md_timestamp - 604800  # -7 días por defecto
            
            # La fecha de fin es ANTES del MD actual (el microciclo NO incluye el partido)
            # Buscar la última actividad antes del MD
            df_antes_este_md = df[df['start_time'] < md_timestamp]
            if not df_antes_este_md.empty:
                end_timestamp = df_antes_este_md['start_time'].max()
                end_date = datetime.fromtimestamp(end_timestamp)
                # Para queries, usar el día del MD (sin incluir el MD mismo, solo hasta las 23:59 del día anterior)
                end_date_for_query = datetime.fromtimestamp(md_timestamp - 1)  # 1 segundo antes del MD
            else:
                # Si no hay actividades antes, usar el día anterior al MD
                end_date = datetime.fromtimestamp(md_timestamp - 86400)
                end_date_for_query = datetime.fromtimestamp(md_timestamp - 1)
            
            start_date = datetime.fromtimestamp(start_timestamp)
            
            microciclo = {
                'id': f'mc_{idx}',
                'label': f"Semana {partido_nombre} ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})",
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date_for_query.strftime('%Y-%m-%d %H:%M:%S'),  # Timestamp exacto para excluir el MD
                'partido_nombre': partido_nombre,
                'is_current': False
            }
            
            microciclos.append(microciclo)
        
        # Añadir "Semana actual" (desde el último MD incluido hasta hoy)
        if not df_md.empty:
            ultimo_md_timestamp = df_md['start_time'].max()
            
            # La semana actual INCLUYE el último MD (que la inicia)
            start_timestamp = ultimo_md_timestamp
            start_date = datetime.fromtimestamp(start_timestamp)
            end_date = datetime.now()
            
            microciclo_actual = {
                'id': 'mc_actual',
                'label': f"Semana Actual ({start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')})",
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S'),
                'partido_nombre': 'Semana Actual',
                'is_current': True
            }
            
            microciclos.append(microciclo_actual)
        
        # Invertir para que el más reciente esté primero
        microciclos.reverse()
        
        return microciclos
        
    except Exception as e:
        print(f"Error obteniendo microciclos: {e}")
        import traceback
        traceback.print_exc()
        return []

