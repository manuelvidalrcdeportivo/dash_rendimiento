"""
ULTRA-OPTIMIZACIÓN: Solo 2 queries SQL masivas para cargar TODO el microciclo.

ESTRATEGIA:
1. Query 1: TODO el microciclo (todas las métricas juntas)
2. Query 2: Últimos 4 MDs (todas las métricas juntas)
3. Procesamiento en memoria con pandas (super rápido)
"""

import pandas as pd
import re
from utils.db_manager import get_db_connection


def cargar_microciclo_ultrarapido_v2(microciclo_id, jugadores_ids):
    """
    SOLO 2 QUERIES MASIVAS - La forma más rápida posible.
    
    Returns:
        dict con todos los datos procesados
    """
    # Cargando microciclo con 2 queries masivas
    
    engine = get_db_connection()
    if not engine:
        return None
    
    # Formatear IDs con comillas
    jugadores_ids_quoted = ','.join([f"'{j}'" for j in jugadores_ids])
    
    # ========================================
    # QUERY 1: TODO EL MICROCICLO (todas las métricas en UNA query)
    # ========================================
    # Query 1: Cargando TODO el microciclo
    
    query_microciclo = f'''
        SELECT 
            activity_tag,
            athlete_id,
            athlete_name,
            athlete_position,
            participation_type,
            activity_date,
            field_time,
            total_distance,
            distancia_21_kmh,
            distancia_24_kmh,
            acc_dec_total,
            ritmo_medio,
            distance_per_minute,
            activity_name
        FROM microciclos_metricas_procesadas
        WHERE microciclo_id = '{microciclo_id}'
          AND athlete_position != 'Goal Keeper'
    '''
    
    df_microciclo = pd.read_sql(query_microciclo, engine)
    # Datos cargados correctamente
    
    if df_microciclo.empty:
        return None
    
    # Obtener fecha del MD para máximos históricos
    # LÓGICA SIMPLE: Hay 1 MD por microciclo (por estructura de datos)
    # Buscar por TAG, tomar el primero cronológicamente
    # IGNORAR nombres de partidos (solo para hover)
    
    df_md = df_microciclo[df_microciclo['activity_tag'] == 'MD']
    
    if df_md.empty:
        # No hay MD en este microciclo
        fecha_md = None
    else:
        fecha_md = df_md['activity_date'].min()  # Primer MD cronológicamente
        # MD encontrado
    
    # Extraer año/temporada del microciclo_id para filtrar solo partidos de la misma temporada
    # Formato: mc_2025-10-26_J11_RCD_Vs_R_VALLADOLID
    temporada_actual = None
    match_temporada = re.search(r'mc_(\d{4})-', microciclo_id)
    if match_temporada:
        temporada_actual = int(match_temporada.group(1))
        # Temporada detectada
    elif fecha_md is not None:
        # Si no se puede extraer del microciclo_id (ej: mc_actual), usar año del MD
        temporada_actual = pd.to_datetime(fecha_md).year
        # Temporada detectada del MD
    else:
        # Fallback: usar año actual
        from datetime import datetime
        temporada_actual = datetime.now().year
        # Usando temporada actual
    
    # ========================================
    # QUERY 2: ÚLTIMOS 4 MDs (todas las métricas en UNA query)
    # ========================================
    # Query 2: Cargando últimos 4 MDs
    
    # Buscar máximos históricos: MD actual + hasta 3 anteriores (máximo 4 total)
    # IMPORTANTE: Considerar fecha de inicio de temporada y límite real de partidos
    if temporada_actual and fecha_md is not None:
        # Fecha de inicio de temporada (ajustar según sea necesario)
        fecha_inicio_temporada = f"{temporada_actual}-08-10"
        
        # INCLUIR el MD actual (<=) + anteriores desde inicio de temporada
        condicion_fecha = f"AND activity_date <= '{fecha_md}' AND activity_date >= '{fecha_inicio_temporada}'"
        msg_fecha = f"hasta {fecha_md} (desde inicio temporada {fecha_inicio_temporada})"
        
        query_historicos = f'''
            SELECT 
                activity_date,
                MAX(activity_name) as activity_name,
                MAX(microciclo_id) as microciclo_id,
                AVG(CASE 
                    WHEN field_time >= 4200 
                    THEN total_distance * (5640.0 / field_time) 
                    ELSE NULL 
                END) as avg_total_distance,
                AVG(CASE 
                    WHEN field_time >= 4200 
                    THEN distancia_21_kmh * (5640.0 / field_time) 
                    ELSE NULL 
                END) as avg_distancia_21,
                AVG(CASE 
                    WHEN field_time >= 4200 
                    THEN distancia_24_kmh * (5640.0 / field_time) 
                    ELSE NULL 
                END) as avg_distancia_24,
                AVG(CASE 
                    WHEN field_time >= 4200 
                    THEN acc_dec_total * (5640.0 / field_time) 
                    ELSE NULL 
                END) as avg_acc_dec,
                AVG(CASE 
                    WHEN field_time >= 4200 
                    THEN distance_per_minute
                    ELSE NULL 
                END) as avg_ritmo_medio
            FROM microciclos_metricas_procesadas
            WHERE activity_tag = 'MD'
              {condicion_fecha}
              AND YEAR(activity_date) = {temporada_actual if temporada_actual else 'YEAR(CURDATE())'}
              AND athlete_position != 'Goal Keeper'
              AND field_time >= 4200
              AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
            GROUP BY activity_date
            ORDER BY activity_date DESC
            LIMIT 4
        '''
        
        df_historicos = pd.read_sql(query_historicos, engine)
        # Máximos históricos cargados
        
        # VALIDACIÓN: Verificar cuántos partidos realmente tenemos
        num_partidos_disponibles = len(df_historicos)
        if num_partidos_disponibles < 4:
            # Ajustar mensaje para reflejar la realidad
            if num_partidos_disponibles == 1:
                msg_partidos = f"Solo {num_partidos_disponibles} partido disponible desde inicio de temporada"
            else:
                msg_partidos = f"Solo {num_partidos_disponibles} partidos disponibles desde inicio de temporada"
        else:
            msg_partidos = f"{num_partidos_disponibles} partidos (ventana completa)"
        
        # Calcular max/min por métrica y obtener el partido del máximo
        maximos_historicos = {}
        if not df_historicos.empty:
            for col in ['avg_total_distance', 'avg_distancia_21', 'avg_distancia_24', 'avg_acc_dec', 'avg_ritmo_medio']:
                col_data = df_historicos[[col, 'activity_date', 'activity_name', 'microciclo_id']].dropna(subset=[col])
                if len(col_data) > 0:
                    # Mapear nombres de columna a nombres de métrica
                    metric_map = {
                        'avg_total_distance': 'total_distance',
                        'avg_distancia_21': 'distancia_21_kmh',
                        'avg_distancia_24': 'distancia_24_kmh',
                        'avg_acc_dec': 'acc_dec_total',
                        'avg_ritmo_medio': 'ritmo_medio'
                    }
                    metric_name = metric_map[col]
                    
                    # Obtener valor máximo y su fecha
                    idx_max = col_data[col].idxmax()
                    max_val = col_data.loc[idx_max, col]
                    fecha_max = col_data.loc[idx_max, 'activity_date']
                    
                    # Procesando métrica
                    
                    # Obtener nombre del partido directamente del DataFrame
                    partido_max = None
                    if pd.notna(col_data.loc[idx_max, 'activity_name']):
                        partido_max = col_data.loc[idx_max, 'activity_name']
                    elif pd.notna(col_data.loc[idx_max, 'microciclo_id']):
                        # Extraer del microciclo_id si no hay activity_name
                        mc_id = col_data.loc[idx_max, 'microciclo_id']
                        match = re.search(r'_([^_]+_Vs_[^_]+)$', mc_id)
                        if match:
                            partido_max = match.group(1).replace('_', ' ')
                    
                    maximos_historicos[metric_name] = {
                        'max': max_val,
                        'min': col_data[col].min(),
                        'partido_max': partido_max,
                        'fecha_max': fecha_max
                    }
                    # Máximo calculado
        
        # Máximos calculados
    else:
        maximos_historicos = {}
        # Sin máximos históricos
    
    # ========================================
    # PROCESAMIENTO EN MEMORIA (pandas super rápido)
    # ========================================
    # Procesando datos en memoria
    
    # Mapeo de columnas SQL a nombres de métrica del dashboard
    columnas_metricas = {
        'total_distance': 'total_distance',
        'distancia_21_kmh': 'distancia_21_kmh',
        'distancia_24_kmh': 'distancia_24_kmh',
        'acc_dec_total': 'acc_dec_total',
        'ritmo_medio': 'ritmo_medio'
    }
    
    # Columnas disponibles
    
    # Obtener nombre del partido del MD real (desde activity_name)
    nombre_partido = None
    if 'MD' in df_microciclo['activity_tag'].values and 'activity_name' in df_microciclo.columns:
        # Obtener el activity_name del MD (partido real)
        df_md_name = df_microciclo[df_microciclo['activity_tag'] == 'MD']
        if not df_md_name.empty and pd.notna(df_md_name['activity_name'].iloc[0]):
            nombre_partido = df_md_name['activity_name'].iloc[0]
            # Nombre del partido obtenido
    
    # Procesar cada métrica
    datos_por_metrica = {}
    
    # Crear DataFrame filtrado para ENTRENAMIENTOS (solo jugadores seleccionados)
    # Filtrar Part/Rehab de TODOS los entrenamientos (MD-X y MD+X)
    df_entrenamientos = df_microciclo[
        (df_microciclo['activity_tag'] != 'MD') & 
        (df_microciclo['athlete_id'].isin(jugadores_ids))
    ].copy()
    
    # Entrenamientos antes de filtrar
    
    # Filtrar Part/Rehab de TODOS los entrenamientos (MD-X y MD+X)
    # Solo mantener participation_type Full (NULL o no Part/Rehab)
    df_entrenamientos_filtrado = df_entrenamientos[
        (df_entrenamientos['participation_type'].isna()) | 
        (~df_entrenamientos['participation_type'].isin(['Part', 'Rehab']))
    ].copy()
    
    # Entrenamientos filtrados
    
    # Reemplazar df_entrenamientos con la versión filtrada
    df_entrenamientos = df_entrenamientos_filtrado
    
    # DataFrame para MD (TODOS los jugadores, solo el primer MD cronológicamente)
    if fecha_md is not None:
        df_md_completo = df_microciclo[
            (df_microciclo['activity_tag'] == 'MD') & 
            (df_microciclo['activity_date'] == fecha_md)
        ].copy()
    else:
        df_md_completo = pd.DataFrame()
    
    # Jugadores procesados
    
    for col_name, metric_name in columnas_metricas.items():
        # Validar que la columna existe
        if col_name not in df_microciclo.columns:
            # Columna no encontrada
            continue
        
        # Agrupar ENTRENAMIENTOS (solo jugadores seleccionados)
        # Ya filtrados los compensatorios por participation_type = Full
        
        df_metrica_entrenos = df_entrenamientos.groupby('activity_tag').agg({
            col_name: 'mean',
            'athlete_id': 'count',
            'activity_date': 'min'
        }).reset_index()
        df_metrica_entrenos.columns = ['activity_tag', 'avg_metric', 'count_athletes', 'fecha']
        
        # Logging para MD+1 y MD+2 (compensatorios)
        if metric_name == 'total_distance':
            for tag in ['MD+1', 'MD+2']:
                df_tag = df_metrica_entrenos[df_metrica_entrenos['activity_tag'] == tag]
                if not df_tag.empty:
                    valor = df_tag['avg_metric'].values[0]
                    count = df_tag['count_athletes'].values[0]
                    # Valor calculado
        
        # Agrupar MD
        # Si es jugador individual, filtrar solo ese jugador. Si no, usar todos.
        es_jugador_individual = jugadores_ids and len(jugadores_ids) == 1
        
        if not df_md_completo.empty:
            # Si es jugador individual, usar solo sus datos
            if es_jugador_individual:
                df_md_para_procesar = df_md_completo[df_md_completo['athlete_id'] == jugadores_ids[0]]
            else:
                df_md_para_procesar = df_md_completo
            
            if not df_md_para_procesar.empty:
                df_metrica_md = df_md_para_procesar.groupby('activity_tag').agg({
                    col_name: 'mean',
                    'athlete_id': 'count',
                    'activity_date': 'min'
                }).reset_index()
                df_metrica_md.columns = ['activity_tag', 'avg_metric', 'count_athletes', 'fecha']
                
                # Combinar entrenamientos + MD
                df_metrica = pd.concat([df_metrica_entrenos, df_metrica_md], ignore_index=True)
            else:
                df_metrica = df_metrica_entrenos
        else:
            df_metrica = df_metrica_entrenos
        
        # Para métricas que requieren filtro +70 mins en MD
        if metric_name in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total', 'ritmo_medio'] and not df_md_completo.empty:
            # Filtrar jugadores con +70 mins en MD
            if es_jugador_individual:
                # Jugador individual: solo su MD
                df_md_filtrado = df_md_completo[
                    (df_md_completo['athlete_id'] == jugadores_ids[0]) & 
                    (df_md_completo['field_time'] >= 4200)
                ]
            else:
                # Equipo: todos los jugadores +70'
                df_md_filtrado = df_md_completo[df_md_completo['field_time'] >= 4200]
            
            if not df_md_filtrado.empty:
                # Estandarizar a 94 minutos SOLO para distancias y aceleraciones
                # Ritmo medio: usar distance_per_minute en MDs (NO estandarizar)
                if metric_name in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
                    valor_estandarizado = (df_md_filtrado[col_name] * (5640 / df_md_filtrado['field_time'])).mean()
                else:
                    # Para ritmo_medio: usar distance_per_minute en MDs, no estandarizar
                    valor_estandarizado = df_md_filtrado['distance_per_minute'].mean()
                
                count_filtrado = len(df_md_filtrado['athlete_id'].unique())
                
                # Añadir field_time si es jugador individual
                if es_jugador_individual and 'field_time' in df_md_filtrado.columns:
                    field_time_promedio = df_md_filtrado['field_time'].mean()
                    df_metrica.loc[df_metrica['activity_tag'] == 'MD', 'field_time'] = field_time_promedio
                
                # Actualizar valor del MD
                df_metrica.loc[df_metrica['activity_tag'] == 'MD', 'avg_metric'] = valor_estandarizado
                df_metrica.loc[df_metrica['activity_tag'] == 'MD', 'count_athletes'] = count_filtrado
                modo_txt = "INDIVIDUAL" if es_jugador_individual else "EQUIPO"
        
        datos_por_metrica[metric_name] = df_metrica
        # Métrica procesada
    
    # Métricas procesadas
    
    # Los umbrales ahora están hardcodeados en la función de generación de gráficos
    # para mejorar el rendimiento (sin queries adicionales)
    # Umbrales hardcodeados
    
    # Días presentes calculados
    
    return {
        'datos_por_metrica': datos_por_metrica,
        'maximos_historicos': maximos_historicos,
        'nombre_partido': nombre_partido,
        'df_raw': df_microciclo
    }


