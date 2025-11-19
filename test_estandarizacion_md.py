"""
Test para verificar que el MD del EQUIPO se estandariza correctamente a 94 minutos
"""

from pages.seguimiento_carga_ultra_optimizado import cargar_microciclo_ultrarapido_v2
from utils.db_manager import get_db_connection
import pandas as pd

print("=" * 80)
print("TEST ESTANDARIZACIÓN MD - MODO EQUIPO")
print("=" * 80)

# Obtener lista de jugadores (sin porteros)
engine = get_db_connection()
query_jugadores = """
SELECT DISTINCT athlete_id, athlete_name
FROM microciclos_metricas_procesadas
WHERE athlete_position != 'Goal Keeper'
  AND activity_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
LIMIT 10
"""
df_jugadores = pd.read_sql(query_jugadores, engine)
jugadores_ids = df_jugadores['athlete_id'].tolist()

print(f"\n✅ {len(jugadores_ids)} jugadores seleccionados (MODO EQUIPO)")

# Test con un microciclo que tiene MD
microciclo_test = 'mc_2025-10-26_J11_RCD_Vs_R_VALLADOLID'

print(f"\n📊 Probando microciclo: {microciclo_test}")
print("-" * 80)

# Cargar datos del microciclo
resultado = cargar_microciclo_ultrarapido_v2(microciclo_test, jugadores_ids)

if resultado:
    # Obtener datos del MD para total_distance
    datos_total_distance = resultado['datos_por_metrica']['total_distance']
    df_md = datos_total_distance[datos_total_distance['activity_tag'] == 'MD']
    
    if not df_md.empty:
        valor_md_grafico = df_md['avg_metric'].iloc[0]
        num_jugadores = df_md['count_athletes'].iloc[0]
        
        print(f"\n📈 VALOR MD EN GRÁFICO (total_distance):")
        print(f"  - Valor mostrado: {valor_md_grafico:.2f} m")
        print(f"  - Jugadores: {num_jugadores}")
        
        # Obtener máximo histórico para comparar
        maximos = resultado['maximos_historicos']['total_distance']
        max_historico = maximos['max']
        
        print(f"\n🎯 MÁXIMO HISTÓRICO:")
        print(f"  - Valor: {max_historico:.2f} m")
        print(f"  - Partido: {maximos['partido_max']}")
        
        # Verificar datos RAW del MD
        df_raw = resultado['df_raw']
        df_md_raw = df_raw[df_raw['activity_tag'] == 'MD']
        
        if not df_md_raw.empty:
            print(f"\n🔍 DATOS RAW DEL MD:")
            
            # Todos los jugadores
            print(f"\n  TODOS LOS JUGADORES:")
            print(f"    - Total jugadores: {len(df_md_raw)}")
            print(f"    - Distancia promedio: {df_md_raw['total_distance'].mean():.2f} m")
            print(f"    - Minutos promedio: {df_md_raw['field_time'].mean()/60:.1f} min")
            
            # Solo +70 minutos
            df_md_70 = df_md_raw[df_md_raw['field_time'] >= 4200]
            print(f"\n  SOLO JUGADORES +70 MINUTOS:")
            print(f"    - Total jugadores: {len(df_md_70)}")
            print(f"    - Distancia promedio: {df_md_70['total_distance'].mean():.2f} m")
            print(f"    - Minutos promedio: {df_md_70['field_time'].mean()/60:.1f} min")
            
            # Estandarizado a 94'
            df_md_70_std = df_md_70.copy()
            df_md_70_std['total_distance_std'] = df_md_70_std['total_distance'] * (5640.0 / df_md_70_std['field_time'])
            print(f"\n  ESTANDARIZADO A 94 MINUTOS:")
            print(f"    - Distancia promedio: {df_md_70_std['total_distance_std'].mean():.2f} m")
            
            # Verificar si coincide
            diferencia = abs(valor_md_grafico - df_md_70_std['total_distance_std'].mean())
            
            print(f"\n✅ VERIFICACIÓN:")
            if diferencia < 1:
                print(f"  ✓ El valor del gráfico COINCIDE con el estandarizado (+70' a 94')")
                print(f"  ✓ Diferencia: {diferencia:.2f} m (despreciable)")
            else:
                print(f"  ✗ El valor del gráfico NO coincide")
                print(f"  ✗ Diferencia: {diferencia:.2f} m")
                print(f"  ✗ Esperado: {df_md_70_std['total_distance_std'].mean():.2f} m")
                print(f"  ✗ Obtenido: {valor_md_grafico:.2f} m")
    else:
        print("❌ No hay datos de MD en el resultado")
else:
    print("❌ Error al cargar microciclo")

print("\n" + "=" * 80)
print("FIN DEL TEST")
print("=" * 80)
