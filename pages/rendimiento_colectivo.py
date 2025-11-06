# pages/rendimiento_colectivo.py

from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from utils.layouts import standard_page

# Importar el contenido de evolutivo temporada para la pestaña 2
from pages.competicion_evolutivo_temporada import build_layout_content_only as get_evolutivo_temporada_content

# Importar el contenido de diagramas funcionales para la pestaña 4
from pages.diagramas_funcionales import get_diagramas_funcionales_content

def get_tendencia_resultados_content():
    """Contenido de la pestaña Tendencia Resultados - Importa desde tendencia_resultados.py"""
    from pages.tendencia_resultados import get_tendencia_resultados_content as get_tendencia_content
    return get_tendencia_content()

def get_perfil_estilo_content():
    """Contenido de la sub-pestaña Estilo - Importa desde competicion_estilo.py"""
    from pages.competicion_estilo import get_estilo_content
    return html.Div(get_estilo_content(), style={'padding': '10px 15px'})

def get_perfil_rendimiento_content():
    """Contenido de la sub-pestaña Rendimiento - Reutiliza evolutivo temporada sin título"""
    return html.Div(get_evolutivo_temporada_content(), style={'padding': '10px 15px'})

def get_perfil_estilo_rendimiento_content():
    """Contenido de la pestaña Perfil Estilo-Rendimiento con sub-navegación"""
    return html.Div([
        # Sub-navegación para Perfil Estilo-Rendimiento
        html.Div([
            html.Div([
                html.Button(
                    "Perfil Estilo de Juego",
                    id="subtab-per-estilo",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#1e3d59",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "padding": "12px 40px",
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "minWidth": "260px"
                    }
                ),
                html.Button(
                    "Perfil Rendimiento",
                    id="subtab-per-rendimiento",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 40px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "minWidth": "260px"
                    }
                ),
                html.Button(
                    "Diagramas Funcionales",
                    id="subtab-per-diagramas",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 40px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "minWidth": "260px"
                    }
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "padding": "20px 0",
                "borderBottom": "1px solid #e9ecef"
            })
        ], style={
            "backgroundColor": "white",
            "marginBottom": "20px"
        }),
        
        # Contenido dinámico según sub-pestaña seleccionada
        html.Div([
            html.Div(
                id="per-subtab-content",
                children=get_perfil_estilo_content()  # Por defecto mostrar Estilo
            )
        ], className="p-0")
    ])

def get_uso_aprovechamiento_content():
    """Contenido de la pestaña Uso Aprovechamiento de Plantilla"""
    return html.Div([
        html.Div([
            html.I(className="fas fa-users me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
            html.H4("Uso y Aprovechamiento de Plantilla", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-4"),
        html.P(
            "Esta sección mostrará el análisis del uso y aprovechamiento de la plantilla.",
            className="text-muted"
        ),
        html.Div([
            html.I(className="fas fa-hard-hat fa-3x mb-3", style={"color": "#ffc107"}),
            html.H5("En Desarrollo", style={"color": "#6c757d"})
        ], style={"textAlign": "center", "padding": "60px 20px"})
    ], className="p-4")

# Función eliminada - ahora se usa get_diagramas_funcionales_content() importada arriba

def get_mapas_funcionales_old():
    """DEPRECADO - Contenido antiguo de Mapas Funcionales"""
    from pages.mapas_estilo_rendimiento import create_scatter_block
    
    return html.Div([
        # Sub-navegación para Mapas Funcionales
        html.Div([
            html.Div([
                html.Button(
                    "Goles",
                    id="subtab-mf-goles",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#1e3d59",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "padding": "12px 35px",
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                    }
                ),
                html.Button(
                    "Eficacia",
                    id="subtab-mf-eficacia",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 35px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px"
                    }
                ),
                html.Button(
                    "Funcionalidad Of. / Def. ",
                    id="subtab-mf-funcionalidad",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 35px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px"
                    }
                ),
                html.Button(
                    "Físico-Combatividad",
                    id="subtab-mf-fisico",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 35px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease"
                    }
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "padding": "20px 0",
                "borderBottom": "1px solid #e9ecef"
            })
        ], style={
            "backgroundColor": "white",
            "marginBottom": "20px"
        }),
        
        # Contenido dinámico según sub-pestaña seleccionada
        html.Div([
            html.Div(
                id="mf-subtab-content",
                children=[
                    # Por defecto mostrar Goles
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
                    )
                ]
            )
        ], className="p-4")
    ])

def get_contextos_partidos_content():
    """Contenido de la pestaña Contextos Partidos - Importa desde contextos_partidos.py"""
    from pages.contextos_partidos import get_contextos_partidos_content as get_contextos_content
    return get_contextos_content()