def calcular_maximo_individual_jugador(athlete_id, metric_name, fecha_referencia=None):
    """
    Calcula el máximo individual de un jugador en los últimos 4 MDs con +70 minutos.
    
    Args:
        athlete_id: ID del jugador
        metric_name: Nombre de la métrica (ej: 'total_distance')
        fecha_referencia: Fecha del partido actual (para buscar hacia atrás)
    
    Returns:
        dict con:
        - 'max': Valor máximo estandarizado a 94'
        - 'partido_max': Nombre del partido donde alcanzó el máximo
        - 'fecha_max': Fecha del partido máximo
        - 'tiene_datos': True si tiene al menos 1 MD +70'
        - 'ultimo_md_fecha': Fecha del último MD +70' (si no tiene 4)
        - 'warning': Mensaje de alerta si no tiene datos suficientes
    """
    # Cálculo silencioso de máximo individual
    
    engine = get_db_connection()
    if not engine:
        return {
            'max': None,
            'partido_max': None,
            'fecha_max': None,
            'tiene_datos': False,
            'ultimo_md_fecha': None,
            'warning': 'ERROR: No se pudo conectar a la base de datos'
        }
    
    # Mapeo de nombres de métricas a columnas de BD
    # Para ritmo_medio: usamos distance_per_minute en partidos (MD)
    columnas_metricas = {
        'total_distance': 'total_distance',
        'distancia_+21_km/h_(m)': 'distancia_21_kmh',
        'distancia_+24_km/h_(m)': 'distancia_24_kmh',
        'distancia+28_(km/h)': 'distancia_28_kmh',
        'gen2_acceleration_band7plus_total_effort_count': 'acc_dec_total',
        'average_player_load': 'distance_per_minute'  # Cambiado para usar distance_per_minute en MDs
    }
    
    col_name = columnas_metricas.get(metric_name, metric_name)
    
    # Determinar si esta métrica debe estandarizarse (NO para ritmo_medio/distance_per_minute)
    debe_estandarizar = metric_name not in ['average_player_load', 'ritmo_medio']
    
    # Query para obtener MÁXIMO ABSOLUTO desde inicio de temporada
    # Ya NO filtramos por fecha_referencia - usamos TODO el periodo
    query = f'''
        SELECT 
            activity_date,
            activity_name,
            field_time,
            {col_name} as metric_value
        FROM microciclos_metricas_procesadas
        WHERE athlete_id = '{athlete_id}'
          AND activity_tag = 'MD'
          AND field_time >= 4200
          AND activity_date >= '2025-08-10'
        ORDER BY activity_date DESC
    '''
    
    try:
        df = pd.read_sql(query, engine)
        
        if df.empty:
            # No tiene ningún MD con +70 minutos
            # FALLBACK: Buscar partido donde jugó más minutos (sin filtro +70')
            query_max_minutos = f'''
                SELECT 
                    activity_date,
                    activity_name,
                    field_time,
                    {col_name} as metric_value
                FROM microciclos_metricas_procesadas
                WHERE athlete_id = '{athlete_id}'
                  AND activity_tag = 'MD'
                  AND field_time > 0
                  AND activity_date >= '2025-08-10'
                ORDER BY field_time DESC
                LIMIT 1
            '''
            
            df_max_min = pd.read_sql(query_max_minutos, engine)
            
            if df_max_min.empty:
                # No tiene ningún MD registrado
                return {
                    'max': None,
                    'partido_max': None,
                    'fecha_max': None,
                    'tiene_datos': False,
                    'ultimo_md_fecha': None,
                    'warning': '🔴🔴 ALERTA: Ningún partido registrado en temporada',
                    'num_partidos': 0
                }
            else:
                # Usar el partido donde jugó más minutos y estandarizar (solo si la métrica lo requiere)
                field_time = df_max_min['field_time'].iloc[0]
                metric_value = df_max_min['metric_value'].iloc[0]
                if debe_estandarizar:
                    valor_std = metric_value * (5640 / field_time)
                else:
                    valor_std = metric_value
                partido = df_max_min['activity_name'].iloc[0]
                fecha = df_max_min['activity_date'].iloc[0]
                
                # Usando partido con más minutos
                
                return {
                    'max': valor_std,
                    'partido_max': partido,
                    'fecha_max': fecha,
                    'tiene_datos': True,
                    'ultimo_md_fecha': fecha,
                    'warning': f'🔴 ALERTA: Sin partidos +70\'. Referencia: {field_time/60:.0f}\' en {partido}',
                    'num_partidos': 1
                }
        
        # Tiene al menos 1 MD con +70 minutos
        
        # Estandarizar a 94 minutos (5640 segundos) solo si la métrica lo requiere
        if debe_estandarizar:
            df['metric_value_std'] = df['metric_value'] * (5640 / df['field_time'])
        else:
            df['metric_value_std'] = df['metric_value']
        
        # Obtener el MÁXIMO ABSOLUTO de todos los partidos
        idx_max = df['metric_value_std'].idxmax()
        max_value = df.loc[idx_max, 'metric_value_std']
        partido_max = df.loc[idx_max, 'activity_name']
        fecha_max = df.loc[idx_max, 'activity_date']
        
        # Info sobre cantidad de partidos considerados
        warning = None
        if len(df) == 1:
            warning = f'⚠️ Solo 1 partido +70\' disponible'
        elif len(df) < 4:
            warning = f'⚠️ {len(df)} partidos +70\' disponibles'
        
        return {
            'max': max_value,
            'partido_max': partido_max,
            'fecha_max': fecha_max,
            'tiene_datos': True,
            'ultimo_md_fecha': df['activity_date'].iloc[0],  # El más reciente
            'warning': warning,
            'num_partidos': len(df)
        }
        
    except Exception as e:
        # Error en cálculo de máximo
        return {
            'max': None,
            'partido_max': None,
            'fecha_max': None,
            'tiene_datos': False,
            'ultimo_md_fecha': None,
            'warning': f'ERROR: {str(e)}'
        }


