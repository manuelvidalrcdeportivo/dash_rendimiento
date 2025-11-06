"""
Diagramas Funcionales: Mapas de dispersión organizados por categorías
Restaura EXACTAMENTE los mapas originales de Mapas Funcionales
"""

from dash import html, dcc, callback, Input, Output, ALL
from pages.mapas_estilo_rendimiento import create_scatter_plot

# Mapeo completo de cada subsección a sus parámetros de gráfico
MAPAS_PARAMS = {
    # Goles
    "goles_totales": {
        "metric_x": "TeamGoals", "metric_y": "TeamGoalsAgainst",
        "label_x": "Goles a Favor", "label_y": "Goles en Contra",
        "title": "Goles Totales", "invert_y": True
    },
    "goles_juego_dinamico": {
        "metric_x": "TeamGoalsDynamic", "metric_y": "TeamGoalsAgainstDynamic",
        "label_x": "Goles JD a Favor", "label_y": "Goles JD en Contra",
        "title": "Goles en Juego Dinámico", "invert_y": True
    },
    "goles_balon_parado": {
        "metric_x": "TeamGoalsSetPlayNoPenalty", "metric_y": "TeamGoalsAgainstSetPlayNoPenalty",
        "label_x": "Goles ABP a Favor sin Penaltis", "label_y": "Goles ABP en Contra sin Penaltis",
        "title": "Goles de Balón Parado", "invert_y": True
    },
    # Eficacia
    "eficacia_ofensiva": {
        "metric_x": "TeamEffectivenessOffensiveConstruction", "metric_y": "TeamEffectivenessCompletion",
        "label_x": "Eficacia Construcción Ofensiva (%)", "label_y": "Eficacia Finalización (%)",
        "title": "Eficacia Ofensiva"
    },
    "eficacia_defensiva": {
        "metric_x": "TeamEffectivenessDefensiveContainment", "metric_y": "TeamEfectivenessAvoidance",
        "label_x": "Eficacia Contención Defensiva (%)", "label_y": "Eficacia Evitación (%)",
        "title": "Eficacia Defensiva"
    },
    "eficacia_peligrosidad": {
        "metric_x": "TeamExpectedGoals", "metric_y": "TeamExpectedGoalsAgainst",
        "label_x": "xG a Favor", "label_y": "xG en Contra",
        "title": "Peligrosidad Generada vs Peligrosidad Concedida", "invert_y": True
    },
    # Funcionalidad
    "funcionalidad_profundidad": {
        "metric_x": "TeamPossessionsTimeP", "metric_y": "TeamShots",
        "label_x": "Posesión (%)", "label_y": "Remates Totales",
        "title": "Profundidad Ofensiva"
    },
    "funcionalidad_agresividad": {
        "metric_x": "TeamRecoveriesOppositeFieldP", "metric_y": "TeamRecoveriesQuickP",
        "label_x": "Recuperaciones Campo Contrario (%)", "label_y": "Recuperaciones Rápidas (%)",
        "title": "Agresividad e Intensidad Defensiva"
    },
    # Físico-Combatividad
    "fisico_volumen": {
        "metric_x": "TeamDistanceTotal", "metric_y": "TeamDistanceHighSprint",
        "label_x": "Distancia Total (m)", "label_y": "Distancia High Sprint (m)",
        "title": "Volumen y Calidad de Esfuerzo"
    },
    "fisico_faltas": {
        "metric_x": "TeamFoulsAwarded", "metric_y": "TeamFoulsCommited",
        "label_x": "Faltas Recibidas", "label_y": "Faltas Cometidas",
        "title": "Combatividad - Faltas", "invert_y": True
    }
}

