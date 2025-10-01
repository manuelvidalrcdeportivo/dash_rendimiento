# utils/db_manager.py

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv
import sys

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
        SELECT id, first_name, last_name 
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
        DataFrame con actividades filtradas
    """
    try:
        engine = get_db_connection()
        if engine is None:
            return pd.DataFrame()
        query = '''
            SELECT * FROM activities
            WHERE start_time >= %s AND start_time <= %s
            ORDER BY start_time ASC
        '''
        df = pd.read_sql(query, engine, params=(start_timestamp, end_timestamp))
        return df
    except Exception as e:
        
        return pd.DataFrame()

def get_participants_for_activities(activity_ids):
    """
    Devuelve los jugadores participantes en una lista de actividades.
    Args:
        activity_ids (list): lista de activity_id
    Returns:
        DataFrame con columnas: activity_id, athlete_id
    """
    try:
        engine = get_db_connection()
        if engine is None or not activity_ids:
            return pd.DataFrame(columns=["activity_id", "athlete_id"])
        query = '''
            SELECT activity_id, athlete_id FROM activity_athletes
            WHERE activity_id IN %s
        '''
        df = pd.read_sql(query, engine, params=(tuple(activity_ids),))
        return df
    except Exception as e:
        
        return pd.DataFrame(columns=["activity_id", "athlete_id"])

def add_grupo_dia_column(actividades_df):
    """
    Añade una columna 'grupo_dia' al DataFrame de actividades, SOLO usando los tags de tipo 'DayCode' (tag_type_id == '09bdd0ac-3477-11ef-8148-06e64249fcaf').
    Ignora los demás tag_type_id (GPS, Injected, etc).
    Normaliza las etiquetas 'Game -X' a 'MD-X' para unificar nomenclatura.
    """
    import json
    import re
    DAYCODE_TAG_TYPE_ID = '09bdd0ac-3477-11ef-8148-06e64249fcaf'
    try:
        engine = get_db_connection()
        if engine is None or actividades_df.empty or 'tag_list_json' not in actividades_df.columns:
            actividades_df['grupo_dia'] = 'Sin clasificar'
            return actividades_df
        # Obtener todos los nombres de días de referencia para DayCode desde activity_tags
        tags_df = pd.read_sql(f"SELECT DISTINCT name FROM activity_tags WHERE tag_type_id = '{DAYCODE_TAG_TYPE_ID}'", engine)
        dias_ref = set(tags_df['name'].dropna().tolist())
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
        query = '''
            SELECT activity_id, athlete_id, parameter_value
            FROM activity_athlete_metrics
            WHERE activity_id IN %s AND athlete_id IN %s AND parameter_name = %s
        '''
        df = pd.read_sql(query, engine, params=(tuple(activity_ids), tuple(athlete_ids), parameter_name))
        return df
    except Exception as e:
        
        return pd.DataFrame(columns=["activity_id", "athlete_id", "parameter_value"])

# Función para obtener los parámetros disponibles (aunque por ahora solo es total_distance)
def get_available_parameters():
    """
    Devuelve la lista de parámetros disponibles para seleccionar.
    Incluye distancia total y otras métricas de rendimiento.
    
    Returns:
        Lista de parámetros disponibles con su valor interno y etiqueta para mostrar.
    """
    return [
        {'value': 'total_distance', 'label': 'Distancia Media Sesión (m)'},
        {'value': 'velocity_band6_total_distance', 'label': 'Velocity Band 6 Distance (Session) (m)'},
        {'value': 'high_speed_distance', 'label': 'HSR Distance (m)'},
        {'value': 'average_player_load', 'label': 'Average Player Load'}
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
            'velocity_band6_total_distance': 'Velocity Band Band 6 Distance (Session) (m)',
            'high_speed_distance': 'HSR Distance (m)',
            'average_player_load': 'Average Player Load'
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
        
        # Consulta para obtener solo los rankings compuestos
        query = """
        SELECT 
            metric_id,
            ranking_position
        FROM indicadores_rendimiento 
        WHERE team_name = %s 
        AND metric_category IN ('RANKINGS COMPUESTOS', 'RANKING GLOBAL')
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