# Layout principal
layout = standard_page([
    # Título
    html.Div([
        html.H2("CONTROL PROCESO COMPETICIÓN - Rendimiento Colectivo", 
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
                    "Tendencia Resultados",
                    id="tab-rc-tendencia",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#6c757d",
                        "border": "none",
                        "borderBottom": "3px solid transparent",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "500",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "20%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Perfil Estilo-Rendimiento",
                    id="tab-rc-perfil",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#1e3d59",
                        "border": "none",
                        "borderBottom": "3px solid #1e3d59",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "600",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "25%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Uso-Aprovechamiento Plantilla",
                    id="tab-rc-aprovechamiento",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#6c757d",
                        "border": "none",
                        "borderBottom": "3px solid transparent",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "500",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "25%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Contextos Partidos",
                    id="tab-rc-contextos",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#6c757d",
                        "border": "none",
                        "borderBottom": "3px solid transparent",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "500",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "25%",
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
            html.Div(id="rc-tab-content", children=get_perfil_estilo_rendimiento_content())
        ], style={
            "backgroundColor": "white",
            "borderRadius": "0 0 8px 8px",
            "minHeight": "400px"
        })
    ], className="shadow-sm", style={"border": "1px solid #e9ecef", "borderRadius": "8px"})
])

# DEPRECADO - Callback antiguo de Mapas Funcionales (ahora se usa sidebar en diagramas_funcionales.py)
# @callback(
#     [Output("subtab-mf-goles", "style"),
#      Output("subtab-mf-eficacia", "style"),
#      Output("subtab-mf-funcionalidad", "style"),
#      Output("subtab-mf-fisico", "style"),
#      Output("mf-subtab-content", "children")],
#     [Input("subtab-mf-goles", "n_clicks"),
#      Input("subtab-mf-eficacia", "n_clicks"),
#      Input("subtab-mf-funcionalidad", "n_clicks"),
#      Input("subtab-mf-fisico", "n_clicks")]
# )
def update_mf_subtabs_old(n_goles, n_eficacia, n_funcionalidad, n_fisico):
    """DEPRECADO - Actualiza las sub-pestañas de Mapas Funcionales"""
    from pages.mapas_estilo_rendimiento import create_scatter_block
    
    # Estilos
    style_inactive = {
        "backgroundColor": "#f8f9fa",
        "color": "#6c757d",
        "border": "1px solid #e9ecef",
        "borderRadius": "6px",
        "padding": "12px 35px",
        "fontWeight": "500",
        "fontSize": "14px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px"
    }
    
    style_active = {
        "backgroundColor": "#1e3d59",
        "color": "white",
        "border": "none",
        "borderRadius": "6px",
        "padding": "12px 35px",
        "fontWeight": "600",
        "fontSize": "14px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
    }
    
    # Detectar qué botón fue clickeado
    ctx = dash.callback_context
    if not ctx.triggered:
        active_subtab = 0  # Goles por defecto
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'subtab-mf-goles':
            active_subtab = 0
        elif button_id == 'subtab-mf-eficacia':
            active_subtab = 1
        elif button_id == 'subtab-mf-funcionalidad':
            active_subtab = 2
        elif button_id == 'subtab-mf-fisico':
            active_subtab = 3
        else:
            active_subtab = 0
    
    # Establecer estilos
    styles = [style_inactive] * 4
    styles[active_subtab] = style_active
    
    # Establecer contenido
    if active_subtab == 0:
        content = create_scatter_block(
            block_id="goles",
            title="Goles",
            icon="fa-futbol",
            options=[
                {"label": "Totales", "value": "totales"},
                {"label": "Juego Dinámico", "value": "juego_dinamico"},
                {"label": "Balón Parado", "value": "balon_parado"}
            ],
            default_option="totales"
        )
    elif active_subtab == 1:
        content = create_scatter_block(
            block_id="eficacia",
            title="Eficacia",
            icon="fa-bullseye",
            options=[
                {"label": "Ofensiva", "value": "ofensiva"},
                {"label": "Defensiva", "value": "defensiva"},
                {"label": "Peligrosidad", "value": "peligrosidad"}
            ],
            default_option="ofensiva"
        )
        # Nota: Los ejes X e Y han sido intercambiados en mapas_estilo_rendimiento.py para Ofensiva y Defensiva
    elif active_subtab == 2:
        content = create_scatter_block(
            block_id="funcionalidad",
            title="Funcionalidad Of. / Def.",
            icon="fa-cogs",
            options=[
                {"label": "Profundidad Ofensiva", "value": "profundidad_ofensiva"},
                {"label": "Agresividad-Intensidad Def.", "value": "agresividad_intensidad"}
            ],
            default_option="profundidad_ofensiva"
        )
    else:
        content = create_scatter_block(
            block_id="fisico_combatividad",
            title="Físico - Combatividad",
            icon="fa-running",
            options=[
                {"label": "Volumen - Calidad Esfuerzo", "value": "volumen_calidad"},
                {"label": "Faltas", "value": "faltas"}
            ],
            default_option="volumen_calidad"
        )
    
    return styles[0], styles[1], styles[2], styles[3], content


