"""
Utilidades para generación de gráficos de carga de entrenamiento.
Código extraído de seguimiento_carga.py manteniendo la lógica exacta.
"""

import pandas as pd
import plotly.graph_objects as go
import re
from utils.entrenamiento_metricas import detectar_tipo_microciclo


def generar_grafico_optimizado_precargado(df_summary, metric, metrica_label, maximos_historicos, umbrales_df, nombre_partido):
    """
    Versión ultra-optimizada que genera gráficos directamente desde datos ya procesados.
    NO hace ninguna query adicional. Umbrales hardcodeados.
    
    Esta es la función EXACTA del archivo original (líneas 1203-1614).
    """
    
    # Determinar unidad
    unidad = " m" if "(m)" in metrica_label else ""
    
    # Ordenar días según lógica MD
    orden_dias = ["MD", "MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "Sin clasificar"]
    dias_con_datos = df_summary['activity_tag'].unique().tolist()
    dias_ordenados = [d for d in orden_dias if d in dias_con_datos]
    
    # Colores en escala de azules (igual que original)
    colores_azules = {
        'MD-6': '#A8DADC',
        'MD-5': '#86C5D8',
        'MD-4': '#64B0D4',
        'MD-3': '#479FCD',
        'MD-2': '#2B8DC6',
        'MD-1': '#1E78B4',
        'MD': '#0d3b66'
    }
    
    # Obtener máximos históricos
    max_historico_md = maximos_historicos.get('max') if maximos_historicos else None
    min_historico_md = maximos_historicos.get('min') if maximos_historicos else None
    
    # Crear gráfico
    fig = go.Figure()
    
    # Añadir cada día como barra (LÓGICA EXACTA DEL ORIGINAL)
    for _, row in df_summary.iterrows():
        dia = row['activity_tag']
        valor = row['avg_metric']
        num_jugadores = row['count_athletes']
        
        # Obtener fecha si está disponible
        fecha_str = ""
        if 'fecha' in row and pd.notna(row['fecha']):
            try:
                fecha = pd.to_datetime(row['fecha'])
                fecha_str = f"<br>Fecha: <b>{fecha.strftime('%d/%m/%Y')}</b>"
            except:
                pass
        
        # Obtener minutos jugados si está disponible (para jugador individual)
        minutos_str = ""
        if 'field_time' in row and pd.notna(row['field_time']) and dia == 'MD':
            minutos = int(row['field_time'] / 60)  # Convertir segundos a minutos
            minutos_str = f"<br>Minutos jugados: <b>{minutos}'</b>"
        
        # Determinar visibilidad por defecto (solo días MD-X y MD)
        es_dia_md = bool(re.match(r'^MD[-+]?\d*$', dia))
        visible_por_defecto = True if es_dia_md else 'legendonly'
        
        # Color según el día
        color = colores_azules.get(dia, '#6c757d')
        
        # Calcular % sobre MÁXIMO HISTÓRICO (línea naranja) si aplica
        porcentaje_md = ""
        if max_historico_md and max_historico_md > 0:
            pct = (valor / max_historico_md) * 100
            if dia == 'MD':
                # Para MD, solo mostrar el nombre del partido
                if nombre_partido:
                    porcentaje_md = f"<br><b>{nombre_partido}</b>"
                else:
                    porcentaje_md = ""
            else:
                porcentaje_md = f"<br>% sobre máx histórico: <b>{pct:.1f}%</b>"
        
        # Tooltip - Diferenciar entre equipo (Media) y jugador individual (Valor individual)
        if num_jugadores == 1:
            tipo_valor = "Valor individual"
            info_jugadores = ""  # No mostrar "Jugadores: 1"
        else:
            tipo_valor = "Media equipo"
            info_jugadores = f"<br>Jugadores: {num_jugadores}"
        
        hovertemplate = f"<b>{dia}</b>" + \
                      fecha_str + \
                      minutos_str + \
                      f"<br>{metrica_label} ({tipo_valor}): <b>{valor:.1f}{unidad}</b>" + \
                      porcentaje_md + \
                      info_jugadores + \
                      "<br><extra></extra>"
        
        # Añadir barra con texto del % sobre máximo histórico
        text_label = f"{valor:.1f}{unidad}"
        if max_historico_md and max_historico_md > 0 and dia != 'MD':
            pct = (valor / max_historico_md) * 100
            text_label = f"{pct:.0f}%"  # Mostrar % en la barra
        
        fig.add_trace(go.Bar(
            name=dia,
            x=[dia],
            y=[valor],
            marker=dict(
                color=color,
                line=dict(color='#0d3b66' if dia == 'MD' else color, width=1.5)
            ),
            text=[text_label],
            textposition="outside",
            hovertemplate=hovertemplate,
            visible=visible_por_defecto,
            showlegend=True
        ))
    
    # AÑADIR UMBRALES POR DÍA - RELATIVOS AL MÁXIMO HISTÓRICO (línea naranja)
    # Multiplicadores por métrica (relativos a la línea naranja = 100%)
    # UMBRALES SEGÚN TIPO DE MICROCICLO (CÓDIGO EXACTO LÍNEAS 1312-1432)
    
    umbrales_estandar = {
        'total_distance': {
            'MD-4': {'min': 0.45, 'max': 0.6},
            'MD-3': {'min': 0.65, 'max': 0.80},
            'MD-2': {'min': 0.35, 'max': 0.5},
            'MD-1': {'min': 0.25, 'max': 0.4}
        },
        'distancia_21_kmh': {
            'MD-4': {'min': 0.20, 'max': 0.30},
            'MD-3': {'min': 0.5, 'max': 0.8},
            'MD-2': {'min': 0.15, 'max': 0.3},
            'MD-1': {'min': 0.15, 'max': 0.3}
        },
        'distancia_24_kmh': {
            'MD-4': {'min': 0.20, 'max': 0.4},
            'MD-3': {'min': 0.40, 'max': 0.60},
            'MD-2': {'min': 0.10, 'max': 0.2},
            'MD-1': {'min': 0.10, 'max': 0.2}
        },
        'acc_dec_total': {
            'MD-4': {'min': 0.75, 'max': 1},
            'MD-3': {'min': 0.5, 'max': 0.7},
            'MD-2': {'min': 0.35, 'max': 0.65},
            'MD-1': {'min': 0.3, 'max': 0.55}
        },
        'ritmo_medio': {
            'MD-4': {'min': 0.65, 'max': 0.80},
            'MD-3': {'min': 0.70, 'max': 0.90},
            'MD-2': {'min': .45, 'max': 0.70},
            'MD-1': {'min': 0.40, 'max': 0.60}
        }
    }
    
    umbrales_extendido = {
        'total_distance': {
            'MD-5': {'min': 0.30, 'max': 0.50},
            'MD-4': {'min': 0.45, 'max': 0.60},
            'MD-3': {'min': 0.65, 'max': 0.80},
            'MD-2': {'min': 0.35, 'max': 0.50},
            'MD-1': {'min': 0.25, 'max': 0.40}
        },
        'distancia_21_kmh': {
            'MD-5': {'min': 0.10, 'max': 0.30},
            'MD-4': {'min': 0.20, 'max': 0.30},
            'MD-3': {'min': 0.50, 'max': 0.80},
            'MD-2': {'min': 0.10, 'max': 0.25},
            'MD-1': {'min': 0.10, 'max': 0.25}
        },
        'distancia_24_kmh': {
            'MD-5': {'min': 0.10, 'max': 0.20},
            'MD-4': {'min': 0.10, 'max': 0.20},
            'MD-3': {'min': 0.40, 'max': 0.60},
            'MD-2': {'min': 0.10, 'max': 0.20},
            'MD-1': {'min': 0.10, 'max': 0.20}
        },
        'acc_dec_total': {
            'MD-5': {'min': 0.65, 'max': 0.90},
            'MD-4': {'min': 0.75, 'max': 1.00},
            'MD-3': {'min': 0.50, 'max': 0.70},
            'MD-2': {'min': 0.30, 'max': 0.65},
            'MD-1': {'min': 0.30, 'max': 0.55}
        },
        'ritmo_medio': {
            'MD-5': {'min': 0.55, 'max': 0.75},
            'MD-4': {'min': 0.65, 'max': 0.80},
            'MD-3': {'min': 0.70, 'max': 0.90},
            'MD-2': {'min': 0.45, 'max': 0.70},
            'MD-1': {'min': 0.40, 'max': 0.60}
        }
    }
    
    umbrales_reducido = {
        'total_distance': {
            'MD-3': {'min': 0.65, 'max': 0.8},
            'MD-2': {'min': 0.35, 'max': 0.5},
            'MD-1': {'min': 0.25, 'max': 0.40}
        },
        'distancia_21_kmh': {
            'MD-3': {'min': 0.50, 'max': 0.80},
            'MD-2': {'min': 0.10, 'max': 0.25},
            'MD-1': {'min': 0.1, 'max': 0.25}
        },
        'distancia_24_kmh': {
            'MD-3': {'min': 0.40, 'max': 0.60},
            'MD-2': {'min': 0.10, 'max': 0.20},
            'MD-1': {'min': 0.10, 'max': 0.20}
        },
        'acc_dec_total': {
            'MD-3': {'min': 0.50, 'max': 0.70},
            'MD-2': {'min': 0.35, 'max': 0.65},
            'MD-1': {'min': 0.30, 'max': 0.55}
        },
        'ritmo_medio': {
            'MD-3': {'min': 0.70, 'max': 0.90},
            'MD-2': {'min': 0.45, 'max': 0.75},
            'MD-1': {'min': 0.35, 'max': 0.60}
        }
    }
    
    umbrales_superrecortado = {
        'total_distance': {
            'MD-2': {'min': 0.35, 'max': 0.6},
            'MD-1': {'min': 0.50, 'max': 0.90}
        },
        'distancia_21_kmh': {
            'MD-2': {'min': 0.10, 'max': 0.30},
            'MD-1': {'min': 0.10, 'max': 0.30}
        },
        'distancia_24_kmh': {
            'MD-2': {'min': 0.10, 'max': 0.20},
            'MD-1': {'min': 0.10, 'max': 0.20}
        },
        'acc_dec_total': {
            'MD-2': {'min': 0.35, 'max': 0.65},
            'MD-1': {'min': 0.30, 'max': 0.55}
        },
        'ritmo_medio': {
            'MD-2': {'min': 0.45, 'max': 0.75},
            'MD-1': {'min': 0.35, 'max': 0.55}
        }
    }
    
    # Detectar tipo de microciclo (solo si no viene en maximos_historicos)
    if maximos_historicos and 'tipo_microciclo' in maximos_historicos:
        tipo_microciclo = maximos_historicos['tipo_microciclo']
    else:
        tipo_microciclo = detectar_tipo_microciclo(dias_ordenados)
    
    # Seleccionar umbrales según tipo
    if tipo_microciclo == 'extendido':
        umbrales_multiplicadores = umbrales_extendido
    elif tipo_microciclo == 'superrecortado':
        umbrales_multiplicadores = umbrales_superrecortado
    elif tipo_microciclo == 'reducido':
        umbrales_multiplicadores = umbrales_reducido
    else:
        umbrales_multiplicadores = umbrales_estandar
    
    # Solo aplicar umbrales si tenemos máximo histórico (línea naranja)
    if max_historico_md and max_historico_md > 0 and metric in umbrales_multiplicadores:
        umbrales_metrica = umbrales_multiplicadores[metric]
        umbrales_añadidos = False
        
        for idx, dia in enumerate(dias_ordenados):
            if dia in umbrales_metrica:
                # Calcular valores absolutos a partir de multiplicadores
                min_val = max_historico_md * umbrales_metrica[dia]['min']
                max_val = max_historico_md * umbrales_metrica[dia]['max']
                
                # Rectángulo de rango recomendado
                fig.add_shape(
                    type="rect",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=min_val, y1=max_val,
                    fillcolor="rgba(200, 255, 200, 0.3)",
                    line=dict(width=0),
                    layer="below"
                )
                
                # Línea máximo (roja)
                fig.add_shape(
                    type="line",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=max_val, y1=max_val,
                    line=dict(color="rgba(255, 0, 0, 0.9)", width=3),
                )
                
                # Línea mínimo (roja)
                fig.add_shape(
                    type="line",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=min_val, y1=min_val,
                    line=dict(color="rgba(255, 0, 0, 0.9)", width=3),
                )
                
                umbrales_añadidos = True
        
        # Añadir leyendas para umbrales
        if umbrales_añadidos:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color='rgba(255, 0, 0, 0.9)'),
                name='Máximo recomendado',
                showlegend=True
            ))
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color='rgba(255, 0, 0, 0.9)'),
                name='Mínimo recomendado',
                showlegend=True
            ))
    
    # UMBRALES PARA COMPENSATORIOS (MD+X): 55%-70% para todas las métricas
    if max_historico_md and max_historico_md > 0:
        for idx, dia in enumerate(dias_ordenados):
            # Detectar si es compensatorio (MD+1, MD+2, MD+3, etc.)
            if re.match(r'^MD\+\d+$', dia):
                # Umbrales fijos: 55%-70% del máximo histórico
                min_val_comp = max_historico_md * 0.55
                max_val_comp = max_historico_md * 0.70
                
                # Rectángulo de rango recomendado (color diferente para distinguir)
                fig.add_shape(
                    type="rect",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=min_val_comp, y1=max_val_comp,
                    fillcolor="rgba(173, 216, 230, 0.3)",  # Azul claro
                    line=dict(width=0),
                    layer="below"
                )
                
                # Línea máximo (azul)
                fig.add_shape(
                    type="line",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=max_val_comp, y1=max_val_comp,
                    line=dict(color="rgba(70, 130, 180, 0.9)", width=3),  # Azul acero
                )
                
                # Línea mínimo (azul)
                fig.add_shape(
                    type="line",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=min_val_comp, y1=min_val_comp,
                    line=dict(color="rgba(70, 130, 180, 0.9)", width=3),  # Azul acero
                )
    
    # Añadir línea naranja del máximo SOBRE el MD
    if max_historico_md and 'MD' in dias_ordenados:
        try:
            idx_md = dias_ordenados.index('MD')
            
            # Detectar si es jugador individual o equipo
            # Un jugador individual siempre tiene num_partidos definido (aunque sea 0)
            es_individual = maximos_historicos and 'num_partidos' in maximos_historicos
            
            if es_individual:
                # Jugador individual: máximo absoluto de la temporada
                partido_max_label = f"Mejor marca: {maximos_historicos['partido_max']} (100%)"
                hover_title = "<b>Mejor marca personal</b>"
                num_partidos = maximos_historicos.get('num_partidos', 0)
                hover_info = f"{num_partidos} partido{'s' if num_partidos != 1 else ''} +70' en temporada"
            else:
                # Equipo: promedio últimos 4 MDs
                partido_max_label = "Máx últimos 4 MDs (100%)"
                hover_title = "<b>Máximo de últimos 4 MDs</b>"
                hover_info = "Promedio equipo"
            
            # Añadir línea naranja como shape (más visible)
            fig.add_shape(
                type="line",
                x0=idx_md-0.35, x1=idx_md+0.35,
                y0=max_historico_md, y1=max_historico_md,
                line=dict(color="rgba(255, 150, 0, 0.9)", width=4),
                layer="above"
            )
            
            # Añadir trace invisible para el hover y leyenda
            fig.add_trace(go.Scatter(
                x=['MD'],
                y=[max_historico_md],
                mode='markers',
                marker=dict(size=0.1, color="rgba(255, 150, 0, 0.9)"),
                name=partido_max_label,
                hovertemplate=f"{hover_title}<br>" +
                             (f"Partido: <b>{maximos_historicos.get('partido_max')}</b><br>" if maximos_historicos and maximos_historicos.get('partido_max') else "") +
                             f"Valor: <b>{max_historico_md:.1f}{unidad}</b><br>" +
                             f"{hover_info}<br>" +
                             "Referencia para los % (100%)<extra></extra>",
                showlegend=True
            ))
        except Exception as e:
            print(f"⚠️ Error añadiendo línea naranja: {e}")
    
    # Layout (EXACTO DEL ORIGINAL)
    fig.update_layout(
        title=None,
        xaxis=dict(
            title=dict(
                text="Día del microciclo",
                font=dict(size=13, color="#1e3d59", family="Montserrat")
            ),
            tickfont=dict(size=11, family="Montserrat"),
            categoryorder='array',
            categoryarray=dias_ordenados
        ),
        yaxis=dict(
            title=dict(
                text=metrica_label,  # Sin unidad aquí
                font=dict(size=13, color="#1e3d59", family="Montserrat")
            ),
            tickfont=dict(size=11, family="Montserrat"),
            rangemode='tozero'
        ),
        bargap=0.3,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=550,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#e0e0e0",
            borderwidth=1,
            font=dict(size=11, family="Montserrat")
        ),
        margin=dict(t=40, b=120, l=80, r=40),
        font=dict(family="Montserrat"),
        barmode='group'
    )
    
    return fig