def obtener_compensatorios_tabla(microciclos, jugadores_ids=None):
    """
    Obtiene los valores de compensatorio (MD+1 o MD+2) en distancia total para cada microciclo.
    USA EL MISMO CÁLCULO que el gráfico de visualización de carga (pandas groupby).
    
    Args:
        microciclos: Lista de diccionarios con microciclos
        jugadores_ids: Lista de IDs de jugadores a incluir (None = todos excepto porteros)
    
    Retorna dict: {microciclo_id: {'valor': float, 'porcentaje': float, 'color': str}}
    """
    engine = get_db_connection()
    compensatorios = {}
    
    # Cálculo de compensatorios
    
    # Query para obtener máximos históricos (IGUAL que tabla evolutiva para Distancia Total)
    # Normalizado a 94 mins para jugadores con +70 mins
    # IMPORTANTE: Filtrar desde inicio de temporada
    from datetime import datetime
    temporada_actual = datetime.now().year
    fecha_inicio_temporada = f"{temporada_actual}-08-10"
    
    query_maximos = f'''
        SELECT 
            activity_date as fecha_md,
            AVG(CASE WHEN field_time >= 4200 THEN total_distance * (5640/field_time) END) as max_total_distance
        FROM microciclos_metricas_procesadas
        WHERE activity_tag = 'MD'
          AND athlete_position != 'Goal Keeper'
          AND field_time >= 4200
          AND activity_date >= '{fecha_inicio_temporada}'
          AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
        GROUP BY activity_date
        ORDER BY activity_date DESC
    '''
    
    df_maximos = pd.read_sql(query_maximos, engine)
    
    for mc in microciclos:
        mc_id = mc['id']
        
        try:
            # Cargar datos del microciclo completo (igual que el gráfico)
            query_microciclo = f'''
                SELECT 
                    activity_tag,
                    athlete_id,
                    activity_date,
                    total_distance,
                    athlete_position,
                    participation_type
                FROM microciclos_metricas_procesadas
                WHERE microciclo_id = '{mc_id}'
                  AND athlete_position != 'Goal Keeper'
            '''
            
            df_mc = pd.read_sql(query_microciclo, engine)
            
            if df_mc.empty:
                compensatorios[mc_id] = {'valor': None, 'porcentaje': None, 'color': 'gris'}
                continue
            
            # Obtener fecha del MD (para buscar máximo histórico)
            df_md = df_mc[df_mc['activity_tag'] == 'MD']
            if df_md.empty:
                compensatorios[mc_id] = {'valor': None, 'porcentaje': None, 'color': 'gris'}
                continue
            
            fecha_md = df_md['activity_date'].min()
            
            # Filtrar por jugadores seleccionados (IGUAL que el gráfico)
            # Procesando compensatorio
            
            if jugadores_ids:
                df_entrenamientos = df_mc[
                    (df_mc['activity_tag'] != 'MD') &
                    (df_mc['athlete_id'].isin(jugadores_ids))
                ]
            else:
                df_entrenamientos = df_mc[df_mc['activity_tag'] != 'MD']
            
            # Buscar MD+1 primero
            df_md_plus_1 = df_entrenamientos[
                (df_entrenamientos['activity_tag'] == 'MD+1') &
                ((df_entrenamientos['participation_type'].isna()) | 
                 (~df_entrenamientos['participation_type'].isin(['Part', 'Rehab'])))
            ]
            
            # MD+1 disponible
            
            # Usar MD+1 si tiene datos
            if not df_md_plus_1.empty and not df_md_plus_1['total_distance'].isna().all():
                df_compensatorio = df_md_plus_1
                compensatorio_tag = 'MD+1'
            else:
                # Buscar MD+2
                df_md_plus_2_sin_filtro = df_entrenamientos[df_entrenamientos['activity_tag'] == 'MD+2']
                df_md_plus_2 = df_entrenamientos[
                    (df_entrenamientos['activity_tag'] == 'MD+2') &
                    ((df_entrenamientos['participation_type'].isna()) | 
                     (~df_entrenamientos['participation_type'].isin(['Part', 'Rehab'])))
                ]
                
                # MD+2 procesado
                
                df_compensatorio = df_md_plus_2
                compensatorio_tag = 'MD+2'
            
            # Si no hay ni MD+1 ni MD+2, sin datos
            if df_compensatorio.empty or df_compensatorio['total_distance'].isna().all():
                compensatorios[mc_id] = {'valor': None, 'porcentaje': None, 'color': 'gris'}
                continue
            
            # Calcular promedio con pandas (IGUAL que el gráfico)
            valor = df_compensatorio['total_distance'].mean()
            num_jugadores = len(df_compensatorio['athlete_id'].unique())
            
            # Compensatorio calculado
            
            if pd.isna(valor):
                compensatorios[mc_id] = {'valor': None, 'porcentaje': None, 'color': 'gris'}
                continue
            
            # Obtener máximos históricos hasta esta fecha (últimos 4 MDs desde inicio de temporada)
            df_maximos_hasta_fecha = df_maximos[df_maximos['fecha_md'] <= fecha_md].head(4)
            
            # VALIDACIÓN: Verificar cuántos partidos realmente tenemos
            num_partidos_disponibles = len(df_maximos_hasta_fecha)
            
            if not df_maximos_hasta_fecha.empty:
                # IMPORTANTE: Usar MAX de los máximos (igual que el gráfico)
                max_historico = df_maximos_hasta_fecha['max_total_distance'].max()
                
                # Máximo histórico obtenido (basado en {num_partidos_disponibles} partidos)
                
                # Calcular porcentaje relativo al máximo histórico (igual que otras métricas)
                porcentaje = (valor / max_historico) * 100 if max_historico > 0 else 0
                
                # Redondear ANTES de asignar color (igual que resto de métricas)
                porcentaje_redondeado = round(porcentaje)
                
                # Porcentaje calculado
                
                # Color con zona de tolerancia ±5% absoluto
                # Rango óptimo: 55-70%
                # Tolerancia: ±5% absoluto → naranja 50-54% y 71-75%
                
                if 55 <= porcentaje_redondeado <= 70:
                    color = 'verde'  # Dentro del rango óptimo (55-70%)
                elif 50 <= porcentaje_redondeado < 55:
                    color = 'naranja'  # Zona de tolerancia inferior (50-54%)
                elif 70 < porcentaje_redondeado <= 75:
                    color = 'naranja'  # Zona de tolerancia superior (71-75%)
                elif porcentaje_redondeado < 50:
                    color = 'rojo_claro'  # Muy por debajo del mínimo (<50%)
                else:  # > 75
                    color = 'rojo_oscuro'  # Muy por encima del máximo (>75%)
                
                # Color asignado
                
                compensatorios[mc_id] = {
                    'valor': valor,
                    'porcentaje': porcentaje_redondeado,
                    'color': color
                }
            else:
                compensatorios[mc_id] = {
                    'valor': None,
                    'porcentaje': None,
                    'color': 'gris'
                }
        except Exception as e:
            # Error en microciclo
            compensatorios[mc_id] = {
                'valor': None,
                'porcentaje': None,
                'color': 'gris'
            }
    
    # Compensatorios calculados
    
    engine.dispose()
    return compensatorios

