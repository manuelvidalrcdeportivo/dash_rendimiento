"""
Evolutivo Temporada (Competición): Visualización tipo ranking por métrica.
- Lee tabla indicadores_rendimiento (metrica, valor, ranking)
- Dibuja un grid (22 filas = rangos 1..22, columnas = métricas)
- Para cada métrica, rellena desde abajo hasta 'ranking' (ranking=1 rellena toda la columna)
- Colores: 1-6 verde, 7-16 amarillo, 17-22 rojo. Celdas vacías gris claro.
"""

from dash import html, dcc
from utils.layouts import standard_page
from utils.db_manager import get_db_connection, get_laliga_db_connection, get_indicadores_rendimiento_laliga, get_available_teams_laliga, get_available_metrics_laliga, get_all_teams_rankings_laliga, get_rankings_compuestos_laliga
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import inspect


def fetch_indicadores_rendimiento_laliga(team_name="RC Deportivo"):
    """Obtiene metrica, valor, ranking desde la BD LaLiga para un equipo específico."""
    try:
        df = get_indicadores_rendimiento_laliga(team_name)
        
        if df.empty:
            raise RuntimeError("Sin datos en LaLiga")
        
        # Filtrar solo las métricas definidas en los grupos
        df_filtered = filter_metrics_by_groups(df)
        
        if df_filtered.empty:
            raise RuntimeError("Sin métricas válidas")
        
        return df_filtered
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo indicadores de LaLiga: {e}")
        return None

def filter_metrics_by_groups(df):
    """
    Filtra las métricas del DataFrame para incluir solo las definidas en GROUPS_ORIGINAL
    y aplica el mapeo a nombres cortos.
    """
    if df.empty:
        return df
    
    # Obtener todas las métricas definidas en los grupos originales
    all_group_metrics = []
    for _, metrics in GROUPS_ORIGINAL:
        all_group_metrics.extend(metrics)
    
    # Filtrar el DataFrame para incluir solo las métricas de los grupos
    filtered_df = df[df['metrica'].isin(all_group_metrics)].copy()
    
    if len(filtered_df) < len(all_group_metrics):
        missing_metrics = set(all_group_metrics) - set(filtered_df['metrica'].tolist())
    
    # Aplicar mapeo a nombres cortos
    filtered_df['metrica_original'] = filtered_df['metrica']  # Guardar nombre original
    filtered_df['metrica'] = filtered_df['metrica'].map(METRIC_NAME_MAPPING).fillna(filtered_df['metrica'])
    
    
    return filtered_df

# ELIMINADAS funciones de fallback con datos falsos - nunca se deben mostrar datos inventados

def fetch_indicadores_rendimiento(team_name="RC Deportivo"):
    """Función principal que intenta LaLiga primero, luego VALD si existe.
    Si no hay conexión a BD, retorna DataFrame vacío - NUNCA datos inventados."""
    try:
        # Intentar primero con LaLiga
        df = fetch_indicadores_rendimiento_laliga(team_name)
        if df is not None and not df.empty:
            return df
    except Exception as e:
        print(f"Error conectando a LaLiga DB: {e}")
    
    # Intentar VALD solo si la tabla existe
    try:
        engine = get_db_connection()
        if engine is not None:
            insp = inspect(engine)
            if 'indicadores_rendimiento' in insp.get_table_names():
                df = pd.read_sql("SELECT metrica, valor, ranking FROM indicadores_rendimiento", engine)
                df['ranking'] = pd.to_numeric(df['ranking'], errors='coerce').astype('Int64')
                df = df.dropna(subset=['metrica', 'ranking'])
                if not df.empty:
                    return df
    except Exception as e:
        print(f"Error conectando a VALD DB: {e}")
    
    # Sin conexión - retornar DataFrame vacío
    print("[ERROR] No se pudo conectar a ninguna base de datos")
    return pd.DataFrame(columns=["metrica", "valor", "ranking"])


def _band_for_rank(rank: int) -> int:
    """Devuelve banda de color: 1=verde(1-6), 2=amarillo(7-16), 3=rojo(17-22)."""
    if 1 <= rank <= 6:
        return 1
    if 7 <= rank <= 16:
        return 2
    if 17 <= rank <= 22:
        return 3
    return 0


# Mapeo de nombres originales LaLiga a nombres cortos para visualización
METRIC_NAME_MAPPING = {
    # Estilo
    "Iniciativa de Juego (Puntos)": "Iniciativa de Juego",
    "Posesión del Balón (%)": "Posesión del Balón",
    "Centroide colectivo global": "Centroide colectivo",
    "Recuperaciones en campo contrario (% Total)": "% Recup. campo contrario",
    
    # Rendimiento ofensivo
    "Eficacia Construcción Ofensiva (%)": "Eficacia Construcción Of. (%)",
    "Eficacia Finalización (%)": "Eficacia Finalización (%)",
    "Expected Goals (xG)": "Xg a Favor",
    "Goles a favor (Nº)": "Goles a favor",
    
    # Rendimiento defensivo
    "Eficacia Contención Defensiva (%)": "Eficacia Contención Def. (%)",
    "Eficacia Evitación (%)": "Eficacia Evitación (%)",
    "Expected Goals en Contra (xG)": "xG en Contra",
    "Goles en contra Totales (Nº)": "Goles en contra",
    
    # Rendimiento físico
    "Distancia Total Recorrida (m.)": "Distancia Total",
    "Distancia Recorrida > 21 km/h (m.)": "Distancia > 21 km/h",
    "Distancia High Sprint > 24 km/h (m.)": "Distancia > 24 km/h (m.)",
    
    # Balón Parado
    "Expected Goals Balón Parado sin Penaltis (xG)": "xG S.P A.B.P",
    "Goles a favor Balón Parado sin Penaltis (Nº)": "Goles S.P A.B.P",
    "Expected Goals en Contra Balón Parado sin Penaltis (xG)": "xG en contra S.P A.B.P",
    "Goles en contra Balón Parado sin Penaltis (Nº)": "Goles en contra S.P A.B.P",
}

# Definición de grupos usando nombres originales (para mapeo con BD)
GROUPS_ORIGINAL = [
    ("Estilo", [
        "Iniciativa de Juego (Puntos)",
        "Posesión del Balón (%)",
        "Centroide colectivo global",
        "Recuperaciones en campo contrario (% Total)",
    ]),
    ("Rendimiento ofensivo", [
        "Eficacia Construcción Ofensiva (%)",
        "Eficacia Finalización (%)",
        "Expected Goals (xG)",
        "Goles a favor (Nº)",
    ]),
    ("Rendimiento defensivo", [
        "Eficacia Contención Defensiva (%)",
        "Eficacia Evitación (%)",
        "Expected Goals en Contra (xG)",
        "Goles en contra Totales (Nº)",
    ]),
    ("Rendimiento físico", [
        "Distancia Total Recorrida (m.)",
        "Distancia Recorrida > 21 km/h (m.)",
        "Distancia High Sprint > 24 km/h (m.)",
    ]),
    ("Balón Parado", [
        "Expected Goals Balón Parado sin Penaltis (xG)",
        "Goles a favor Balón Parado sin Penaltis (Nº)",
        "Expected Goals en Contra Balón Parado sin Penaltis (xG)",
        "Goles en contra Balón Parado sin Penaltis (Nº)",
    ]),
]

# Definición de grupos con nombres cortos (para visualización)
GROUPS = [
    ("Estilo", [
        "Iniciativa de Juego",
        "Posesión del Balón",
        "Centroide colectivo",
        "% Recup. campo contrario",
    ]),
    ("Rendimiento ofensivo", [
        "Eficacia Construcción Of. (%)",
        "Eficacia Finalización (%)",
        "Xg a Favor",
        "Goles a favor",
    ]),
    ("Rendimiento defensivo", [
        "Eficacia Contención Def. (%)",
        "Eficacia Evitación (%)",
        "xG en Contra",
        "Goles en contra",
    ]),
    ("Rendimiento físico", [
        "Distancia Total",
        "Distancia > 21 km/h",
        "Distancia > 24 km/h (m.)",
    ]),
    ("Balón Parado", [
        "xG S.P A.B.P",
        "Goles S.P A.B.P",
        "xG en contra S.P A.B.P",
        "Goles en contra S.P A.B.P",
    ]),
]

