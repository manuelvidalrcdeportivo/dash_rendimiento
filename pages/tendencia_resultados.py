# pages/tendencia_resultados.py

import dash
from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def create_last_match_card(match):
    """Crea tarjeta del último partido con escudos"""
    resultado_colors = {
        'Victoria': '#28a745',
        'Empate': '#ffc107',
        'Derrota': '#dc3545'
    }
    
    color = resultado_colors.get(match['resultado'], '#6c757d')
    
    # Obtener escudos
    escudo_depor = '/assets/Escudos/RC Deportivo.png'
    escudo_rival = get_escudo_path(match['opponent_name'])
    
    # Determinar orden según condición
    if match['condicion'] == 'Local':
        escudo_izq = escudo_depor
        escudo_der = escudo_rival
        goles_izq = match['goles_favor']
        goles_der = match['goles_contra']
        nombre_izq = "RC Deportivo"
        nombre_der = match['opponent_name']
    else:
        escudo_izq = escudo_rival
        escudo_der = escudo_depor
        goles_izq = match['goles_contra']
        goles_der = match['goles_favor']
        nombre_izq = match['opponent_name']
        nombre_der = "RC Deportivo"
    
    return html.Div([
        html.Div("Último Partido", style={
            'fontSize': '12px',
            'color': '#6c757d',
            'fontWeight': '500',
            'marginBottom': '10px',
            'textAlign': 'center'
        }),
        html.Div([
            # Equipo izquierdo
            html.Div([
                html.Img(src=escudo_izq, style={
                    'height': '40px',
                    'width': '40px',
                    'objectFit': 'contain',
                    'marginBottom': '5px'
                }),
                html.Div(nombre_izq[:15] + '...' if len(nombre_izq) > 15 else nombre_izq, style={
                    'fontSize': '11px',
                    'color': '#6c757d',
                    'textAlign': 'center'
                })
            ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),
            
            # Marcador
            html.Div([
                html.Span(f"{goles_izq}", style={
                    'fontSize': '32px',
                    'fontWeight': '700',
                    'color': color
                }),
                html.Span(" - ", style={
                    'fontSize': '24px',
                    'fontWeight': '500',
                    'color': '#6c757d',
                    'margin': '0 8px'
                }),
                html.Span(f"{goles_der}", style={
                    'fontSize': '32px',
                    'fontWeight': '700',
                    'color': color
                })
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
            
            # Equipo derecho
            html.Div([
                html.Img(src=escudo_der, style={
                    'height': '40px',
                    'width': '40px',
                    'objectFit': 'contain',
                    'marginBottom': '5px'
                }),
                html.Div(nombre_der[:15] + '...' if len(nombre_der) > 15 else nombre_der, style={
                    'fontSize': '11px',
                    'color': '#6c757d',
                    'textAlign': 'center'
                })
            ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'})
    ], 
    id={'type': 'match-card-timeline', 'index': match.get('match_id', 0)},
    n_clicks=0,
    style={
        'padding': '15px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '10px',
        'border': f'2px solid {color}',
        'cursor': 'pointer',
        'transition': 'transform 0.2s ease'
    })


def create_kpi_card(title, value, subtitle="", icon="fa-chart-line", color="#1e3d59"):
    """Crea una tarjeta KPI atractiva"""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas {icon}", style={
                    'fontSize': '32px',
                    'color': color,
                    'marginBottom': '10px'
                }),
                html.H3(str(value), style={
                    'color': color,
                    'fontWeight': '700',
                    'margin': '10px 0 5px 0'
                }),
                html.P(title, style={
                    'color': '#6c757d',
                    'fontSize': '14px',
                    'fontWeight': '500',
                    'margin': '0'
                }),
                html.P(subtitle, style={
                    'color': '#adb5bd',
                    'fontSize': '12px',
                    'margin': '5px 0 0 0'
                }) if subtitle else None
            ], style={'textAlign': 'center'})
        ])
    ], className="shadow-sm h-100", style={'border': 'none', 'borderRadius': '12px'})


def get_escudo_path(team_name):
    """Obtiene la ruta del escudo de un equipo"""
    from pages.contextos_partidos import get_escudo_path as get_escudo
    return get_escudo(team_name)


