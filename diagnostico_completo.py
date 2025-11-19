from utils.db_manager import get_db_connection
import pandas as pd

engine = get_db_connection()

print("=" * 80)
print("DIAGNÓSTICO COMPLETO - SEGUIMIENTO DE CARGA")
print("=" * 80)

# 1. Verificar microciclos recientes
print("\n1. MICROCICLOS DISPONIBLES (últimos 60 días):")
print("-" * 80)
query1 = """
SELECT 
    microciclo_id,
    MIN(activity_date) as fecha_inicio,
    MAX(activity_date) as fecha_fin,
    COUNT(DISTINCT activity_tag) as num_tags,
    GROUP_CONCAT(DISTINCT activity_tag ORDER BY activity_tag) as tags,
    SUM(CASE WHEN activity_tag = 'MD' THEN 1 ELSE 0 END) as tiene_md
FROM microciclos_metricas_procesadas
WHERE activity_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
GROUP BY microciclo_id
ORDER BY fecha_inicio DESC
"""
df1 = pd.read_sql(query1, engine)
print(df1.to_string())

# 2. Verificar el microciclo más reciente con detalle
if not df1.empty:
    mc_reciente = df1.iloc[0]['microciclo_id']
    print(f"\n2. DETALLE DEL MICROCICLO MÁS RECIENTE: {mc_reciente}")
    print("-" * 80)
    
    query2 = f"""
    SELECT 
        activity_tag,
        activity_name,
        activity_date,
        COUNT(DISTINCT athlete_id) as num_jugadores,
        AVG(total_distance) as avg_distancia,
        AVG(field_time) as avg_minutos
    FROM microciclos_metricas_procesadas
    WHERE microciclo_id = '{mc_reciente}'
    GROUP BY activity_tag, activity_name, activity_date
    ORDER BY activity_date
    """
    df2 = pd.read_sql(query2, engine)
    print(df2.to_string())

# 3. Verificar si hay MDs en general
print("\n3. TODOS LOS MDs REGISTRADOS (últimos 60 días):")
print("-" * 80)
query3 = """
SELECT 
    microciclo_id,
    activity_tag,
    activity_name,
    activity_date,
    COUNT(DISTINCT athlete_id) as num_jugadores,
    AVG(field_time) as avg_minutos
FROM microciclos_metricas_procesadas
WHERE activity_tag = 'MD'
  AND activity_date >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
GROUP BY microciclo_id, activity_tag, activity_name, activity_date
ORDER BY activity_date DESC
"""
df3 = pd.read_sql(query3, engine)
print(df3.to_string())

# 4. Verificar actividades "Unknown"
print("\n4. ACTIVIDADES CON TAG 'Unknown':")
print("-" * 80)
query4 = """
SELECT 
    microciclo_id,
    activity_name,
    activity_date,
    COUNT(DISTINCT athlete_id) as num_jugadores,
    AVG(field_time) as avg_minutos
FROM microciclos_metricas_procesadas
WHERE activity_tag = 'Unknown'
  AND activity_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY microciclo_id, activity_name, activity_date
ORDER BY activity_date DESC
LIMIT 10
"""
df4 = pd.read_sql(query4, engine)
print(df4.to_string())

# 5. Verificar cómo se está poblando la tabla
print("\n5. PROCESO DE POBLACIÓN DE LA TABLA:")
print("-" * 80)
print("La tabla 'microciclos_metricas_procesadas' se puebla desde:")
print("  - Tabla 'activities' (actividades originales)")
print("  - Tabla 'activity_athletes' (métricas por jugador)")
print("")
print("PROBLEMA DETECTADO:")
print("  ✗ Los microciclos NO tienen actividades con tag 'MD' (partido)")
print("  ✗ Solo tienen entrenamientos (MD-1, MD-2, MD-3, MD-4, MD+1, etc.)")
print("  ✗ Algunos tienen tag 'Unknown' que podrían ser partidos")
print("")
print("POSIBLES CAUSAS:")
print("  1. El script que procesa las actividades NO está identificando los partidos")
print("  2. Los partidos tienen un tag diferente en la tabla 'activities'")
print("  3. Los partidos no se están incluyendo en los microciclos")
print("  4. Cambió la lógica de asignación de tags en el procesamiento")

print("\n" + "=" * 80)
print("FIN DEL DIAGNÓSTICO")
print("=" * 80)