# Mapeo de nombres de grupos a metric_id de rankings compuestos
GROUP_TO_RANKING_ID = {
    "Estilo": "RankingEstilo",
    "Rendimiento ofensivo": "RankingOfensivo", 
    "Rendimiento defensivo": "RankingDefensivo",
    "Rendimiento físico": "RankingFísico",
    "Balón Parado": "RankingBalónParado"
}


def _band_to_color(band: int) -> str:
    if band == 1:
        return '#2ecc71'  # verde
    if band == 2:
        return '#f1c40f'  # amarillo
    if band == 3:
        return '#e74c3c'  # rojo
    return '#f5f6fa'      # vacío


def _order_metrics_by_groups(df: pd.DataFrame):
    """
    Devuelve la lista de métricas ordenadas según GROUPS y un diccionario con
    posiciones por grupo: {group_name: (start_idx, end_idx, present_metric_list)}
    """
    all_metrics = df['metrica'].tolist()
    ordered = []
    group_pos = {}
    for gname, metrics in GROUPS:
        present = [m for m in metrics if m in all_metrics]
        if present:
            start = len(ordered)
            ordered.extend(present)
            end = len(ordered) - 1
            group_pos[gname] = (start, end, present)
    # Añadir cualquier métrica sobrante que no esté en los grupos
    leftovers = [m for m in all_metrics if m not in ordered]
    ordered.extend(leftovers)
    return ordered, group_pos


def _get_color_for_ranking(ranking):
    """Obtiene el color basado en el ranking"""
    if ranking is None:
        return '#cccccc'  # Gris si no hay datos
    
    if ranking <= 6:
        return '#2ecc71'  # Verde
    elif ranking <= 16:
        return '#f1c40f'  # Amarillo
    else:
        return '#e74c3c'  # Rojo


def _get_button_style(ranking, width):
    """Genera el estilo para un botón de sección"""
    return {
        'width': width, 'padding': '10px 5px', 'margin': '2px 1px',
        'backgroundColor': _get_color_for_ranking(ranking),
        'border': '2px solid black', 'color': 'black',
        'fontFamily': 'Montserrat', 'fontWeight': 'bold',
        'fontSize': '12px', 'cursor': 'pointer',
        'textAlign': 'center'
    }


def build_collapsed_metrics(df: pd.DataFrame, collapsed_sections: set) -> tuple:
    """Construye las métricas colapsando las secciones seleccionadas"""
    
    # Mapear secciones a sus rankings compuestos
    section_to_ranking = {
        'ESTILO': 'RankingEstilo',
        'RENDIMIENTO OFENSIVO': 'RankingOfensivo', 
        'RENDIMIENTO DEFENSIVO': 'RankingDefensivo',
        'RENDIMIENTO FÍSICO': 'RankingFísico',
        'BALÓN PARADO': 'RankingBalónParado'
    }
    
    # Obtener rankings compuestos
    try:
        rankings_compuestos = get_rankings_compuestos_laliga("RC Deportivo")
    except:
        rankings_compuestos = {}
    
    # Ordenar métricas por grupos
    ordered_metrics, group_pos = _order_metrics_by_groups(df)
    df_by_metric = {row['metrica']: row for _, row in df.iterrows()}
    
    # Construir nueva lista de métricas colapsando las seleccionadas
    new_ordered_metrics = []
    new_group_pos = {}
    
    for gname, (start_idx, end_idx, present) in group_pos.items():
        if not present:
            continue
            
        if gname.upper() in collapsed_sections:
            # Sección colapsada: usar ranking compuesto
            ranking_id = section_to_ranking.get(gname.upper())
            if ranking_id and ranking_id in rankings_compuestos:
                # Crear métrica sintética para el ranking compuesto
                composite_metric = f"{gname}_COMPUESTO"
                new_ordered_metrics.append(composite_metric)
                
                # Añadir datos sintéticos para esta métrica
                df_by_metric[composite_metric] = {
                    'metrica': composite_metric,
                    'ranking': rankings_compuestos[ranking_id],
                    'valor': rankings_compuestos[ranking_id]  # Usar ranking como valor
                }
                
                # Actualizar posiciones de grupo
                new_start = len(new_ordered_metrics) - 1
                new_group_pos[gname] = (new_start, new_start, [composite_metric])
            else:
                # Fallback: usar métricas originales
                new_start = len(new_ordered_metrics)
                new_ordered_metrics.extend(present)
                new_end = len(new_ordered_metrics) - 1
                new_group_pos[gname] = (new_start, new_end, present)
        else:
            # Sección expandida: usar métricas originales
            new_start = len(new_ordered_metrics)
            new_ordered_metrics.extend(present)
            new_end = len(new_ordered_metrics) - 1
            new_group_pos[gname] = (new_start, new_end, present)
    
    return new_ordered_metrics, new_group_pos, df_by_metric


