# utils/carga_jugadores.py
"""
Funciones para análisis de cargas máximas en partidos (MD) por jugador
"""

import pandas as pd
import json
from datetime import datetime
from utils.db_manager import get_db_connection, get_all_athletes

def calcular_estadisticas_md_jugadores(inicio_temporada='2025-08-15'):
    """
    Calcula estadísticas de carga máxima para cada jugador en actividades MD desde inicio de temporada.
    Solo considera partidos donde el jugador jugó más de 70 minutos (4200 segundos).
    Los valores se estandarizan a 94 minutos (5640 segundos).
    
    Args:
        inicio_temporada (str): Fecha de inicio en formato 'YYYY-MM-DD'
    
    Returns:
        DataFrame con columnas: jugador_id, jugador_nombre, metrica, num_partidos_70min, 
                               media_estandarizada, maximo_estandarizado, media_3_maximos, media_5_maximos
    """
    
    # Métricas a analizar
    metricas_estandarizables = [
        'total_distance',
        'distancia_+21_km/h_(m)',
        'distancia_+24_km/h_(m)',
        'distancia+28_(km/h)',
        'gen2_acceleration_band7plus_total_effort_count',
        'average_player_load'
    ]
    
    metricas_no_estandarizables = [
        'max_vel'  # La velocidad máxima es un valor puntual, no se estandariza
    ]
    
    todas_metricas = metricas_estandarizables + metricas_no_estandarizables
    
    # Constantes
    MIN_FIELD_TIME = 4200  # 70 minutos en segundos
    STANDARIZATION_TIME = 5640  # 94 minutos en segundos
    
    try:
        print(f"DEBUG: Iniciando cálculo de estadísticas MD desde {inicio_temporada}")
        engine = get_db_connection()
        if engine is None:
            print("ERROR: No se pudo conectar a la base de datos")
            return pd.DataFrame()
        
        # Convertir fecha de inicio a timestamp
        inicio_ts = int(datetime.strptime(inicio_temporada, '%Y-%m-%d').timestamp())
        print(f"DEBUG: Timestamp de inicio: {inicio_ts}")
        
        # Obtener actividades MD desde inicio de temporada
        # Usar una búsqueda más simple para evitar problemas con comillas en LIKE
        query_actividades = '''
            SELECT id, start_time, name, tag_list_json
            FROM activities
            WHERE start_time >= %s
            ORDER BY start_time ASC
        '''
        df_actividades = pd.read_sql(query_actividades, engine, params=(inicio_ts,))
        
        # Filtrar actividades MD usando Python en lugar de SQL
        def es_md(tag_json_str):
            try:
                if pd.isna(tag_json_str):
                    return False
                tags = json.loads(tag_json_str)
                for tag in tags:
                    if tag.get('name') == 'MD':
                        return True
                return False
            except:
                return False
        
        df_actividades['es_md'] = df_actividades['tag_list_json'].apply(es_md)
        df_actividades = df_actividades[df_actividades['es_md']].copy()
        df_actividades = df_actividades[['id', 'start_time', 'name']]  # Solo columnas necesarias
        
        print(f"DEBUG: Actividades MD encontradas: {len(df_actividades)}")
        
        if df_actividades.empty:
            print("WARNING: No se encontraron actividades MD")
            return pd.DataFrame()
        
        activity_ids = df_actividades['id'].tolist()
        
        # Obtener todas las métricas en una sola consulta
        resultados = []
        
        # Primero obtener field_time para todos los partidos y jugadores
        print("DEBUG: Obteniendo field_time para filtrar partidos...")
        ids_str = ','.join([f"'{id}'" for id in activity_ids])
        query_field_time = f'''
            SELECT 
                activity_id,
                athlete_id,
                CAST(parameter_value AS DECIMAL(10,2)) as field_time
            FROM activity_athlete_metrics
            WHERE parameter_name = 'field_time'
            AND activity_id IN ({ids_str})
            AND parameter_value IS NOT NULL
            AND parameter_value != ''
        '''
        df_field_time = pd.read_sql(query_field_time, engine)
        
        # Filtrar solo partidos con más de 70 minutos
        df_field_time_filtered = df_field_time[df_field_time['field_time'] >= MIN_FIELD_TIME].copy()
        print(f"DEBUG: {len(df_field_time_filtered)} registros con field_time >= 70 mins de {len(df_field_time)} totales")
        
        for metrica in todas_metricas:
            # Construir consulta con IDs entrecomillados (son UUIDs/strings)
            query_metricas = f'''
                SELECT 
                    aam.activity_id,
                    aam.athlete_id,
                    CAST(aam.parameter_value AS DECIMAL(10,2)) as valor
                FROM activity_athlete_metrics aam
                WHERE aam.parameter_name = '{metrica}'
                AND aam.activity_id IN ({ids_str})
                AND aam.parameter_value IS NOT NULL
                AND aam.parameter_value != ''
            '''
            
            print(f"DEBUG: Procesando métrica {metrica}...")
            df_metrica = pd.read_sql(query_metricas, engine)
            
            if df_metrica.empty:
                continue
            
            # Merge con field_time
            df_metrica = df_metrica.merge(
                df_field_time_filtered[['activity_id', 'athlete_id', 'field_time']],
                on=['activity_id', 'athlete_id'],
                how='inner'  # Solo mantener registros con field_time >= 70 mins
            )
            
            print(f"DEBUG: {len(df_metrica)} registros con +70 mins para {metrica}")
            
            if df_metrica.empty:
                continue
            
            # Estandarizar valores a 94 minutos (solo para métricas acumulativas)
            if metrica in metricas_estandarizables:
                df_metrica['valor_estandarizado'] = df_metrica['valor'] * (STANDARIZATION_TIME / df_metrica['field_time'])
            else:
                # Para métricas no estandarizables (como max_vel), usar el valor real
                df_metrica['valor_estandarizado'] = df_metrica['valor']
            
            # Merge con información de actividades
            df_metrica = df_metrica.merge(
                df_actividades[['id', 'name', 'start_time']], 
                left_on='activity_id', 
                right_on='id',
                how='left'
            )
            
            # Agrupar por jugador
            for athlete_id in df_metrica['athlete_id'].unique():
                df_jugador = df_metrica[df_metrica['athlete_id'] == athlete_id].copy()
                
                # Ordenar por valor estandarizado descendente
                df_jugador = df_jugador.sort_values('valor_estandarizado', ascending=False)
                
                num_partidos = len(df_jugador)
                
                # Si no hay partidos con +70 mins, advertir
                if num_partidos == 0:
                    print(f"WARNING: Jugador {athlete_id} no tiene partidos con +70 mins para {metrica}")
                    continue
                
                # Calcular estadísticas con valores estandarizados
                media_estandarizada = df_jugador['valor_estandarizado'].mean()
                maximo_estandarizado = df_jugador['valor_estandarizado'].max()
                
                # Media de los 3 y 5 máximos
                top_3 = df_jugador.head(3)
                media_3_maximos = top_3['valor_estandarizado'].mean()
                
                top_5 = df_jugador.head(5)
                media_5_maximos = top_5['valor_estandarizado'].mean()
                
                # Información de los partidos con los máximos (top 5)
                partidos_info = []
                for _, row in top_5.iterrows():
                    fecha = datetime.fromtimestamp(row['start_time']).strftime('%d/%m/%Y')
                    mins_jugados = int(row['field_time'] / 60)
                    
                    # Indicar si el valor está estandarizado o no
                    es_estandarizado = metrica in metricas_estandarizables
                    
                    partidos_info.append({
                        'fecha': fecha,
                        'partido': row['name'] if pd.notna(row['name']) else 'Partido',
                        'valor': row['valor_estandarizado'],
                        'valor_real': row['valor'],
                        'minutos': mins_jugados,
                        'estandarizado': es_estandarizado
                    })
                
                resultados.append({
                    'athlete_id': athlete_id,
                    'metrica': metrica,
                    'num_partidos_70min': num_partidos,
                    'media_estandarizada': round(media_estandarizada, 2),
                    'maximo_estandarizado': round(maximo_estandarizado, 2),
                    'media_3_maximos': round(media_3_maximos, 2),
                    'media_5_maximos': round(media_5_maximos, 2),
                    'partidos_maximos': partidos_info
                })
        
        df_resultado = pd.DataFrame(resultados)
        
        # Añadir nombres de jugadores
        if not df_resultado.empty:
            atletas = get_all_athletes()
            df_resultado = df_resultado.merge(
                atletas[['id', 'full_name', 'position_name']],
                left_on='athlete_id',
                right_on='id',
                how='left'
            )
            df_resultado = df_resultado.rename(columns={'full_name': 'jugador_nombre', 'position_name': 'posicion'})
        
        print(f"DEBUG: Resultados finales: {len(df_resultado)} filas, {df_resultado['jugador_nombre'].nunique()} jugadores únicos")
        return df_resultado
        
    except Exception as e:
        print(f"Error calculando estadísticas MD: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