# Configuración de las 4 secciones con referencias a MAPAS_PARAMS
SECCIONES_CONFIG = [
    {
        "title": "Goles",
        "icon": "fa-futbol",
        "subsecciones": [
            {"label": "Totales", "map_key": "goles_totales"},
            {"label": "Juego Dinámico", "map_key": "goles_juego_dinamico"},
            {"label": "Balón Parado", "map_key": "goles_balon_parado"}
        ]
    },
    {
        "title": "Eficacia",
        "icon": "fa-bullseye",
        "subsecciones": [
            {"label": "Ofensiva", "map_key": "eficacia_ofensiva"},
            {"label": "Defensiva", "map_key": "eficacia_defensiva"},
            {"label": "Peligrosidad", "map_key": "eficacia_peligrosidad"}
        ]
    },
    {
        "title": "Funcionalidad Of. / Def.",
        "icon": "fa-cogs",
        "subsecciones": [
            {"label": "Profundidad Ofensiva", "map_key": "funcionalidad_profundidad"},
            {"label": "Agresividad-Intensidad Def.", "map_key": "funcionalidad_agresividad"}
        ]
    },
    {
        "title": "Físico - Combatividad",
        "icon": "fa-running",
        "subsecciones": [
            {"label": "Volumen - Calidad Esfuerzo", "map_key": "fisico_volumen"},
            {"label": "Faltas", "map_key": "fisico_faltas"}
        ]
    }
]

# DEPRECADO - Configuración anterior con sidebar (no funcionaba bien)
MAPAS_CONFIG_OLD = {
    "goles": {
        "title": "Goles",
        "icon": "fa-futbol",
        "color": "#28a745",
        "mapas": [
            {"id": "xg_goles", "label": "xG vs Goles", "x": "TeamExpectedGoals", "y": "TeamGoals", "x_label": "xG", "y_label": "Goles"},
            {"id": "goles_of_def", "label": "Goles a Favor vs En Contra", "x": "TeamGoals", "y": "OpponentGoals", "x_label": "Goles a Favor", "y_label": "Goles en Contra", "invert_y": True}
        ]
    },
    "eficacia": {
        "title": "Eficacia",
        "icon": "fa-bullseye",
        "color": "#007bff",
        "mapas": [
            {"id": "eficacia_of_def", "label": "Eficacia Ofensiva vs Defensiva", "x": "ValesrEfiOf", "y": "ValesrEfiDef", "x_label": "Eficacia Ofensiva", "y_label": "Eficacia Defensiva"},
            {"id": "precision_tiro", "label": "Precisión de Tiro", "x": "TeamShots", "y": "TeamShotsOnTarget", "x_label": "Tiros", "y_label": "A Portería"},
            {"id": "duelos_aereos", "label": "Duelos Aéreos", "x": "TeamAerialRatio", "y": "OpponentAerialRatio", "x_label": "% Duelos Aéreos", "y_label": "% Rival", "invert_y": True}
        ]
    },
    "funcionalidad_of": {
        "title": "Funcionalidad Ofensiva",
        "icon": "fa-arrow-up",
        "color": "#fd7e14",
        "mapas": [
            {"id": "profundidad", "label": "Profundidad Ofensiva", "x": "TeamPossessionsForwardZoneP", "y": "TeamOffensiveDevelopment", "x_label": "% Pos. Zona Ofensiva", "y_label": "Elaboración"},
            {"id": "centros", "label": "Centros", "x": "TeamCrosses", "y": "TeamLongPasses", "x_label": "Centros", "y_label": "Pases Largos"},
            {"id": "tiros_xg", "label": "Tiros y xG", "x": "TeamShots", "y": "TeamExpectedGoals", "x_label": "Tiros", "y_label": "xG"}
        ]
    },
    "funcionalidad_def": {
        "title": "Funcionalidad Defensiva",
        "icon": "fa-shield-alt",
        "color": "#dc3545",
        "mapas": [
            {"id": "recuperaciones", "label": "Recuperaciones", "x": "TeamRecoveriesOppositeFieldP", "y": "TeamRecoveriesQuickP", "x_label": "% Recup. Campo Rival", "y_label": "% Recup. Rápidas"},
            {"id": "altura_ritmo", "label": "Altura y Ritmo Recuperación", "x": "TeamRecoveriesAverageHeight", "y": "TeamRecoveryRate", "x_label": "Altura Media", "y_label": "Ritmo Recuperación"}
        ]
    },
    "fisico": {
        "title": "Físico-Combatividad",
        "icon": "fa-running",
        "color": "#6f42c1",
        "mapas": [
            {"id": "distancias", "label": "Distancias Totales", "x": "TeamDistanceTotal", "y": "OpponentDistanceTotal", "x_label": "Distancia Total", "y_label": "Dist. Total Rival", "invert_y": True},
            {"id": "sprint", "label": "Distancias en Sprint", "x": "TeamDistanceSprint", "y": "TeamDistanceHighSprint", "x_label": "Dist. Sprint", "y_label": "Dist. High Sprint"}
        ]
    }
}