def build_ranking_heatmap(df: pd.DataFrame, selected_view='expanded', collapsed_sections=None, team_name='RC Deportivo') -> go.Figure:
    if collapsed_sections is None:
        collapsed_sections = set()
    
    # Validar que haya datos disponibles
    if df is None or df.empty:
        # Crear figura vacía con mensaje de error
        fig = go.Figure()
        fig.add_annotation(
            text="⚠️ NO HAY DATOS DISPONIBLES<br><br>No se pudo conectar a la base de datos<br>o no hay indicadores de rendimiento disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#dc3545", family="Montserrat"),
            align="center"
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='white',
            height=600
        )
        return fig
    
    # Construir métricas considerando las secciones colapsadas
    if collapsed_sections:
        ordered_metrics, group_pos, df_by_metric = build_collapsed_metrics(df, collapsed_sections)
    else:
        # Vista expandida (por defecto): mostrar todas las métricas
        ordered_metrics, group_pos = _order_metrics_by_groups(df)
        df_by_metric = {row['metrica']: row for _, row in df.iterrows()}
    
    values = [df_by_metric[m]['valor'] for m in ordered_metrics]
    ranks = [int(df_by_metric[m]['ranking']) for m in ordered_metrics]
    
    # Obtener rankings compuestos desde la BD
    try:
        rankings_compuestos = get_rankings_compuestos_laliga("RC Deportivo")
        if not rankings_compuestos:
            print("[WARNING] No se pudieron obtener rankings compuestos de la BD")
            rankings_compuestos = {}
    except Exception as e:
        print(f"[ERROR] Error obteniendo rankings compuestos: {e}")
        rankings_compuestos = {}
    
    # Obtener información de todos los equipos para hover usando nombres originales
    # Crear mapeo inverso para obtener nombres originales
    reverse_mapping = {v: k for k, v in METRIC_NAME_MAPPING.items()}
    original_metrics = [reverse_mapping.get(m, m) for m in ordered_metrics]
    all_teams_rankings = get_all_teams_rankings_laliga(original_metrics)
    
    # Convertir las claves del diccionario a nombres cortos
    all_teams_rankings_short = {}
    for original_name, rankings in all_teams_rankings.items():
        short_name = METRIC_NAME_MAPPING.get(original_name, original_name)
        all_teams_rankings_short[short_name] = rankings
    all_teams_rankings = all_teams_rankings_short

    # Preparar etiquetas envueltas en varias líneas para el eje X
    def wrap_label(text: str, max_line_len: int = 16) -> str:
        words = str(text).split()
        if not words:
            return ""
        lines, line = [], ""
        for w in words:
            if len(line) + (1 if line else 0) + len(w) <= max_line_len:
                line = (line + " " + w).strip()
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        return "<br>".join(lines)

    metrics_wrapped = [wrap_label(m) for m in ordered_metrics]

    n_rows = 22
    y_vals = list(range(1, n_rows + 1))  # 1 (arriba) -> 22 (abajo)

    # Matrices z y customdata
    z = []  # 0=vacio, 1=verde, 2=amarillo, 3=rojo
    customdata = []  # por celda: [rank, valor, team_at_rank, value_at_rank]

    # Precalcular banda por columna
    bands = [_band_for_rank(rk) for rk in ranks]

    for y in y_vals:
        row_vals = []
        row_custom = []
        for col_idx, rk in enumerate(ranks):
            metric_name = ordered_metrics[col_idx]
            # Relleno desde abajo hasta 'rk': con y >= rk la celda se considera rellena
            filled = 1 if y >= rk else 0
            val = bands[col_idx] if filled else 0
            row_vals.append(val)
            
            # Información para hover: equipo en la posición y de esta métrica
            team_at_position = "N/A"
            value_at_position = "N/A"
            
            if metric_name in all_teams_rankings and y in all_teams_rankings[metric_name]:
                team_info = all_teams_rankings[metric_name][y]
                team_at_position = team_info['team']
                value_at_position = team_info['value']
            
            # RC Deportivo info para esta métrica
            rc_rank = rk
            rc_value = values[col_idx]
            
            row_custom.append([rc_rank, rc_value, team_at_position, value_at_position, y])
        z.append(row_vals)
        customdata.append(row_custom)

    # Colorscale discreta basada en zmin=0, zmax=3
    colorscale = [
        [0.0, '#f5f6fa'],  # vacío
        [0.24, '#f5f6fa'],
        [0.25, '#2ecc71'],  # verde
        [0.49, '#2ecc71'],
        [0.50, '#f1c40f'],  # amarillo
        [0.74, '#f1c40f'],
        [0.75, '#e74c3c'],  # rojo
        [1.0, '#e74c3c'],
    ]

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        row_heights=[0.06, 0.10, 0.74, 0.10], vertical_spacing=0.02
    )

    fig.add_trace(
        go.Heatmap(
            z=z,
            x=ordered_metrics,
            y=y_vals,
            colorscale=colorscale,
            zmin=0,
            zmax=3,
            showscale=False,
            xgap=5,
            ygap=4,
            hoverinfo='none',
            customdata=customdata,
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "<b>Posición %{customdata[4]}:</b> %{customdata[2]}<br>" +
                "Valor en esta posición: %{customdata[3]}<br>" +
                "<br>" +
                f"<b>{team_name}:</b><br>" +
                "Ranking: %{customdata[0]}/22<br>" +
                "Valor: %{customdata[1]}<extra></extra>"
            ),
        ),
        row=3, col=1
    )

    # Layout general con escudo del RC Deportivo
    fig.update_layout(
        height=1000,  # Aumentar altura para acomodar etiquetas inclinadas
        margin=dict(l=50, r=40, t=60, b=200),  # Aumentar margen superior para el escudo
        plot_bgcolor='white',
        paper_bgcolor='white',
        # Añadir escudo del RC Deportivo en la esquina superior izquierda
        images=[dict(
            source="/assets/escudos/RC Deportivo.png",
            xref="paper", yref="paper",
            x=0.01, y=0.99,  # Posición superior izquierda
            sizex=0.08, sizey=0.08,  # Tamaño del escudo
            xanchor="left", yanchor="top",
            sizing="contain",
            layer="above"
        )],
        # Añadir título con el nombre del equipo
        title=dict(
            text="<b>RC DEPORTIVO LA CORUÑA</b> - Indicadores de Rendimiento",
            font=dict(size=20, color='#1e3d59', family='Montserrat', weight='bold'),
            x=0.12,  # Después del escudo
            xanchor='left',
            y=0.98,
            yanchor='top'
        )
    )

    # Fila 1: Rendimiento Global (arriba de todo)
    fig.update_xaxes(row=1, col=1, showticklabels=False, showgrid=False, zeroline=False, matches='x')
    fig.update_yaxes(row=1, col=1, visible=False, range=[0, 1])
    
    # Fila 2: Bloques de secciones con bordes
    fig.update_xaxes(row=2, col=1, showticklabels=False, categoryorder='array', categoryarray=ordered_metrics, showgrid=False, zeroline=False, matches='x')
    fig.update_yaxes(row=2, col=1, visible=False, range=[0, 1])

    # Fila 3 (heatmap): ocultar etiquetas del eje X para que queden solo en la fila 4
    fig.update_xaxes(
        row=3, col=1,
        title='', type='category', tickangle=0,
        tickfont=dict(size=16),
        showticklabels=False,
        automargin=True, showgrid=False, zeroline=False,
        categoryorder='array', categoryarray=ordered_metrics,
    )
    # Eje Y principal (fila 3)
    fig.update_yaxes(
        row=3, col=1,
        title='Ranking',
        tickmode='linear', tick0=1, dtick=1,
        tickfont=dict(size=14, family="Montserrat"), showgrid=False, zeroline=False,
        autorange='reversed'
    )
    # Fila 4: mostrar etiquetas de métricas (bajo el heatmap)
    # Añadimos una traza invisible para forzar render de los ticks del eje X
    fig.add_trace(
        go.Scatter(x=ordered_metrics, y=[0]*len(ordered_metrics), mode='markers',
                    marker=dict(opacity=0), hoverinfo='skip', showlegend=False),
        row=4, col=1
    )
    fig.update_xaxes(
        row=4, col=1,
        title='', type='category', tickangle=0,  # Etiquetas horizontales sin inclinación
        tickfont=dict(size=10, family="Montserrat"),  # Fuente Montserrat
        tickvals=ordered_metrics, ticktext=metrics_wrapped,
        automargin=True, showgrid=False, zeroline=False, showticklabels=True,
        categoryorder='array', categoryarray=ordered_metrics,
        matches='x', side='top', ticklabelposition='inside', ticks='outside', ticklen=0, ticklabelstandoff=8
    )
    fig.update_yaxes(row=4, col=1, visible=False, range=[0, 1])

    # FILA 1: Rendimiento Global (arriba de todo)
    if "RankingGlobal" in rankings_compuestos:
        overall_ranking = int(rankings_compuestos["RankingGlobal"])
    elif len(ranks) > 0:
        overall_ranking = float(np.mean(ranks))
    else:
        overall_ranking = np.nan
    
    if not np.isnan(overall_ranking):
        band_overall = _band_for_rank(int(round(overall_ranking)))
        color_overall = _band_to_color(band_overall)
        fig.add_shape(
            type='rect', xref='x domain', yref='y',
            x0=0.0, x1=1.0, y0=0.0, y1=1.0,
            fillcolor=color_overall, line=dict(color='black', width=2),
            layer='above'
        )
        overall_text = f"RENDIMIENTO GLOBAL ({overall_ranking:.0f})" if isinstance(overall_ranking, int) else f"RENDIMIENTO GLOBAL ({overall_ranking:.1f})"
        fig.add_annotation(
            x=0.5, y=0.5,
            xref='x domain', yref='y',
            text=overall_text,
            font=dict(size=20, color='black', family="Montserrat", weight="bold"),
            showarrow=False, align='center',
            xanchor='center', yanchor='middle'
        )

    # FILA 2: Bloques de secciones con bordes claramente definidos
    for gname, (start_idx, end_idx, present) in group_pos.items():
        if not present:
            continue
        
        # Usar el ranking compuesto desde la BD si está disponible
        ranking_id = GROUP_TO_RANKING_ID.get(gname)
        if ranking_id and ranking_id in rankings_compuestos:
            group_ranking = int(rankings_compuestos[ranking_id])
        else:
            # Fallback: calcular media de las métricas presentes
            rank_map = {m: int(df_by_metric[m]['ranking']) for m in ordered_metrics if m in df_by_metric}
            group_ranking = float(np.mean([rank_map[m] for m in present if m in rank_map]))
        
        band = _band_for_rank(int(round(group_ranking)))
        color = _band_to_color(band)
        
        # Usar las métricas reales para posicionamiento exacto
        first_metric = present[0]
        last_metric = present[-1]
        
        # Encontrar las posiciones exactas en ordered_metrics
        start_pos = ordered_metrics.index(first_metric) 
        end_pos = ordered_metrics.index(last_metric)
        
        # Bloque principal de la sección (fila 2)
        fig.add_shape(
            type='rect', xref='x3', yref='y2',
            x0=start_pos - 0.5, x1=end_pos + 0.5, y0=0.0, y1=1.0,
            fillcolor=color, line=dict(color='black', width=2),
            layer='above'
        )
        
        # Líneas verticales de separación entre secciones
        if start_pos > 0:  # No dibujar línea al inicio del primer grupo
            fig.add_shape(
                type='line', xref='x3', yref='paper',
                x0=start_pos - 0.5, x1=start_pos - 0.5, y0=0.0, y1=0.94,
                line=dict(color='black', width=2)
            )
        
        # Línea derecha (final de la sección) - solo para el último grupo
        if end_pos == len(ordered_metrics) - 1:  # Si es el último grupo
            fig.add_shape(
                type='line', xref='x3', yref='paper',
                x0=end_pos + 0.5, x1=end_pos + 0.5, y0=0.0, y1=0.94,
                line=dict(color='black', width=2)
            )
        
        # Etiqueta del grupo centrada en las métricas reales
        center_pos = (start_pos + end_pos) / 2
        group_text = f"{gname.upper()} ({group_ranking:.0f})" if isinstance(group_ranking, int) else f"{gname.upper()} ({group_ranking:.1f})"
        fig.add_annotation(
            x=center_pos,
            y=0.5,
            xref='x3', yref='y2',
            text=group_text,
            font=dict(size=14, color='black', family="Montserrat", weight="bold"),
            showarrow=False, align='center',
            xanchor='center', yanchor='middle'
        )

    return fig


