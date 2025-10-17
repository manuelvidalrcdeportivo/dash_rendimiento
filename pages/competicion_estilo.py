"""
Evolutivo Estilo: Página dedicada a métricas de Estilo de juego
Estructura: ESTILO GLOBAL con 3 sub-rankings (Identidad General, Ofensiva, Defensiva)
"""

from dash import html, dcc, callback, Input, Output, State, ALL, clientside_callback, ClientsideFunction
from utils.db_manager import (get_indicadores_rendimiento_laliga, get_rankings_compuestos_laliga, 
                               get_all_teams_rankings_laliga, get_metric_evolution_by_matchday, 
                               get_match_opponents_by_matchday, get_metric_info_from_name,
                               get_laliga_db_connection)
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash

# Mapeo de nombres originales a nombres cortos para visualización
METRIC_NAME_MAPPING_ESTILO = {
    # Identidad General
    "Iniciativa de Juego (Puntos)": "Iniciativa de Juego",
    "Centroide colectivo global": "Centroide colectivo",
    
    # Identidad Ofensiva
    "Posesión del Balón (%)": "% Posesión",
    "Elaboración Ofensiva (Pases/Posesión)": "Elaboración Ofensiva",
    "Ritmo de Circulación (Pases/Min)": "Ritmo Circulación",
    "Modo de Canalización (% Pase Largo)": "% Pase Largo",
    "Centros totales (Nº)": "Centros",
    
    # Identidad Defensiva
    "Recuperaciones en campo contrario (% Total)": "% Recup. campo contrario",
    "Recuperaciones Rápidas <5 (%)": "% Recuperaciones Rápidas",
    "Ritmo de Recuperación (Recuperaciones/Min)": "Ritmo Recuperación",
    "Recuperaciones totales / Altura media (Propia Puerta m.)": "Altura media recuperación",
}

# Definición de grupos usando nombres originales (para mapeo con BD)
GROUPS_ORIGINAL_ESTILO = [
    ("Identidad General", [
        "Iniciativa de Juego (Puntos)",
        "Centroide colectivo global",
    ]),
    ("Identidad Ofensiva", [
        "Posesión del Balón (%)",
        "Elaboración Ofensiva (Pases/Posesión)",
        "Ritmo de Circulación (Pases/Min)",
        "Modo de Canalización (% Pase Largo)",
        "Centros totales (Nº)",
    ]),
    ("Identidad Defensiva", [
        "Recuperaciones en campo contrario (% Total)",
        "Recuperaciones Rápidas <5 (%)",
        "Ritmo de Recuperación (Recuperaciones/Min)",
        "Recuperaciones totales / Altura media (Propia Puerta m.)",
    ]),
]

# Definición de grupos con nombres cortos (para visualización)
GROUPS_ESTILO = [
    ("Identidad General", [
        "Iniciativa de Juego",
        "Centroide colectivo",
    ]),
    ("Identidad Ofensiva", [
        "% Posesión",
        "Elaboración Ofensiva",
        "Ritmo Circulación",
        "% Pase Largo",
        "Centros",
    ]),
    ("Identidad Defensiva", [
        "% Recup. campo contrario",
        "% Recuperaciones Rápidas",
        "Ritmo Recuperación",
        "Altura media recuperación",
    ]),
]

# Mapeo de nombres de grupos a metric_id de rankings compuestos
GROUP_TO_RANKING_ID_ESTILO = {
    "Estilo Global": "RankingEstilo",
    "Identidad General": "RankingEstilo-IdentidadGeneral",
    "Identidad Ofensiva": "RankingEstilo-IdentidadOfensiva", 
    "Identidad Defensiva": "RankingEstilo-IdentidadDefensiva"
}


# ============================================================================
# FUNCIONES AUXILIARES PARA DIAGRAMA DE DISPERSIÓN
# ============================================================================