# Callback para manejar el cambio de sub-pestañas en Perfil Estilo-Rendimiento
@callback(
    [Output("subtab-per-estilo", "style"),
     Output("subtab-per-rendimiento", "style"),
     Output("subtab-per-diagramas", "style"),
     Output("per-subtab-content", "children")],
    [Input("subtab-per-estilo", "n_clicks"),
     Input("subtab-per-rendimiento", "n_clicks"),
     Input("subtab-per-diagramas", "n_clicks")]
)
def update_per_subtabs(n_estilo, n_rendimiento, n_diagramas):
    """Actualiza las sub-pestañas de Perfil Estilo-Rendimiento"""
    
    # Estilos
    style_inactive = {
        "backgroundColor": "#f8f9fa",
        "color": "#6c757d",
        "border": "1px solid #e9ecef",
        "borderRadius": "6px",
        "padding": "12px 40px",
        "fontWeight": "500",
        "fontSize": "14px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px",
        "minWidth": "260px"
    }
    
    style_active = {
        "backgroundColor": "#1e3d59",
        "color": "white",
        "border": "none",
        "borderRadius": "6px",
        "padding": "12px 40px",
        "fontWeight": "600",
        "fontSize": "14px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "minWidth": "260px"
    }
    
    # Detectar qué botón fue clickeado
    ctx = dash.callback_context
    if not ctx.triggered:
        active_subtab = 0  # Estilo por defecto
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'subtab-per-estilo':
            active_subtab = 0
        elif button_id == 'subtab-per-rendimiento':
            active_subtab = 1
        elif button_id == 'subtab-per-diagramas':
            active_subtab = 2
        else:
            active_subtab = 0
    
    # Establecer estilos
    styles = [style_inactive] * 3
    styles[active_subtab] = style_active
    
    # Establecer contenido
    if active_subtab == 0:
        content = get_perfil_estilo_content()
    elif active_subtab == 1:
        content = get_perfil_rendimiento_content()
    else:
        content = get_diagramas_funcionales_content()
    
    return styles[0], styles[1], styles[2], content


# Callback para manejar el cambio de pestañas
@callback(
    [Output("tab-rc-tendencia", "style"),
     Output("tab-rc-perfil", "style"),
     Output("tab-rc-aprovechamiento", "style"),
     Output("tab-rc-contextos", "style"),
     Output("rc-tab-content", "children")],
    [Input("tab-rc-tendencia", "n_clicks"),
     Input("tab-rc-perfil", "n_clicks"),
     Input("tab-rc-aprovechamiento", "n_clicks"),
     Input("tab-rc-contextos", "n_clicks")]
)
def update_tabs(n_clicks_tendencia, n_clicks_perfil, n_clicks_aprovechamiento, n_clicks_contextos):
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
        "fontSize": "15px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "width": "25%",
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
        "fontSize": "15px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "width": "25%",
        "textAlign": "center"
    }
    
    # Detectar qué botón fue clickeado usando callback_context
    ctx = dash.callback_context
    if not ctx.triggered:
        # Carga inicial: mostrar primera pestaña (Tendencia Resultados)
        active_tab = 0
    else:
        # Obtener el ID del botón que disparó el callback
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Mapear botón a índice de pestaña
        if button_id == 'tab-rc-tendencia':
            active_tab = 0
        elif button_id == 'tab-rc-perfil':
            active_tab = 1
        elif button_id == 'tab-rc-aprovechamiento':
            active_tab = 2
        elif button_id == 'tab-rc-contextos':
            active_tab = 3
        else:
            active_tab = 1
    
    # Establecer estilos según la pestaña activa
    styles = [style_inactive] * 4
    styles[active_tab] = style_active
    
    # Establecer contenido según la pestaña activa
    if active_tab == 0:
        content = get_tendencia_resultados_content()
    elif active_tab == 1:
        content = get_perfil_estilo_rendimiento_content()
    elif active_tab == 2:
        content = get_uso_aprovechamiento_content()
    else:
        content = get_contextos_partidos_content()
    
    return styles[0], styles[1], styles[2], styles[3], content