def create_match_timeline_card(match):
    """Crea una tarjeta de partido para la línea temporal con escudos"""
    resultado_colors = {
        'Victoria': '#28a745',
        'Empate': '#ffc107',
        'Derrota': '#dc3545'
    }
    
    color = resultado_colors.get(match['resultado'], '#6c757d')
    
    # Obtener escudos
    escudo_depor = '/assets/Escudos/RC Deportivo.png'
    escudo_rival = get_escudo_path(match['opponent_name'])
    
    # Determinar orden según condición
    if match['condicion'] == 'Local':
        escudo_izq = escudo_depor
        escudo_der = escudo_rival
        goles_izq = match['goles_favor']
        goles_der = match['goles_contra']
    else:
        escudo_izq = escudo_rival
        escudo_der = escudo_depor
        goles_izq = match['goles_contra']
        goles_der = match['goles_favor']
    
    return html.Div([
        # Jornada
        html.Div([
            html.Span(f"J{match['match_day_number']}", style={
                'fontSize': '11px',
                'fontWeight': '600',
                'color': 'white',
                'backgroundColor': color,
                'padding': '4px 10px',
                'borderRadius': '6px'
            })
        ], style={'marginBottom': '10px', 'textAlign': 'center'}),
        
        # Escudos y resultado
        html.Div([
            # Escudo izquierdo
            html.Div([
                html.Img(src=escudo_izq, style={
                    'height': '40px',
                    'width': '40px',
                    'objectFit': 'contain'
                })
            ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),
            
            # Marcador
            html.Div([
                html.Span(f"{goles_izq}", style={
                    'fontSize': '24px',
                    'fontWeight': '700',
                    'color': color
                }),
                html.Span(" - ", style={
                    'fontSize': '20px',
                    'fontWeight': '500',
                    'color': '#6c757d',
                    'margin': '0 5px'
                }),
                html.Span(f"{goles_der}", style={
                    'fontSize': '24px',
                    'fontWeight': '700',
                    'color': color
                })
            ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),
            
            # Escudo derecho
            html.Div([
                html.Img(src=escudo_der, style={
                    'height': '40px',
                    'width': '40px',
                    'objectFit': 'contain'
                })
            ], style={'flex': '1', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'})
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '8px'}),
        
        # Nombre rival (pequeño)
        html.Div([
            html.Span(match['opponent_name'], style={
                'fontSize': '11px',
                'fontWeight': '500',
                'color': '#6c757d',
                'textAlign': 'center'
            })
        ], style={'textAlign': 'center'})
    ], 
    id={'type': 'match-card-timeline', 'index': match.get('match_id', match['match_day_number'])},
    n_clicks=0,
    style={
        'padding': '15px',
        'backgroundColor': 'white',
        'border': f'2px solid {color}',
        'borderRadius': '10px',
        'minWidth': '140px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
        'cursor': 'pointer',
        'transition': 'transform 0.2s ease'
    })


def create_standings_compact(standings_data):
    """Crea tabla clasificatoria compacta para el header"""
    if not standings_data or 'context_standings' not in standings_data:
        return html.Div()
    
    context_df = standings_data['context_standings']
    
    if context_df.empty:
        return html.Div()
    
    def create_compact_row(row, is_depor=False, total_teams=22):
        """Crea una fila compacta"""
        change_icon = ""
        change_color = "#6c757d"
        if row['position_change'] > 0:
            change_icon = "↑"
            change_color = "#28a745"
        elif row['position_change'] < 0:
            change_icon = "↓"
            change_color = "#dc3545"
        else:
            change_icon = "="
        
        # Determinar color de fondo según zona de clasificación
        position = int(row['position'])
        bg_color = 'transparent'
        border_left = 'none'
        
        if position <= 2:
            # Ascenso directo (1-2) - Verde oscuro
            bg_color = '#c8e6c9' if not is_depor else '#a5d6a7'
            border_left = '4px solid #2e7d32'
        elif position <= 6:
            # Playoff (3-6) - Verde claro
            bg_color = '#e8f5e9' if not is_depor else '#c8e6c9'
            border_left = '4px solid #66bb6a'
        elif position > total_teams - 4:
            # Descenso (últimos 4) - Rojo
            bg_color = '#ffcdd2' if not is_depor else '#ef9a9a'
            border_left = '4px solid #c62828'
        elif is_depor:
            bg_color = '#fff3e0'
            border_left = '4px solid #ffc107'
        
        row_style = {
            'display': 'flex',
            'alignItems': 'center',
            'padding': '10px 12px',
            'borderBottom': '1px solid #f0f0f0',
            'backgroundColor': bg_color,
            'fontWeight': '600' if is_depor else '400',
            'borderRadius': '6px',
            'borderLeft': border_left,
            'marginBottom': '2px'
        }
        
        return html.Div([
            # Posición
            html.Div([
                html.Span(str(int(row['position'])), style={
                    'fontSize': '14px',
                    'fontWeight': '700',
                    'color': '#1e3d59'
                }),
                html.Span(change_icon, style={
                    'fontSize': '10px',
                    'color': change_color,
                    'marginLeft': '3px'
                })
            ], style={'width': '45px', 'textAlign': 'center'}),
            
            # Escudo
            html.Img(src=get_escudo_path(row['team_name']), style={
                'height': '24px',
                'width': '24px',
                'objectFit': 'contain',
                'marginRight': '10px'
            }),
            
            # Equipo (nombre corto si es muy largo)
            html.Div(
                row['team_name'][:18] + '...' if len(row['team_name']) > 18 else row['team_name'],
                style={
                    'flex': '1',
                    'fontSize': '14px',
                    'color': '#1e3d59',
                    'whiteSpace': 'nowrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis'
                }
            ),
            
            # PJ (Partidos Jugados)
            html.Div(str(int(row['matches_played'])), style={
                'width': '35px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#6c757d'
            }),
            
            # Puntos
            html.Div(str(int(row['points'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '15px',
                'fontWeight': '700',
                'color': '#1e3d59'
            })
        ], style=row_style)
    
    # Crear filas
    total_teams = len(standings_data.get('full_standings', context_df))
    rows = []
    for _, row in context_df.iterrows():
        is_depor = row['team_name'] == "RC Deportivo"
        rows.append(create_compact_row(row, is_depor, total_teams))
    
    return html.Div([
        # Título
        html.Div([
            html.I(className="fas fa-trophy me-2", style={'color': '#ffc107', 'fontSize': '16px'}),
            html.Span("Clasificación", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': '#1e3d59'
            })
        ], style={'marginBottom': '12px'}),
        
        # Cabecera mini
        html.Div([
            html.Div("Pos", style={'width': '45px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Equipo", style={'flex': '1', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d', 'marginLeft': '34px'}),
            html.Div("PJ", style={'width': '35px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Pts", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'})
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'padding': '8px 12px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '6px',
            'marginBottom': '10px'
        }),
        
        # Filas
        html.Div(rows, style={'maxHeight': '280px', 'overflowY': 'auto'}),
        
        # Botón ver más
        html.Div([
            html.Button([
                html.I(className="fas fa-expand-alt me-1", style={'fontSize': '10px'}),
                html.Span("Ver tabla completa", style={'fontSize': '11px'})
            ], id='standings-modal-open-btn', n_clicks=0, style={
                'backgroundColor': 'transparent',
                'border': '1px solid #dee2e6',
                'color': '#6c757d',
                'padding': '6px 12px',
                'borderRadius': '4px',
                'fontSize': '11px',
                'fontWeight': '500',
                'cursor': 'pointer',
                'width': '100%',
                'marginTop': '10px'
            })
        ]),
        
        # Modal con tabla completa
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Clasificación Completa")),
            dbc.ModalBody([
                create_standings_full_table(standings_data) if standings_data else html.Div()
            ]),
            dbc.ModalFooter(
                dbc.Button("Cerrar", id="close-standings-modal-btn", className="ms-auto", n_clicks=0)
            )
        ], id='standings-full-modal', is_open=False, size='xl')
    ])


def create_standings_full_table(standings_data):
    """Crea tabla clasificatoria completa con todas las columnas y filtro"""
    if not standings_data or 'full_standings' not in standings_data:
        return html.Div()
    
    full_df = standings_data['full_standings']
    
    if full_df.empty:
        return html.Div()
    
    return html.Div([
        # Filtro de últimos 5 partidos
        html.Div([
            dbc.RadioItems(
                id='standings-filter-radio',
                options=[
                    {'label': ' Clasificación General', 'value': 'general'},
                    {'label': ' Últimos 5 Partidos', 'value': 'last5'}
                ],
                value='general',
                inline=True,
                style={'fontSize': '13px'}
            )
        ], style={'marginBottom': '15px', 'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px'}),
        
        # Tabla completa
        html.Div(id='standings-full-table-content', children=[
            create_full_standings_rows(full_df)
        ])
    ])


def create_full_standings_rows(df, filter_type='general'):
    """Crea las filas de la tabla completa"""
    # Cabecera según el tipo de filtro
    if filter_type == 'last5':
        # Vista simplificada para últimos 5 partidos
        header = html.Div([
            html.Div("Pos", style={'width': '50px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Equipo", style={'flex': '1', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d', 'marginLeft': '34px'}),
            html.Div("Forma (Ú5)", style={'width': '150px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Pts Ú5", style={'width': '60px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'})
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'padding': '10px 12px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '6px',
            'marginBottom': '10px'
        })
    else:
        # Vista completa para clasificación general
        header = html.Div([
            html.Div("Pos", style={'width': '50px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Equipo", style={'flex': '1', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d', 'marginLeft': '34px'}),
            html.Div("PJ", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("PG", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("PE", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("PP", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("GF", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("GC", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("DG", style={'width': '50px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Forma", style={'width': '120px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
            html.Div("Pts", style={'width': '50px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'})
        ], style={
            'display': 'flex',
            'alignItems': 'center',
            'padding': '10px 12px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '6px',
            'marginBottom': '10px'
        })
    
    # Filas
    rows = []
    total_teams = len(df)
    for _, row in df.iterrows():
        is_depor = row['team_name'] == "RC Deportivo"
        position = int(row['position'])
        
        # Determinar color
        bg_color = 'transparent'
        border_left = 'none'
        
        if position <= 2:
            bg_color = '#c8e6c9' if not is_depor else '#a5d6a7'
            border_left = '4px solid #2e7d32'
        elif position <= 6:
            bg_color = '#e8f5e9' if not is_depor else '#c8e6c9'
            border_left = '4px solid #66bb6a'
        elif position > total_teams - 4:
            bg_color = '#ffcdd2' if not is_depor else '#ef9a9a'
            border_left = '4px solid #c62828'
        elif is_depor:
            bg_color = '#fff3e0'
            border_left = '4px solid #ffc107'
        
        # Forma (últimos 5 partidos)
        forma_str = row.get('last_5_matches', '')
        forma_icons = []
        for result in forma_str:
            color_forma = '#28a745' if result == 'V' else '#ffc107' if result == 'E' else '#dc3545'
            forma_icons.append(
                html.Span(result, style={
                    'display': 'inline-block',
                    'width': '20px',
                    'height': '20px',
                    'lineHeight': '20px',
                    'textAlign': 'center',
                    'fontWeight': '600',
                    'color': 'white',
                    'backgroundColor': color_forma,
                    'borderRadius': '4px',
                    'margin': '0 2px',
                    'fontSize': '11px'
                })
            )
        
        # Crear fila según el tipo de filtro
        if filter_type == 'last5':
            # Vista simplificada: solo Pos, Equipo, Forma y Pts Ú5
            rows.append(html.Div([
                # Posición
                html.Div(str(position), style={'width': '50px', 'textAlign': 'center', 'fontSize': '14px', 'fontWeight': '700', 'color': '#1e3d59'}),
                # Escudo y equipo
                html.Div([
                    html.Img(src=get_escudo_path(row['team_name']), style={'height': '24px', 'width': '24px', 'objectFit': 'contain', 'marginRight': '10px'}),
                    html.Span(row['team_name'], style={'fontSize': '14px', 'color': '#1e3d59'})
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center'}),
                # Forma
                html.Div(forma_icons, style={'width': '150px', 'display': 'flex', 'justifyContent': 'center'}),
                # Puntos Ú5
                html.Div(str(int(row['last_5_points'])), style={'width': '60px', 'textAlign': 'center', 'fontSize': '16px', 'fontWeight': '700', 'color': '#1e3d59'})
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '12px',
                'borderBottom': '1px solid #f0f0f0',
                'backgroundColor': bg_color,
                'fontWeight': '600' if is_depor else '400',
                'borderRadius': '6px',
                'borderLeft': border_left,
                'marginBottom': '2px'
            }))
        else:
            # Vista completa: todas las columnas
            rows.append(html.Div([
                # Posición
                html.Div(str(position), style={'width': '50px', 'textAlign': 'center', 'fontSize': '14px', 'fontWeight': '700', 'color': '#1e3d59'}),
                # Escudo y equipo
                html.Div([
                    html.Img(src=get_escudo_path(row['team_name']), style={'height': '24px', 'width': '24px', 'objectFit': 'contain', 'marginRight': '10px'}),
                    html.Span(row['team_name'], style={'fontSize': '14px', 'color': '#1e3d59'})
                ], style={'flex': '1', 'display': 'flex', 'alignItems': 'center'}),
                html.Div(str(int(row['matches_played'])), style={'width': '40px', 'textAlign': 'center', 'fontSize': '13px', 'color': '#6c757d'}),
                html.Div(str(int(row['matches_won'])), style={'width': '40px', 'textAlign': 'center', 'fontSize': '13px', 'color': '#28a745'}),
                html.Div(str(int(row['matches_drawn'])), style={'width': '40px', 'textAlign': 'center', 'fontSize': '13px', 'color': '#ffc107'}),
                html.Div(str(int(row['matches_lost'])), style={'width': '40px', 'textAlign': 'center', 'fontSize': '13px', 'color': '#dc3545'}),
                html.Div(str(int(row['goals_for'])), style={'width': '40px', 'textAlign': 'center', 'fontSize': '13px', 'color': '#6c757d'}),
                html.Div(str(int(row['goals_against'])), style={'width': '40px', 'textAlign': 'center', 'fontSize': '13px', 'color': '#6c757d'}),
                html.Div(f"+{int(row['goal_difference'])}" if row['goal_difference'] > 0 else str(int(row['goal_difference'])), 
                         style={'width': '50px', 'textAlign': 'center', 'fontSize': '13px', 'fontWeight': '600', 
                                'color': '#28a745' if row['goal_difference'] > 0 else '#dc3545' if row['goal_difference'] < 0 else '#6c757d'}),
                html.Div(forma_icons, style={'width': '120px', 'display': 'flex', 'justifyContent': 'center'}),
                html.Div(str(int(row['points'])), style={'width': '50px', 'textAlign': 'center', 'fontSize': '15px', 'fontWeight': '700', 'color': '#1e3d59'})
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '12px',
                'borderBottom': '1px solid #f0f0f0',
                'backgroundColor': bg_color,
                'fontWeight': '600' if is_depor else '400',
                'borderRadius': '6px',
                'borderLeft': border_left,
                'marginBottom': '2px'
            }))
    
    return html.Div([header] + rows)


def create_standings_table(standings_data):
    """Crea tabla clasificatoria compacta y expandible"""
    if not standings_data or 'context_standings' not in standings_data:
        return html.Div()
    
    context_df = standings_data['context_standings']
    full_df = standings_data['full_standings']
    team_position = standings_data.get('team_position')
    
    if context_df.empty:
        return html.Div()
    
    def create_row(row, is_depor=False):
        """Crea una fila de la tabla"""
        # Determinar color de cambio de posición
        change_icon = ""
        change_color = "#6c757d"
        if row['position_change'] > 0:
            change_icon = "↑"
            change_color = "#28a745"
        elif row['position_change'] < 0:
            change_icon = "↓"
            change_color = "#dc3545"
        else:
            change_icon = "="
        
        # Estilo de fila
        row_style = {
            'display': 'flex',
            'alignItems': 'center',
            'padding': '12px 15px',
            'borderBottom': '1px solid #e9ecef',
            'backgroundColor': '#e8f5e9' if is_depor else 'white',
            'fontWeight': '600' if is_depor else '400'
        }
        
        return html.Div([
            # Posición
            html.Div([
                html.Span(str(int(row['position'])), style={
                    'fontSize': '16px',
                    'fontWeight': '700',
                    'color': '#1e3d59'
                }),
                html.Span(change_icon, style={
                    'fontSize': '12px',
                    'color': change_color,
                    'marginLeft': '5px'
                })
            ], style={'width': '60px', 'textAlign': 'center'}),
            
            # Escudo y Equipo
            html.Div([
                html.Img(src=get_escudo_path(row['team_name']), style={
                    'height': '24px',
                    'width': '24px',
                    'objectFit': 'contain',
                    'marginRight': '10px'
                }),
                html.Span(row['team_name'], style={
                    'fontSize': '14px',
                    'color': '#1e3d59'
                })
            ], style={
                'flex': '1',
                'display': 'flex',
                'alignItems': 'center'
            }),
            
            # PJ
            html.Div(str(int(row['matches_played'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#6c757d'
            }),
            
            # PG
            html.Div(str(int(row['matches_won'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#28a745'
            }),
            
            # PE
            html.Div(str(int(row['matches_drawn'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#ffc107'
            }),
            
            # PP
            html.Div(str(int(row['matches_lost'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#dc3545'
            }),
            
            # GF
            html.Div(str(int(row['goals_for'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#6c757d'
            }),
            
            # GC
            html.Div(str(int(row['goals_against'])), style={
                'width': '40px',
                'textAlign': 'center',
                'fontSize': '13px',
                'color': '#6c757d'
            }),
            
            # DG
            html.Div(
                f"+{int(row['goal_difference'])}" if row['goal_difference'] > 0 else str(int(row['goal_difference'])),
                style={
                    'width': '50px',
                    'textAlign': 'center',
                    'fontSize': '13px',
                    'fontWeight': '600',
                    'color': '#28a745' if row['goal_difference'] > 0 else '#dc3545' if row['goal_difference'] < 0 else '#6c757d'
                }
            ),
            
            # Puntos
            html.Div(str(int(row['points'])), style={
                'width': '50px',
                'textAlign': 'center',
                'fontSize': '16px',
                'fontWeight': '700',
                'color': '#1e3d59'
            })
        ], style=row_style)
    
    # Crear filas de la tabla resumida
    rows_compact = []
    for _, row in context_df.iterrows():
        is_depor = row['team_name'] == "RC Deportivo"
        rows_compact.append(create_row(row, is_depor))
    
    # Crear filas de la tabla completa
    rows_full = []
    for _, row in full_df.iterrows():
        is_depor = row['team_name'] == "RC Deportivo"
        rows_full.append(create_row(row, is_depor))
    
    return html.Div([
        # Tabla resumida (visible por defecto)
        html.Div([
            # Encabezado
            html.Div([
                html.I(className="fas fa-trophy me-2", style={'color': '#ffc107', 'fontSize': '20px'}),
                html.H5("Clasificación", style={
                    'color': '#1e3d59',
                    'display': 'inline',
                    'fontWeight': '600',
                    'margin': '0'
                })
            ], style={'marginBottom': '15px'}),
            
            # Cabecera de tabla
            html.Div([
                html.Div("Pos", style={'width': '60px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("Equipo", style={'flex': '1', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("PJ", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("PG", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("PE", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("PP", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("GF", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("GC", style={'width': '40px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("DG", style={'width': '50px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'}),
                html.Div("Pts", style={'width': '50px', 'textAlign': 'center', 'fontSize': '12px', 'fontWeight': '600', 'color': '#6c757d'})
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '10px 15px',
                'backgroundColor': '#f8f9fa',
                'borderBottom': '2px solid #dee2e6'
            }),
            
            # Filas
            html.Div(rows_compact, id='standings-compact-rows'),
            
            # Botón expandir
            html.Div([
                html.Button([
                    html.I(className="fas fa-chevron-down me-2", id='standings-expand-icon'),
                    html.Span("Ver clasificación completa", id='standings-expand-text')
                ], id='standings-expand-btn', n_clicks=0, style={
                    'backgroundColor': 'transparent',
                    'border': '1px solid #1e3d59',
                    'color': '#1e3d59',
                    'padding': '8px 20px',
                    'borderRadius': '6px',
                    'fontSize': '13px',
                    'fontWeight': '500',
                    'cursor': 'pointer',
                    'transition': 'all 0.2s ease'
                })
            ], style={'textAlign': 'center', 'padding': '15px'})
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'marginBottom': '30px',
            'overflow': 'hidden'
        }),
        
        # Tabla completa (oculta por defecto)
        html.Div([
            html.Div(rows_full)
        ], id='standings-full-table', style={'display': 'none'})
    ], id='standings-container')


# Callback para abrir/cerrar modal de clasificación
@callback(
    Output('standings-full-modal', 'is_open'),
    [Input('standings-modal-open-btn', 'n_clicks'),
     Input('close-standings-modal-btn', 'n_clicks')],
    [State('standings-full-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_standings_modal(open_clicks, close_clicks, is_open):
    """Abre/cierra el modal de clasificación completa"""
    from dash import ctx
    
    if not ctx.triggered:
        return False
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'standings-modal-open-btn':
        return True
    elif button_id == 'close-standings-modal-btn':
        return False
    
    return is_open


# Callback para filtrar tabla por últimos 5 partidos
@callback(
    Output('standings-full-table-content', 'children'),
    [Input('standings-filter-radio', 'value')],
    [State('standings-full-modal', 'is_open')],
    prevent_initial_call=True
)
def filter_standings_table(filter_value, is_open):
    """Filtra la tabla según clasificación general o últimos 5 partidos"""
    from utils.db_manager import get_league_standings
    
    if not is_open:
        return dash.no_update
    
    standings_data = get_league_standings(team_name="RC Deportivo")
    
    if not standings_data or 'full_standings' not in standings_data:
        return html.Div("No hay datos disponibles")
    
    df = standings_data['full_standings'].copy()
    
    if filter_value == 'last5':
        # Ordenar por puntos de últimos 5 partidos
        df = df.sort_values('last_5_points', ascending=False).reset_index(drop=True)
        df['position'] = range(1, len(df) + 1)
    
    return create_full_standings_rows(df, filter_value)


# Callback para abrir modal de informes al hacer clic en un partido
@callback(
    [Output('match-reports-modal', 'is_open'),
     Output('match-reports-content', 'children')],
    [Input({'type': 'match-card-timeline', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('close-match-reports-modal', 'n_clicks')],
    [State('match-reports-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_match_reports_modal(match_clicks, close_click, is_open):
    """Abre/cierra modal de informes del partido"""
    from dash import ctx
    from utils.db_manager import get_match_reports_links
    
    if not ctx.triggered:
        return False, ""
    
    triggered_id = ctx.triggered[0]['prop_id']
    
    # Si se hizo clic en cerrar
    if 'close-match-reports-modal' in triggered_id:
        return False, ""
    
    # Si se hizo clic en una tarjeta de partido
    if 'match-card-timeline' in triggered_id:
        # Verificar que hubo un clic real
        if not any(match_clicks):
            return dash.no_update, dash.no_update
        
        # Extraer el match_id del trigger
        import json
        trigger_str = ctx.triggered[0]['prop_id'].split('.')[0]
        match_data = json.loads(trigger_str)
        match_id = match_data['index']
        
        # Obtener los links de informes
        links = get_match_reports_links(match_id)
        
        # Crear contenido del modal
        content = html.Div([
            html.P("Selecciona el tipo de informe que deseas ver:", style={'marginBottom': '20px', 'color': '#6c757d'}),
            
            # Botón Informe Postpartido
            html.Div([
                html.A([
                    html.Button([
                        html.I(className="fas fa-file-alt me-2"),
                        "Ver Informe Postpartido"
                    ], style={
                        'width': '100%',
                        'padding': '15px',
                        'backgroundColor': '#1e3d59',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '8px',
                        'fontSize': '16px',
                        'fontWeight': '600',
                        'cursor': 'pointer' if links.get('postpartido_link') else 'not-allowed',
                        'opacity': '1' if links.get('postpartido_link') else '0.5'
                    }, disabled=not links.get('postpartido_link'))
                ], href=links.get('postpartido_link', '#'), target="_blank" if links.get('postpartido_link') else "_self")
            ], style={'marginBottom': '15px'}),
            
            # Botón Informe Evolutivo
            html.Div([
                html.A([
                    html.Button([
                        html.I(className="fas fa-chart-line me-2"),
                        "Ver Informe Evolutivo"
                    ], style={
                        'width': '100%',
                        'padding': '15px',
                        'backgroundColor': '#28a745',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '8px',
                        'fontSize': '16px',
                        'fontWeight': '600',
                        'cursor': 'pointer' if links.get('evolutivo_link') else 'not-allowed',
                        'opacity': '1' if links.get('evolutivo_link') else '0.5'
                    }, disabled=not links.get('evolutivo_link'))
                ], href=links.get('evolutivo_link', '#'), target="_blank" if links.get('evolutivo_link') else "_self")
            ]),
            
            # Mensaje si no hay informes
            html.Div([
                html.I(className="fas fa-info-circle me-2", style={'color': '#ffc107'}),
                html.Span("No hay informes disponibles para este partido", style={'color': '#6c757d', 'fontSize': '14px'})
            ], style={'marginTop': '20px', 'textAlign': 'center'}) if not links.get('postpartido_link') and not links.get('evolutivo_link') else html.Div()
        ])
        
        return True, content
    
    return False, ""


def get_tendencia_resultados_content():
    """Contenido principal de la página de Tendencia de Resultados"""
    return html.Div([
        # Contenedor principal
        html.Div(id='tendencia-content-container'),
        
        # Trigger oculto para carga inicial
        html.Div(id='tendencia-trigger', style={'display': 'none'}),
        
        # Modal para informes de partido
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Informes del Partido")),
            dbc.ModalBody([
                html.Div(id='match-reports-content')
            ]),
            dbc.ModalFooter(
                dbc.Button("Cerrar", id="close-match-reports-modal", className="ms-auto", n_clicks=0)
            )
        ], id='match-reports-modal', is_open=False, size='md'),
        
        # Store para datos del partido seleccionado
        dcc.Store(id='selected-match-data')
        
    ], className="p-4")


# Callback para cargar datos y construir visualizaciones (solo carga inicial)
@callback(
    Output('tendencia-content-container', 'children'),
    [Input('tendencia-trigger', 'children')],
    prevent_initial_call=False
)
def update_tendencia_content(trigger):
    """Construye todo el contenido de tendencia de resultados"""
    from utils.db_manager import get_results_trend_statistics, get_league_standings
    
    try:
        # Obtener estadísticas y clasificación
        stats = get_results_trend_statistics(team_name="RC Deportivo")
        standings_data = get_league_standings(team_name="RC Deportivo")
        
        if not stats or stats.get('total_partidos', 0) == 0:
            return html.Div([
                html.I(className="fas fa-info-circle fa-3x mb-3", style={"color": "#17a2b8"}),
                html.H5("No hay datos disponibles", style={"color": "#6c757d"}),
                html.P("No se encontraron partidos en la base de datos.", className="text-muted")
            ], style={"textAlign": "center", "padding": "60px 20px"})
        
        # Construir contenido
        return html.Div([
            # Título principal
            html.Div([
                html.I(className="fas fa-chart-line me-2", style={"fontSize": "28px", "color": "#1e3d59"}),
                html.H3("Tendencia de Resultados", style={
                    "color": "#1e3d59", 
                    "display": "inline",
                    "fontWeight": "700"
                })
            ], className="mb-4"),
            
            # Header con escudo, KPIs y clasificación
            html.Div([
                # Columna izquierda: Escudo y nombre
                html.Div([
                    html.Div([
                        html.Img(src='/assets/Escudos/RC Deportivo.png', style={
                            'height': '100px',
                            'width': '100px',
                            'objectFit': 'contain',
                            'marginBottom': '15px'
                        }),
                        html.Div('RC Deportivo', style={
                            'fontSize': '16px',
                            'fontWeight': '600',
                            'color': '#1e3d59',
                            'textAlign': 'center'
                        })
                    ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justifyContent': 'center'}),
                    
                    # Posición en la parte inferior
                    html.Div([
                        html.Div(f"{standings_data.get('team_position', '-')}º", style={
                            'fontSize': '48px',
                            'fontWeight': '700',
                            'color': '#1e3d59',
                            'lineHeight': '1'
                        }) if standings_data.get('team_position') else html.Div('-', style={'fontSize': '48px', 'color': '#6c757d'}),
                        html.Div('Posición', style={
                            'fontSize': '13px',
                            'color': '#6c757d',
                            'fontWeight': '500',
                            'marginTop': '8px',
                            'letterSpacing': '0.5px'
                        })
                    ], style={
                        'textAlign': 'center',
                        'padding': '15px 20px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '10px',
                        'width': '100%'
                    })
                ], style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'marginRight': '50px',
                    'paddingRight': '50px',
                    'borderRight': '2px solid #e9ecef',
                    'minWidth': '180px'
                }),
                
                # KPIs en grid
                html.Div([
                    # Fila 1: Partidos y Puntos
                    html.Div([
                        # Partidos Jugados
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-calendar-check", style={
                                    'fontSize': '24px',
                                    'color': '#1e3d59',
                                    'marginBottom': '8px'
                                }),
                                html.Div(str(stats['total_partidos']), style={
                                    'fontSize': '42px',
                                    'fontWeight': '700',
                                    'color': '#1e3d59',
                                    'lineHeight': '1'
                                }),
                                html.Div('Partidos Jugados', style={
                                    'fontSize': '13px',
                                    'color': '#6c757d',
                                    'fontWeight': '500',
                                    'marginTop': '5px'
                                })
                            ], style={'textAlign': 'center'})
                        ], style={
                            'flex': '1',
                            'padding': '20px',
                            'backgroundColor': '#f8f9fa',
                            'borderRadius': '10px',
                            'marginRight': '15px'
                        }),
                        
                        # Puntos
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-star", style={
                                    'fontSize': '24px',
                                    'color': '#1e3d59',
                                    'marginBottom': '8px'
                                }),
                                html.Div(str(stats['puntos_totales']), style={
                                    'fontSize': '42px',
                                    'fontWeight': '700',
                                    'color': '#1e3d59',
                                    'lineHeight': '1'
                                }),
                                html.Div('Puntos', style={
                                    'fontSize': '13px',
                                    'color': '#6c757d',
                                    'fontWeight': '500',
                                    'marginTop': '5px'
                                })
                            ], style={'textAlign': 'center'})
                        ], style={
                            'flex': '1',
                            'padding': '20px',
                            'backgroundColor': '#f8f9fa',
                            'borderRadius': '10px'
                        })
                    ], style={'display': 'flex', 'marginBottom': '15px'}),
                    
                    # Fila 2: Goles y Racha
                    html.Div([
                        # Diferencia de Goles
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-futbol", style={
                                    'fontSize': '24px',
                                    'color': '#28a745' if stats['diferencia_goles'] >= 0 else '#dc3545',
                                    'marginBottom': '8px'
                                }),
                                html.Div(
                                    f"+{stats['diferencia_goles']}" if stats['diferencia_goles'] >= 0 else str(stats['diferencia_goles']),
                                    style={
                                        'fontSize': '42px',
                                        'fontWeight': '700',
                                        'color': '#28a745' if stats['diferencia_goles'] >= 0 else '#dc3545',
                                        'lineHeight': '1'
                                    }
                                ),
                                html.Div('Diferencia Goles', style={
                                    'fontSize': '13px',
                                    'color': '#6c757d',
                                    'fontWeight': '500',
                                    'marginTop': '5px'
                                })
                            ], style={'textAlign': 'center'})
                        ], style={
                            'flex': '1',
                            'padding': '20px',
                            'backgroundColor': '#e8f5e9' if stats['diferencia_goles'] >= 0 else '#ffebee',
                            'borderRadius': '10px',
                            'marginRight': '15px'
                        }),
                        
                        # Racha
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-fire", style={
                                    'fontSize': '24px',
                                    'color': '#28a745' if stats['racha_actual'][-1] == 'V' else '#ffc107' if stats['racha_actual'][-1] == 'E' else '#dc3545',
                                    'marginBottom': '8px'
                                }),
                                html.Div('Últimos 5 Partidos', style={
                                    'fontSize': '13px',
                                    'color': '#6c757d',
                                    'fontWeight': '500',
                                    'marginBottom': '10px'
                                }),
                                html.Div([
                                    html.Span(r, style={
                                        'display': 'inline-block',
                                        'width': '36px',
                                        'height': '36px',
                                        'lineHeight': '36px',
                                        'textAlign': 'center',
                                        'fontWeight': '700',
                                        'color': 'white',
                                        'backgroundColor': '#28a745' if r == 'V' else '#ffc107' if r == 'E' else '#dc3545',
                                        'borderRadius': '8px',
                                        'margin': '0 3px',
                                        'fontSize': '16px'
                                    }) for r in stats['racha_actual']
                                ])
                            ], style={'textAlign': 'center'})
                        ], style={
                            'flex': '1',
                            'padding': '20px',
                            'backgroundColor': '#e8f5e9' if stats['racha_actual'][-1] == 'V' else '#fff8e1' if stats['racha_actual'][-1] == 'E' else '#ffebee',
                            'borderRadius': '10px'
                        })
                    ], style={'display': 'flex', 'marginBottom': '15px'}),
                    
                    # Fila 3: Último partido
                    html.Div([
                        create_last_match_card(stats['ultimos_partidos'][-1]) if stats.get('ultimos_partidos') else html.Div()
                    ], style={'marginTop': '10px'})
                ], style={'flex': '1'}),
                
                # Separador vertical
                html.Div(style={
                    'width': '2px',
                    'backgroundColor': '#e9ecef',
                    'margin': '0 30px',
                    'alignSelf': 'stretch'
                }),
                
                # Tabla clasificatoria compacta
                html.Div([
                    create_standings_compact(standings_data) if standings_data else html.Div()
                ], style={'flex': '1.2'})
            ], style={
                'display': 'flex',
                'alignItems': 'stretch',
                'padding': '30px',
                'backgroundColor': 'white',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'marginBottom': '30px'
            }),
            
            # Fila 1: Últimos partidos
            dbc.Row([
                dbc.Col([
                    html.Div([
                        # Título de la sección
                        html.Div([
                            html.I(className="fas fa-history me-2", style={'color': '#1e3d59', 'fontSize': '20px'}),
                            html.H5("Últimos 10 Partidos", style={
                                'color': '#1e3d59',
                                'display': 'inline',
                                'fontWeight': '600',
                                'margin': '0'
                            })
                        ], style={'marginBottom': '20px'}),
                        
                        # Timeline de partidos
                        html.Div([
                            create_match_timeline_card(match) 
                            for match in stats['ultimos_partidos']
                        ], style={
                            'display': 'flex',
                            'overflowX': 'auto',
                            'gap': '15px',
                            'padding': '10px 0'
                        })
                    ], style={
                        'backgroundColor': 'white',
                        'borderRadius': '12px',
                        'padding': '25px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                    })
                ], width=12, className="mb-4")
            ]),
            
            # Fila 2: Gráficos de distribución
            dbc.Row([
                # Gráfico de torta: Resultados Totales
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([
                                html.I(className="fas fa-chart-pie me-2"),
                                "Distribución de Resultados"
                            ], style={'color': '#1e3d59', 'marginBottom': '20px'}),
                            
                            dcc.Graph(
                                figure=create_results_pie_chart(stats),
                                config={'displayModeBar': False},
                                style={'height': '300px'}
                            )
                        ])
                    ], className="shadow-sm h-100", style={'border': 'none', 'borderRadius': '12px'})
                ], width=12, md=4, className="mb-4"),
                
                # Gráfico de torta: Como Local
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([
                                html.I(className="fas fa-home me-2"),
                                "Como Local"
                            ], style={'color': '#1e3d59', 'marginBottom': '20px'}),
                            
                            dcc.Graph(
                                figure=create_condition_pie_chart(stats, 'Local'),
                                config={'displayModeBar': False},
                                style={'height': '300px'}
                            )
                        ])
                    ], className="shadow-sm h-100", style={'border': 'none', 'borderRadius': '12px'})
                ], width=12, md=4, className="mb-4"),
                
                # Gráfico de torta: Como Visitante
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([
                                html.I(className="fas fa-plane me-2"),
                                "Como Visitante"
                            ], style={'color': '#1e3d59', 'marginBottom': '20px'}),
                            
                            dcc.Graph(
                                figure=create_condition_pie_chart(stats, 'Visitante'),
                                config={'displayModeBar': False},
                                style={'height': '300px'}
                            )
                        ])
                    ], className="shadow-sm h-100", style={'border': 'none', 'borderRadius': '12px'})
                ], width=12, md=4, className="mb-4")
            ])
        ])
        
    except Exception as e:
        print(f"Error en update_tendencia_content: {e}")
        import traceback
        traceback.print_exc()
        
        return html.Div([
            html.I(className="fas fa-exclamation-triangle fa-3x mb-3", style={"color": "#dc3545"}),
            html.H5("Error al cargar datos", style={"color": "#6c757d"}),
            html.P(f"Error: {str(e)}", className="text-muted")
        ], style={"textAlign": "center", "padding": "60px 20px"})


