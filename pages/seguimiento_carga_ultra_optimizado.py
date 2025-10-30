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
          AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
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
                END) as avg_acc_dec
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
            for col in ['avg_total_distance', 'avg_distancia_21', 'avg_distancia_24', 'avg_acc_dec']:
                col_data = df_historicos[[col, 'activity_date', 'activity_name', 'microciclo_id']].dropna(subset=[col])
                if len(col_data) > 0:
                    # Mapear nombres de columna a nombres de métrica
                    metric_map = {
                        'avg_total_distance': 'total_distance',
                        'avg_distancia_21': 'distancia_21_kmh',
                        'avg_distancia_24': 'distancia_24_kmh',
                        'avg_acc_dec': 'acc_dec_total'
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
    df_entrenamientos = df_microciclo[
        (df_microciclo['activity_tag'] != 'MD') & 
        (df_microciclo['athlete_id'].isin(jugadores_ids))
    ].copy()
    
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
        df_metrica_entrenos = df_entrenamientos.groupby('activity_tag').agg({
            col_name: 'mean',
            'athlete_id': 'count',
            'activity_date': 'min'
        }).reset_index()
        df_metrica_entrenos.columns = ['activity_tag', 'avg_metric', 'count_athletes', 'fecha']
        
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
    
    return {
        'datos_por_metrica': datos_por_metrica,
        'maximos_historicos': maximos_historicos,
        'nombre_partido': nombre_partido,
        'df_raw': df_microciclo
    }
