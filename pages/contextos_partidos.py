# pages/contextos_partidos.py

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
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


def get_contextos_partidos_content():
    """
    Contenido principal de la página de Contextos de Partidos.
    """
    return html.Div([
        # Título
        html.Div([
            html.I(className="fas fa-th-large me-2", style={"fontSize": "24px", "color": "#1e3d59"}),
            html.H4("Matriz de Contextos de Partidos", style={"color": "#1e3d59", "display": "inline"})
        ], className="mb-3"),
        
        # Descripción
        html.P([
            "Clasificación de partidos según ",
            html.Strong("resultado tipo"),
            " (Positivo/Negativo) y ",
            html.Strong("contexto tipo"),
            " (Favorable/Desfavorable). ",
            html.Span("Haz clic en un partido para ver detalles.", style={'fontStyle': 'italic', 'color': '#6c757d'})
        ], className="text-muted mb-4"),
        
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
        
    ], className="p-4")


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
        
        # Construir título del modal
        if match_info['condicion'] == 'Local':
            title = f"RC Deportivo {match_info['goles_favor']}-{match_info['goles_contra']} {match_info['opponent_name']}"
        else:
            title = f"{match_info['opponent_name']} {match_info['goles_contra']}-{match_info['goles_favor']} RC Deportivo"
        
        # Construir cuerpo del modal con explicación detallada
        body = html.Div([
            # Resultado
            html.Div([
                html.H5("📊 Resultado del Partido", style={'color': '#1e3d59', 'marginBottom': '15px'}),
                html.P([
                    f"En este partido el resultado ha sido ",
                    html.Strong(f"{match_info['resultado']}", style={
                        'color': '#28a745' if match_info['resultado'] == 'Victoria' else '#dc3545' if match_info['resultado'] == 'Derrota' else '#ffc107'
                    }),
                    f" como {match_info['condicion'].lower()}."
                ], style={'fontSize': '15px', 'lineHeight': '1.6'})
            ], style={'marginBottom': '25px'}),
            
            # Explicación del resultado tipo
            html.Div([
                html.H5("✅ Clasificación del Resultado", style={'color': '#1e3d59', 'marginBottom': '15px'}),
                html.P([
                    f"Este resultado se clasifica como ",
                    html.Strong(f"{match_info['resultado_tipo']}", style={
                        'color': '#28a745' if match_info['resultado_tipo'] == 'Positivo' else '#dc3545'
                    }),
                    f" porque ",
                    html.Span(
                        "las victorias siempre son positivas." if match_info['resultado'] == 'Victoria'
                        else "las derrotas siempre son negativas." if match_info['resultado'] == 'Derrota'
                        else f"los empates como {match_info['condicion'].lower()} se consideran {'positivos' if match_info['condicion'] == 'Visitante' else 'negativos'}."
                    )
                ], style={'fontSize': '15px', 'lineHeight': '1.6'})
            ], style={'marginBottom': '25px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'}),
            
            # Contexto del marcador
            html.Div([
                html.H5("⏱️ Contexto del Marcador", style={'color': '#1e3d59', 'marginBottom': '15px'}),
                html.P([
                    f"El contexto ha sido ",
                    html.Strong(f"{match_info['contexto_tipo']}", style={
                        'color': '#28a745' if match_info['contexto_tipo'] == 'Favorable' else '#dc3545'
                    }),
                    f" al ir el equipo:"
                ], style={'fontSize': '15px', 'lineHeight': '1.6', 'marginBottom': '10px'}),
                
                # Porcentajes de tiempo
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-arrow-up", style={'marginRight': '8px', 'color': '#28a745'}),
                            html.Strong("Ganando: ", style={'color': '#28a745'}),
                            html.Span(f"{match_info['pct_ganando']:.1f}% del tiempo")
                        ], style={'marginBottom': '8px'}),
                        
                        html.Div([
                            html.I(className="fas fa-equals", style={'marginRight': '8px', 'color': '#ffc107'}),
                            html.Strong("Empatando: ", style={'color': '#ffc107'}),
                            html.Span(f"{match_info['pct_empatando']:.1f}% del tiempo")
                        ], style={'marginBottom': '8px'}),
                        
                        html.Div([
                            html.I(className="fas fa-arrow-down", style={'marginRight': '8px', 'color': '#dc3545'}),
                            html.Strong("Perdiendo: ", style={'color': '#dc3545'}),
                            html.Span(f"{match_info['pct_perdiendo']:.1f}% del tiempo")
                        ])
                    ], style={'fontSize': '14px'})
                ], style={'padding': '15px', 'backgroundColor': 'white', 'borderRadius': '6px', 'border': '1px solid #dee2e6'}),
                
                html.P([
                    html.Br(),
                    f"El equipo pasó la mayor parte del tiempo ",
                    html.Strong(f"{match_info['contexto_preferente'].lower()}", style={
                        'color': '#28a745' if match_info['contexto_preferente'] in ['Ganando', 'Empatando'] else '#dc3545'
                    }),
                    f", lo que genera un contexto {match_info['contexto_tipo'].lower()}."
                ], style={'fontSize': '15px', 'lineHeight': '1.6', 'marginTop': '15px'})
            ], style={'marginBottom': '25px'})
        ])
        
        return True, title, body
    
    return False, "", ""
