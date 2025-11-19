# pages/contextos_partidos.py

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import os

def get_escudo_path(team_name):
    """
    Obtiene la ruta del escudo de un equipo.
    Mapea nombres de laliga_matches a nombres de archivos de escudos (que usan nombres de laliga_teams).
    
    Args:
        team_name (str): Nombre del equipo (como aparece en laliga_matches o match_context_analysis)
    
    Returns:
        str: Ruta relativa al escudo
    """
    # Mapeo completo de nombres en laliga_matches a archivos de escudos (nombres de laliga_teams)
    # Los archivos de escudos usan los nombres de laliga_teams
    team_to_file = {
        # Depor
        'Deportivo de La Coruña': 'RC Deportivo.png',
        'RC Deportivo': 'RC Deportivo.png',
        
        # Segunda División - Mapeo de nombres laliga_matches a laliga_teams
        'Albacete Balompié': 'Albacete BP.png',
        'Albacete BP': 'Albacete BP.png',
        
        'Burgos Club de Fútbol': 'Burgos CF.png',
        'Burgos': 'Burgos CF.png',
        
        'Club Deportivo Castellón': 'CD Castellón.png',
        'CD Castellón': 'CD Castellón.png',
        
        'Club Deportivo Leganés': 'CD Leganés.png',
        'CD Leganés': 'CD Leganés.png',
        'Leganés': 'CD Leganés.png',
        
        'Club Deportivo Mirandés': 'CD Mirandés.png',
        'CD Mirandés': 'CD Mirandés.png',
        'Mirandés': 'CD Mirandés.png',
        
        'Cádiz Club de Fútbol': 'Cádiz CF.png',
        'Cádiz CF': 'Cádiz CF.png',
        'Cádiz': 'Cádiz CF.png',
        
        'Córdoba Club de Fútbol': 'Córdoba CF.png',
        'Córdoba CF': 'Córdoba CF.png',
        'Córdoba': 'Córdoba CF.png',
        
        'Granada Club de Fútbol': 'Granada CF.png',
        'Granada CF': 'Granada CF.png',
        'Granada': 'Granada CF.png',
        
        'Málaga Club de Fútbol': 'Málaga CF.png',
        'Málaga CF': 'Málaga CF.png',
        'Málaga': 'Málaga CF.png',
        
        'Real Racing Club': 'Real Racing Club.png',
        'Racing de Santander': 'Real Racing Club.png',
        'Racing': 'Real Racing Club.png',
        
        'Real Sporting de Gijón': 'Real Sporting.png',
        'Real Sporting': 'Real Sporting.png',
        'Sporting de Gijón': 'Real Sporting.png',
        
        'Real Zaragoza': 'Real Zaragoza.png',
        'Zaragoza': 'Real Zaragoza.png',
        
        'Sociedad Deportiva Eibar': 'SD Eibar.png',
        'SD Eibar': 'SD Eibar.png',
        'Eibar': 'SD Eibar.png',
        
        'Sociedad Deportiva Huesca': 'SD Huesca.png',
        'SD Huesca': 'SD Huesca.png',
        'Huesca': 'SD Huesca.png',
        
        'Unión Deportiva Almería': 'UD Almería.png',
        'UD Almería': 'UD Almería.png',
        'Almería': 'UD Almería.png',
        
        'Unión Deportiva Las Palmas': 'UD Las Palmas.png',
        'UD Las Palmas': 'UD Las Palmas.png',
        'Las Palmas': 'UD Las Palmas.png',
        
        'Real Valladolid Club de Fútbol': 'Real Valladolid CF.png',
        'Real Valladolid CF': 'Real Valladolid CF.png',
        'Real Valladolid': 'Real Valladolid CF.png',
        
        'Fútbol Club Andorra': 'FC Andorra.png',
        'FC Andorra': 'FC Andorra.png',
        'Andorra': 'FC Andorra.png',
        
        'Real Sociedad B': 'Real Sociedad B.png',
        
        'AD Ceuta': 'Ceuta.png',
        'Ceuta': 'Ceuta.png',
        
        'Cultural y Deportiva Leonesa': 'Cultural.png',
        'Cultural Leonesa': 'Cultural.png'
    }
    
    # Buscar en el mapeo
    if team_name in team_to_file:
        escudo_file = team_to_file[team_name]
    else:
        # Si no está en el mapeo, intentar con el nombre + .png
        escudo_file = f"{team_name}.png"
    
    # Retornar ruta completa
    return f'/assets/Escudos/{escudo_file}'


