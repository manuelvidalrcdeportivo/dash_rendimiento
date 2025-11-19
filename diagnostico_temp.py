from utils.db_manager import get_db_connection
import pandas as pd

engine = get_db_connection()

# Verificar partidos en activities
query = """
SELECT 
    id,
    name,
    start_time
FROM activities
WHERE start_time >= DATE_SUB(CURDATE(), INTERVAL 60 DAY)
  AND (name LIKE '%%Vs%%' OR name LIKE '%%J%%')
ORDER BY start_time DESC
LIMIT 10
"""

print('=== PARTIDOS EN TABLA activities ===')
df = pd.read_sql(query, engine)
print(df.to_string())

# Verificar si esos partidos están en microciclos_metricas_procesadas
if not df.empty:
    activity_ids = "','".join(df['id'].tolist())
    query2 = f"""
    SELECT DISTINCT
        activity_id,
        activity_name,
        activity_tag,
        microciclo_id,
        activity_date
    FROM microciclos_metricas_procesadas
    WHERE activity_id IN ('{activity_ids}')
    """
    
    print('\n=== ESOS PARTIDOS EN microciclos_metricas_procesadas ===')
    df2 = pd.read_sql(query2, engine)
    print(df2.to_string())
