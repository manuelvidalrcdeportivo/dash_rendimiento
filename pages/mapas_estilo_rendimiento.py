# pages/mapas_estilo_rendimiento.py

from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
import plotly.graph_objects as go
import pandas as pd
from utils.layouts import standard_page
from utils.db_manager import get_laliga_db_connection

# Contenido de las pestañas
def get_evolucion_resultados_content():
    """Contenido de la pestaña Evolución Resultados"""
    return html.Div([
        html.Div([
            html.I(className="fas fa-chart-line me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
            html.H4("Evolución de Resultados", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-4"),
        html.P(
            "Aquí se mostrará la evolución de los resultados del equipo a lo largo de la temporada.",
            className="text-muted"
        )
    ], className="p-4")

def get_contextos_partidos_content():
    """Contenido de la pestaña Contextos de Partidos"""
    return html.Div([
        html.Div([
            html.I(className="fas fa-futbol me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
            html.H4("Contextos de Partidos", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-4"),
        html.P(
            "Análisis de los diferentes contextos de los partidos (local/visitante,dinámica de marcador, etc.).",
            className="text-muted"
        )
    ], className="p-4")

def get_scatter_data(metric_x, metric_y):
    """Obtiene datos para scatter plot desde la BD"""
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
        print(f"Error obteniendo datos scatter: {e}")
        return None

def create_scatter_plot(metric_x, metric_y, label_x, label_y, invert_y=False, custom_title=None):
    """Crea un scatter plot con escudos de equipos y líneas medias"""
    
    # Título: personalizado o automático
    title = custom_title if custom_title else f"{label_x} vs {label_y}"
    
    # Obtener datos
    df = get_scatter_data(metric_x, metric_y)
    
    if df is None or df.empty:
        return html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle fa-2x mb-3", style={"color": "#dc3545"}),
                html.P("No hay datos disponibles para este diagrama", style={"color": "#6c757d"})
            ], style={"textAlign": "center", "padding": "100px 20px"})
        ])
    
    # Añadir jitter para evitar solapamientos (pequeña variación aleatoria)
    import numpy as np
    np.random.seed(42)  # Para reproducibilidad
    
    # Calcular rangos
    x_range = df[metric_x].max() - df[metric_x].min()
    y_range = df[metric_y].max() - df[metric_y].min()
    
    # Añadir jitter muy pequeño (0.3% del rango) para separar puntos solapados
    df['x_jitter'] = df[metric_x] + np.random.uniform(-x_range*0.003, x_range*0.003, len(df))
    df['y_jitter'] = df[metric_y] + np.random.uniform(-y_range*0.003, y_range*0.003, len(df))
    
    # Calcular medias para las líneas (usar valores originales)
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
    
    # Añadir puntos invisibles para el hover (mantener interactividad)
    for idx, row in df.iterrows():
        team = row['team_name']
        x_val = row['x_jitter']  # Usar valores con jitter
        y_val = row['y_jitter']
        
        fig.add_trace(go.Scatter(
            x=[x_val],
            y=[y_val],
            mode='markers',
            marker=dict(
                size=25,
                color='rgba(0,0,0,0)',  # Transparente
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
            x_val = row['x_jitter']  # Usar valores con jitter
            y_val = row['y_jitter']
            
            fig.add_trace(go.Scatter(
                x=[x_val],
                y=[y_val],
                mode='markers',
                marker=dict(
                    size=48,  # Más grande para rodear bien el escudo
                    color='rgba(0,0,0,0)',
                    line=dict(width=3, color='#007bff')
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Tamaño de las imágenes (ya calculamos x_range e y_range arriba)
    
    # Tamaño de las imágenes en unidades de datos (proporcional al rango)
    img_size_x = x_range * 0.19  # 4% del rango X
    img_size_y = y_range * 0.19  # 4% del rango Y
    
    # Añadir escudos como imágenes
    images = []
    for idx, row in df.iterrows():
        team = row['team_name']
        x_val = row['x_jitter']  # Usar valores con jitter
        y_val = row['y_jitter']
        
        # Mismo tamaño para todos (el destacado es con el círculo azul)
        size_multiplier = 1.0
        
        images.append(dict(
            source=f'/assets/Escudos/{team}.png',
            xref="x",
            yref="y",
            x=x_val,
            y=y_val,
            sizex=img_size_x * size_multiplier,
            sizey=img_size_y * size_multiplier,
            xanchor="center",
            yanchor="middle",
            sizing="contain",
            layer="above"
        ))
    
    # Configurar layout con fondo transparente y más espacio
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color='#1e3d59', family='Montserrat', weight='bold'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text=label_x, font=dict(size=14, color='#495057', family='Montserrat')),
            gridcolor='rgba(233, 236, 239, 0.5)',
            showgrid=True,
            zeroline=False,  # Ocultar línea del cero
            # Añadir margen para aprovechar más espacio
            range=[df[metric_x].min() - x_range * 0.08, df[metric_x].max() + x_range * 0.08]
        ),
        yaxis=dict(
            title=dict(text=label_y, font=dict(size=14, color='#495057', family='Montserrat')),
            gridcolor='rgba(233, 236, 239, 0.5)',
            showgrid=True,
            zeroline=False,  # Ocultar línea del cero
            # Añadir margen para aprovechar más espacio
            range=[df[metric_y].min() - y_range * 0.08, df[metric_y].max() + y_range * 0.08],
            # Invertir eje si es necesario (para métricas donde menos es mejor)
            autorange='reversed' if invert_y else True
        ),
        images=images,
        plot_bgcolor='rgba(0,0,0,0)',  # Transparente
        paper_bgcolor='rgba(0,0,0,0)',  # Transparente
        hovermode='closest',
        height=600,  # Más alto
        margin=dict(l=70, r=30, t=60, b=70),  # Ajustar márgenes
        font=dict(family='Montserrat')
    )
    
    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={'height': '600px'}
    )

def get_mapas_rendimiento_content():
    """Contenido de la pestaña Mapas de Rendimiento"""
    return html.Div([
        # BLOQUE 1: GOLES
        create_scatter_block(
            block_id="goles",
            title="Goles",
            icon="fa-futbol",
            options=[
                {"label": "Totales", "value": "totales"},
                {"label": "Juego Dinámico", "value": "juego_dinamico"},
                {"label": "Balón Parado", "value": "balon_parado"}
            ],
            default_option="totales"
        ),
        
        # BLOQUE 2: EFICACIA
        create_scatter_block(
            block_id="eficacia",
            title="Eficacia",
            icon="fa-bullseye",
            options=[
                {"label": "Ofensiva", "value": "ofensiva"},
                {"label": "Defensiva", "value": "defensiva"},
                {"label": "Peligrosidad", "value": "peligrosidad"}
            ],
            default_option="ofensiva"
        ),
        
        # BLOQUE 3: FUNCIONALIDAD
        create_scatter_block(
            block_id="funcionalidad",
            title="Funcionalidad",
            icon="fa-cogs",
            options=[
                {"label": "Profundidad Ofensiva", "value": "profundidad_ofensiva"},
                {"label": "Agresividad-Intensidad Def.", "value": "agresividad_intensidad"}
            ],
            default_option="profundidad_ofensiva"
        ),
        
        # BLOQUE 4: FÍSICO-COMBATIVIDAD
        create_scatter_block(
            block_id="fisico_combatividad",
            title="Físico - Combatividad",
            icon="fa-running",
            options=[
                {"label": "Volumen - Calidad Esfuerzo", "value": "volumen_calidad"},
                {"label": "Faltas", "value": "faltas"}
            ],
            default_option="volumen_calidad"
        )
    ], className="p-4")

def create_scatter_block(block_id, title, icon, options, default_option):
    """Crea un bloque con selector y diagrama de dispersión"""
    return html.Div([
        # Título del bloque con fondo azul
        html.Div([
            html.I(className=f"fas {icon} me-3", style={"fontSize": "22px", "color": "white"}),
            html.H4(title, style={"color": "white", "display": "inline", "fontWeight": "700", "margin": "0"})
        ], style={
            "backgroundColor": "#1e3d59",
            "padding": "15px 20px",
            "borderRadius": "8px 8px 0 0",
            "marginBottom": "0"
        }),
        
        # Contenedor principal dividido en 2 columnas
        html.Div([
            # Columna izquierda: Selectores
            html.Div([
                html.Div([
                    html.Button(
                        opt["label"],
                        id={"type": f"{block_id}-option", "index": opt["value"]},
                        className="scatter-option-btn",
                        style={
                            "width": "100%",
                            "padding": "12px 15px",
                            "marginBottom": "10px",
                            "border": "2px solid #1e3d59" if opt["value"] == default_option else "2px solid #e9ecef",
                            "backgroundColor": "#1e3d59" if opt["value"] == default_option else "white",
                            "color": "white" if opt["value"] == default_option else "#6c757d",
                            "borderRadius": "8px",
                            "cursor": "pointer",
                            "fontWeight": "600" if opt["value"] == default_option else "500",
                            "fontSize": "13px",
                            "transition": "all 0.2s ease",
                            "textAlign": "center"
                        }
                    ) for opt in options
                ])
            ], style={
                "width": "20%",
                "paddingRight": "15px",
                "paddingTop": "20px"
            }),
            
            # Columna derecha: Diagrama de dispersión
            html.Div([
                dcc.Loading(
                    id=f"loading-{block_id}",
                    type="circle",
                    color="#1e3d59",
                    children=[
                        html.Div(
                            id=f"{block_id}-scatter-plot",
                            children=create_placeholder_scatter(block_id, default_option),
                            style={
                                "backgroundColor": "#f8f9fa",
                                "borderRadius": "8px",
                                "padding": "30px",
                                "minHeight": "600px",
                                "height": "100%"
                            }
                        )
                    ]
                )
            ], style={
                "width": "80%",
                "borderLeft": "2px solid #e9ecef",
                "paddingLeft": "15px",
                "paddingTop": "20px",
                "paddingBottom": "20px"
            })
        ], style={
            "display": "flex",
            "width": "100%",
            "backgroundColor": "white"
        }),
        
        # Store para guardar la opción seleccionada
        dcc.Store(id=f"{block_id}-selected-option", data=default_option)
        
    ], style={
        "marginBottom": "40px",
        "padding": "0",
        "backgroundColor": "white",
        "borderRadius": "10px",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
        "overflow": "hidden"
    })

def create_placeholder_scatter(block_id, option):
    """Crea un placeholder para el diagrama de dispersión"""
    return html.Div([
        html.Div([
            html.I(className="fas fa-chart-scatter fa-3x mb-3", style={"color": "#6c757d"}),
            html.H6(f"Diagrama de Dispersión", style={"color": "#6c757d"}),
            html.P(f"Opción: {option}", className="text-muted small")
        ], style={
            "textAlign": "center",
            "padding": "60px 20px"
        })
    ])

# Layout principal
layout = standard_page([
    # Título
    html.Div([
        html.H2("CONTROL PROCESO COMPETICIÓN - Mapas de Estilo-Rendimiento", 
                className="mb-4", 
                style={
                    "color": "#1e3d59", 
                    "backgroundColor": "transparent",
                    "fontWeight": "600",
                    "textAlign": "center",
                    "padding": "1rem 0"
                })
    ], style={"backgroundColor": "transparent"}),
    
    # Container principal con pestañas
    html.Div([
        # Header de pestañas
        html.Div([
            html.Div([
                html.Button(
                    "Evolución Resultados",
                    id="tab-evolucion-resultados",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#1e3d59",
                        "border": "none",
                        "borderBottom": "3px solid #1e3d59",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "600",
                        "fontSize": "16px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "33.33%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Contextos de Partidos",
                    id="tab-contextos-partidos",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#6c757d",
                        "border": "none",
                        "borderBottom": "3px solid transparent",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "500",
                        "fontSize": "16px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "33.33%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Mapas de Rendimiento",
                    id="tab-mapas-rendimiento",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#6c757d",
                        "border": "none",
                        "borderBottom": "3px solid transparent",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "500",
                        "fontSize": "16px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "33.33%",
                        "textAlign": "center"
                    }
                )
            ], style={
                "display": "flex",
                "width": "100%",
                "borderBottom": "1px solid #e9ecef"
            })
        ], style={
            "backgroundColor": "#f8f9fa",
            "borderRadius": "8px 8px 0 0"
        }),
        
        # Contenido de las pestañas
        html.Div([
            html.Div(id="mapas-tab-content", children=get_evolucion_resultados_content())
        ], style={
            "backgroundColor": "white",
            "borderRadius": "0 0 8px 8px",
            "minHeight": "400px"
        })
    ], className="shadow-sm", style={"border": "1px solid #e9ecef", "borderRadius": "8px"})
])

# Callback para manejar el cambio de pestañas
@callback(
    [Output("tab-evolucion-resultados", "style"),
     Output("tab-contextos-partidos", "style"),
     Output("tab-mapas-rendimiento", "style"),
     Output("mapas-tab-content", "children")],
    [Input("tab-evolucion-resultados", "n_clicks"),
     Input("tab-contextos-partidos", "n_clicks"),
     Input("tab-mapas-rendimiento", "n_clicks")]
)
def update_tabs(n_clicks_evolucion, n_clicks_contextos, n_clicks_mapas):
    """Actualiza el estilo de las pestañas y el contenido según la selección"""
    
    # Estilos base
    style_inactive = {
        "backgroundColor": "transparent",
        "color": "#6c757d",
        "border": "none",
        "borderBottom": "3px solid transparent",
        "borderRadius": "0",
        "padding": "15px 0",
        "fontWeight": "500",
        "fontSize": "16px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "width": "33.33%",
        "textAlign": "center"
    }
    
    style_active = {
        "backgroundColor": "transparent",
        "color": "#1e3d59",
        "border": "none",
        "borderBottom": "3px solid #1e3d59",
        "borderRadius": "0",
        "padding": "15px 0",
        "fontWeight": "600",
        "fontSize": "16px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "width": "33.33%",
        "textAlign": "center"
    }
    
    # Detectar qué botón fue clickeado usando callback_context
    ctx = dash.callback_context
    if not ctx.triggered:
        # Carga inicial: mostrar primera pestaña
        active_tab = 0
    else:
        # Obtener el ID del botón que disparó el callback
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Mapear botón a índice de pestaña
        if button_id == 'tab-evolucion-resultados':
            active_tab = 0
        elif button_id == 'tab-contextos-partidos':
            active_tab = 1
        elif button_id == 'tab-mapas-rendimiento':
            active_tab = 2
        else:
            active_tab = 0
    
    # Establecer estilos según la pestaña activa
    styles = [style_inactive, style_inactive, style_inactive]
    styles[active_tab] = style_active
    
    # Establecer contenido según la pestaña activa
    if active_tab == 0:
        content = get_evolucion_resultados_content()
    elif active_tab == 1:
        content = get_contextos_partidos_content()
    else:
        content = get_mapas_rendimiento_content()
    
    return styles[0], styles[1], styles[2], content

# Callbacks para los bloques de scatter plots
# Callback genérico para cada bloque usando pattern matching
@callback(
    Output({"type": "goles-option", "index": dash.dependencies.ALL}, "style"),
    Output("goles-scatter-plot", "children"),
    Output("goles-selected-option", "data"),
    Input({"type": "goles-option", "index": dash.dependencies.ALL}, "n_clicks"),
    State("goles-selected-option", "data")
)
def update_goles_scatter(n_clicks_list, current_option):
    """Actualiza el scatter plot del bloque Goles"""
    return update_scatter_block(
        n_clicks_list, 
        current_option, 
        "goles",
        ["totales", "juego_dinamico", "balon_parado"]
    )

@callback(
    Output({"type": "eficacia-option", "index": dash.dependencies.ALL}, "style"),
    Output("eficacia-scatter-plot", "children"),
    Output("eficacia-selected-option", "data"),
    Input({"type": "eficacia-option", "index": dash.dependencies.ALL}, "n_clicks"),
    State("eficacia-selected-option", "data")
)
def update_eficacia_scatter(n_clicks_list, current_option):
    """Actualiza el scatter plot del bloque Eficacia"""
    return update_scatter_block(
        n_clicks_list, 
        current_option, 
        "eficacia",
        ["ofensiva", "defensiva", "peligrosidad"]
    )

@callback(
    Output({"type": "funcionalidad-option", "index": dash.dependencies.ALL}, "style"),
    Output("funcionalidad-scatter-plot", "children"),
    Output("funcionalidad-selected-option", "data"),
    Input({"type": "funcionalidad-option", "index": dash.dependencies.ALL}, "n_clicks"),
    State("funcionalidad-selected-option", "data")
)
def update_funcionalidad_scatter(n_clicks_list, current_option):
    """Actualiza el scatter plot del bloque Funcionalidad"""
    return update_scatter_block(
        n_clicks_list, 
        current_option, 
        "funcionalidad",
        ["profundidad_ofensiva", "agresividad_intensidad"]
    )

@callback(
    Output({"type": "fisico_combatividad-option", "index": dash.dependencies.ALL}, "style"),
    Output("fisico_combatividad-scatter-plot", "children"),
    Output("fisico_combatividad-selected-option", "data"),
    Input({"type": "fisico_combatividad-option", "index": dash.dependencies.ALL}, "n_clicks"),
    State("fisico_combatividad-selected-option", "data")
)
def update_fisico_scatter(n_clicks_list, current_option):
    """Actualiza el scatter plot del bloque Físico-Combatividad"""
    return update_scatter_block(
        n_clicks_list, 
        current_option, 
        "fisico_combatividad",
        ["volumen_calidad", "faltas"]
    )

def update_scatter_block(n_clicks_list, current_option, block_id, option_values):
    """Función genérica para actualizar cualquier bloque de scatter"""
    
    # Estilos base
    style_inactive = {
        "width": "100%",
        "padding": "12px 20px",
        "marginBottom": "10px",
        "border": "2px solid #e9ecef",
        "backgroundColor": "white",
        "color": "#6c757d",
        "borderRadius": "8px",
        "cursor": "pointer",
        "fontWeight": "500",
        "fontSize": "14px",
        "transition": "all 0.2s ease",
        "textAlign": "left"
    }
    
    style_active = {
        "width": "100%",
        "padding": "12px 20px",
        "marginBottom": "10px",
        "border": "2px solid #1e3d59",
        "backgroundColor": "#1e3d59",
        "color": "white",
        "borderRadius": "8px",
        "cursor": "pointer",
        "fontWeight": "600",
        "fontSize": "14px",
        "transition": "all 0.2s ease",
        "textAlign": "left"
    }
    
    # Detectar qué botón fue clickeado
    ctx = dash.callback_context
    if not ctx.triggered:
        # Carga inicial
        selected_option = current_option
    else:
        # Obtener el botón clickeado
        triggered_id = ctx.triggered[0]['prop_id']
        if 'index' in triggered_id:
            import json
            # Extraer el índice del botón clickeado
            id_dict = json.loads(triggered_id.split('.')[0])
            selected_option = id_dict['index']
        else:
            selected_option = current_option
    
    # Crear estilos para cada botón
    styles = []
    for opt_value in option_values:
        if opt_value == selected_option:
            styles.append(style_active)
        else:
            styles.append(style_inactive)
    
    # Crear el contenido del scatter plot según el bloque y opción
    # BLOQUE GOLES
    if block_id == "goles":
        if selected_option == "totales":
            scatter_content = create_scatter_plot(
                metric_x="TeamGoals",
                metric_y="TeamGoalsAgainst",
                label_x="Goles a Favor",
                label_y="Goles en Contra",
                invert_y=True
            )
        elif selected_option == "juego_dinamico":
            scatter_content = create_scatter_plot(
                metric_x="TeamGoalsDynamic",
                metric_y="TeamGoalsAgainstDynamic",
                label_x="Goles JD a Favor",
                label_y="Goles JD en Contra",
                invert_y=True
            )
        elif selected_option == "balon_parado":
            scatter_content = create_scatter_plot(
                metric_x="TeamGoalsSetPlayNoPenalty",
                metric_y="TeamGoalsAgainstSetPlayNoPenalty",
                label_x="Goles ABP a Favor sin Penaltis ",
                label_y="Goles ABP en Contra sin Penaltis",
                invert_y=True
            )
        else:
            scatter_content = create_placeholder_scatter(block_id, selected_option)
    
    # BLOQUE EFICACIA
    elif block_id == "eficacia":
        if selected_option == "ofensiva":
            scatter_content = create_scatter_plot(
                metric_x="TeamEffectivenessOffensiveConstruction",
                metric_y="TeamEffectivenessCompletion",
                label_x="Eficacia Construcción Ofensiva (%)",
                label_y="Eficacia Finalización (%)",
                invert_y=False
            )
        elif selected_option == "defensiva":
            scatter_content = create_scatter_plot(
                metric_x="TeamEffectivenessDefensiveContainment",
                metric_y="TeamEfectivenessAvoidance",
                label_x="Eficacia Contención Defensiva (%)",
                label_y="Eficacia Evitación (%)",
                invert_y=False
            )
        elif selected_option == "peligrosidad":
            scatter_content = create_scatter_plot(
                metric_x="TeamExpectedGoals",
                metric_y="TeamExpectedGoalsAgainst",
                label_x="xG a Favor",
                label_y="xG en Contra",
                invert_y=True,
                custom_title="Peligrosidad Generada vs Peligrosidad Concedida"
            )
        else:
            scatter_content = create_placeholder_scatter(block_id, selected_option)
    
    # BLOQUE FUNCIONALIDAD
    elif block_id == "funcionalidad":
        if selected_option == "profundidad_ofensiva":
            scatter_content = create_scatter_plot(
                metric_x="TeamPossessionsTimeP",
                metric_y="TeamShots",
                label_x="Posesión (%)",
                label_y="Remates Totales",
                invert_y=False
            )
        elif selected_option == "agresividad_intensidad":
            scatter_content = create_scatter_plot(
                metric_x="TeamRecoveriesOppositeFieldP",
                metric_y="TeamRecoveriesQuickP",
                label_x="Recuperaciones Campo Contrario (%)",
                label_y="Recuperaciones Rápidas (%)",
                invert_y=False
            )
        else:
            scatter_content = create_placeholder_scatter(block_id, selected_option)
    
    # BLOQUE FÍSICO-COMBATIVIDAD
    elif block_id == "fisico_combatividad":
        if selected_option == "volumen_calidad":
            scatter_content = create_scatter_plot(
                metric_x="TeamDistanceTotal",
                metric_y="TeamDistanceHighSprint",
                label_x="Distancia Total (m)",
                label_y="Distancia High Sprint (m)",
                invert_y=False
            )
        elif selected_option == "faltas":
            scatter_content = create_scatter_plot(
                metric_x="TeamFoulsAwarded",
                metric_y="TeamFoulsCommited",
                label_x="Faltas Recibidas",
                label_y="Faltas Cometidas",
                invert_y=True
            )
        else:
            scatter_content = create_placeholder_scatter(block_id, selected_option)
    
    else:
        scatter_content = create_placeholder_scatter(block_id, selected_option)
    
    return styles, scatter_content, selected_option