def legend_block():
    # Leyenda estilizada y compacta
    box_style = {
        'display': 'inline-block',
        'width': '12px',
        'height': '12px',
        'marginRight': '5px',
        'borderRadius': '2px',
        'border': '1px solid rgba(0,0,0,0.2)',
    }
    text_style = {
        'fontSize': '11px',
        'color': '#666',
        'fontFamily': 'Montserrat'
    }
    return html.Div([
        html.Span([
            html.Span(style={**box_style, 'background': '#2ecc71'}),
            html.Span('1–6', style=text_style)
        ], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '8px'}),
        html.Span([
            html.Span(style={**box_style, 'background': '#f1c40f'}),
            html.Span('7–16', style=text_style)
        ], style={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '8px'}),
        html.Span([
            html.Span(style={**box_style, 'background': '#e74c3c'}),
            html.Span('17–22', style=text_style)
        ], style={'display': 'inline-flex', 'alignItems': 'center'})
    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '0px', 'whiteSpace': 'nowrap'})

def description_block():
    return html.Div([
        html.P(
            [
                html.Span('Cada columna representa una métrica; las filas muestran el ranking que ocupa el equipo en la competición (1 arriba → 22 abajo). '),
                html.Span('El color refleja la banda de rendimiento por métrica y por grupo.'),
            ],
            className='text-muted', style={'fontStyle': 'italic'}
        )
    ], className='mb-2')


def _group_tied_teams(rankings_dict):
    """
    Agrupa equipos que están empatados (mismo valor en la métrica).
    
    Args:
        rankings_dict: {ranking_position: {'team': 'nombre', 'value': valor}}
    
    Returns:
        dict: {ranking_position: [{'team': 'nombre', 'value': valor}, ...]} o dict simple si no hay empates
    """
    if not rankings_dict:
        return {}
    
    # Crear diccionario inverso: valor -> [equipos]
    value_to_teams = {}
    for ranking, data in rankings_dict.items():
        value = data.get('value')
        if value is not None:
            value_key = round(float(value), 2)  # Redondear a 2 decimales para comparar
            if value_key not in value_to_teams:
                value_to_teams[value_key] = []
            value_to_teams[value_key].append({
                'ranking': ranking,
                'team': data['team'],
                'value': data['value']
            })
    
    # Si no hay empates, retornar estructura original
    has_ties = any(len(teams) > 1 for teams in value_to_teams.values())
    if not has_ties:
        return rankings_dict
    
    # Reconstruir con empates agrupados
    result = {}
    for value_key, teams in value_to_teams.items():
        if len(teams) == 1:
            # Un solo equipo en esta posición
            ranking = teams[0]['ranking']
            result[ranking] = {
                'team': teams[0]['team'],
                'value': teams[0]['value']
            }
        else:
            # Múltiples equipos empatados
            # Todos comparten la misma posición (la más alta)
            min_ranking = min(t['ranking'] for t in teams)
            result[min_ranking] = [
                {'team': t['team'], 'value': t['value']} for t in teams
            ]
    
    return result


