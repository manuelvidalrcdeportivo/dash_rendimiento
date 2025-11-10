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
    print(f"⚡⚡⚡ ULTRA-OPTIMIZACIÓN: Cargando microciclo con 2 queries masivas")
    
    engine = get_db_connection()
    if not engine:
        return None
    
    # Formatear IDs con comillas
    jugadores_ids_quoted = ','.join([f"'{j}'" for j in jugadores_ids])
    
    # ========================================
    # QUERY 1: TODO EL MICROCICLO (todas las métricas en UNA query)
    # ========================================
    print("📦 Query 1: Cargando TODO el microciclo (5 métricas)...")
    
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
            activity_name
        FROM microciclos_metricas_procesadas
        WHERE microciclo_id = '{microciclo_id}'
          AND athlete_position != 'Goal Keeper'
    '''
    
    df_microciclo = pd.read_sql(query_microciclo, engine)
    print(f"✅ {len(df_microciclo)} registros cargados (1 query)")
    print(f"  ℹ️ Jugadores únicos: {df_microciclo['athlete_id'].nunique()} (TODOS sin porteros)")
    
    if df_microciclo.empty:
        return None
    
    # Obtener fecha del MD para máximos históricos
    # LÓGICA SIMPLE: Hay 1 MD por microciclo (por estructura de datos)
    # Buscar por TAG, tomar el primero cronológicamente
    # IGNORAR nombres de partidos (solo para hover)
    
    df_md = df_microciclo[df_microciclo['activity_tag'] == 'MD']
    
    if df_md.empty:
        print("⚠️ No hay MD en este microciclo")
        fecha_md = None
    else:
        fecha_md = df_md['activity_date'].min()  # Primer MD cronológicamente
        print(f"  ℹ️ MD del microciclo: {fecha_md}")
    
    # Extraer año/temporada del microciclo_id para filtrar solo partidos de la misma temporada
    # Formato: mc_2025-10-26_J11_RCD_Vs_R_VALLADOLID
    temporada_actual = None
    match_temporada = re.search(r'mc_(\d{4})-', microciclo_id)
    if match_temporada:
        temporada_actual = int(match_temporada.group(1))
        print(f"  ℹ️ Temporada detectada del microciclo_id: {temporada_actual}")
    elif fecha_md is not None:
        # Si no se puede extraer del microciclo_id (ej: mc_actual), usar año del MD
        temporada_actual = pd.to_datetime(fecha_md).year
        print(f"  ℹ️ Temporada detectada del MD: {temporada_actual}")
    else:
        # Fallback: usar año actual
        from datetime import datetime
        temporada_actual = datetime.now().year
        print(f"  ℹ️ Temporada por defecto (año actual): {temporada_actual}")
    
    # ========================================
    # QUERY 2: ÚLTIMOS 4 MDs (todas las métricas en UNA query)
    # ========================================
    print("📊 Query 2: Cargando últimos 4 MDs (todas las métricas)...")
    
    # Buscar máximos históricos: MD actual + 3 anteriores = 4 total
    if temporada_actual and fecha_md is not None:
        # INCLUIR el MD actual (<=) + 3 anteriores
        condicion_fecha = f"AND activity_date <= '{fecha_md}'"
        msg_fecha = f"hasta {fecha_md} (incluye MD actual + 3 anteriores)"
        
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
                    THEN ritmo_medio
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
        print(f"✅ {len(df_historicos)} MDs históricos cargados (1 query)")
        print(f"  📅 {msg_fecha} (temporada {temporada_actual})")
        if not df_historicos.empty:
            print(f"  📅 Fechas encontradas: {', '.join([str(d) for d in df_historicos['activity_date'].tolist()])}")
            if 'activity_name' in df_historicos.columns:
                for idx, row in df_historicos.iterrows():
                    partido = row['activity_name'] if pd.notna(row['activity_name']) else 'N/A'
                    print(f"    • {row['activity_date']}: {partido}")
        
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
                    
                    # Debug: Mostrar todos los valores de esta métrica
                    if metric_name == 'distancia_21_kmh':
                        print(f"\n  🔍 DEBUG {metric_name}:")
                        for idx, row in col_data.iterrows():
                            partido_debug = row['activity_name'] if pd.notna(row['activity_name']) else 'N/A'
                            print(f"    • {row['activity_date']}: {row[col]:.1f}m - {partido_debug}")
                    
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
                    print(f"  ℹ️ {metric_name}: MAX={max_val:.1f} MIN={col_data[col].min():.1f}")
                    print(f"     → Partido del máximo: {partido_max if partido_max else 'N/A'} ({fecha_max})")
        
        print(f"✅ Máximos calculados para {len(maximos_historicos)} métricas")
    else:
        maximos_historicos = {}
        print("⚠️ No se pudieron calcular máximos históricos (sin MD o sin temporada)")
    
    # ========================================
    # PROCESAMIENTO EN MEMORIA (pandas super rápido)
    # ========================================
    print("⚡ Procesando datos en memoria...")
    
    # Mapeo de columnas SQL a nombres de métrica del dashboard
    columnas_metricas = {
        'total_distance': 'total_distance',
        'distancia_21_kmh': 'distancia_21_kmh',
        'distancia_24_kmh': 'distancia_24_kmh',
        'acc_dec_total': 'acc_dec_total',
        'ritmo_medio': 'ritmo_medio'
    }
    
    print(f"📊 Columnas disponibles en df_microciclo: {df_microciclo.columns.tolist()}")
    
    # Obtener nombre del partido del MD real (desde activity_name)
    nombre_partido = None
    if 'MD' in df_microciclo['activity_tag'].values and 'activity_name' in df_microciclo.columns:
        # Obtener el activity_name del MD (partido real)
        df_md_name = df_microciclo[df_microciclo['activity_tag'] == 'MD']
        if not df_md_name.empty and pd.notna(df_md_name['activity_name'].iloc[0]):
            nombre_partido = df_md_name['activity_name'].iloc[0]
            print(f"  ℹ️ Nombre del partido MD: {nombre_partido}")
    
    # Procesar cada métrica
    datos_por_metrica = {}
    
    # Crear DataFrame filtrado para ENTRENAMIENTOS (solo jugadores seleccionados)
    # Filtrar Part/Rehab de TODOS los entrenamientos (MD-X y MD+X)
    df_entrenamientos = df_microciclo[
        (df_microciclo['activity_tag'] != 'MD') & 
        (df_microciclo['athlete_id'].isin(jugadores_ids))
    ].copy()
    
    print(f"  ℹ️ Entrenamientos ANTES de filtrar Part/Rehab: {len(df_entrenamientos)} registros")
    
    # Filtrar Part/Rehab de TODOS los entrenamientos (MD-X y MD+X)
    # Solo mantener participation_type Full (NULL o no Part/Rehab)
    df_entrenamientos_filtrado = df_entrenamientos[
        (df_entrenamientos['participation_type'].isna()) | 
        (~df_entrenamientos['participation_type'].isin(['Part', 'Rehab']))
    ].copy()
    
    print(f"  ℹ️ Entrenamientos DESPUÉS de filtrar Part/Rehab: {len(df_entrenamientos_filtrado)} registros")
    print(f"  ℹ️ Registros eliminados (Part/Rehab): {len(df_entrenamientos) - len(df_entrenamientos_filtrado)}")
    
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
    
    print(f"  ℹ️ Entrenamientos: {df_entrenamientos['athlete_id'].nunique()} jugadores seleccionados")
    if not df_md_completo.empty:
        print(f"  ℹ️ MD (partido): {df_md_completo['athlete_id'].nunique()} jugadores (TODOS)")
    else:
        print(f"  ℹ️ MD (partido): No hay MD en este microciclo")
    
    for col_name, metric_name in columnas_metricas.items():
        # Validar que la columna existe
        if col_name not in df_microciclo.columns:
            print(f"  ⚠️ Columna '{col_name}' no encontrada, saltando...")
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
                    print(f"    → {tag}: {valor:.1f}m (promedio de {count} jugadores Full)")
        
        # Agrupar MD (TODOS los jugadores, procesamiento especial después)
        if not df_md_completo.empty:
            df_metrica_md = df_md_completo.groupby('activity_tag').agg({
                col_name: 'mean',
                'athlete_id': 'count',
                'activity_date': 'min'
            }).reset_index()
            df_metrica_md.columns = ['activity_tag', 'avg_metric', 'count_athletes', 'fecha']
            
            # Combinar entrenamientos + MD
            df_metrica = pd.concat([df_metrica_entrenos, df_metrica_md], ignore_index=True)
        else:
            df_metrica = df_metrica_entrenos
        
        # Para métricas que requieren filtro +70 mins en MD
        if metric_name in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total', 'ritmo_medio'] and not df_md_completo.empty:
            # Filtrar jugadores con +70 mins en MD (usando TODOS los jugadores)
            df_md_filtrado = df_md_completo[df_md_completo['field_time'] >= 4200]
            
            if not df_md_filtrado.empty:
                # Estandarizar a 94 minutos SOLO para distancias y aceleraciones
                # Ritmo medio NO se estandariza (ya es m/min)
                if metric_name in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
                    valor_estandarizado = (df_md_filtrado[col_name] * (5640 / df_md_filtrado['field_time'])).mean()
                else:
                    # Para ritmo_medio: solo filtrar +70 mins, no estandarizar
                    valor_estandarizado = df_md_filtrado[col_name].mean()
                
                count_filtrado = len(df_md_filtrado['athlete_id'].unique())
                
                # Actualizar valor del MD
                df_metrica.loc[df_metrica['activity_tag'] == 'MD', 'avg_metric'] = valor_estandarizado
                df_metrica.loc[df_metrica['activity_tag'] == 'MD', 'count_athletes'] = count_filtrado
                print(f"    → MD {metric_name}: {valor_estandarizado:.1f} (TODOS: {count_filtrado} jug. +70')")
        
        datos_por_metrica[metric_name] = df_metrica
        print(f"  ✓ {metric_name}")
    
    print(f"✅ {len(datos_por_metrica)} métricas procesadas en memoria")
    
    # Los umbrales ahora están hardcodeados en la función de generación de gráficos
    # para mejorar el rendimiento (sin queries adicionales)
    print("✅ Umbrales hardcodeados (sin queries)")
    
    # Mostrar días presentes
    dias_presentes = []
    if 'total_distance' in datos_por_metrica:
        dias_presentes = datos_por_metrica['total_distance']['activity_tag'].tolist()
    print(f"   Días presentes: {dias_presentes}")
    
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
    print(f"🔍 Calculando máximo individual para jugador {athlete_id} - {metric_name}")
    
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
    columnas_metricas = {
        'total_distance': 'total_distance',
        'distancia_+21_km/h_(m)': 'distancia_21_kmh',
        'distancia_+24_km/h_(m)': 'distancia_24_kmh',
        'distancia+28_(km/h)': 'distancia_28_kmh',
        'gen2_acceleration_band7plus_total_effort_count': 'acc_dec_total',
        'average_player_load': 'ritmo_medio'
    }
    
    col_name = columnas_metricas.get(metric_name, metric_name)
    
    # Query para obtener últimos 4 MDs con +70 minutos del jugador
    # INCLUIR el MD actual (<=) igual que Microciclo Equipo
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
          {f"AND activity_date <= '{fecha_referencia}'" if fecha_referencia else ""}
        ORDER BY activity_date DESC
        LIMIT 4
    '''
    
    try:
        df = pd.read_sql(query, engine)
        
        if df.empty:
            # No tiene ningún MD con +70 minutos en últimos 4
            print(f"  ⚠️ Jugador {athlete_id}: SIN partidos +70' en últimos 4 MDs")
            
            # FALLBACK 1: Buscar desde inicio de temporada (15/08/2024)
            query_temporada = f'''
                SELECT 
                    activity_date,
                    activity_name,
                    field_time,
                    {col_name} as metric_value
                FROM microciclos_metricas_procesadas
                WHERE athlete_id = '{athlete_id}'
                  AND activity_tag = 'MD'
                  AND field_time >= 4200
                  AND activity_date >= '2024-08-15'
                ORDER BY activity_date DESC
                LIMIT 4
            '''
            
            df_temporada = pd.read_sql(query_temporada, engine)
            
            if not df_temporada.empty:
                # Tiene al menos 1 MD +70' en la temporada
                print(f"  ✅ Encontrados {len(df_temporada)} partidos +70' desde inicio de temporada")
                
                # Estandarizar y obtener máximo
                df_temporada['metric_value_std'] = df_temporada['metric_value'] * (5640 / df_temporada['field_time'])
                idx_max = df_temporada['metric_value_std'].idxmax()
                max_value = df_temporada.loc[idx_max, 'metric_value_std']
                partido_max = df_temporada.loc[idx_max, 'activity_name']
                fecha_max = df_temporada.loc[idx_max, 'activity_date']
                
                return {
                    'max': max_value,
                    'partido_max': partido_max,
                    'fecha_max': fecha_max,
                    'tiene_datos': True,
                    'ultimo_md_fecha': df_temporada['activity_date'].iloc[0],
                    'warning': f'⚠️ Solo {len(df_temporada)} partido(s) +70\' en temporada (desde 15/08)',
                    'num_partidos': len(df_temporada)
                }
            
            # FALLBACK 2: Buscar partido donde jugó más minutos (sin filtro +70')
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
                  AND activity_date >= '2024-08-15'
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
                # Usar el partido donde jugó más minutos y estandarizar
                field_time = df_max_min['field_time'].iloc[0]
                metric_value = df_max_min['metric_value'].iloc[0]
                valor_std = metric_value * (5640 / field_time)
                partido = df_max_min['activity_name'].iloc[0]
                fecha = df_max_min['activity_date'].iloc[0]
                
                print(f"  ⚠️ Usando partido con más minutos: {field_time/60:.0f}' ({partido})")
                
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
        print(f"  ✅ Jugador {athlete_id}: {len(df)} partidos +70' encontrados")
        
        # Estandarizar a 94 minutos (5640 segundos)
        df['metric_value_std'] = df['metric_value'] * (5640 / df['field_time'])
        
        # Obtener el máximo
        idx_max = df['metric_value_std'].idxmax()
        max_value = df.loc[idx_max, 'metric_value_std']
        partido_max = df.loc[idx_max, 'activity_name']
        fecha_max = df.loc[idx_max, 'activity_date']
        
        # Verificar si tiene menos de 4 MDs
        warning = None
        if len(df) < 4:
            warning = f'⚠️ Solo {len(df)} partido(s) +70\' en últimos 4 MDs'
        
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
        print(f"  ❌ Error calculando máximo individual: {e}")
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
    
    print("\n" + "="*80)
    print("🔍 CÁLCULO DE COMPENSATORIOS PARA TABLA EVOLUTIVA")
    print("="*80)
    print(f"Total microciclos a procesar: {len(microciclos)}")
    print(f"Jugadores seleccionados: {len(jugadores_ids) if jugadores_ids else 'TODOS (sin porteros)'}\n")
    
    # Query para obtener máximos históricos (IGUAL que tabla evolutiva para Distancia Total)
    # Normalizado a 94 mins para jugadores con +70 mins
    query_maximos = '''
        SELECT 
            activity_date as fecha_md,
            AVG(CASE WHEN field_time >= 4200 THEN total_distance * (5640/field_time) END) as max_total_distance
        FROM microciclos_metricas_procesadas
        WHERE activity_tag = 'MD'
          AND athlete_position != 'Goal Keeper'
          AND field_time >= 4200
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
            print(f"\n📊 COMPENSATORIO {mc_id}:")
            print(f"  Jugadores seleccionados: {len(jugadores_ids) if jugadores_ids else 'TODOS'}")
            
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
            
            if not df_md_plus_1.empty:
                print(f"  MD+1: {df_md_plus_1['athlete_id'].nunique()} jug, {df_md_plus_1['total_distance'].mean():.1f}m")
            
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
                
                print(f"  MD+2 sin filtro Part/Rehab: {len(df_md_plus_2_sin_filtro)} registros")
                if not df_md_plus_2_sin_filtro.empty:
                    print(f"    Jugadores: {df_md_plus_2_sin_filtro['athlete_id'].nunique()}")
                    print(f"    Distancia promedio: {df_md_plus_2_sin_filtro['total_distance'].mean():.1f}m")
                
                print(f"  MD+2 CON filtro Part/Rehab: {len(df_md_plus_2)} registros")
                if not df_md_plus_2.empty:
                    print(f"    Jugadores: {df_md_plus_2['athlete_id'].nunique()}")
                    print(f"    Distancia promedio: {df_md_plus_2['total_distance'].mean():.1f}m")
                    print(f"    Jugadores: {sorted(df_md_plus_2['athlete_id'].unique())}")
                
                df_compensatorio = df_md_plus_2
                compensatorio_tag = 'MD+2'
            
            # Si no hay ni MD+1 ni MD+2, sin datos
            if df_compensatorio.empty or df_compensatorio['total_distance'].isna().all():
                compensatorios[mc_id] = {'valor': None, 'porcentaje': None, 'color': 'gris'}
                continue
            
            # Calcular promedio con pandas (IGUAL que el gráfico)
            valor = df_compensatorio['total_distance'].mean()
            num_jugadores = len(df_compensatorio['athlete_id'].unique())
            
            print(f"  ✅ Compensatorio elegido: {compensatorio_tag}")
            print(f"     Valor calculado: {valor:.1f}m (promedio de {num_jugadores} jugadores)")
            
            if pd.isna(valor):
                compensatorios[mc_id] = {'valor': None, 'porcentaje': None, 'color': 'gris'}
                continue
            
            # Obtener máximos históricos hasta esta fecha (últimos 4 MDs)
            df_maximos_hasta_fecha = df_maximos[df_maximos['fecha_md'] <= fecha_md].head(4)
            
            if not df_maximos_hasta_fecha.empty:
                # IMPORTANTE: Usar MAX de los máximos (igual que el gráfico)
                max_historico = df_maximos_hasta_fecha['max_total_distance'].max()
                
                print(f"     Máximo histórico: {max_historico:.1f}m (máximo de {len(df_maximos_hasta_fecha)} MDs)")
                print(f"     Fechas usadas: {df_maximos_hasta_fecha['fecha_md'].tolist()}")
                print(f"     Valores: {df_maximos_hasta_fecha['max_total_distance'].tolist()}")
                
                # Calcular porcentaje relativo al máximo histórico (igual que otras métricas)
                porcentaje = (valor / max_historico) * 100 if max_historico > 0 else 0
                
                # Redondear ANTES de asignar color (igual que resto de métricas)
                porcentaje_redondeado = round(porcentaje)
                
                print(f"     Porcentaje: {porcentaje:.2f}% → {porcentaje_redondeado}%")
                
                # Color: verde (55-70%), rojo_claro (<55%), rojo_oscuro (>70%)
                if 55 <= porcentaje_redondeado <= 70:
                    color = 'verde'
                elif porcentaje_redondeado < 55:
                    color = 'rojo_claro'
                else:  # > 70
                    color = 'rojo_oscuro'
                
                print(f"     Color: {color}")
                print(f"     📋 VALOR EN TABLA: {porcentaje_redondeado}%\n")
                
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
            print(f"  ❌ Error en {mc_id}: {e}")
            compensatorios[mc_id] = {
                'valor': None,
                'porcentaje': None,
                'color': 'gris'
            }
    
    print("\n" + "="*80)
    print(f"✅ COMPENSATORIOS CALCULADOS: {len(compensatorios)} microciclos")
    print("="*80 + "\n")
    
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
    print(f"📊 Cargando tabla evolutiva de microciclos...")
    
    engine = get_db_connection()
    if not engine:
        return None
    
    try:
        # Query 1: Obtener todos los microciclos de la temporada (ordenados cronológicamente)
        # Filtrar desde 08/08/2025 (inicio de temporada)
        query_microciclos = '''
            SELECT DISTINCT
                microciclo_id,
                microciclo_nombre,
                MIN(activity_date) as fecha_inicio,
                MAX(activity_date) as fecha_fin,
                MAX(CASE WHEN activity_tag = 'MD' THEN activity_date END) as fecha_md,
                MAX(CASE WHEN activity_tag = 'MD' THEN activity_name END) as partido_nombre
            FROM microciclos_metricas_procesadas
            WHERE athlete_position != 'Goal Keeper'
              AND activity_date >= '2025-08-08'
            GROUP BY microciclo_id, microciclo_nombre
            HAVING fecha_md IS NOT NULL
            ORDER BY fecha_inicio ASC
        '''
        
        df_microciclos = pd.read_sql(query_microciclos, engine)
        
        if df_microciclos.empty:
            print("  ⚠️ No se encontraron microciclos")
            return None
        
        print(f"  ✅ {len(df_microciclos)} microciclos encontrados")
        
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
        # Necesitamos el máximo histórico para calcular los %
        # IMPORTANTE: Usar los mismos filtros que en seguimiento de carga
        query_maximos = '''
            SELECT 
                activity_date as fecha_md,
                AVG(CASE WHEN field_time >= 4200 THEN total_distance * (5640/field_time) END) as max_total_distance,
                AVG(CASE WHEN field_time >= 4200 THEN distancia_21_kmh * (5640/field_time) END) as max_distancia_21_kmh,
                AVG(CASE WHEN field_time >= 4200 THEN distancia_24_kmh * (5640/field_time) END) as max_distancia_24_kmh,
                AVG(CASE WHEN field_time >= 4200 THEN acc_dec_total * (5640/field_time) END) as max_acc_dec_total,
                AVG(CASE WHEN field_time >= 4200 THEN ritmo_medio END) as max_ritmo_medio
            FROM microciclos_metricas_procesadas
            WHERE activity_tag = 'MD'
              AND athlete_position != 'Goal Keeper'
              AND field_time >= 4200
              AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
            GROUP BY activity_date
            ORDER BY activity_date DESC
        '''
        
        df_maximos = pd.read_sql(query_maximos, engine)
        
        print(f"  ✅ Datos cargados: {len(df_entrenamientos)} registros de entrenamientos")
        
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
            
            # Obtener máximos históricos hasta esta fecha (últimos 4 MDs)
            df_maximos_hasta_fecha = df_maximos[df_maximos['fecha_md'] <= fecha_md].head(4)
            
            # Calcular acumulado para cada métrica
            for metrica in metricas:
                col_avg = f'avg_{metrica}'
                col_max = f'max_{metrica}'
                
                # Ya NO es necesario agrupar porque SQL ya agrupa por activity_tag
                # SQL: GROUP BY microciclo_id, activity_tag
                # Resultado: 1 registro por (microciclo, activity_tag)
                
                # Obtener valores de entrenamientos (MD-X) - ya vienen agrupados de SQL
                valores_entrenamientos = df_mc[col_avg].dropna().tolist()
                
                if not valores_entrenamientos or df_maximos_hasta_fecha.empty:
                    acumulados[metrica][mc_id] = {
                        'acumulado': None,
                        'color': 'gris',
                        'min_umbral': None,
                        'max_umbral': None
                    }
                    continue
                
                # Obtener máximo histórico
                max_historico = df_maximos_hasta_fecha[col_max].max()
                
                if not max_historico or max_historico == 0:
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
        
        # Determinar tipo de microciclo basado en los DÍAS PRESENTES (igual que en Seguimiento de Carga)
        # Usar la misma lógica que detectar_tipo_microciclo()
        from pages.seguimiento_carga import detectar_tipo_microciclo
        
        for mc_info in microciclos_info:
            mc_id = mc_info['id']
            
            # Obtener días presentes en este microciclo desde df_entrenamientos
            df_mc = df_entrenamientos[df_entrenamientos['microciclo_id'] == mc_id]
            
            if df_mc.empty:
                mc_info['tipo_microciclo'] = 'especial'
                print(f"  📊 {mc_info['jornada']}: Sin entrenamientos → Tipo: especial")
                continue
            
            # Obtener lista de activity_tags únicos
            dias_presentes = df_mc['activity_tag'].unique().tolist()
            
            # Detectar tipo usando la misma función que el seguimiento de carga
            tipo = detectar_tipo_microciclo(dias_presentes)
            
            print(f"  📊 {mc_info['jornada']}: Días presentes {dias_presentes} → Tipo: {tipo}")
            mc_info['tipo_microciclo'] = tipo
        
        # Ahora asignar umbrales y colores basados en el tipo de microciclo
        from pages.seguimiento_carga import get_metricas_config_por_tipo
        
        for mc_info in microciclos_info:
            mc_id = mc_info['id']
            tipo = mc_info['tipo_microciclo']
            
            print(f"  🎨 Asignando colores para {mc_info['jornada']} (tipo: {tipo})")
            
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
                elif acumulado_val < min_umbral:
                    color = 'rojo_claro'  # Por debajo del mínimo
                elif acumulado_val <= max_umbral:
                    color = 'verde'  # Dentro del rango
                else:
                    color = 'rojo_oscuro'  # Por encima del máximo
                
                # Formatear valor para logging
                valor_str = f"{acumulado_val:.1f}" if acumulado_val is not None else "N/A"
                print(f"    • {metrica_id}: {valor_str}% -> {color} (min:{min_umbral}, max:{max_umbral})")
                
                acumulados[metrica_id][mc_id].update({
                    'color': color,
                    'min_umbral': min_umbral,
                    'max_umbral': max_umbral
                })
        
        print(f"  ✅ Acumulados calculados para {len(microciclos_info)} microciclos")
        
        return {
            'microciclos': microciclos_info,
            'acumulados': acumulados,
            'jugadores_ids': jugadores_ids  # Para cálculo de compensatorios
        }
        
    except Exception as e:
        print(f"  ❌ Error cargando tabla evolutiva: {e}")
        import traceback
        traceback.print_exc()
        return None