# DEPRECADO - Sidebar anterior
def create_sidebar_item_old(categoria_id, config, is_first=False):
    """Crea un item del sidebar con sus sub-mapas"""
    categoria_style = {
        'padding': '12px 16px',
        'cursor': 'pointer',
        'borderLeft': f'4px solid {config["color"]}',
        'backgroundColor': '#f8f9fa' if is_first else 'white',
        'marginBottom': '2px',
        'transition': 'all 0.2s ease'
    }
    
    mapa_items = []
    for idx, mapa in enumerate(config["mapas"]):
        mapa_style = {
            'padding': '8px 16px 8px 32px',
            'cursor': 'pointer',
            'fontSize': '13px',
            'color': '#6c757d',
            'backgroundColor': '#f8f9fa' if (is_first and idx == 0) else 'white',
            'borderLeft': '2px solid #e9ecef',
            'transition': 'all 0.2s ease'
        }
        
        mapa_items.append(
            html.Div(
                mapa["label"],
                id={'type': 'mapa-item', 'categoria': categoria_id, 'mapa': mapa["id"]},
                style=mapa_style,
                className='mapa-sidebar-item'
            )
        )
    
    return html.Div([
        # Categoría principal
        html.Div([
            html.I(className=f"fas {config['icon']} me-2", style={'color': config['color']}),
            html.Span(config["title"], style={'fontWeight': '600', 'color': '#1e3d59'})
        ], id={'type': 'categoria-item', 'id': categoria_id}, style=categoria_style, className='categoria-sidebar-item'),
        
        # Sub-mapas
        html.Div(mapa_items, id=f'mapas-{categoria_id}', style={'display': 'block' if is_first else 'none'})
    ])


