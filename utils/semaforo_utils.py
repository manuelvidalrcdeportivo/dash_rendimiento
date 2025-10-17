# utils/semaforo_utils.py

"""
Utilidades para calcular estados de semáforo de todas las secciones
"""

import pandas as pd
from datetime import datetime
from utils.db_manager import get_evaluaciones_medicas, get_estadisticas_por_jugador, get_fechas_entrenamiento_disponibles
from utils.soccersystem_data import get_team_anthropometry_timeseries


def get_medico_status():
    """
    Calcula el estado del semáforo médico basado en las evaluaciones más recientes
    Usa la MISMA lógica que la sección médica existente
    NUEVA LÓGICA: Verde=0 jugadores en rojo, Amarillo=1-3 jugadores en rojo, Rojo=más de 3
    Returns: dict con 'color', 'estado', 'detalle'
    """
    try:
        # Obtener la fecha más reciente con evaluaciones
        fechas = get_fechas_entrenamiento_disponibles()
        
        if not fechas:
            return {
                'color': '#6c757d',  # Gris - sin datos
                'estado': 'SIN DATOS',
                'detalle': 'No hay evaluaciones médicas disponibles'
            }
        
        fecha_reciente = fechas[0]  # La más reciente
        df = get_evaluaciones_medicas(str(fecha_reciente))
        
        if df.empty:
            return {
                'color': '#6c757d',
                'estado': 'SIN DATOS', 
                'detalle': f'No hay evaluaciones para {fecha_reciente}'
            }
        
        # Contar jugadores en estado "Fisio/RTP" (rojo)
        jugadores_en_rojo = len(df[df['evaluacion'] == 'Fisio/RTP'])
        total_jugadores = len(df)
        
        
        # Aplicar nueva lógica según número de jugadores en rojo
        if jugadores_en_rojo == 0:
            return {
                'color': '#28a745',  # Verde
                'estado': 'ÓPTIMO',
                'detalle': f'Todos los {total_jugadores} jugadores están en estado normal'
            }
        elif 1 <= jugadores_en_rojo <= 3:
            return {
                'color': '#ffc107',  # Amarillo
                'estado': 'VIGILANCIA',
                'detalle': f'{jugadores_en_rojo} jugador(es) en fisio/RTP de {total_jugadores}'
            }
        else:  # más de 3 jugadores
            return {
                'color': '#dc3545',  # Rojo
                'estado': 'CRÍTICO',
                'detalle': f'{jugadores_en_rojo} jugadores en fisio/RTP de {total_jugadores}'
            }
            
    except Exception as e:
        print(f"Error calculando estado médico: {e}")
        import traceback
        traceback.print_exc()
        return {
            'color': '#6c757d',
            'estado': 'ERROR',
            'detalle': f'Error al calcular estado: {str(e)}'
        }


def get_nutricion_status():
    """
    Calcula el estado nutricional basado en datos antropométricos (% grasa corporal)
    Usa la MISMA lógica que la sección antropométrica existente
    Returns: dict con 'color', 'estado', 'detalle'
    """
    try:
        # Usar la misma lógica que estado_funcional_antropometrico.py
        from datetime import datetime
        import pandas as pd
        
        df_current = get_team_anthropometry_timeseries(category="Primer Equipo")
        
        if df_current is None or df_current.empty:
            return {
                'color': '#6c757d',  # Gris - sin datos
                'estado': 'SIN DATOS',
                'detalle': 'No hay datos antropométricos disponibles'
            }
        
        # Aplicar la misma lógica que en antropométrico
        df_current['fecha'] = pd.to_datetime(df_current['fecha'], format='%Y-%m-%d', errors='coerce')
        fecha_ultima_medicion = df_current['fecha'].max()
        
        # Filtrar por fecha más reciente y datos válidos de grasa
        mask = ((df_current['fecha'] == fecha_ultima_medicion) & 
                (df_current["pct_grasa"].notna()))
        df_display = df_current[mask].copy()
        
        if df_display.empty:
            return {
                'color': '#6c757d',
                'estado': 'SIN DATOS',
                'detalle': f'No hay datos de % grasa para {fecha_ultima_medicion.strftime("%d/%m/%Y")}'
            }
        
        # Calcular promedio de grasa (misma lógica que antropométrico)
        grasa_col = df_display.loc[df_display["pct_grasa"].notna(), "pct_grasa"]
        promedio_grasa = grasa_col.mean()
        total_jugadores = len(grasa_col)
        
        
        # Aplicar LOS MISMOS umbrales que en antropométrico
        if promedio_grasa <= 10.0:
            return {
                'color': '#28a745',  # Verde - ÓPTIMO
                'estado': 'ÓPTIMO',
                'detalle': f'Promedio grasa corporal: {promedio_grasa:.1f}% ({total_jugadores} jugadores)'
            }
        elif promedio_grasa <= 10.5:
            return {
                'color': '#ffc107',  # Amarillo - VIGILANCIA (antes era "ACEPTABLE")
                'estado': 'VIGILANCIA',
                'detalle': f'Promedio grasa corporal: {promedio_grasa:.1f}% ({total_jugadores} jugadores)'
            }
        else:
            return {
                'color': '#dc3545',  # Rojo - CRÍTICO (antes era "ALTO")
                'estado': 'CRÍTICO',
                'detalle': f'Promedio grasa corporal: {promedio_grasa:.1f}% ({total_jugadores} jugadores)'
            }
            
    except Exception as e:
        print(f"Error calculando estado nutricional: {e}")
        import traceback
        traceback.print_exc()
        return {
            'color': '#6c757d',
            'estado': 'ERROR',
            'detalle': f'Error al calcular estado: {str(e)}'
        }