def create_results_pie_chart(stats):
    """Crea gráfico de torta de resultados totales con número en el centro"""
    labels = ['Victorias', 'Empates', 'Derrotas']
    values = [stats['victorias'], stats['empates'], stats['derrotas']]
    colors = ['#28a745', '#ffc107', '#dc3545']
    
    total = stats['total_partidos']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.5,
        textinfo='label+percent',
        textfont=dict(size=13, color='white', family='Montserrat', weight='bold'),
        hovertemplate='<b>%{label}</b><br>%{value} partidos<br>%{percent}<extra></extra>'
    )])
    
    # Añadir número en el centro
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:12px'>Partidos</span>",
        x=0.5, y=0.5,
        font=dict(size=32, color='#1e3d59', family='Montserrat'),
        showarrow=False
    )
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat')
    )
    
    return fig


def create_condition_pie_chart(stats, condicion):
    """Crea gráfico de torta para una condición específica (Local o Visitante)"""
    condicion_stats = stats.get('por_condicion', {}).get(condicion, {})
    
    if not condicion_stats:
        # Si no hay datos, mostrar gráfico vacío
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos",
            x=0.5, y=0.5,
            font=dict(size=16, color='#6c757d'),
            showarrow=False
        )
        fig.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    labels = ['Victorias', 'Empates', 'Derrotas']
    values = [
        condicion_stats.get('victorias', 0),
        condicion_stats.get('empates', 0),
        condicion_stats.get('derrotas', 0)
    ]
    colors = ['#28a745', '#ffc107', '#dc3545']
    
    total = condicion_stats.get('total', 0)
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.5,
        textinfo='label+percent',
        textfont=dict(size=13, color='white', family='Montserrat', weight='bold'),
        hovertemplate='<b>%{label}</b><br>%{value} partidos<br>%{percent}<extra></extra>'
    )])
    
    # Añadir número en el centro
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='font-size:12px'>Partidos</span>",
        x=0.5, y=0.5,
        font=dict(size=32, color='#1e3d59', family='Montserrat'),
        showarrow=False
    )
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat')
    )
    
    return fig