def cargar_tabla_evolutiva_microciclos(jugadores_ids=None):
    """
    Carga TODOS los microciclos de la temporada y calcula acumulados para tabla evolutiva.
    
    ULTRA-OPTIMIZADO: Una sola query masiva para todos los microciclos.
    
    Args:
        jugadores_ids: Lista de IDs de jugadores (None = todos excepto porteros)
    
    Returns:
        dict con estructura:
        {
            'microciclos': [
                {
                    'id': 'mc_2025-08-16_J1_...',
                    'jornada': 'J1',
                    'rival': 'GRANADA CF',
                    'fecha_md': '2025-08-16',
                    'tipo_microciclo': 'estandar'
                },
                ...
            ],
            'acumulados': {
                'total_distance': {
                    'mc_2025-08-16_J1_...': {
                        'acumulado': 185.5,  # % acumulado
                        'color': 'verde',  # verde, rojo_claro, rojo_oscuro
                        'min_umbral': 170,
                        'max_umbral': 230
                    },
                    ...
                },
                ...
            }
        }
    """
    # Cargando tabla evolutiva
    
    engine = get_db_connection()
    if not engine:
        return None
    
    try:
        # Determinar fecha de inicio de temporada dinámicamente
        from datetime import datetime
        temporada_actual = datetime.now().year
        fecha_inicio_temporada = f"{temporada_actual}-08-10"
        
        # Query 1: Obtener todos los microciclos de la temporada (ordenados cronológicamente)
        # Filtrar desde inicio de temporada dinámico
        query_microciclos = f'''
            SELECT DISTINCT
                microciclo_id,
                microciclo_nombre,
                MIN(activity_date) as fecha_inicio,
                MAX(activity_date) as fecha_fin,
                MAX(CASE WHEN activity_tag = 'MD' THEN activity_date END) as fecha_md,
                MAX(CASE WHEN activity_tag = 'MD' THEN activity_name END) as partido_nombre
            FROM microciclos_metricas_procesadas
            WHERE athlete_position != 'Goal Keeper'
              AND activity_date >= '{fecha_inicio_temporada}'
            GROUP BY microciclo_id, microciclo_nombre
            HAVING fecha_md IS NOT NULL
            ORDER BY fecha_inicio ASC
        '''
        
        df_microciclos = pd.read_sql(query_microciclos, engine)
        
        if df_microciclos.empty:
            # No se encontraron microciclos
            return None
        
        # Microciclos encontrados
        
        # Procesar información de cada microciclo
        microciclos_info = []
        for _, row in df_microciclos.iterrows():
            # Label simplificado: quitar "Semana" y fechas
            # Ejemplo: "Semana J1 GRANADA CF VS RC DEPORTIVO" -> "J1 GRANADA CF VS RC DEPORTIVO"
            label_simplificado = row['microciclo_nombre'].replace('Semana ', '')
            
            # Extraer jornada para la tabla
            match_jornada = re.search(r'J(\d+)', row['microciclo_nombre'])
            jornada = f"J{match_jornada.group(1)}" if match_jornada else "???"
            
            microciclos_info.append({
                'id': row['microciclo_id'],
                'label': label_simplificado,  # Label simplificado sin "Semana" ni fechas
                'jornada': jornada,  # Solo la jornada para primera línea
                'fecha_md': row['fecha_md'],
                'tipo_microciclo': None  # Se calculará después
            })
        
        # Query 2: Obtener datos de entrenamientos (MD-X) para TODOS los microciclos
        # Solo necesitamos los entrenamientos, no MD ni compensatorios
        # TAMBIÉN obtener los activity_tags para detectar el tipo de microciclo
        filtro_jugadores = ""
        if jugadores_ids:
            jugadores_ids_quoted = ','.join([f"'{j}'" for j in jugadores_ids])
            filtro_jugadores = f"AND athlete_id IN ({jugadores_ids_quoted})"
        
        query_entrenamientos = f'''
            SELECT 
                microciclo_id,
                activity_tag,
                AVG(total_distance) as avg_total_distance,
                AVG(distancia_21_kmh) as avg_distancia_21_kmh,
                AVG(distancia_24_kmh) as avg_distancia_24_kmh,
                AVG(acc_dec_total) as avg_acc_dec_total,
                AVG(ritmo_medio) as avg_ritmo_medio,
                COUNT(DISTINCT athlete_id) as num_athletes
            FROM microciclos_metricas_procesadas
            WHERE activity_tag REGEXP '^MD-[0-9]+$'
              AND athlete_position != 'Goal Keeper'
              AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
              {filtro_jugadores}
            GROUP BY microciclo_id, activity_tag
            ORDER BY microciclo_id, activity_tag
        '''
        
        df_entrenamientos = pd.read_sql(query_entrenamientos, engine)
        
        # Query 3: Obtener máximos históricos para cada microciclo (últimos 4 MDs)
        # 🎯 DIFERENCIA CLAVE: Si es UN SOLO jugador, usar máximos INDIVIDUALES
        # Si son múltiples jugadores, usar máximos del EQUIPO
        es_jugador_individual = jugadores_ids and len(jugadores_ids) == 1
        df_partidos_jugador = pd.DataFrame()  # Inicializar para evitar problemas de scope
        
        if es_jugador_individual:
            jugador_id = jugadores_ids[0]
            # Modo jugador individual
            
            # 🚀 UNA SOLA query para obtener el MÁXIMO ABSOLUTO de cada métrica
            # Primero intentar con partidos +70'
            query_max_jugador = f'''
                SELECT 
                    MAX(total_distance * (5640/field_time)) as max_total_distance,
                    MAX(distancia_21_kmh * (5640/field_time)) as max_distancia_21_kmh,
                    MAX(distancia_24_kmh * (5640/field_time)) as max_distancia_24_kmh,
                    MAX(acc_dec_total * (5640/field_time)) as max_acc_dec_total,
                    MAX(distance_per_minute) as max_ritmo_medio
                FROM microciclos_metricas_procesadas
                WHERE athlete_id = '{jugador_id}'
                  AND activity_tag = 'MD'
                  AND field_time >= 4200
                  AND activity_date >= '{fecha_inicio_temporada}'
            '''
            
            df_max_jugador = pd.read_sql(query_max_jugador, engine)
            
            # Verificar si encontramos valores válidos
            tiene_datos_70 = not df_max_jugador.empty and df_max_jugador['max_total_distance'].notna().any()
            
            if not tiene_datos_70:
                # FALLBACK: Buscar el partido donde jugó más minutos (sin filtro +70')
                # Sin partidos +70', buscando partido con más minutos
                query_max_jugador_fallback = f'''
                    SELECT 
                        MAX(total_distance * (5640/field_time)) as max_total_distance,
                        MAX(distancia_21_kmh * (5640/field_time)) as max_distancia_21_kmh,
                        MAX(distancia_24_kmh * (5640/field_time)) as max_distancia_24_kmh,
                        MAX(acc_dec_total * (5640/field_time)) as max_acc_dec_total,
                        MAX(distance_per_minute) as max_ritmo_medio
                    FROM microciclos_metricas_procesadas
                    WHERE athlete_id = '{jugador_id}'
                      AND activity_tag = 'MD'
                      AND activity_date >= '{fecha_inicio_temporada}'
                    ORDER BY field_time DESC
                    LIMIT 1
                '''
                df_max_jugador = pd.read_sql(query_max_jugador_fallback, engine)
            
            # Convertir a diccionario simple para uso posterior
            maximos_absolutos_jugador = {}
            if not df_max_jugador.empty:
                maximos_absolutos_jugador = {
                    'total_distance': df_max_jugador['max_total_distance'].iloc[0],
                    'distancia_21_kmh': df_max_jugador['max_distancia_21_kmh'].iloc[0],
                    'distancia_24_kmh': df_max_jugador['max_distancia_24_kmh'].iloc[0],
                    'acc_dec_total': df_max_jugador['max_acc_dec_total'].iloc[0],
                    'ritmo_medio': df_max_jugador['max_ritmo_medio'].iloc[0]
                }
                # Máximos absolutos calculados
            else:
                # No se encontraron partidos para el jugador
                for metrica in metricas:
                    maximos_absolutos_jugador[metrica] = None
            
            # DataFrame vacío para mantener compatibilidad (no se usa en modo individual)
            df_maximos = pd.DataFrame()
            df_partidos_jugador = pd.DataFrame()  # No necesitamos el DF completo
            
        else:
            # Modo EQUIPO: Usar promedios de todos los jugadores (lógica original)
            # IMPORTANTE: Filtrar desde inicio de temporada
            query_maximos = f'''
                SELECT 
                    activity_date as fecha_md,
                    AVG(CASE WHEN field_time >= 4200 THEN total_distance * (5640/field_time) END) as max_total_distance,
                    AVG(CASE WHEN field_time >= 4200 THEN distancia_21_kmh * (5640/field_time) END) as max_distancia_21_kmh,
                    AVG(CASE WHEN field_time >= 4200 THEN distancia_24_kmh * (5640/field_time) END) as max_distancia_24_kmh,
                    AVG(CASE WHEN field_time >= 4200 THEN acc_dec_total * (5640/field_time) END) as max_acc_dec_total,
                    AVG(CASE WHEN field_time >= 4200 THEN distance_per_minute END) as max_ritmo_medio
                FROM microciclos_metricas_procesadas
                WHERE activity_tag = 'MD'
                  AND athlete_position != 'Goal Keeper'
                  AND field_time >= 4200
                  AND activity_date >= '{fecha_inicio_temporada}'
                  AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
                GROUP BY activity_date
                ORDER BY activity_date DESC
            '''
            
            df_maximos = pd.read_sql(query_maximos, engine)
        
        # Datos de entrenamientos cargados
        
        # Calcular acumulados para cada métrica y microciclo
        metricas = ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total', 'ritmo_medio']
        acumulados = {metrica: {} for metrica in metricas}
        
        for mc_info in microciclos_info:
            mc_id = mc_info['id']
            fecha_md = mc_info['fecha_md']
            
            # Filtrar entrenamientos de este microciclo
            df_mc = df_entrenamientos[df_entrenamientos['microciclo_id'] == mc_id]
            
            if df_mc.empty:
                # No hay entrenamientos, marcar como sin datos
                for metrica in metricas:
                    acumulados[metrica][mc_id] = {
                        'acumulado': None,
                        'color': 'gris',
                        'min_umbral': None,
                        'max_umbral': None
                    }
                mc_info['tipo_microciclo'] = 'especial'
                continue
            
            # 🎯 CALCULAR MÁXIMOS según modo (individual vs equipo)
            if es_jugador_individual:
                # ✅ Usar MÁXIMO ABSOLUTO del jugador (ya calculado, no depende de fecha)
                # Este máximo se usa para TODOS los microciclos
                maximos_individuales = maximos_absolutos_jugador
            else:
                # Modo EQUIPO: Usar DataFrame de máximos del equipo (últimos 4 desde inicio de temporada)
                df_maximos_hasta_fecha = df_maximos[df_maximos['fecha_md'] <= fecha_md].head(4)
                
                # VALIDACIÓN: Verificar cuántos partidos realmente tenemos
                num_partidos_disponibles = len(df_maximos_hasta_fecha)
                if num_partidos_disponibles < 4:
                    # Ajustar cálculo basado en partidos reales disponibles
                    pass  # El cálculo sigue siendo válido con menos de 4 partidos
            
            # Calcular acumulado para cada métrica
            for metrica in metricas:
                col_avg = f'avg_{metrica}'
                col_max = f'max_{metrica}'
                
                # Ya NO es necesario agrupar porque SQL ya agrupa por activity_tag
                # SQL: GROUP BY microciclo_id, activity_tag
                # Resultado: 1 registro por (microciclo, activity_tag)
                
                # Obtener valores de entrenamientos (MD-X) - ya vienen agrupados de SQL
                valores_entrenamientos = df_mc[col_avg].dropna().tolist()
                
                if not valores_entrenamientos:
                    acumulados[metrica][mc_id] = {
                        'acumulado': None,
                        'color': 'gris',
                        'min_umbral': None,
                        'max_umbral': None
                    }
                    continue
                
                # Obtener máximo histórico según modo
                if es_jugador_individual:
                    max_historico = maximos_individuales.get(metrica)
                else:
                    if df_maximos_hasta_fecha.empty:
                        max_historico = None
                    else:
                        max_historico = df_maximos_hasta_fecha[col_max].max()
                
                # Validar que el máximo existe y es válido
                if max_historico is None or pd.isna(max_historico) or max_historico == 0:
                    acumulados[metrica][mc_id] = {
                        'acumulado': None,
                        'color': 'gris',
                        'min_umbral': None,
                        'max_umbral': None
                    }
                    continue
                
                # Calcular % de cada entrenamiento sobre el máximo histórico
                porcentajes = [(valor / max_historico) * 100 for valor in valores_entrenamientos]
                
                # Acumulado depende del tipo de métrica
                if metrica == 'ritmo_medio':
                    acumulado_pct = sum(porcentajes) / len(porcentajes)  # Media
                else:
                    acumulado_pct = sum(porcentajes)  # Suma
                
                # IMPORTANTE: Redondear ANTES de guardar para que el color se base en el valor mostrado
                acumulado_pct_redondeado = round(acumulado_pct)
                
                # Guardar acumulado REDONDEADO (sin determinar color aún, se hará después con tipo_microciclo)
                acumulados[metrica][mc_id] = {
                    'acumulado': acumulado_pct_redondeado,  # Guardar redondeado
                    'color': None,  # Se asignará después
                    'min_umbral': None,  # Se asignará después
                    'max_umbral': None,  # Se asignará después
                    'num_entrenamientos': len(valores_entrenamientos)
                }
        
        # Determinar tipo de microciclo basado en los DÍAS PRESENTES
        # Usar función local (movida desde seguimiento_carga.py)
        
        for mc_info in microciclos_info:
            mc_id = mc_info['id']
            
            # Obtener días presentes en este microciclo desde df_entrenamientos
            df_mc = df_entrenamientos[df_entrenamientos['microciclo_id'] == mc_id]
            
            if df_mc.empty:
                mc_info['tipo_microciclo'] = 'especial'
                # Sin entrenamientos → Tipo: especial
                continue
            
            # Obtener lista de activity_tags únicos
            dias_presentes = df_mc['activity_tag'].unique().tolist()
            
            # Detectar tipo usando la misma función que el seguimiento de carga
            tipo = detectar_tipo_microciclo(dias_presentes)
            
            # Tipo detectado
            mc_info['tipo_microciclo'] = tipo
        
        # Ahora asignar umbrales y colores basados en el tipo de microciclo
        # Usar función local (movida desde seguimiento_carga.py)
        
        for mc_info in microciclos_info:
            mc_id = mc_info['id']
            tipo = mc_info['tipo_microciclo']
            
            # Asignando colores
            
            if tipo == 'especial':
                # Sin umbrales, color gris
                for metrica in metricas:
                    if acumulados[metrica][mc_id].get('acumulado') is not None:
                        acumulados[metrica][mc_id]['color'] = 'gris'
                    else:
                        # Asegurarse de que tenga color aunque sea None
                        acumulados[metrica][mc_id]['color'] = 'gris'
                continue
            
            # Obtener configuración de umbrales para este tipo
            config = get_metricas_config_por_tipo(tipo)
            
            for config_metrica in config:
                metrica_id = config_metrica['id']
                if metrica_id not in metricas:
                    continue
                
                min_umbral = config_metrica['min']
                max_umbral = config_metrica['max']
                acumulado_val = acumulados[metrica_id][mc_id].get('acumulado')
                
                if acumulado_val is None:
                    color = 'gris'
                else:
                    # Zona de tolerancia ±5% absoluto (no relativo)
                    # Ejemplo: rango 60-80% → naranja 55-59% y 81-85%
                    
                    if acumulado_val < (min_umbral - 5):
                        color = 'rojo_claro'  # Muy por debajo del mínimo (< min-5)
                    elif acumulado_val < min_umbral:
                        color = 'naranja'  # Zona de tolerancia inferior (min-5 a min-1)
                    elif acumulado_val <= max_umbral:
                        color = 'verde'  # Dentro del rango óptimo
                    elif acumulado_val <= (max_umbral + 5):
                        color = 'naranja'  # Zona de tolerancia superior (max+1 a max+5)
                    else:
                        color = 'rojo_oscuro'  # Muy por encima del máximo (> max+5)
                
                # Valor procesado
                
                acumulados[metrica_id][mc_id].update({
                    'color': color,
                    'min_umbral': min_umbral,
                    'max_umbral': max_umbral
                })
        
        # Acumulados calculados
        
        return {
            'microciclos': microciclos_info,
            'acumulados': acumulados,
            'jugadores_ids': jugadores_ids  # Para cálculo de compensatorios
        }
        
    except Exception as e:
        # Error cargando tabla evolutiva
        import traceback
        traceback.print_exc()
        return None