def get_diagramas_funcionales_content():
    """Layout principal de Diagramas Funcionales - Con sidebar lateral"""
    
    # Crear items del sidebar
    sidebar_items = []
    for i, seccion in enumerate(SECCIONES_CONFIG):
        # Sección principal (cabecera)
        seccion_header = html.Div([
            html.I(className=f"fas {seccion['icon']} me-2", style={'color': '#1e3d59', 'fontSize': '16px'}),
            html.Span(seccion['title'], style={'fontWeight': '600', 'color': '#1e3d59', 'fontSize': '14px'})
        ], id={'type': 'df-seccion-header', 'index': i}, style={
            'padding': '12px 16px',
            'cursor': 'pointer',
            'backgroundColor': '#f8f9fa' if i == 0 else 'white',
            'borderLeft': f'4px solid #1e3d59',
            'borderBottom': '1px solid #e9ecef',
            'transition': 'all 0.2s ease',
            'userSelect': 'none'
        }, className='df-seccion-header')
        
        # Subsecciones
        subsecciones = []
        for j, subseccion in enumerate(seccion['subsecciones']):
            # Estilo más destacado para la seleccionada (primera por defecto)
            is_selected = (i == 0 and j == 0)
            subsecciones.append(
                html.Div(
                    subseccion['label'],
                    id={'type': 'df-subseccion', 'seccion': i, 'opcion': j},
                    style={
                        'padding': '10px 16px 10px 40px',
                        'cursor': 'pointer',
                        'fontSize': '13px',
                        'color': '#ffffff' if is_selected else '#6c757d',
                        'backgroundColor': '#1e3d59' if is_selected else 'white',
                        'borderLeft': '4px solid #1e3d59' if is_selected else '2px solid #e9ecef',
                        'borderBottom': '1px solid #f0f0f0',
                        'transition': 'all 0.2s ease',
                        'userSelect': 'none',
                        'fontWeight': '700' if is_selected else '500'
                    },
                    className='df-subseccion'
                )
            )
        
        # Contenedor de subsecciones (colapsable)
        subsecciones_container = html.Div(
            subsecciones,
            id={'type': 'df-subsecciones-container', 'index': i},
            style={'display': 'block' if i == 0 else 'none'}
        )
        
        sidebar_items.append(html.Div([seccion_header, subsecciones_container]))
    
    return html.Div([
        html.Div([
            # Sidebar izquierda (25%)
            html.Div([
                html.Div([
                    html.I(className="fas fa-list-ul me-2", style={'fontSize': '16px', 'color': '#1e3d59'}),
                    html.H5("Categorías", style={'color': '#1e3d59', 'margin': '0', 'fontWeight': '600', 'display': 'inline'})
                ], style={'padding': '16px', 'borderBottom': '2px solid #e9ecef'}),
                
                html.Div(sidebar_items, style={'overflowY': 'auto', 'maxHeight': 'calc(100vh - 300px)'})
            ], style={
                'width': '25%',
                'backgroundColor': 'white',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.08)',
                'marginRight': '20px',
                'height': 'fit-content',
                'position': 'sticky',
                'top': '20px'
            }),
            
            # Contenido principal (75%)
            html.Div([
                dcc.Loading(
                    id='df-loading',
                    type='circle',
                    color='#1e3d59',
                    children=[
                        html.Div(
                            id='df-main-content',
                            children=[
                                # Contenido por defecto: primera subsección
                                html.Div([
                                    html.Div([
                                        create_scatter_plot(
                                            metric_x="TeamGoals",
                                            metric_y="TeamGoalsAgainst",
                                            label_x="Goles a Favor",
                                            label_y="Goles en Contra",
                                            custom_title="Goles Totales",
                                            invert_y=True
                                        )
                                    ], style={'padding': '20px'})
                                ])
                            ]
                        )
                    ]
                )
            ], style={
                'width': '75%',
                'backgroundColor': 'white',
                'borderRadius': '8px',
                'padding': '0',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.08)',
                'minHeight': '600px'
            })
        ], style={
            'display': 'flex',
            'width': '100%'
        })
    ], className='p-4')