def build_custom_heatmap_html(df, rankings_compuestos, collapsed_sections=None, team_name='RC Deportivo'):
    """Construye un heatmap completamente personalizado en HTML/CSS"""
    
    if collapsed_sections is None:
        collapsed_sections = set()
    
    # Obtener datos organizados
    ordered_metrics, group_pos = _order_metrics_by_groups(df)
    df_by_metric = {row['metrica']: row for _, row in df.iterrows()}
    
    # Verificar si TODO está colapsado (vista Global)
    all_section_names = [name for name in group_pos.keys()]
    all_collapsed = all(name.upper() in collapsed_sections for name in all_section_names)
    
    # Construir lista de métricas considerando colapsados
    metrics_display = []
    groups_display = []
    
    # Construir las métricas (SIEMPRE, para evitar errores de callback)
    current_col = 0
    
    # Si TODO está colapsado, mostrar solo RankingGlobal
    if all_collapsed:
        global_ranking_value = rankings_compuestos.get('RankingGlobal', 4)
        metrics_display.append({
            'name': 'Rendimiento Global',
            'short_name': 'Global',
            'ranking': int(global_ranking_value),
            'is_composite': True,
            'colspan': len(all_section_names),  # Ocupa todo el ancho
            'ranking_id': 'RankingGlobal'
        })
        
        # Añadir grupos display vacíos para mantener estructura de callback
        col_idx = 0
        for gname, (start_idx, end_idx, present) in group_pos.items():
            if not present:
                continue
            ranking_id = GROUP_TO_RANKING_ID.get(gname)
            group_ranking = rankings_compuestos.get(ranking_id, 11) if ranking_id in rankings_compuestos else 11
            num_metrics = len(present) if present else 1
            
            groups_display.append({
                'name': gname,
                'start_col': col_idx,
                'end_col': col_idx,
                'ranking': group_ranking,
                'collapsed': True,
                'visual_width': num_metrics
            })
            col_idx += 1
    else:
        # Vista normal o parcialmente colapsada
        for gname, (start_idx, end_idx, present) in group_pos.items():
            if not present:
                continue
                
            ranking_id = GROUP_TO_RANKING_ID.get(gname)
            group_ranking = rankings_compuestos.get(ranking_id, 11) if ranking_id in rankings_compuestos else 11
            
            # Contar cuántas métricas tiene este grupo
            num_metrics_in_group = len(present) if present else 1
            
            if gname.upper() in collapsed_sections:
                # Colapsado: 1 columna pero ocupa el espacio de todas las métricas originales
                # Usar el ranking_id como nombre para poder obtener datos de todos los equipos
                metrics_display.append({
                    'name': gname,
                    'short_name': gname[:15],
                    'ranking': int(group_ranking),
                    'is_composite': True,
                    'colspan': num_metrics_in_group,  # Ancho visual
                    'ranking_id': ranking_id  # Para obtener datos de BD
                })
                groups_display.append({
                    'name': gname,
                    'start_col': current_col,
                    'end_col': current_col,  # Solo 1 columna real
                    'ranking': group_ranking,
                    'collapsed': True,
                    'visual_width': num_metrics_in_group  # Ancho visual
                })
                current_col += 1
            else:
                # Expandido: columnas individuales
                start_col = current_col
                for metric in present:
                    if metric in df_by_metric:
                        metrics_display.append({
                            'name': metric,
                            'short_name': metric[:20],
                            'ranking': int(df_by_metric[metric]['ranking']),
                            'is_composite': False,
                            'colspan': 1
                        })
                        current_col += 1
                groups_display.append({
                    'name': gname,
                    'start_col': start_col,
                    'end_col': current_col - 1,
                    'ranking': group_ranking,
                    'collapsed': False,
                    'visual_width': num_metrics_in_group
                })
    
    # Obtener rankings de todos los equipos para tooltips
    try:
        # Crear mapeo inverso para obtener nombres originales (como en BD)
        reverse_mapping = {v: k for k, v in METRIC_NAME_MAPPING.items()}
        
        # Separar métricas individuales de rankings compuestos
        individual_metrics = []
        composite_ranking_ids = []
        
        for m in metrics_display:
            if m.get('is_composite') and m.get('ranking_id'):
                # Es un ranking compuesto
                composite_ranking_ids.append(m['ranking_id'])
            else:
                # Es métrica individual
                individual_metrics.append(m['name'])
        
        # Convertir nombres cortos a originales para métricas individuales
        original_metrics = [reverse_mapping.get(m, m) for m in individual_metrics]
        
        # Obtener datos de métricas individuales
        all_teams_rankings = {}
        if original_metrics:
            all_teams_rankings_original = get_all_teams_rankings_laliga(original_metrics)
            # Convertir claves a nombres cortos y agrupar empates
            for original_name, rankings in all_teams_rankings_original.items():
                short_name = METRIC_NAME_MAPPING.get(original_name, original_name)
                grouped = _group_tied_teams(rankings)
                all_teams_rankings[short_name] = grouped
        
        # Obtener datos de rankings compuestos usando query especial por metric_id
        if composite_ranking_ids:
            try:
                engine = get_laliga_db_connection()
                if engine:
                    placeholders = ','.join(['%s'] * len(composite_ranking_ids))
                    query = f"""
                    SELECT 
                        metric_id,
                        team_name,
                        ranking_position,
                        metric_value
                    FROM indicadores_rendimiento 
                    WHERE metric_id IN ({placeholders})
                    ORDER BY metric_id, ranking_position
                    """
                    
                    import pandas as pd
                    df_composite = pd.read_sql(query, engine, params=tuple(composite_ranking_ids))
                    
                    if not df_composite.empty:
                        # Crear diccionario temporal por metric_id
                        # IMPORTANTE: Acumulamos equipos con misma ranking_position
                        # Estructura: {metric_id: {ranking: [{'team': 'nombre', 'value': valor}, ...]}}
                        temp_rankings = {}
                        for idx, row in df_composite.iterrows():
                            metric_id = row['metric_id']
                            ranking = int(row['ranking_position'])
                            team = row['team_name']
                            value = row['metric_value']
                            
                            if metric_id not in temp_rankings:
                                temp_rankings[metric_id] = {}
                            
                            # CLAVE: Acumular equipos en la misma posición (empates reales de BD)
                            if ranking not in temp_rankings[metric_id]:
                                temp_rankings[metric_id][ranking] = []
                            
                            temp_rankings[metric_id][ranking].append({
                                'team': team,
                                'value': value
                            })
                        
                        # Convertir a nombres de grupo y agrupar empates
                        for metric_id, rankings in temp_rankings.items():
                            # Encontrar el nombre del grupo correspondiente
                            group_name = None
                            for m in metrics_display:
                                if m.get('ranking_id') == metric_id:
                                    group_name = m['name']
                                    break
                            
                            if group_name:
                                # Convertir listas de 1 elemento a dict simple
                                # rankings ya tiene estructura: {pos: [{'team': ..., 'value': ...}, ...]}
                                final_rankings = {}
                                for pos, teams_list in rankings.items():
                                    if len(teams_list) == 1:
                                        # Un solo equipo en esta posición
                                        final_rankings[pos] = teams_list[0]
                                    else:
                                        # Múltiples equipos (empate real de BD)
                                        final_rankings[pos] = teams_list
                                
                                all_teams_rankings[group_name] = final_rankings
            except Exception as e:
                # Error silencioso, continuar con rankings vacíos
                pass
        
    except Exception as e:
        # Error silencioso, continuar con rankings vacíos
        all_teams_rankings = {}
    
    # Construir HTML
    global_ranking = rankings_compuestos.get('RankingGlobal', 4)
    
    return build_heatmap_components(metrics_display, groups_display, global_ranking, all_teams_rankings, team_name)