# ============================================
# FUNCIONES MOVIDAS DESDE seguimiento_carga.py
# ============================================

def detectar_tipo_microciclo(dias_presentes):
    """
    Detecta el tipo de microciclo según los días de entrenamiento presentes.
    
    Tipos:
    - EXTENDIDO: Tiene MD-5 (5 entrenamientos: MD-5, MD-4, MD-3, MD-2, MD-1)
    - SUPERRECORTADO: NO tiene MD-3 ni MD-4 (2 entrenamientos: MD-2, MD-1)
    - REDUCIDO: NO tiene MD-5 ni MD-4 pero tiene MD-3 (3 entrenamientos: MD-3, MD-2, MD-1)
    - ESTÁNDAR: Tiene MD-4 pero NO MD-5 (4 entrenamientos: MD-4, MD-3, MD-2, MD-1)
    
    Args:
        dias_presentes: Lista de tags de días (ej: ['MD+1', 'MD-4', 'MD-3', 'MD-2', 'MD-1', 'MD'])
    
    Returns:
        str: 'extendido', 'superrecortado', 'reducido', o 'estandar'
    """
    if not dias_presentes:
        return 'estandar'
    
    # Extendido
    if 'MD-5' in dias_presentes or 'MD-6' in dias_presentes:
        return 'extendido'
    # Superrecortado (solo MD-2 y MD-1, sin MD-3)
    elif 'MD-3' not in dias_presentes and 'MD-4' not in dias_presentes:
        return 'superrecortado'
    # Reducido (tiene MD-3 pero no MD-4)
    elif 'MD-4' not in dias_presentes:
        return 'reducido'
    # Estándar
    else:
        return 'estandar'