def create_match_card(match_info, depor_name="RC Deportivo"):
    """
    Crea una tarjeta visual para un partido con escudos y resultado.
    Al hacer clic abre un modal con detalles.
    
    Args:
        match_info (dict): Información del partido
        depor_name (str): Nombre del Depor
    
    Returns:
        html.Div: Tarjeta del partido
    """
    # Determinar equipos local y visitante
    if match_info['condicion'] == 'Local':
        equipo_local = depor_name
        equipo_visitante = match_info['opponent_name']
        goles_local = match_info['goles_favor']
        goles_visitante = match_info['goles_contra']
    else:
        equipo_local = match_info['opponent_name']
        equipo_visitante = depor_name
        goles_local = match_info['goles_contra']
        goles_visitante = match_info['goles_favor']
    
    # Obtener rutas de escudos
    escudo_local = get_escudo_path(equipo_local)
    escudo_visitante = get_escudo_path(equipo_visitante)
    
    # Color del borde según resultado
    resultado_colors = {
        'Victoria': '#28a745',  # Verde
        'Empate': '#ffc107',    # Amarillo
        'Derrota': '#dc3545'    # Rojo
    }
    border_color = resultado_colors.get(match_info['resultado'], '#6c757d')
    
    return html.Div([
        html.Div([
            # Escudo local
            html.Div([
                html.Img(
                    src=escudo_local,
                    style={
                        'height': '30px',
                        'width': '30px',
                        'objectFit': 'contain'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'width': '35px'}),
            
            # Marcador
            html.Div([
                html.Span(f"{goles_local}", style={'fontWeight': 'bold', 'fontSize': '16px'}),
                html.Span(" - ", style={'margin': '0 5px', 'color': '#6c757d'}),
                html.Span(f"{goles_visitante}", style={'fontWeight': 'bold', 'fontSize': '16px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'margin': '0 10px'}),
            
            # Escudo visitante
            html.Div([
                html.Img(
                    src=escudo_visitante,
                    style={
                        'height': '30px',
                        'width': '30px',
                        'objectFit': 'contain'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'width': '35px'})
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '8px 12px',
            'margin': '5px 0',
            'backgroundColor': 'white',
            'border': f'2px solid {border_color}',
            'borderRadius': '8px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'cursor': 'pointer',
            'transition': 'all 0.2s ease'
        }, className='match-card', **{'data-match-id': match_info['match_id']})
    ], 
    id={'type': 'match-card-wrapper', 'index': match_info['match_id']},
    style={'position': 'relative'})


def create_context_cell(matches, cell_title, cell_color):
    """
    Crea una celda de la matriz con los partidos correspondientes.
    
    Args:
        matches (list): Lista de partidos
        cell_title (str): Título de la celda
        cell_color (str): Color de fondo de la celda
    
    Returns:
        html.Div: Celda de la matriz
    """
    return html.Div([
        # Título de la celda
        html.Div([
            html.H5(cell_title, style={
                'color': 'white',
                'fontWeight': '600',
                'fontSize': '14px',
                'margin': '0',
                'textAlign': 'center'
            })
        ], style={
            'backgroundColor': cell_color,
            'padding': '12px',
            'borderRadius': '8px 8px 0 0'
        }),
        
        # Contenido de partidos
        html.Div([
            html.Div([
                create_match_card(match) for match in matches
            ] if matches else [
                html.Div([
                    html.I(className="fas fa-inbox", style={'fontSize': '24px', 'color': '#dee2e6', 'marginBottom': '8px'}),
                    html.P("Sin partidos", style={'color': '#6c757d', 'fontSize': '12px', 'margin': '0'})
                ], style={'textAlign': 'center', 'padding': '20px'})
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'gap': '5px'
            })
        ], style={
            'backgroundColor': '#f8f9fa',
            'padding': '15px',
            'borderRadius': '0 0 8px 8px',
            'minHeight': '200px',
            'maxHeight': '400px',
            'overflowY': 'auto'
        }),
        
        # Contador de partidos
        html.Div([
            html.Span(f"{len(matches)} partido{'s' if len(matches) != 1 else ''}", style={
                'fontSize': '11px',
                'color': '#6c757d',
                'fontWeight': '500'
            })
        ], style={
            'textAlign': 'center',
            'padding': '8px',
            'backgroundColor': 'white',
            'borderRadius': '0 0 8px 8px',
            'borderTop': '1px solid #dee2e6'
        })
    ], style={
        'border': '1px solid #dee2e6',
        'borderRadius': '8px',
        'backgroundColor': 'white',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
    })


def get_matriz_contextos_content():
    """
    Contenido de la sub-sección Matriz de Contextos de Partidos.
    """
    return html.Div([
        # Contenedor de la matriz
        html.Div(id='contextos-matrix-container', children=[
            # Mensaje de carga inicial
            html.Div([
                dbc.Spinner(color="primary", size="lg"),
                html.P("Cargando análisis de contextos...", className="mt-3 text-muted")
            ], style={'textAlign': 'center', 'padding': '60px'})
        ]),
        
        # Store para datos de partidos
        dcc.Store(id='contextos-data-store'),
        
        # Modal para detalles del partido
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='modal-match-title')),
            dbc.ModalBody(id='modal-match-body'),
            dbc.ModalFooter(
                dbc.Button("Cerrar", id="close-match-modal", className="ms-auto", n_clicks=0)
            )
        ], id='match-detail-modal', is_open=False, size='lg')
        
    ])


def get_estilo_eficacia_ofensiva_content():
    """
    Contenido de la sub-sección Estilo - Eficacia Ofensiva.
    """
    return html.Div([
        html.Div([
            html.I(className="fas fa-chart-line me-2", style={"fontSize": "20px", "color": "#1e3d59"}),
            html.H5("Estilo - Eficacia Ofensiva", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-3"),
        html.Div([
            html.I(className="fas fa-hard-hat fa-3x mb-3", style={"color": "#ffc107"}),
            html.H5("En Desarrollo", style={"color": "#6c757d"})
        ], style={"textAlign": "center", "padding": "60px 20px"})
    ])


def get_estilo_eficacia_defensiva_content():
    """
    Contenido de la sub-sección Estilo - Eficacia Defensiva.
    """
    return html.Div([
        html.Div([
            html.I(className="fas fa-shield-alt me-2", style={"fontSize": "20px", "color": "#1e3d59"}),
            html.H5("Estilo - Eficacia Defensiva", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-3"),
        html.Div([
            html.I(className="fas fa-hard-hat fa-3x mb-3", style={"color": "#ffc107"}),
            html.H5("En Desarrollo", style={"color": "#6c757d"})
        ], style={"textAlign": "center", "padding": "60px 20px"})
    ])


def get_rendimiento_fisico_content():
    """
    Contenido de la sub-sección Rendimiento Físico.
    """
    return html.Div([
        html.Div([
            html.I(className="fas fa-running me-2", style={"fontSize": "20px", "color": "#1e3d59"}),
            html.H5("Rendimiento Físico", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-3"),
        html.Div([
            html.I(className="fas fa-hard-hat fa-3x mb-3", style={"color": "#ffc107"}),
            html.H5("En Desarrollo", style={"color": "#6c757d"})
        ], style={"textAlign": "center", "padding": "60px 20px"})
    ])


def get_rendimiento_balon_parado_content():
    """
    Contenido de la sub-sección Rendimiento Balón Parado.
    """
    return html.Div([
        html.Div([
            html.I(className="fas fa-futbol me-2", style={"fontSize": "20px", "color": "#1e3d59"}),
            html.H5("Rendimiento Balón Parado", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-3"),
        html.Div([
            html.I(className="fas fa-hard-hat fa-3x mb-3", style={"color": "#ffc107"}),
            html.H5("En Desarrollo", style={"color": "#6c757d"})
        ], style={"textAlign": "center", "padding": "60px 20px"})
    ])


def get_contextos_partidos_content():
    """
    Contenido principal de la página de Contextos de Partidos con navegación por sub-secciones.
    """
    return html.Div([
        # Sub-navegación para Contextos Partidos
        html.Div([
            html.Div([
                html.Button(
                    "Matriz Contextos Partidos",
                    id="subtab-ctx-matriz",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#1e3d59",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "padding": "10px 20px",
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "minWidth": "220px"
                    }
                ),
                html.Button(
                    "Estilo - Eficacia Ofensiva",
                    id="subtab-ctx-estilo-of",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "10px 20px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "minWidth": "220px"
                    }
                ),
                html.Button(
                    "Estilo - Eficacia Defensiva",
                    id="subtab-ctx-estilo-def",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "10px 20px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "minWidth": "220px"
                    }
                ),
                html.Button(
                    "Rendimiento Físico",
                    id="subtab-ctx-fisico",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "10px 20px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "minWidth": "200px"
                    }
                ),
                html.Button(
                    "Rendimiento Balón Parado",
                    id="subtab-ctx-balon-parado",
                    className="subtab-button",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "10px 20px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "minWidth": "230px"
                    }
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "padding": "20px 0",
                "borderBottom": "1px solid #e9ecef",
                "flexWrap": "wrap",
                "gap": "10px"
            })
        ], style={
            "backgroundColor": "white",
            "marginBottom": "20px"
        }),
        
        # Contenido dinámico según sub-sección seleccionada
        html.Div([
            html.Div(
                id="ctx-subtab-content",
                children=get_matriz_contextos_content()  # Por defecto mostrar Matriz
            )
        ], className="p-4")
    ])


# Callback para cargar la matriz de contextos (solo carga inicial)
# IMPORTANTE: Este callback se registra cuando se importa el módulo
@callback(
    Output('contextos-matrix-container', 'children'),
    [Input('contextos-data-store', 'data')],
    prevent_initial_call=False
)
def update_contextos_matrix(dummy):
    """
    Actualiza la matriz de contextos de partidos.
    """
    from utils.db_manager import get_matches_by_context_matrix
    
    try:
        # Obtener datos de la matriz
        matrix = get_matches_by_context_matrix(team_name="RC Deportivo")
        
        # Verificar si hay datos
        total_matches = sum(
            len(matrix[resultado][contexto]) 
            for resultado in ['Positivo', 'Negativo'] 
            for contexto in ['Favorable', 'Desfavorable']
        )
        
        if total_matches == 0:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-info-circle fa-3x mb-3", style={"color": "#17a2b8"}),
                    html.H5("No hay datos disponibles", style={"color": "#6c757d"}),
                    html.P("No se encontraron partidos con análisis de contexto en la base de datos.", 
                           className="text-muted")
                ], style={"textAlign": "center", "padding": "60px 20px"})
            ])
        
        # Colores ajustados: verde para favorable, rojo para desfavorable
        colors = {
            'Positivo': {
                'Favorable': '#28a745',      # Verde
                'Desfavorable': '#dc3545'    # Rojo
            },
            'Negativo': {
                'Favorable': '#28a745',      # Verde
                'Desfavorable': '#dc3545'    # Rojo
            }
        }
        
        # Crear la matriz 2x2 (2 columnas lado a lado)
        return html.Div([
            # Contenedor principal con 2 columnas
            html.Div([
                # COLUMNA 1: RESULTADO POSITIVO
                html.Div([
                    # Encabezado Resultado Positivo
                    html.Div([
                        html.H4("RESULTADO POSITIVO", style={
                            'color': 'white',
                            'fontWeight': '700',
                            'margin': '0',
                            'textAlign': 'center',
                            'textTransform': 'uppercase',
                            'letterSpacing': '1px'
                        })
                    ], style={
                        'backgroundColor': '#28a745',
                        'padding': '20px',
                        'borderRadius': '8px 8px 0 0',
                        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                    }),
                    
                    # Sub-columnas: Favorable y Desfavorable
                    html.Div([
                        # Positivo - Favorable
                        html.Div([
                            create_context_cell(
                                matrix['Positivo']['Favorable'],
                                'CONTEXTO FAVORABLE',
                                colors['Positivo']['Favorable']
                            )
                        ], style={'flex': '1', 'marginRight': '5px'}),
                        
                        # Positivo - Desfavorable
                        html.Div([
                            create_context_cell(
                                matrix['Positivo']['Desfavorable'],
                                'CONTEXTO DESFAVORABLE',
                                colors['Positivo']['Desfavorable']
                            )
                        ], style={'flex': '1', 'marginLeft': '5px'})
                    ], style={
                        'display': 'flex',
                        'marginTop': '10px'
                    })
                ], style={'flex': '1', 'marginRight': '15px'}),
                
                # COLUMNA 2: RESULTADO NEGATIVO
                html.Div([
                    # Encabezado Resultado Negativo
                    html.Div([
                        html.H4("RESULTADO NEGATIVO", style={
                            'color': 'white',
                            'fontWeight': '700',
                            'margin': '0',
                            'textAlign': 'center',
                            'textTransform': 'uppercase',
                            'letterSpacing': '1px'
                        })
                    ], style={
                        'backgroundColor': '#dc3545',
                        'padding': '20px',
                        'borderRadius': '8px 8px 0 0',
                        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'
                    }),
                    
                    # Sub-columnas: Favorable y Desfavorable
                    html.Div([
                        # Negativo - Favorable
                        html.Div([
                            create_context_cell(
                                matrix['Negativo']['Favorable'],
                                'CONTEXTO FAVORABLE',
                                colors['Negativo']['Favorable']
                            )
                        ], style={'flex': '1', 'marginRight': '5px'}),
                        
                        # Negativo - Desfavorable
                        html.Div([
                            create_context_cell(
                                matrix['Negativo']['Desfavorable'],
                                'CONTEXTO DESFAVORABLE',
                                colors['Negativo']['Desfavorable']
                            )
                        ], style={'flex': '1', 'marginLeft': '5px'})
                    ], style={
                        'display': 'flex',
                        'marginTop': '10px'
                    })
                ], style={'flex': '1', 'marginLeft': '15px'})
            ], style={
                'display': 'flex',
                'width': '100%'
            }),
            
            # Store para guardar todos los datos de partidos (para el modal)
            dcc.Store(id='all-matches-store', data=matrix)
        ])
        
    except Exception as e:
        print(f"Error en update_contextos_matrix: {e}")
        import traceback
        traceback.print_exc()
        
        return html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle fa-3x mb-3", style={"color": "#dc3545"}),
                html.H5("Error al cargar datos", style={"color": "#6c757d"}),
                html.P(f"Error: {str(e)}", className="text-muted")
            ], style={"textAlign": "center", "padding": "60px 20px"})
        ])


# Callback para abrir el modal con detalles del partido
@callback(
    [Output('match-detail-modal', 'is_open'),
     Output('modal-match-title', 'children'),
     Output('modal-match-body', 'children')],
    [Input({'type': 'match-card-wrapper', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('close-match-modal', 'n_clicks')],
    [State('match-detail-modal', 'is_open'),
     State('all-matches-store', 'data')],
    prevent_initial_call=True
)
def toggle_match_modal(match_clicks, close_clicks, is_open, all_matches_data):
    """
    Abre/cierra el modal y muestra detalles del partido seleccionado.
    """
    from dash import ctx
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    
    # Verificar si alguna tarjeta fue clickeada
    if not any(match_clicks):
        return dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Si se hizo clic en cerrar
    if 'close-match-modal' in triggered_id:
        return False, "", ""
    
    # Si se hizo clic en una tarjeta de partido
    if 'match-card-wrapper' in triggered_id:
        # Extraer el match_id del trigger
        import json
        trigger_dict = json.loads(triggered_id.split('.')[0])
        match_id = trigger_dict['index']
        
        # Buscar el partido en all_matches_data
        if not all_matches_data:
            return False, "", ""
        
        match_info = None
        for resultado in ['Positivo', 'Negativo']:
            for contexto in ['Favorable', 'Desfavorable']:
                for match in all_matches_data[resultado][contexto]:
                    if match['match_id'] == match_id:
                        match_info = match
                        break
                if match_info:
                    break
            if match_info:
                break
        
        if not match_info:
            return False, "", ""
        
        # Colores según resultado
        resultado_colors = {
            'Victoria': '#28a745',  # Verde
            'Empate': '#ffc107',    # Amarillo
            'Derrota': '#dc3545'    # Rojo
        }
        
        # Título del modal
        title = html.Div([
            html.Span(f"Jornada {match_info['match_day_number']} - ", style={'fontSize': '18px', 'fontWeight': '600'}),
            html.Span(f"{match_info['opponent_name']}", style={'fontSize': '18px', 'fontWeight': '700', 'color': '#1e3d59'}),
            html.Span(f" ({match_info['condicion']})", style={'fontSize': '16px', 'color': '#6c757d'})
        ])
        
        # Cuerpo del modal
        body = html.Div([
            # Información del partido
            html.Div([
                html.P([
                    html.Strong("Fecha: "),
                    match_info['match_date'].strftime('%d/%m/%Y') if isinstance(match_info['match_date'], pd.Timestamp) else match_info['match_date']
                ], style={'fontSize': '14px', 'marginBottom': '8px'}),
                
                html.P([
                    html.Strong("Resultado: "),
                    f"{match_info['goles_favor']} - {match_info['goles_contra']} ",
                    html.Span(f"({match_info['resultado']})", style={
                        'fontWeight': '600',
                        'color': resultado_colors.get(match_info['resultado'], '#6c757d')
                    })
                ], style={'fontSize': '14px', 'marginBottom': '15px'})
            ], style={'marginBottom': '20px'}),
            
            # Análisis del resultado
            html.Div([
                html.P([
                    html.Strong("Clasificación del Resultado", style={'color': '#1e3d59'})
                ], style={'marginBottom': '8px'}),
                
                html.P([
                    f"Resultado ",
                    html.Strong(f"{match_info['resultado']}", style={
                        'color': resultado_colors.get(match_info['resultado'], '#6c757d')
                    }),
                    f" como {match_info['condicion'].lower()} → Clasificación: ",
                    html.Strong(f"{match_info['resultado_tipo']}", style={
                        'color': '#28a745' if match_info['resultado_tipo'] == 'Positivo' else '#dc3545'
                    })
                ], style={'fontSize': '14px', 'lineHeight': '1.6'})
            ], style={'marginBottom': '20px'}),
            
            # Análisis del contexto
            html.Div([
                html.P([
                    html.Strong("Contexto del Marcador", style={'color': '#1e3d59'})
                ], style={'marginBottom': '8px'}),
                
                html.P([
                    html.Strong("Ganando: "),
                    f"{match_info['pct_ganando']:.1f}% | ",
                    html.Strong("Empatando: "),
                    f"{match_info['pct_empatando']:.1f}% | ",
                    html.Strong("Perdiendo: "),
                    f"{match_info['pct_perdiendo']:.1f}%"
                ], style={'fontSize': '14px', 'marginBottom': '10px'}),
                
                html.P([
                    f"Estados favorables: ",
                    html.Strong(f"{match_info['pct_ganando'] + match_info['pct_empatando']:.1f}%", style={
                        'color': '#28a745' if (match_info['pct_ganando'] + match_info['pct_empatando']) > match_info['pct_perdiendo'] else '#dc3545'
                    }),
                    f" | Estados desfavorables: ",
                    html.Strong(f"{match_info['pct_perdiendo']:.1f}%", style={
                        'color': '#dc3545' if match_info['pct_perdiendo'] > (match_info['pct_ganando'] + match_info['pct_empatando']) else '#28a745'
                    })
                ], style={'fontSize': '14px', 'marginBottom': '10px'}),
                
                html.P([
                    f"Contexto: ",
                    html.Strong(f"{match_info['contexto_tipo']}", style={
                        'color': '#28a745' if match_info['contexto_tipo'] == 'Favorable' else '#dc3545'
                    }),
                    f" (el equipo pasó ",
                    html.Strong(
                        f"{match_info['pct_ganando'] + match_info['pct_empatando']:.1f}% en estados favorables" 
                        if (match_info['pct_ganando'] + match_info['pct_empatando']) > match_info['pct_perdiendo'] 
                        else f"{match_info['pct_perdiendo']:.1f}% perdiendo"
                    ),
                    ")"
                ], style={'fontSize': '14px', 'lineHeight': '1.6'})
            ], style={'marginBottom': '20px'})
        ])
        
        return True, title, body
    
    return False, "", ""


# Callback para actualizar las sub-pestañas de Contextos Partidos
@callback(
    [Output("subtab-ctx-matriz", "style"),
     Output("subtab-ctx-estilo-of", "style"),
     Output("subtab-ctx-estilo-def", "style"),
     Output("subtab-ctx-fisico", "style"),
     Output("subtab-ctx-balon-parado", "style"),
     Output("ctx-subtab-content", "children")],
    [Input("subtab-ctx-matriz", "n_clicks"),
     Input("subtab-ctx-estilo-of", "n_clicks"),
     Input("subtab-ctx-estilo-def", "n_clicks"),
     Input("subtab-ctx-fisico", "n_clicks"),
     Input("subtab-ctx-balon-parado", "n_clicks")]
)
def update_ctx_subtabs(n_matriz, n_estilo_of, n_estilo_def, n_fisico, n_balon_parado):
    """
    Actualiza las sub-pestañas de Contextos Partidos.
    """
    # Estilos
    style_inactive = {
        "backgroundColor": "#f8f9fa",
        "color": "#6c757d",
        "border": "1px solid #e9ecef",
        "borderRadius": "6px",
        "padding": "10px 20px",
        "fontWeight": "500",
        "fontSize": "12px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px"
    }
    
    style_active = {
        "backgroundColor": "#1e3d59",
        "color": "white",
        "border": "none",
        "borderRadius": "6px",
        "padding": "10px 20px",
        "fontWeight": "600",
        "fontSize": "12px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
    }
    
    # Detectar qué botón fue clickeado
    ctx = dash.callback_context
    if not ctx.triggered:
        active_subtab = 0  # Matriz por defecto
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'subtab-ctx-matriz':
            active_subtab = 0
        elif button_id == 'subtab-ctx-estilo-of':
            active_subtab = 1
        elif button_id == 'subtab-ctx-estilo-def':
            active_subtab = 2
        elif button_id == 'subtab-ctx-fisico':
            active_subtab = 3
        elif button_id == 'subtab-ctx-balon-parado':
            active_subtab = 4
        else:
            active_subtab = 0
    
    # Establecer estilos (añadir minWidth específico para cada botón)
    styles = [style_inactive.copy() for _ in range(5)]
    styles[active_subtab] = style_active.copy()
    
    # Añadir minWidth específico
    styles[0]["minWidth"] = "220px"
    styles[1]["minWidth"] = "220px"
    styles[2]["minWidth"] = "220px"
    styles[3]["minWidth"] = "200px"
    styles[4]["minWidth"] = "230px"
    
    # Establecer contenido
    if active_subtab == 0:
        content = get_matriz_contextos_content()
    elif active_subtab == 1:
        content = get_estilo_eficacia_ofensiva_content()
    elif active_subtab == 2:
        content = get_estilo_eficacia_defensiva_content()
    elif active_subtab == 3:
        content = get_rendimiento_fisico_content()
    elif active_subtab == 4:
        content = get_rendimiento_balon_parado_content()
    else:
        content = get_matriz_contextos_content()
    
    return styles[0], styles[1], styles[2], styles[3], styles[4], content