def build_heatmap_components(metrics, groups, global_ranking, all_teams_rankings=None, team_name='RC Deportivo'):
    """Construye los componentes HTML del heatmap - EXACTO a funcionalidad Plotly"""
    
    if all_teams_rankings is None:
        all_teams_rankings = {}
    
    # Calcular ancho total considerando colspan (ancho visual)
    total_visual_cols = sum(m.get('colspan', 1) for m in metrics)
    base_col_width = f"calc((100% - 50px) / {total_visual_cols})"  # 50px para columna de posiciones
    
    # Bloque global
    global_block = html.Div(
        f"RENDIMIENTO GLOBAL ({int(global_ranking)})",
        id='heatmap-block-global',
        style={
            'backgroundColor': _get_color_for_ranking(global_ranking),
            'border': '3px solid black',
            'padding': '12px',
            'textAlign': 'center',
            'fontFamily': 'Montserrat',
            'fontWeight': 'bold',
            'fontSize': '18px',
            'cursor': 'pointer',
            'marginBottom': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }
    )
    
    # Bloques de secciones - SIEMPRE presentes para evitar errores de callback
    section_blocks_items = []
    
    # Detectar si es vista global (solo una métrica con RankingGlobal)
    is_global_view = len(metrics) == 1 and metrics[0].get('ranking_id') == 'RankingGlobal'
    
    for group in groups:
        # Usar ancho visual para mantener proporción al colapsar
        visual_width = group.get('visual_width', 1)
        width_percent = (visual_width / total_visual_cols) * 100
        
        # En vista global, ocultar los bloques de sección individuales
        display_style = 'none' if is_global_view else 'block'
        
        section_blocks_items.append(
            html.Div(
                f"{group['name'].upper()} ({int(group['ranking'])})",
                id=f"heatmap-block-{group['name'].replace(' ', '-').lower()}",
                className='heatmap-section-block',  # Añadir clase para hover
                style={
                    'backgroundColor': _get_color_for_ranking(group['ranking']),
                    'border': '2px solid black',
                    'padding': '8px 4px',
                    'textAlign': 'center',
                    'fontFamily': 'Montserrat',
                    'fontWeight': 'bold',
                    'fontSize': '12px',
                    'cursor': 'pointer',
                    'width': f"{width_percent}%",
                    'boxSizing': 'border-box',
                    'transition': 'all 0.2s ease',
                    'display': display_style  # Ocultar en vista global
                }
            )
        )
    
    # Bloque especial visible solo en vista global
    global_view_block = None
    if is_global_view:
        global_view_block = html.Div(
            f"RENDIMIENTO GLOBAL ({int(metrics[0]['ranking'])})",
            id='heatmap-block-rendimiento-global-visible',
            style={
                'backgroundColor': _get_color_for_ranking(metrics[0]['ranking']),
                'border': '2px solid black',
                'padding': '8px 4px',
                'textAlign': 'center',
                'fontFamily': 'Montserrat',
                'fontWeight': 'bold',
                'fontSize': '14px',
                'marginBottom': '10px',
                'marginLeft': '50px',
                'cursor': 'default'
            }
        )
    
    section_blocks = html.Div(
        section_blocks_items,
        style={
            'display': 'flex',
            'gap': '0px',
            'marginBottom': '10px' if not is_global_view else '0px',
            'width': 'calc(100% - 50px)',  # Alinear con grid
            'marginLeft': '50px'
        }
    )
    
    # Grid del heatmap con BORDES de grupo
    grid_rows = []
    
    # Fila de encabezados
    header_cells = [html.Div('Pos', style={
        'width': '50px',
        'fontWeight': 'bold',
        'fontFamily': 'Montserrat',
        'fontSize': '11px',
        'textAlign': 'center',
        'padding': '5px 0'
    })]
    
    for i, metric in enumerate(metrics):
        # Bordes: grupos (gruesos) y métricas (discretos)
        border_left = '1px solid #e0e0e0'  # División discreta entre métricas
        border_right = 'none'
        
        # Bordes de grupo (más gruesos)
        for group in groups:
            if i == group['start_col']:
                border_left = '2px solid black'  # Inicio de grupo: grueso
            if i == group['end_col']:
                border_right = '2px solid black'  # Fin de grupo: grueso
        
        # Calcular ancho considerando colspan
        metric_colspan = metric.get('colspan', 1)
        metric_width = f"calc({base_col_width} * {metric_colspan})"
        
        header_cells.append(
            html.Div(
                metric['name'],  # Usar nombre completo
                title=metric['name'],  # Tooltip con nombre completo
                style={
                    'width': metric_width,  # Ancho basado en colspan
                    'padding': '8px 2px',
                    'fontFamily': 'Montserrat',
                    'fontSize': '9px',
                    'fontWeight': '600',
                    'textAlign': 'center',
                    'borderBottom': '2px solid black',
                    'borderLeft': border_left,
                    'borderRight': border_right,
                    'overflow': 'hidden',
                    'whiteSpace': 'normal',  # Permitir múltiples líneas
                    'wordWrap': 'break-word',  # Romper palabras largas
                    'lineHeight': '1.2',
                    'minHeight': '40px',  # Altura mínima para 2-3 líneas
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'boxSizing': 'border-box'
                }
            )
        )
    
    grid_rows.append(
        html.Div(header_cells, style={
            'display': 'flex',
            'alignItems': 'flex-end',
            'marginBottom': '2px'
        })
    )
    
    # 22 filas de ranking - LLENADO DESDE ABAJO
    for pos in range(1, 23):
        row_cells = [
            html.Div(
                str(pos),
                style={
                    'width': '50px',
                    'fontFamily': 'Montserrat',
                    'fontSize': '11px',
                    'fontWeight': 'bold',  # SIEMPRE en negrita
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'color': '#2c3e50',
                    'height': '22px'
                }
            )
        ]
        
        for i, metric in enumerate(metrics):
            # Lógica CORRECTA: llenar desde abajo hasta el ranking
            # Si el ranking es 4, llenar posiciones 4, 5, 6, ..., 22
            is_filled = pos >= metric['ranking']
            is_current = pos == metric['ranking']
            
            # Color basado en la posición actual
            if is_filled:
                bg_color = _get_color_for_ranking(metric['ranking'])
            else:
                bg_color = '#f5f6fa'
            
            # Bordes: grupos (gruesos) y métricas (discretos)
            border_left = '1px solid #e0e0e0'  # División discreta entre métricas
            border_right = 'none'
            border_bottom = '1px solid #dfe6e9'
            
            # Bordes de grupo (más gruesos)
            for group in groups:
                if i == group['start_col']:
                    border_left = '2px solid black'  # Inicio de grupo: grueso
                if i == group['end_col']:
                    border_right = '2px solid black'  # Fin de grupo: grueso
            
            # Última fila tiene borde inferior de grupo
            if pos == 22:
                for group in groups:
                    if group['start_col'] <= i <= group['end_col']:
                        border_bottom = '2px solid black'
            
            # Obtener nombre del equipo en esta posición para esta métrica
            metric_name = metric['name']
            
            # Buscar equipos en esta posición (puede haber empates)
            teams_at_position = []
            rc_depor_value = None
            
            if metric_name in all_teams_rankings:
                metric_rankings = all_teams_rankings[metric_name]
                
                # La estructura puede ser: {ranking: {'team': 'nombre', 'value': valor}} o {ranking: [...]}
                if pos in metric_rankings:
                    data_at_pos = metric_rankings[pos]
                    # Si es un dict simple (un solo equipo)
                    if isinstance(data_at_pos, dict) and 'team' in data_at_pos:
                        teams_at_position.append(data_at_pos)
                    # Si es una lista (múltiples equipos empatados)
                    elif isinstance(data_at_pos, list):
                        teams_at_position = data_at_pos
                
                # Obtener valor de RC Deportivo
                rc_ranking = metric['ranking']
                if rc_ranking in metric_rankings:
                    rc_data = metric_rankings[rc_ranking]
                    if isinstance(rc_data, dict):
                        rc_depor_value = rc_data.get('value')
                    elif isinstance(rc_data, list):
                        # RC Deportivo podría estar empatado
                        for team_data in rc_data:
                            if team_name in team_data.get('team', ''):
                                rc_depor_value = team_data.get('value')
                                break
            
            # Construir tooltip con empates y posiciones vacías
            if is_current:
                # Es la posición del equipo seleccionado
                if len(teams_at_position) > 1:
                    # Equipo está empatado
                    other_teams = [t['team'] for t in teams_at_position if team_name not in t['team']]
                    if other_teams:
                        tooltip_text = f"{metric_name} | Pos. {pos} | ★ {team_name} (EMPATE con: {', '.join(other_teams[:2])}{'...' if len(other_teams) > 2 else ''})"
                    else:
                        tooltip_text = f"{metric_name} | Pos. {pos} | ★ {team_name}"
                elif rc_depor_value is not None:
                    tooltip_text = f"{metric_name} | Pos. {pos} | ★ {team_name} | Valor: {rc_depor_value:.2f}"
                else:
                    tooltip_text = f"{metric_name} | Pos. {pos} | ★ {team_name}"
            elif len(teams_at_position) > 0:
                # Hay equipos en esta posición
                if len(teams_at_position) == 1:
                    # Un solo equipo - SIN info de RC Deportivo (ya visible en gráfico)
                    team = teams_at_position[0]
                    tooltip_text = f"{metric_name} | Pos. {pos}: {team['team']} ({team['value']:.2f})"
                else:
                    # Múltiples equipos empatados
                    teams_list = ', '.join([f"{t['team']} ({t['value']:.2f})" for t in teams_at_position[:3]])
                    if len(teams_at_position) > 3:
                        teams_list += f" (+{len(teams_at_position)-3} más)"
                    tooltip_text = f"{metric_name} | Pos. {pos} | EMPATE ({len(teams_at_position)}): {teams_list}"
            else:
                # Posición vacía - verificar si hay empate en posición anterior
                empate_anterior = False
                if metric_name in all_teams_rankings and pos > 1:
                    for prev_pos in range(pos-1, max(0, pos-3), -1):
                        if prev_pos in all_teams_rankings[metric_name]:
                            data = all_teams_rankings[metric_name][prev_pos]
                            if isinstance(data, list) and len(data) > 1:
                                empate_anterior = True
                                tooltip_text = f"{metric_name} | Pos. {pos} | Vacía (Empate en pos. {prev_pos})"
                                break
                            elif isinstance(data, dict):
                                break
                
                if not empate_anterior:
                    tooltip_text = f"{metric_name} | Pos. {pos} | (Sin datos)"
            
            # Calcular ancho de la celda basado en colspan
            metric_colspan = metric.get('colspan', 1)
            cell_width = f"calc({base_col_width} * {metric_colspan})"
            
            row_cells.append(
                html.Div(
                    '●' if is_current else '',
                    **{'data-tooltip': tooltip_text},  # Para tooltip CSS personalizado
                    className='heatmap-cell',  # Clase para CSS
                    style={
                        'width': cell_width,  # Ancho basado en colspan
                        'height': '22px',
                        'backgroundColor': bg_color,
                        'borderLeft': border_left,
                        'borderRight': border_right,
                        'borderBottom': border_bottom,
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'fontSize': '14px',
                        'color': 'white' if is_current else 'transparent',
                        'fontWeight': 'bold',
                        'boxSizing': 'border-box',
                        'cursor': 'help',  # Cursor de ayuda en TODAS las celdas
                        'position': 'relative'  # Para tooltip CSS
                    }
                )
            )
        
        grid_rows.append(
            html.Div(row_cells, style={
                'display': 'flex',
                'marginBottom': '0px'
            })
        )
    
    heatmap_grid = html.Div(
        grid_rows,
        style={
            'maxHeight': '650px',
            'overflowY': 'auto',
            'border': '1px solid #dfe6e9',
            'borderRadius': '4px',
            'padding': '8px',
            'backgroundColor': 'white'
        }
    )
    
    # Construir lista de componentes a mostrar
    components = [global_block]
    
    # Añadir bloque especial de vista global si existe
    if global_view_block:
        components.append(global_view_block)
    
    components.extend([section_blocks, heatmap_grid])
    
    return html.Div(components, style={'fontFamily': 'Montserrat'})