def get_metricas_config_por_tipo(tipo_microciclo):
    """
    Retorna la configuración de métricas con umbrales según el tipo de microciclo.
    
    Args:
        tipo_microciclo: 'estandar', 'extendido', 'reducido', o 'superrecortado'
    
    Returns:
        Lista de diccionarios con configuración de métricas
    """
    if tipo_microciclo == 'extendido':
        return [
            {'id': 'total_distance', 'label': 'Distancia Total', 'min': 200, 'max': 280, 'tipo': 'suma'},
            {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h', 'min': 100, 'max': 190, 'tipo': 'suma'},
            {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h', 'min': 90, 'max': 170, 'tipo': 'suma'},
            {'id': 'acc_dec_total', 'label': 'Acel/Decel +3 (m/s²)', 'min': 250, 'max': 380, 'tipo': 'suma'},
            {'id': 'ritmo_medio', 'label': 'Ritmo Medio (m/min.)', 'min': 55, 'max': 75, 'tipo': 'media'}
        ]
    elif tipo_microciclo == 'superrecortado':
        return [
            {'id': 'total_distance', 'label': 'Distancia Total', 'min': 60, 'max': 110, 'tipo': 'suma'},
            {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h', 'min': 20, 'max': 60, 'tipo': 'suma'},
            {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h', 'min': 20, 'max': 40, 'tipo': 'suma'},
            {'id': 'acc_dec_total', 'label': 'Acel/Decel +3 (m/s²)', 'min': 65, 'max': 120, 'tipo': 'suma'},
            {'id': 'ritmo_medio', 'label': 'Ritmo Medio (m/min.)', 'min':40, 'max': 65, 'tipo': 'media'}
        ]
    elif tipo_microciclo == 'reducido':
        return [
            {'id': 'total_distance', 'label': 'Distancia Total', 'min': 125, 'max': 170, 'tipo': 'suma'},
            {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h', 'min': 70, 'max': 130, 'tipo': 'suma'},
            {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h', 'min': 60, 'max': 100, 'tipo': 'suma'},
            {'id': 'acc_dec_total', 'label': 'Acel/Decel +3 (m/s²)', 'min': 115, 'max': 190, 'tipo': 'suma'},
            {'id': 'ritmo_medio', 'label': 'Ritmo Medio (m/min.)', 'min': 50, 'max': 75, 'tipo': 'media'}
        ]
    else:  # estandar
        return [
            {'id': 'total_distance', 'label': 'Distancia Total', 'min': 170, 'max': 230, 'tipo': 'suma'},
            {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h', 'min': 90, 'max': 160, 'tipo': 'suma'},
            {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h', 'min': 80, 'max': 140, 'tipo': 'suma'},
            {'id': 'acc_dec_total', 'label': 'Acel/Decel +3 (m/s²)', 'min': 190, 'max': 290, 'tipo': 'suma'},
            {'id': 'ritmo_medio', 'label': 'Ritmo Medio (m/min.)', 'min': 55, 'max': 75, 'tipo': 'media'}
        ]
