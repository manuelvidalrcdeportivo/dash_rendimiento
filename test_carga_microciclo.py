"""
Test para verificar que el código de seguimiento de carga funciona correctamente
con los datos actualizados de la BD.
"""

from pages.seguimiento_carga_ultra_optimizado import cargar_microciclo_ultrarapido_v2
from utils.db_manager import get_db_connection
import pandas as pd

print("=" * 80)
print("TEST DE CARGA DE MICROCICLO")
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

print(f"\n✅ {len(jugadores_ids)} jugadores seleccionados para test")

# Test con un microciclo que SÍ tiene MD
microciclo_test = 'mc_2025-10-26_J11_RCD_Vs_R_VALLADOLID'

print(f"\n📊 Probando microciclo: {microciclo_test}")
print("-" * 80)

try:
    resultado = cargar_microciclo_ultrarapido_v2(microciclo_test, jugadores_ids)
    
    if resultado is None:
        print("❌ ERROR: La función retornó None")
    else:
        print("✅ Datos cargados correctamente")
        print(f"\n📈 RESULTADOS:")
        print(f"  - Nombre partido: {resultado.get('nombre_partido', 'N/A')}")
        print(f"  - Métricas procesadas: {len(resultado.get('datos_por_metrica', {}))}")
        print(f"  - Máximos históricos: {len(resultado.get('maximos_historicos', {}))}")
        
        # Verificar máximos históricos
        maximos = resultado.get('maximos_historicos', {})
        if maximos:
            print(f"\n🎯 MÁXIMOS HISTÓRICOS:")
            for metrica, datos in maximos.items():
                if datos:
                    print(f"  - {metrica}:")
                    print(f"      Max: {datos.get('max', 'N/A'):.2f}")
                    print(f"      Media: {datos.get('media', 'N/A'):.2f}")
                    print(f"      Partido: {datos.get('partido_max', 'N/A')}")
        else:
            print("\n⚠️ WARNING: No se calcularon máximos históricos")
        
        # Verificar datos por métrica
        datos_metricas = resultado.get('datos_por_metrica', {})
        if datos_metricas:
            print(f"\n📊 DATOS POR MÉTRICA:")
            for metrica, df in datos_metricas.items():
                if df is not None and not df.empty:
                    dias = df['activity_tag'].unique()
                    print(f"  - {metrica}: {len(dias)} días ({', '.join(dias)})")
                else:
                    print(f"  - {metrica}: Sin datos")
        else:
            print("\n⚠️ WARNING: No hay datos por métrica")
            
except Exception as e:
    print(f"❌ ERROR al cargar microciclo: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("FIN DEL TEST")
print("=" * 80)
