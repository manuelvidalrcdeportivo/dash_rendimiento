"""
Utilidades para configuración de métricas y detección de tipos de microciclo.
Código extraído de seguimiento_carga.py manteniendo la lógica exacta.
"""

from functools import lru_cache
from utils.db_manager import get_all_athletes


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


def get_metricas_disponibles():
    """
    Retorna la lista de métricas disponibles con sus propiedades.
    ÚNICA FUENTE DE VERDAD para las métricas del sistema.
    """
    return [
        {'id': 'total_distance', 'label': 'Distancia Total (m)', 'label_corto': 'Distancia Total', 'icon': 'fa-route'},
        {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h (m)', 'label_corto': 'Dist. +21 km/h', 'icon': 'fa-running'},
        {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h (m)', 'label_corto': 'Dist. +24 km/h', 'icon': 'fa-bolt'},
        {'id': 'acc_dec_total', 'label': 'Acel/Decel +3 (m/s²)', 'label_corto': 'Acel/Decel +3 (m/s²)', 'icon': 'fa-tachometer-alt'},
        {'id': 'ritmo_medio', 'label': 'Ritmo Medio (m/min.)', 'label_corto': 'Ritmo Medio (m/min.)', 'icon': 'fa-stopwatch'}
    ]


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


# Cache para datos de atletas (evita consultas repetidas)
@lru_cache(maxsize=1)
def get_cached_athletes():
    """Obtiene y cachea la lista de atletas"""
    return get_all_athletes()