def team_selector_premium():
    """Crea el selector premium de equipos con escudos"""
    
    # Lista de equipos (extraída de los escudos disponibles)
    equipos = [
        "RC Deportivo", "Albacete BP", "Burgos CF", "CD Castellón", "CD Leganés",
        "CD Mirandés", "Ceuta", "Cultural", "Cádiz CF", "Córdoba CF",
        "FC Andorra", "Granada CF", "Málaga CF", "Real Racing Club", "Real Sociedad B",
        "Real Sporting", "Real Valladolid CF", "Real Zaragoza", "SD Eibar",
        "SD Huesca", "UD Almería", "UD Las Palmas"
    ]
    
    escudos_items = []
    for equipo in equipos:
        # Determinar si es el equipo por defecto (RC Deportivo)
        is_default = equipo == "RC Deportivo"
        
        escudos_items.append(
            html.Div(
                html.Img(
                    src=f'/assets/escudos/{equipo}.png',
                    id={'type': 'team-shield', 'team': equipo},
                    className='team-shield',
                    title=equipo,
                    style={
                        'width': '100%',
                        'height': '100%',
                        'cursor': 'pointer',
                        'transition': 'all 0.3s ease',
                        'border': '3px solid #007bff' if is_default else '2px solid transparent',
                        'borderRadius': '50%',
                        'padding': '2px',
                        'backgroundColor': 'white',
                        'boxShadow': '0 4px 12px rgba(0,123,255,0.5)' if is_default else '0 2px 4px rgba(0,0,0,0.1)',
                        'objectFit': 'contain',
                        'transform': 'scale(1.1)' if is_default else 'scale(1)'
                    }
                ),
                style={
                    'width': '45px',
                    'height': '45px',
                    'flex': '0 0 auto'
                }
            )
        )
    
    return html.Div([
        # Contenedor simplificado de escudos (eliminado contenedor redundante)
        html.Div(
            escudos_items,
            style={
                'display': 'flex',
                'flexWrap': 'nowrap',
                'justifyContent': 'space-evenly',  # Distribuir uniformemente
                'alignItems': 'center',
                'overflowX': 'auto',
                'overflowY': 'hidden',
                'gap': '8px',
                'padding': '15px 20px',
                'marginBottom': '25px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '10px',
                'boxShadow': '0 3px 10px rgba(0,0,0,0.08)',
                'scrollbarWidth': 'thin',
                'scrollbarColor': '#007bff #f8f9fa'
            }
        ),
        
        # Store para guardar el equipo seleccionado
        dcc.Store(id='selected-team-store', data='RC Deportivo')
    ])