def get_scatter_data_estilo(metric_x, metric_y):
    """Obtiene datos para scatter plot de Estilo desde la BD"""
    try:
        engine = get_laliga_db_connection()
        if not engine:
            return None
        
        query = f"""
        SELECT 
            team_name,
            metric_id,
            metric_value
        FROM indicadores_rendimiento
        WHERE metric_id IN ('{metric_x}', '{metric_y}')
        ORDER BY team_name, metric_id
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return None
        
        # Pivotar para tener una fila por equipo con ambas métricas
        df_pivot = df.pivot(index='team_name', columns='metric_id', values='metric_value').reset_index()
        
        # Verificar que tenemos ambas columnas
        if metric_x not in df_pivot.columns or metric_y not in df_pivot.columns:
            return None
        
        return df_pivot
        
    except Exception as e:
        print(f"Error obteniendo datos scatter estilo: {e}")
        return None


def create_scatter_plot_estilo(metric_x, metric_y, label_x, label_y, invert_y=False, custom_title=None):
    """Crea un scatter plot de Estilo con escudos de equipos y líneas medias"""
    
    # Obtener datos
    df = get_scatter_data_estilo(metric_x, metric_y)
    
    if df is None or df.empty:
        return html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle fa-2x mb-3", style={"color": "#dc3545"}),
                html.P("No hay datos disponibles para este diagrama", style={"color": "#6c757d"})
            ], style={"textAlign": "center", "padding": "100px 20px"})
        ])
    
    # Añadir jitter para evitar solapamientos
    np.random.seed(42)
    
    # Calcular rangos
    x_range = df[metric_x].max() - df[metric_x].min()
    y_range = df[metric_y].max() - df[metric_y].min()
    
    # Añadir jitter muy pequeño (0.3% del rango)
    df['x_jitter'] = df[metric_x] + np.random.uniform(-x_range*0.003, x_range*0.003, len(df))
    df['y_jitter'] = df[metric_y] + np.random.uniform(-y_range*0.003, y_range*0.003, len(df))
    
    # Calcular medias para las líneas
    mean_x = df[metric_x].mean()
    mean_y = df[metric_y].mean()
    
    fig = go.Figure()
    
    # Añadir líneas medias punteadas
    fig.add_hline(
        y=mean_y, 
        line_dash="dash", 
        line_color="#6c757d",
        line_width=2,
        opacity=0.5
    )
    
    fig.add_vline(
        x=mean_x, 
        line_dash="dash", 
        line_color="#6c757d",
        line_width=2,
        opacity=0.5
    )
    
    # Añadir puntos invisibles para el hover
    for idx, row in df.iterrows():
        team = row['team_name']
        x_val = row['x_jitter']
        y_val = row['y_jitter']
        
        fig.add_trace(go.Scatter(
            x=[x_val],
            y=[y_val],
            mode='markers',
            marker=dict(
                size=35,
                color='rgba(0,0,0,0)',
                line=dict(width=0)
            ),
            hovertemplate=f'<b>{team}</b><br>' +
                         f'{label_x}: %{{x:.2f}}<br>' +
                         f'{label_y}: %{{y:.2f}}<extra></extra>',
            showlegend=False,
            name=team
        ))
    
    # Añadir círculos azules para RC Deportivo
    for idx, row in df.iterrows():
        team = row['team_name']
        if team == 'RC Deportivo':
            x_val = row['x_jitter']
            y_val = row['y_jitter']
            
            fig.add_trace(go.Scatter(
                x=[x_val],
                y=[y_val],
                mode='markers',
                marker=dict(
                    size=65,
                    color='rgba(0,0,0,0)',
                    line=dict(width=4, color='#007bff')
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Tamaño de las imágenes en unidades de datos (aumentado)
    img_size_x = x_range * 0.18
    img_size_y = y_range * 0.18
    
    # Añadir escudos como imágenes
    images = []
    for idx, row in df.iterrows():
        team = row['team_name']
        x_val = row['x_jitter']
        y_val = row['y_jitter']
        
        images.append(dict(
            source=f'/assets/Escudos/{team}.png',
            xref="x",
            yref="y",
            x=x_val,
            y=y_val,
            sizex=img_size_x,
            sizey=img_size_y,
            xanchor="center",
            yanchor="middle",
            sizing="contain",
            layer="above"
        ))
    
    # Configurar rangos con margen
    x_min = df[metric_x].min() - x_range * 0.08
    x_max = df[metric_x].max() + x_range * 0.08
    y_min = df[metric_y].min() - y_range * 0.08
    y_max = df[metric_y].max() + y_range * 0.08
    
    # Añadir anotaciones para las etiquetas de los ejes
    annotations = [
        # Eje Y - Superior (Presionante)
        dict(
            text="+ Presionante",
            xref="paper", yref="y",
            x=-0.03, y=y_max,
            showarrow=False,
            font=dict(size=17, color='#6c757d', family='Montserrat'),
            xanchor='center', yanchor='bottom',
            textangle=-90  # Rotación vertical como el título del eje Y
        ),
        # Eje Y - Inferior (Replegante)
        dict(
            text="+ Replegante",
            xref="paper", yref="y",
            x=-0.03, y=y_min,
            showarrow=False,
            font=dict(size=17, color='#6c757d', family='Montserrat'),
            xanchor='center', yanchor='top',
            textangle=-90  # Rotación vertical como el título del eje Y
        ),
        # Eje X - Derecha (Asociativo)
        dict(
            text="+ Asociativo",
            xref="x", yref="paper",
            x=x_max, y=-0.08,
            showarrow=False,
            font=dict(size=17, color='#6c757d', family='Montserrat'),
            xanchor='right', yanchor='top'
        ),
        # Eje X - Izquierda (Directo)
        dict(
            text="+ Directo",
            xref="x", yref="paper",
            x=x_min, y=-0.08,
            showarrow=False,
            font=dict(size=17, color='#6c757d', family='Montserrat'),
            xanchor='left', yanchor='top'
        )
    ]
    
    # Configurar layout SIN título
    fig.update_layout(
        xaxis=dict(
            title=dict(
                text=f"<b>{label_x}</b>", 
                font=dict(size=18, color='#1e3d59', family='Montserrat')
            ),
            gridcolor='rgba(233, 236, 239, 0.5)',
            showgrid=True,
            zeroline=False,
            range=[x_min, x_max],
            showticklabels=False,  # Quitar los ticks numéricos
            ticks=""  # Quitar las marcas de los ticks
        ),
        yaxis=dict(
            title=dict(
                text=f"<b>{label_y}</b>", 
                font=dict(size=18, color='#1e3d59', family='Montserrat')
            ),
            gridcolor='rgba(233, 236, 239, 0.5)',
            showgrid=True,
            zeroline=False,
            range=[y_min, y_max],
            autorange='reversed' if invert_y else True,
            showticklabels=False,  # Quitar los ticks numéricos
            ticks=""  # Quitar las marcas de los ticks
        ),
        images=images,
        annotations=annotations,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        height=750,  # Aumentado de 600 a 750
        margin=dict(l=80, r=120, t=40, b=80),  # Más margen derecha y abajo para etiquetas
        font=dict(family='Montserrat'),
        showlegend=False
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={'height': '750px'}  # Aumentado también aquí
    )


# ============================================================================
# FUNCIONES AUXILIARES PARA PROCESAMIENTO DE DATOS
# ============================================================================

def fetch_indicadores_estilo_laliga(team_name="RC Deportivo"):
    """Obtiene indicadores de estilo desde la BD LaLiga"""
    try:
        df = get_indicadores_rendimiento_laliga(team_name)
        if df.empty:
            return None
        
        # Filtrar solo métricas de estilo
        all_estilo_metrics = []
        for _, metrics in GROUPS_ORIGINAL_ESTILO:
            all_estilo_metrics.extend(metrics)
        
        filtered_df = df[df['metrica'].isin(all_estilo_metrics)].copy()
        
        # Aplicar mapeo a nombres cortos
        filtered_df['metrica_original'] = filtered_df['metrica']
        filtered_df['metrica'] = filtered_df['metrica'].map(METRIC_NAME_MAPPING_ESTILO).fillna(filtered_df['metrica'])
        
        return filtered_df
    except Exception:
        return None


def _order_metrics_by_groups_estilo(df: pd.DataFrame):
    """Ordena métricas según GROUPS_ESTILO"""
    all_metrics = df['metrica'].tolist()
    ordered = []
    group_pos = {}
    for gname, metrics in GROUPS_ESTILO:
        present = [m for m in metrics if m in all_metrics]
        if present:
            start = len(ordered)
            ordered.extend(present)
            end = len(ordered) - 1
            group_pos[gname] = (start, end, present)
    leftovers = [m for m in all_metrics if m not in ordered]
    ordered.extend(leftovers)
    return ordered, group_pos


def _get_color_for_ranking(ranking):
    """Obtiene el color basado en el ranking"""
    if ranking is None:
        return '#cccccc'
    if ranking <= 6:
        return '#2ecc71'
    elif ranking <= 16:
        return '#f1c40f'
    else:
        return '#e74c3c'


# ============================================================================
# LAYOUT
# ============================================================================

def get_estilo_content():
    """Retorna el contenido de la sección Estilo con heatmap específico"""
    # Importar solo lo necesario de evolutivo temporada para reutilizar estructura
    from pages.competicion_evolutivo_temporada import (
        team_selector_premium, 
        legend_block,
        description_block
    )
    
    return html.Div([
        # Inyectar CSS para tooltips personalizados y html2canvas
        html.Div([
            html.Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap'),
            html.Script(src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js')
        ]),
        
        # Toolbar de acciones (botón descarga) alineado a la derecha
        html.Div([
            html.Button(
                html.Img(
                    src='/assets/download.png',
                    style={
                        'width': '20px',
                        'height': '20px',
                        'objectFit': 'contain'
                    }
                ),
                id='btn-download-heatmap-estilo',
                title="Descargar Heatmap como PNG",
                style={
                    'backgroundColor': 'transparent',
                    'border': 'none',
                    'padding': '6px',
                    'cursor': 'pointer',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },
                n_clicks=0
            ),
            # Div invisible para el callback
            html.Div(id='download-trigger-estilo', style={'display': 'none'})
        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '8px', 'margin': '0px 0 0 0'}),
        
        # ====================================================================
        # SECCIÓN: DIAGRAMA DE ESTILO
        # ====================================================================
        html.Div([
            # Título del bloque
            html.Div([
                html.I(className="fas fa-palette me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
                html.H4("Diagrama de Estilo", style={"color": "#1e3d59", "display": "inline"})
            ], className="mb-4"),
            
            # Contenedor del diagrama (sin box intermedia)
            dcc.Loading(
                id="loading-diagrama-estilo",
                type="circle",
                color="#1e3d59",
                children=[
                    html.Div(
                        id="diagrama-estilo-container",
                        children=[
                            create_scatter_plot_estilo(
                                metric_x="ValesEstiloOf",
                                metric_y="ValesEstiloDef",
                                label_x="Estilo Ofensivo",
                                label_y="Estilo Defensivo",
                                custom_title="Diagrama Vales de Estilo"
                            )
                        ]
                    )
                ]
            )
        ], style={"marginBottom": "40px"}),
        
        # Separador visual
        html.Hr(style={'margin': '40px 0', 'borderTop': '2px solid #e9ecef'}),
        
        # ====================================================================
        # SECCIÓN: PERFIL DE ESTILO
        # ====================================================================
        html.Div([
            html.I(className="fas fa-chart-bar me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
            html.H4("Perfil de Estilo", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-4"),
        
        # Selector Premium de Equipos
        team_selector_premium(),
        
        # Store para guardar el estado de las secciones colapsadas
        dcc.Store(id='view-state-store-estilo', data={'collapsed_sections': []}),

        # Contenedor del heatmap HTML personalizado con loader
        dcc.Loading(
            id='loading-heatmap-estilo',
            type='circle',
            color='#007bff',
            children=[
                html.Div([
                    # Contenedor para captura
                    html.Div([
                        # Contenedor del heatmap (rellenado por callback)
                        html.Div(
                            id='custom-heatmap-container-estilo',
                            children=[html.Div(id='heatmap-initial-placeholder-estilo', style={'height': '260px'})],
                            style={'marginTop': '5px', 'marginBottom': '0px'}
                        )
                    ], id='heatmap-capture-area-estilo', style={'position': 'relative', 'backgroundColor': 'white', 'padding': '0px', 'paddingBottom': '0px', 'marginBottom': '0px'}),
                    
                    # Leyenda justo debajo del heatmap
                    html.Div(
                        legend_block(),
                        style={
                            'display': 'flex',
                            'justifyContent': 'flex-end',
                            'marginTop': '5px',
                            'marginRight': '10px',
                            'marginBottom': '0px',
                            'backgroundColor': 'rgba(255, 255, 255, 0.96)',
                            'padding': '6px 10px',
                            'borderRadius': '6px',
                            'boxShadow': '0 2px 6px rgba(0,0,0,0.12)',
                            'border': '1px solid rgba(0,0,0,0.08)',
                            'width': 'fit-content',
                            'marginLeft': 'auto'
                        }
                    ),
                    # Descripción
                    html.Div(
                        description_block(),
                        style={'marginTop': '4px', 'marginBottom': '0px'}
                    )
                ], style={'marginBottom': '0px', 'paddingBottom': '0px', 'display': 'flex', 'flexDirection': 'column', 'gap': '4px'})
            ],
            style={'marginBottom': '0px', 'paddingBottom': '0px', 'minHeight': '0px'}
        ),
        
        # Separador visual
        html.Hr(style={'margin': '40px 0', 'borderTop': '2px solid #e9ecef'}),
        
        # ====================================================================
        # SECCIÓN: EVOLUTIVO DE MÉTRICAS
        # ====================================================================
        html.Div([
            # Título del bloque
            html.Div([
                html.I(className="fas fa-chart-area me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
                html.H4("Evolutivo de Métricas", style={"color": "#1e3d59", "display": "inline"})
            ], className="mb-4"),
            
            # Contenedor del evolutivo (sin box intermedia)
            html.P("Selecciona una métrica para ver su evolución jornada a jornada:",
                  style={
                      'color': '#6c757d',
                      'fontFamily': 'Montserrat, sans-serif',
                      'marginBottom': '15px',
                      'fontSize': '14px'
                  }),
            dcc.Dropdown(
                id='metric-evolution-selector-estilo',
                options=[
                    {'label': METRIC_NAME_MAPPING_ESTILO[metric], 'value': metric}
                    for group_name, metrics in GROUPS_ORIGINAL_ESTILO
                    for metric in metrics
                ],
                value=GROUPS_ORIGINAL_ESTILO[0][1][0] if GROUPS_ORIGINAL_ESTILO else None,  # Primera métrica por defecto
                placeholder='Selecciona una métrica...',
                style={
                    'fontFamily': 'Montserrat, sans-serif',
                    'marginBottom': '20px'
                }
            ),
            
            # Contenedor del gráfico evolutivo con loading
            dcc.Loading(
                id='loading-evolution-estilo',
                type='circle',
                color='#1e3d59',
                children=[html.Div(id='metric-evolution-graph-estilo', children=[])]
            )
        ], style={"marginBottom": "40px"})
    ])


# ============================================================================
# FUNCIONES AUXILIARES PARA PROCESAMIENTO DE DATOS
# ============================================================================

def fetch_indicadores_estilo_laliga(team_name="RC Deportivo"):
    """Obtiene indicadores de estilo desde la BD LaLiga"""
    try:
        df = get_indicadores_rendimiento_laliga(team_name)
        if df.empty:
            return None
        
        # Filtrar solo métricas de estilo
        all_estilo_metrics = []
        for _, metrics in GROUPS_ORIGINAL_ESTILO:
            all_estilo_metrics.extend(metrics)
        
        filtered_df = df[df['metrica'].isin(all_estilo_metrics)].copy()
        
        # Aplicar mapeo a nombres cortos
        filtered_df['metrica_original'] = filtered_df['metrica']
        filtered_df['metrica'] = filtered_df['metrica'].map(METRIC_NAME_MAPPING_ESTILO).fillna(filtered_df['metrica'])
        
        return filtered_df
    except Exception:
        return None


def _order_metrics_by_groups_estilo(df: pd.DataFrame):
    """Ordena métricas según GROUPS_ESTILO"""
    all_metrics = df['metrica'].tolist()
    ordered = []
    group_pos = {}
    for gname, metrics in GROUPS_ESTILO:
        present = [m for m in metrics if m in all_metrics]
        if present:
            start = len(ordered)
            ordered.extend(present)
            end = len(ordered) - 1
            group_pos[gname] = (start, end, present)
    leftovers = [m for m in all_metrics if m not in ordered]
    ordered.extend(leftovers)
    return ordered, group_pos


def _get_color_for_ranking(ranking):
    """Obtiene el color basado en el ranking"""
    if ranking is None:
        return '#cccccc'
    if ranking <= 6:
        return '#2ecc71'
    elif ranking <= 16:
        return '#f1c40f'
    else:
        return '#e74c3c'


def build_estilo_heatmap_html(df, rankings_compuestos, collapsed_sections=None, team_name='RC Deportivo'):
    """Construye el heatmap HTML específico para Estilo"""
    from pages.competicion_evolutivo_temporada import build_heatmap_components
    
    if df is None or df.empty:
        return html.Div([
            html.P("⚠️ NO HAY DATOS DE ESTILO DISPONIBLES", 
                  style={'textAlign': 'center', 'color': '#dc3545', 'padding': '40px'})
        ])
    
    if collapsed_sections is None:
        collapsed_sections = set()
    
    # Obtener datos organizados usando funciones de Estilo
    ordered_metrics, group_pos = _order_metrics_by_groups_estilo(df)
    df_by_metric = {row['metrica']: row for _, row in df.iterrows()}
    
    # Verificar si TODO está colapsado
    all_section_names = [name for name in group_pos.keys()]
    all_collapsed = all(name.upper() in collapsed_sections for name in all_section_names)
    
    # Construir lista de métricas considerando colapsados
    metrics_display = []
    groups_display = []
    current_col = 0
    
    # Si TODO está colapsado, mostrar solo RankingEstilo
    if all_collapsed:
        global_ranking_value = rankings_compuestos.get('RankingEstilo', 11)
        metrics_display.append({
            'name': 'Estilo Global',
            'short_name': 'Global',
            'ranking': int(global_ranking_value),
            'is_composite': True,
            'colspan': len(all_section_names),
            'ranking_id': 'RankingEstilo'
        })
        
        # Añadir grupos display vacíos
        col_idx = 0
        for gname, (start_idx, end_idx, present) in group_pos.items():
            if not present:
                continue
            ranking_id = GROUP_TO_RANKING_ID_ESTILO.get(gname)
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
                
            ranking_id = GROUP_TO_RANKING_ID_ESTILO.get(gname)
            group_ranking = rankings_compuestos.get(ranking_id, 11) if ranking_id in rankings_compuestos else 11
            num_metrics_in_group = len(present) if present else 1
            
            if gname.upper() in collapsed_sections:
                # Colapsado
                metrics_display.append({
                    'name': gname,
                    'short_name': gname[:15],
                    'ranking': int(group_ranking),
                    'is_composite': True,
                    'colspan': num_metrics_in_group,
                    'ranking_id': ranking_id
                })
                groups_display.append({
                    'name': gname,
                    'start_col': current_col,
                    'end_col': current_col,
                    'ranking': group_ranking,
                    'collapsed': True,
                    'visual_width': num_metrics_in_group
                })
                current_col += 1
            else:
                # Expandido
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
        reverse_mapping = {v: k for k, v in METRIC_NAME_MAPPING_ESTILO.items()}
        individual_metrics = []
        composite_ranking_ids = []
        
        for m in metrics_display:
            if m.get('is_composite') and m.get('ranking_id'):
                composite_ranking_ids.append(m['ranking_id'])
            else:
                individual_metrics.append(m['name'])
        
        original_metrics = [reverse_mapping.get(m, m) for m in individual_metrics]
        
        all_teams_rankings = {}
        if original_metrics:
            all_teams_rankings_original = get_all_teams_rankings_laliga(original_metrics)
            for original_name, rankings in all_teams_rankings_original.items():
                short_name = METRIC_NAME_MAPPING_ESTILO.get(original_name, original_name)
                all_teams_rankings[short_name] = rankings
        
        # Obtener datos de rankings compuestos para tooltips
        if composite_ranking_ids:
            try:
                from utils.db_manager import get_laliga_db_connection
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
                        temp_rankings = {}
                        for idx, row in df_composite.iterrows():
                            metric_id = row['metric_id']
                            ranking = int(row['ranking_position'])
                            team = row['team_name']
                            value = row['metric_value']
                            
                            if metric_id not in temp_rankings:
                                temp_rankings[metric_id] = {}
                            
                            if ranking not in temp_rankings[metric_id]:
                                temp_rankings[metric_id][ranking] = []
                            
                            temp_rankings[metric_id][ranking].append({
                                'team': team,
                                'value': value
                            })
                        
                        # Convertir a nombres de grupo y agrupar
                        for metric_id, rankings in temp_rankings.items():
                            # Encontrar el nombre del grupo correspondiente
                            group_name = None
                            for m in metrics_display:
                                if m.get('ranking_id') == metric_id:
                                    group_name = m['name']
                                    break
                            
                            if group_name:
                                # Agrupar equipos con misma posición
                                grouped = {}
                                for pos, teams_data in rankings.items():
                                    grouped[pos] = teams_data
                                all_teams_rankings[group_name] = grouped
            except Exception as e:
                pass  # Si falla, continuar sin tooltips de rankings compuestos
    except Exception as e:
        all_teams_rankings = {}
    
    # Usar ranking de Estilo en lugar de Rendimiento
    global_ranking = rankings_compuestos.get('RankingEstilo', 11)
    
    # Llamar a build_heatmap_components con el título correcto para Estilo
    return build_heatmap_components(
        metrics_display, 
        groups_display, 
        global_ranking, 
        all_teams_rankings, 
        team_name,
        title_prefix='ESTILO GLOBAL'
    )


# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    Output('custom-heatmap-container-estilo', 'children'),
    Output('view-state-store-estilo', 'data'),
    Input('selected-team-store', 'data'),
    State('view-state-store-estilo', 'data')
)
def build_initial_heatmap_estilo(selected_team, current_state):
    """Construye el heatmap de estilo en la carga inicial"""
    try:
        df = fetch_indicadores_estilo_laliga(selected_team or 'RC Deportivo')
    except Exception:
        df = None
    
    try:
        rankings_compuestos = get_rankings_compuestos_laliga(selected_team or 'RC Deportivo')
    except Exception:
        rankings_compuestos = {
            'RankingEstilo': 11,
            'RankingEstilo-IdentidadGeneral': 11,
            'RankingEstilo-IdentidadOfensiva': 11,
            'RankingEstilo-IdentidadDefensiva': 11
        }
    
    collapsed_sections = set(current_state.get('collapsed_sections', [])) if current_state else set()
    
    try:
        heatmap_html = build_estilo_heatmap_html(df, rankings_compuestos, collapsed_sections, selected_team or 'RC Deportivo')
    except Exception as e:
        heatmap_html = html.Div([
            html.P(f"Error generando heatmap: {str(e)}", 
                  style={'textAlign': 'center', 'color': '#dc3545', 'padding': '40px'})
        ])
    
    return heatmap_html, {'collapsed_sections': list(collapsed_sections)}


@callback(
    Output('custom-heatmap-container-estilo', 'children', allow_duplicate=True),
    Output('view-state-store-estilo', 'data', allow_duplicate=True),
    Input({'type': 'heatmap-block', 'index': ALL}, 'n_clicks'),
    [State('view-state-store-estilo', 'data'),
     State('selected-team-store', 'data')],
    prevent_initial_call=True
)
def handle_block_clicks_estilo(clicks_list, current_state, selected_team):
    """Maneja clics en los bloques del heatmap de estilo"""
    ctx = dash.callback_context
    
    # Si no hay trigger o todos los clicks son None/0, no hacer nada
    if not ctx.triggered or all((c is None or c == 0) for c in clicks_list):
        return dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Si el trigger no es un botón de heatmap, no hacer nada
    if not button_id or not button_id.startswith('{'):
        return dash.no_update, dash.no_update
    
    import json
    try:
        id_obj = json.loads(button_id)
        index = id_obj.get('index')
        # Mapeo de índices a nombres de secciones
        index_to_section = {
            'global': 'ESTILO GLOBAL',
            'identidad-general': 'IDENTIDAD GENERAL',
            'identidad-ofensiva': 'IDENTIDAD OFENSIVA',
            'identidad-defensiva': 'IDENTIDAD DEFENSIVA'
        }
        clicked_section = index_to_section.get(index)
    except Exception:
        return dash.no_update, dash.no_update
    
    if not clicked_section:
        return dash.no_update, dash.no_update
    
    # Actualizar secciones colapsadas
    collapsed_sections = set(current_state.get('collapsed_sections', [])) if current_state else set()
    
    # Lógica especial para click en Global: colapsar/expandir todo
    if clicked_section == 'ESTILO GLOBAL':
        all_sections = ['IDENTIDAD GENERAL', 'IDENTIDAD OFENSIVA', 'IDENTIDAD DEFENSIVA']
        if len(collapsed_sections) == len(all_sections):
            # Si todas están colapsadas, expandir todo
            collapsed_sections = set()
        else:
            # Si alguna está expandida, colapsar todo
            collapsed_sections = set(all_sections)
    elif clicked_section:
        # Toggle de sección individual
        if clicked_section in collapsed_sections:
            collapsed_sections.discard(clicked_section)
        else:
            collapsed_sections.add(clicked_section)
    
    # Obtener datos
    try:
        df = fetch_indicadores_estilo_laliga(selected_team or 'RC Deportivo')
    except Exception:
        df = None
    
    try:
        rankings_compuestos = get_rankings_compuestos_laliga(selected_team or 'RC Deportivo')
    except Exception:
        rankings_compuestos = {
            'RankingEstilo': 11,
            'RankingEstilo-IdentidadGeneral': 11,
            'RankingEstilo-IdentidadOfensiva': 11,
            'RankingEstilo-IdentidadDefensiva': 11
        }
    
    heatmap_html = build_estilo_heatmap_html(df, rankings_compuestos, collapsed_sections, selected_team or 'RC Deportivo')
    return heatmap_html, {'collapsed_sections': list(collapsed_sections)}


@callback(
    Output('metric-evolution-graph-estilo', 'children'),
    [Input('metric-evolution-selector-estilo', 'value'),
     Input('selected-team-store', 'data')]
)
def update_metric_evolution_estilo(selected_metric, team_data):
    """Actualiza el gráfico de evolución de una métrica de estilo"""
    if not selected_metric or not team_data:
        return html.Div()
    
    if isinstance(team_data, str):
        team_name = team_data
    elif isinstance(team_data, dict):
        team_name = team_data.get('team', 'RC Deportivo')
    else:
        team_name = 'RC Deportivo'
    
    # Obtener metric_id, metric_category y season_id
    metric_id, metric_category, season_id = get_metric_info_from_name(selected_metric, team_name)
    
    if not metric_id or not metric_category:
        return html.Div(
            "No se pudo obtener información de la métrica seleccionada.",
            style={'color': '#dc3545', 'fontFamily': 'Montserrat, sans-serif', 'padding': '20px'}
        )
    
    # Usar season_id de la BD o 1 por defecto
    if not season_id:
        season_id = 1
    
    # Obtener datos de evolución
    df_evolution = get_metric_evolution_by_matchday(team_name, metric_id, metric_category, season_id)
    
    # Obtener rivales por jornada
    opponents = get_match_opponents_by_matchday(team_name, season_id)
    
    if df_evolution.empty:
        return html.Div(
            f"No hay datos disponibles para {METRIC_NAME_MAPPING_ESTILO.get(selected_metric, selected_metric)}",
            style={'color': '#6c757d', 'fontFamily': 'Montserrat, sans-serif', 'padding': '20px'}
        )
    
    # Crear DataFrame con todas las 42 jornadas
    all_matchdays = pd.DataFrame({'match_day_number': range(1, 43)})
    df_full = all_matchdays.merge(df_evolution, on='match_day_number', how='left')
    
    # Calcular la media de los valores existentes
    mean_value = df_evolution['metric_value'].mean()
    
    # Crear el gráfico
    fig = go.Figure()
    
    # Agregar barras con información del rival en hover
    hover_texts = []
    for _, row in df_full.iterrows():
        matchday = int(row['match_day_number'])
        opponent = opponents.get(matchday, '')
        if pd.notna(row['metric_value']) and opponent:
            hover_texts.append(f"<b>Jornada {matchday}</b><br>vs {opponent}<br>Valor: {row['metric_value']:.2f}")
        elif pd.notna(row['metric_value']):
            hover_texts.append(f"<b>Jornada {matchday}</b><br>Valor: {row['metric_value']:.2f}")
        else:
            hover_texts.append(f"<b>Jornada {matchday}</b><br>Sin datos")
    
    fig.add_trace(go.Bar(
        x=df_full['match_day_number'],
        y=df_full['metric_value'],
        name='Valor',
        marker=dict(
            color='#1e3d59',
            opacity=0.8
        ),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts
    ))
    
    # Agregar línea de media discontinua
    fig.add_trace(go.Scatter(
        x=[1, 42],
        y=[mean_value, mean_value],
        mode='lines',
        name='Media',
        line=dict(color='#e74c3c', width=2, dash='dash'),
        hovertemplate=f'<b>Media:</b> {mean_value:.2f}<extra></extra>'
    ))
    
    metric_display_name = METRIC_NAME_MAPPING_ESTILO.get(selected_metric, selected_metric)
    
    fig.update_layout(
        title=f"Evolución de {metric_display_name}",
        xaxis_title="Jornada",
        yaxis_title=metric_display_name,
        font=dict(family="Montserrat", size=12),
        hovermode='x unified',
        plot_bgcolor='white',
        height=400,
        showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255,255,255,0.8)')
    )
    
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(0,0,0,0.1)',
        dtick=1,
        range=[0.5, 42.5]
    )
    fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


# Callback clientside para descargar el heatmap
clientside_callback(
    ClientsideFunction(namespace='heatmap', function_name='download_heatmap'),
    Output('download-trigger-estilo', 'children'),
    [Input('btn-download-heatmap-estilo', 'n_clicks')],
    [State('selected-team-store', 'data')],
    prevent_initial_call=True
)