# Callback para expandir/colapsar secciones en el sidebar
@callback(
    [Output({'type': 'df-subsecciones-container', 'index': ALL}, 'style'),
     Output({'type': 'df-seccion-header', 'index': ALL}, 'style')],
    [Input({'type': 'df-seccion-header', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def toggle_seccion(*n_clicks_list):
    """Expande/colapsa las subsecciones al hacer click en la cabecera"""
    from dash import ctx
    import json
    
    if not ctx.triggered:
        # Estado inicial: primera sección expandida
        container_styles = [{'display': 'block'} if i == 0 else {'display': 'none'} for i in range(len(SECCIONES_CONFIG))]
        header_styles = [
            {
                'padding': '12px 16px',
                'cursor': 'pointer',
                'backgroundColor': '#f8f9fa' if i == 0 else 'white',
                'borderLeft': '4px solid #1e3d59',
                'borderBottom': '1px solid #e9ecef',
                'transition': 'all 0.2s ease',
                'userSelect': 'none'
            } for i in range(len(SECCIONES_CONFIG))
        ]
        return container_styles, header_styles
    
    # Detectar qué cabecera fue clickeada
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    clicked_info = json.loads(triggered_id)
    clicked_index = clicked_info['index']
    
    # Preparar estilos
    container_styles = []
    header_styles = []
    
    for i in range(len(SECCIONES_CONFIG)):
        # Mostrar solo las subsecciones de la sección clickeada
        if i == clicked_index:
            container_styles.append({'display': 'block'})
            header_styles.append({
                'padding': '12px 16px',
                'cursor': 'pointer',
                'backgroundColor': '#f8f9fa',
                'borderLeft': '4px solid #1e3d59',
                'borderBottom': '1px solid #e9ecef',
                'transition': 'all 0.2s ease',
                'userSelect': 'none'
            })
        else:
            container_styles.append({'display': 'none'})
            header_styles.append({
                'padding': '12px 16px',
                'cursor': 'pointer',
                'backgroundColor': 'white',
                'borderLeft': '4px solid #1e3d59',
                'borderBottom': '1px solid #e9ecef',
                'transition': 'all 0.2s ease',
                'userSelect': 'none'
            })
    
    return container_styles, header_styles


# Callback para actualizar contenido al seleccionar una subsección
@callback(
    [Output({'type': 'df-subseccion', 'seccion': ALL, 'opcion': ALL}, 'style'),
     Output('df-main-content', 'children')],
    [Input({'type': 'df-subseccion', 'seccion': ALL, 'opcion': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def update_content_from_subseccion(*n_clicks_list):
    """Actualiza el contenido principal al hacer click en una subsección"""
    from dash import ctx
    import json
    
    if not ctx.triggered:
        # Contenido por defecto
        return [], html.Div("Seleccione una opción")
    
    # Detectar qué subsección fue clickeada
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    clicked_info = json.loads(triggered_id)
    seccion_index = clicked_info['seccion']
    opcion_index = clicked_info['opcion']
    
    # Preparar estilos para todas las subsecciones
    styles = []
    for i, seccion in enumerate(SECCIONES_CONFIG):
        for j, subseccion in enumerate(seccion['subsecciones']):
            if i == seccion_index and j == opcion_index:
                # Subsección activa - MUY VISIBLE
                styles.append({
                    'padding': '10px 16px 10px 40px',
                    'cursor': 'pointer',
                    'fontSize': '13px',
                    'color': '#ffffff',
                    'backgroundColor': '#1e3d59',
                    'borderLeft': '4px solid #1e3d59',
                    'borderBottom': '1px solid #f0f0f0',
                    'transition': 'all 0.2s ease',
                    'userSelect': 'none',
                    'fontWeight': '700'
                })
            else:
                # Subsección inactiva
                styles.append({
                    'padding': '10px 16px 10px 40px',
                    'cursor': 'pointer',
                    'fontSize': '13px',
                    'color': '#6c757d',
                    'backgroundColor': 'white',
                    'borderLeft': '2px solid #e9ecef',
                    'borderBottom': '1px solid #f0f0f0',
                    'transition': 'all 0.2s ease',
                    'userSelect': 'none',
                    'fontWeight': '500'
                })
    
    # Obtener parámetros del mapa seleccionado
    seccion = SECCIONES_CONFIG[seccion_index]
    subseccion = seccion['subsecciones'][opcion_index]
    map_key = subseccion['map_key']
    map_params = MAPAS_PARAMS[map_key]
    
    # Crear contenido con gráfico (sin título redundante, create_scatter_plot ya lo incluye)
    content = html.Div([
        html.Div([
            create_scatter_plot(
                metric_x=map_params['metric_x'],
                metric_y=map_params['metric_y'],
                label_x=map_params['label_x'],
                label_y=map_params['label_y'],
                invert_y=map_params.get('invert_y', False),
                custom_title=map_params['title']  # Título personalizado
            )
        ], style={'padding': '20px'})
    ])
    
    return styles, content


# Layout para registro en Dash
def layout():
    return get_diagramas_funcionales_content()