def build_layout():
    df = fetch_indicadores_rendimiento()
    
    # Obtener rankings compuestos
    try:
        rankings_compuestos = get_rankings_compuestos_laliga("RC Deportivo")
    except:
        rankings_compuestos = {
            'RankingGlobal': 4,
            'RankingEstilo': 16,
            'RankingOfensivo': 2,
            'RankingDefensivo': 4,
            'RankingFísico': 13,
            'RankingBalónParado': 3
        }
    
    # Construir heatmap HTML inicial (por defecto RC Deportivo)
    heatmap_html = build_custom_heatmap_html(df, rankings_compuestos, set(), 'RC Deportivo')
    
    return standard_page([
        # Inyectar CSS para tooltips personalizados y html2canvas
        html.Div([
            html.Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap'),
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js')
        ]),
        
        # Título con botón de descarga discreto
        html.Div([
            html.H2("Control Rendimiento Competición - Evolutivo Temporada", className="page-title", 
                   style={'textTransform': 'none', 'fontWeight': 600, 'display': 'inline-block', 'marginRight': '20px', 'flex': '1'}),
            html.Button(
                html.Img(
                    src='/assets/download.png',
                    style={
                        'width': '20px',
                        'height': '20px',
                        'objectFit': 'contain'
                    }
                ),
                id='btn-download-heatmap',
                title="Descargar Heatmap como PNG",
                style={
                    'backgroundColor': 'transparent',
                    'border': 'none',
                    'padding': '8px',
                    'cursor': 'pointer',
                    'transition': 'opacity 0.3s ease',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },
                n_clicks=0
            ),
            # Div invisible para el callback
            html.Div(id='download-trigger', style={'display': 'none'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
        
        description_block(),
        
        # Selector Premium de Equipos
        team_selector_premium(),
        
        # Store para guardar el estado de las secciones colapsadas
        dcc.Store(id='view-state-store', data={'collapsed_sections': []}),
        
        # Contenedor del heatmap HTML personalizado con loader
        dcc.Loading(
            id='loading-heatmap',
            type='circle',
            color='#007bff',
            children=[
                html.Div([
                    # Contenedor para captura (sin escudo visible inicialmente)
                    html.Div([
                        # Contenedor del heatmap
                        html.Div(
                            id='custom-heatmap-container',
                            children=[heatmap_html],
                            style={'marginTop': '20px'}
                        )
                    ], id='heatmap-capture-area', style={'position': 'relative', 'backgroundColor': 'white', 'padding': '20px'}),
                    
                    # Leyenda justo debajo del heatmap, alineada a la derecha
                    html.Div(
                        legend_block(),
                        style={
                            'display': 'flex',
                            'justifyContent': 'flex-end',
                            'marginTop': '5px',
                            'marginRight': '10px',
                            'marginBottom': '10px',
                            'backgroundColor': 'rgba(255, 255, 255, 0.96)',
                            'padding': '8px 12px',
                            'borderRadius': '6px',
                            'boxShadow': '0 2px 6px rgba(0,0,0,0.12)',
                            'border': '1px solid rgba(0,0,0,0.08)',
                            'width': 'fit-content',
                            'marginLeft': 'auto'
                        }
                    )
                ])
            ]
        )
    ])


# Callback para manejar clics en los bloques HTML
from dash import callback, Input, Output, State, ALL
import dash

@callback(
    Output('custom-heatmap-container', 'children'),
    Output('view-state-store', 'data'),
    [Input({'type': 'heatmap-block', 'index': ALL}, 'n_clicks'),
     Input('heatmap-block-global', 'n_clicks'),
     Input('heatmap-block-estilo', 'n_clicks'),
     Input('heatmap-block-rendimiento-ofensivo', 'n_clicks'),
     Input('heatmap-block-rendimiento-defensivo', 'n_clicks'),
     Input('heatmap-block-rendimiento-físico', 'n_clicks'),
     Input('heatmap-block-balón-parado', 'n_clicks'),
     Input('selected-team-store', 'data')],  # Añadido equipo seleccionado
    State('view-state-store', 'data'),
    prevent_initial_call=True
)
def handle_block_clicks(*args):
    """Maneja clics en los bloques HTML para alternar secciones"""
    
    # Los dos últimos argumentos son states
    selected_team = args[-2]  # Equipo seleccionado
    current_state = args[-1]  # Estado de view
    
    # Obtener datos del equipo seleccionado
    df = fetch_indicadores_rendimiento(selected_team)
    try:
        rankings_compuestos = get_rankings_compuestos_laliga(selected_team)
    except:
        rankings_compuestos = {
            'RankingGlobal': 4,
            'RankingEstilo': 16,
            'RankingOfensivo': 2,
            'RankingDefensivo': 4,
            'RankingFísico': 13,
            'RankingBalónParado': 3
        }
    
    # Determinar qué botón se clicó
    ctx = dash.callback_context
    if not ctx.triggered:
        collapsed_sections = set()
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Mapear ID de botón a nombre de sección
        button_to_section = {
            'heatmap-block-global': 'RENDIMIENTO GLOBAL',
            'heatmap-block-estilo': 'ESTILO',
            'heatmap-block-rendimiento-ofensivo': 'RENDIMIENTO OFENSIVO',
            'heatmap-block-rendimiento-defensivo': 'RENDIMIENTO DEFENSIVO',
            'heatmap-block-rendimiento-físico': 'RENDIMIENTO FÍSICO',
            'heatmap-block-balón-parado': 'BALÓN PARADO'
        }
        
        clicked_section = button_to_section.get(button_id)
        
        # Obtener secciones colapsadas actuales
        collapsed_sections = set(current_state.get('collapsed_sections', [])) if current_state else set()
        
        if clicked_section == 'RENDIMIENTO GLOBAL':
            # Clic en Global: Colapsar/Expandir TODAS las secciones
            all_sections = ['ESTILO', 'RENDIMIENTO OFENSIVO', 'RENDIMIENTO DEFENSIVO', 'RENDIMIENTO FÍSICO', 'BALÓN PARADO']
            
            if len(collapsed_sections) == len(all_sections):
                # Ya están todas colapsadas → expandir todas
                collapsed_sections = set()
            else:
                # Algunas expandidas → colapsar todas
                collapsed_sections = set(all_sections)
        elif clicked_section:
            # Clic en sección individual
            if clicked_section in collapsed_sections:
                # Si ya está colapsada, expandirla
                collapsed_sections.discard(clicked_section)
            else:
                # Si está expandida, colapsarla
                collapsed_sections.add(clicked_section)
    
    # Reconstruir heatmap con el nombre del equipo seleccionado
    heatmap_html = build_custom_heatmap_html(df, rankings_compuestos, collapsed_sections, selected_team)
    
    return heatmap_html, {'collapsed_sections': list(collapsed_sections)}


@callback(
    Output('selected-team-store', 'data'),
    Output({'type': 'team-shield', 'team': ALL}, 'style'),
    Input({'type': 'team-shield', 'team': ALL}, 'n_clicks'),
    State('selected-team-store', 'data'),
    prevent_initial_call=True
)
def handle_team_selection(n_clicks_list, current_team):
    """Maneja la selección de equipo mediante clics en escudos"""
    
    ctx = dash.callback_context
    if not ctx.triggered:
        # Estilos iniciales con RC Deportivo seleccionado
        return dash.no_update, dash.no_update
    
    # Obtener el equipo clicado
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    import json
    clicked_team_dict = json.loads(triggered_id)
    selected_team = clicked_team_dict['team']
    
    # Lista de equipos (debe coincidir con team_selector_premium)
    equipos = [
        "RC Deportivo", "Albacete BP", "Burgos CF", "CD Castellón", "CD Leganés",
        "CD Mirandés", "Ceuta", "Cultural", "Cádiz CF", "Córdoba CF",
        "FC Andorra", "Granada CF", "Málaga CF", "Real Racing Club", "Real Sociedad B",
        "Real Sporting", "Real Valladolid CF", "Real Zaragoza", "SD Eibar",
        "SD Huesca", "UD Almería", "UD Las Palmas"
    ]
    
    # Crear estilos para todos los escudos
    styles = []
    for equipo in equipos:
        if equipo == selected_team:
            # Estilo para el equipo seleccionado
            style = {
                'width': '100%',
                'height': '100%',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease',
                'border': '3px solid #007bff',
                'borderRadius': '50%',
                'padding': '2px',
                'backgroundColor': 'white',
                'boxShadow': '0 4px 12px rgba(0,123,255,0.5)',
                'transform': 'scale(1.1)',
                'objectFit': 'contain'
            }
        else:
            # Estilo normal
            style = {
                'width': '100%',
                'height': '100%',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease',
                'border': '2px solid transparent',
                'borderRadius': '50%',
                'padding': '2px',
                'backgroundColor': 'white',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'objectFit': 'contain'
            }
        styles.append(style)
    
    return selected_team, styles


# Callback para manejar descarga del heatmap usando html2canvas
from dash import clientside_callback, ClientsideFunction

clientside_callback(
    """
    function(n_clicks, selected_team) {
        if (n_clicks && n_clicks > 0) {
            // Esperar a que html2canvas esté disponible
            setTimeout(function() {
                if (typeof html2canvas === 'undefined') {
                    alert('html2canvas no está cargado. Por favor, recarga la página.');
                    return;
                }
                
                const captureArea = document.getElementById('heatmap-capture-area');
                if (!captureArea) {
                    alert('No se encontró el área de captura.');
                    return;
                }
                
                // Obtener equipo seleccionado (por defecto RC Deportivo)
                const teamName = selected_team || 'RC Deportivo';
                
                // Crear escudo temporalmente para la captura
                const shield = document.createElement('img');
                shield.id = 'temp-shield-for-capture';
                shield.src = '/assets/escudos/' + teamName + '.png';
                shield.style.position = 'absolute';
                shield.style.top = '10px';
                shield.style.right = '10px';
                shield.style.width = '80px';
                shield.style.height = '80px';
                shield.style.objectFit = 'contain';
                shield.style.zIndex = '1000';
                shield.style.backgroundColor = 'white';
                shield.style.borderRadius = '8px';
                shield.style.padding = '5px';
                shield.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
                
                // Añadir escudo al área de captura
                captureArea.appendChild(shield);
                
                // Esperar a que la imagen cargue
                shield.onload = function() {
                    // Configuración de alta calidad para html2canvas
                    html2canvas(captureArea, {
                        scale: 2,  // Alta resolución (2x)
                        useCORS: true,  // Permitir imágenes de otros dominios
                        allowTaint: true,
                        backgroundColor: '#ffffff',
                        logging: false,
                        width: captureArea.scrollWidth,
                        height: captureArea.scrollHeight
                    }).then(function(canvas) {
                        // Eliminar escudo temporal
                        captureArea.removeChild(shield);
                        
                        // Convertir canvas a blob y descargar
                        canvas.toBlob(function(blob) {
                            const url = URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            link.download = teamName.replace(/ /g, '_') + '_Heatmap_Rendimiento.png';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            URL.revokeObjectURL(url);
                        });
                    }).catch(function(error) {
                        // Eliminar escudo en caso de error
                        if (captureArea.contains(shield)) {
                            captureArea.removeChild(shield);
                        }
                        console.error('Error al capturar imagen:', error);
                        alert('Error al generar la imagen. Por favor, inténtalo de nuevo.');
                    });
                };
                
                // Si la imagen no carga (error), eliminar el elemento
                shield.onerror = function() {
                    captureArea.removeChild(shield);
                    alert('No se pudo cargar el escudo del equipo.');
                };
                
            }, 300);  // Dar tiempo para que cargue html2canvas
        }
        return '';
    }
    """,
    Output('download-trigger', 'children'),
    [Input('btn-download-heatmap', 'n_clicks')],
    [State('selected-team-store', 'data')],
    prevent_initial_call=True
)


# Layout dinámico: se ejecuta cada vez que se accede a la página
def layout():
    return build_layout()