def get_psicologico_status():
    """
    Estado psicológico - placeholder por desarrollar
    """
    return {
        'color': '#6c757d',  # Gris - en desarrollo
        'estado': 'EN DESARROLLO',
        'detalle': 'Sección psicológica en desarrollo'
    }


def get_capacidad_status():
    """
    Estado capacidad funcional - placeholder por desarrollar
    """
    return {
        'color': '#6c757d',  # Gris - en desarrollo
        'estado': 'EN DESARROLLO', 
        'detalle': 'Sección capacidad funcional en desarrollo'
    }


def get_entrenamiento_status():
    """
    Estado control proceso entrenamiento - placeholder por desarrollar
    """
    return {
        'color': '#6c757d',  # Gris - en desarrollo
        'estado': 'EN DESARROLLO',
        'detalle': 'Control proceso entrenamiento en desarrollo'
    }


def get_competicion_status():
    """
    Estado rendimiento competición - basado en el Ranking Rendimiento de indicadores de rendimiento
    Usa la misma lógica de colores que evolutivo temporada:
    - Ranking 1-6: Verde (ÓPTIMO)
    - Ranking 7-16: Amarillo (VIGILANCIA)
    - Ranking 17-22: Rojo (CRÍTICO)
    """
    try:
        from utils.db_manager import get_laliga_db_connection
        import pandas as pd
        
        # Obtener el ranking global desde indicadores_rendimiento
        engine = get_laliga_db_connection()
        
        if not engine:
            return {
                'color': '#6c757d',
                'estado': 'SIN DATOS',
                'detalle': 'No se puede conectar a la base de datos'
            }
        
        query = """
        SELECT 
            team_name,
            ranking_position,
            metric_value
        FROM indicadores_rendimiento 
        WHERE metric_id = 'RankingRendimiento'
        AND team_name = 'RC Deportivo'
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return {
                'color': '#6c757d',
                'estado': 'SIN DATOS',
                'detalle': 'No hay datos de Ranking Rendimiento disponibles'
            }
        
        ranking = int(df.iloc[0]['ranking_position'])
        valor = df.iloc[0]['metric_value']
        
        # Aplicar la misma lógica de colores que evolutivo temporada (pero con colores unificados del semáforo)
        if ranking <= 6:
            color = '#28a745'  # Verde oscuro (igual que nutrición/médico)
            estado = 'ÓPTIMO'
            descripcion = f'Ranking Rendimiento: {ranking}º posición (Top 6)'
        elif ranking <= 16:
            color = '#ffc107'  # Amarillo (igual que nutrición/médico)
            estado = 'VIGILANCIA'
            descripcion = f'Ranking Rendimiento: {ranking}º posición (Medio-Alto)'
        else:
            color = '#dc3545'  # Rojo (igual que nutrición/médico)
            estado = 'CRÍTICO'
            descripcion = f'Ranking Rendimiento: {ranking}º posición (Descenso)'
        
        return {
            'color': color,
            'estado': estado,
            'detalle': descripcion
        }
        
    except Exception as e:
        print(f"Error calculando estado competición: {e}")
        import traceback
        traceback.print_exc()
        return {
            'color': '#6c757d',
            'estado': 'ERROR',
            'detalle': f'Error al calcular estado: {str(e)}'
        }


def get_all_semaforo_status():
    """
    Obtiene el estado de todas las secciones del semáforo
    Returns: dict con todas las secciones
    """
    return {
        'competicion': get_competicion_status(),
        'entrenamiento': get_entrenamiento_status(),
        'nutricion': get_nutricion_status(),
        'psicologico': get_psicologico_status(),
        'medico': get_medico_status(),
        'capacidad': get_capacidad_status()
    }


def get_estado_general():
    """
    Calcula un estado general basado en todas las secciones
    Returns: dict con color y estado general
    """
    estados = get_all_semaforo_status()
    
    # Contar estados por color (prioridad: rojo > amarillo > verde > gris)
    colores = [estado['color'] for estado in estados.values()]
    
    # Si hay algún rojo, estado general es crítico
    if '#dc3545' in colores:
        return {
            'color': '#dc3545',
            'estado': 'REQUIERE ATENCIÓN',
            'detalle': 'Una o más áreas necesitan atención inmediata'
        }
    # Si hay amarillo, estado es de vigilancia
    elif '#ffc107' in colores:
        return {
            'color': '#ffc107',
            'estado': 'VIGILANCIA',
            'detalle': 'Algunas áreas requieren seguimiento'
        }
    # Si solo hay verdes, estado óptimo
    elif '#28a745' in colores and '#6c757d' not in colores:
        return {
            'color': '#28a745',
            'estado': 'ÓPTIMO',
            'detalle': 'Todas las áreas evaluadas en buen estado'
        }
    # Si hay verdes y grises (en desarrollo)
    elif '#28a745' in colores:
        return {
            'color': '#28a745',
            'estado': 'PARCIAL',
            'detalle': 'Áreas evaluadas en buen estado, otras en desarrollo'
        }
    # Solo grises (todo en desarrollo)
    else:
        return {
            'color': '#6c757d',
            'estado': 'EN DESARROLLO',
            'detalle': 'La mayoría de secciones están en desarrollo'
        }
