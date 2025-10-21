import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, callback_context
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
from functools import lru_cache
import re
from utils.db_manager import (
    get_activities_by_date_range,
    get_participants_for_activities,
    get_metrics_for_activities_and_athletes,
    get_available_parameters,
    get_variable_thresholds,
    add_grupo_dia_column,
    get_all_athletes,
    get_microciclos,
    get_db_connection
)
from utils.layouts import standard_page
from utils.carga_jugadores import calcular_estadisticas_md_jugadores

# Función para obtener el contenido de "Semana Equipo" (contenido actual)
def get_semana_equipo_content(microciclos=None):
    """Contenido de la pestaña Semana Equipo - Vista actual del microciclo"""
    # Usar microciclos pasados como parámetro o lista vacía
    if microciclos is None:
        microciclos = []
    microciclo_options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos]
    default_microciclo = microciclos[0]['id'] if microciclos else None
    
    return html.Div([
        # Card para filtros
    dbc.Card([
        dbc.CardBody([
            # Fila principal: Microciclo, Métrica y Botón
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Microciclo:", className="form-label", style={
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#1e3d59',
                            'marginBottom': '6px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id="sc-microciclo-dropdown",
                            options=microciclo_options,
                            value=default_microciclo,
                            clearable=False,
                            placeholder="Selecciona un microciclo..."
                        ),
                    ])
                ], width=12, lg=4, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Label("Métrica:", className="form-label", style={
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#1e3d59',
                            'marginBottom': '6px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id="sc-metric-dropdown",
                            options=get_available_parameters(),
                            value="total_distance",
                            clearable=False
                        ),
                    ])
                ], width=12, lg=6, className="mb-2"),
                dbc.Col([
                    dbc.Button("Cargar Datos", id="sc-cargar-btn", style={
                        'backgroundColor': '#1e3d59',
                        'border': 'none',
                        'borderRadius': '8px',
                        'padding': '10px 20px',
                        'fontWeight': '600',
                        'marginTop': '28px'
                    }, className="w-100"),
                ], width=12, lg=2, className="mb-2")
            ]),
            
            # Botón para mostrar selección personalizada
            html.Hr(style={'margin': '15px 0', 'borderColor': '#e0e0e0'}),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-calendar-alt me-2"), "Selección de rango Personalizado"],
                        id="sc-toggle-custom-date",
                        color="link",
                        style={
                            'color': '#6c757d',
                            'textDecoration': 'none',
                            'fontSize': '13px',
                            'padding': '5px 10px'
                        },
                        size="sm"
                    )
                ], width=12)
            ]),
            
            # Collapse para date pickers
            dbc.Collapse([
                html.Hr(style={'margin': '10px 0', 'borderColor': '#e0e0e0'}),
                dbc.Row([
                    dbc.Col([
                        html.Label("Fecha Inicio:", className="form-label", style={
                            'fontWeight': '500',
                            'fontSize': '12px',
                            'color': '#6c757d',
                            'marginBottom': '6px',
                            'display': 'block'
                        }),
                        dcc.DatePickerSingle(
                            id="sc-custom-start-date",
                            display_format="YYYY-MM-DD",
                            placeholder="Fecha inicio",
                            first_day_of_week=1
                        ),
                    ], width=12, lg=4, className="mb-2"),
                    dbc.Col([
                        html.Label("Fecha Fin:", className="form-label", style={
                            'fontWeight': '500',
                            'fontSize': '12px',
                            'color': '#6c757d',
                            'marginBottom': '6px',
                            'display': 'block'
                        }),
                        dcc.DatePickerSingle(
                            id="sc-custom-end-date",
                            display_format="YYYY-MM-DD",
                            placeholder="Fecha fin",
                            first_day_of_week=1
                        ),
                    ], width=12, lg=4, className="mb-2"),
                    dbc.Col([
                        dbc.Button("Aplicar Rango Personalizado", id="sc-apply-custom-date", style={
                            'backgroundColor': '#28a745',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '8px 16px',
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'marginTop': '24px'
                        }, size="sm"),
                    ], width=12, lg=4, className="mb-2")
                ])
            ], id="sc-custom-date-collapse", is_open=False),
            
            # Store para las fechas actuales (del microciclo o personalizadas)
            dcc.Store(id="sc-date-store", data={}),
            
            # Selector de jugadores (aparece dinámicamente)
            html.Div(id="sc-jugadores-container", style={'display': 'none'}, children=[
                html.Hr(style={'margin': '20px 0', 'borderColor': '#e0e0e0'}),
                dbc.Row([
                    dbc.Col([
                        html.Label("Selecciona jugadores (opcional):", className="form-label", style={
                            'fontWeight': '500',
                            'fontSize': '13px',
                            'color': '#6c757d',
                            'marginBottom': '8px'
                        }),
                        dcc.Dropdown(
                            id="sc-player-dropdown",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Todos los jugadores seleccionados por defecto...",
                            className="mb-2"
                        ),
                        dbc.Checklist(
                            id="sc-incluir-porteros",
                            options=[{'label': ' Incluir porteros', 'value': 'incluir'}],
                            value=[],
                            inline=True,
                            style={
                                'fontSize': '12px',
                                'color': '#6c757d',
                                'marginTop': '5px'
                            }
                        ),
                    ], width=12)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Aplicar Filtro", id="sc-filtrar-btn", style={
                            'backgroundColor': '#28a745',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '8px 20px',
                            'fontWeight': '600',
                            'fontSize': '14px'
                        }, size="sm"),
                    ], width=12, className="text-end")
                ], className="mt-2")
            ])
        ])
    ], className="mb-4", style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'border': 'none'
    }),
    
    # Card para gráfico
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5("Visualización de carga microciclo (MD-4 a MD)", style={
                        'color': '#1e3d59',
                        'fontWeight': '600',
                        'fontSize': '18px',
                        'marginBottom': '20px'
                    }),
                    dcc.Loading(
                        id="sc-loading-bar",
                        type="circle",
                        children=[
                            dcc.Graph(id="sc-bar-chart")
                        ]
                    )
                ], width=12)
            ])
        ])
    ], className="mb-4", style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'border': 'none'
    }),
    
    # Botón para mostrar/ocultar datos detallados
    dbc.Row([
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"],
                id="toggle-datos-btn",
                style={
                    'backgroundColor': 'transparent',
                    'border': '2px solid #1e3d59',
                    'color': '#1e3d59',
                    'borderRadius': '8px',
                    'padding': '10px 20px',
                    'fontWeight': '600'
                },
                className="mb-3 w-100"
            ),
        ], width=12)
    ]),
    
    # Card para tabla (ahora oculta por defecto)
    html.Div(
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Datos detallados de rendimiento", style={
                            'color': '#1e3d59',
                            'fontWeight': '600',
                            'fontSize': '18px',
                            'marginBottom': '20px'
                        }),
                        dcc.Loading(
                            id="sc-loading-table",
                            type="circle",
                            children=[
                                html.Div(id="sc-table-container")
                            ]
                        )
                    ], width=12)
                ])
            ])
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none',
            'padding': '20px'
        }),
        id="datos-detallados-container",
        style={"display": "none"} # Oculto por defecto
    )
    ])

# Función para obtener el contenido de "Semana Jugadores"
def get_semana_jugadores_content(microciclos=None):
    """Contenido de la pestaña Semana Jugadores - Acumulado por jugador con colores por día"""
    # Usar microciclos pasados como parámetro o lista vacía
    if microciclos is None:
        microciclos = []
    microciclo_options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos]
    default_microciclo = microciclos[0]['id'] if microciclos else None
    
    return html.Div([
        # Card para filtros
        dbc.Card([
            dbc.CardBody([
                # Fila principal: Microciclo, Métrica y Botón
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Label("Microciclo:", className="form-label", style={
                                'fontWeight': '600',
                                'fontSize': '13px',
                                'color': '#1e3d59',
                                'marginBottom': '6px',
                                'display': 'block'
                            }),
                            dcc.Dropdown(
                                id="sj-microciclo-dropdown",
                                options=microciclo_options,
                                value=default_microciclo,
                                clearable=False,
                                placeholder="Selecciona un microciclo..."
                            ),
                        ])
                    ], width=12, lg=4, className="mb-2"),
                    dbc.Col([
                        html.Div([
                            html.Label("Métrica:", className="form-label", style={
                                'fontWeight': '600',
                                'fontSize': '13px',
                                'color': '#1e3d59',
                                'marginBottom': '6px',
                                'display': 'block'
                            }),
                            dcc.Dropdown(
                                id="sj-metric-dropdown",
                                options=get_available_parameters(),
                                value="total_distance",
                                clearable=False
                            ),
                        ])
                    ], width=12, lg=6, className="mb-2"),
                    dbc.Col([
                        dbc.Button("Cargar Datos", id="sj-cargar-btn", style={
                            'backgroundColor': '#1e3d59',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '10px 20px',
                            'fontWeight': '600',
                            'marginTop': '28px'
                        }, className="w-100"),
                    ], width=12, lg=2, className="mb-2")
                ]),
                
                # Botón para mostrar selección personalizada
                html.Hr(style={'margin': '15px 0', 'borderColor': '#e0e0e0'}),
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-calendar-alt me-2"), "Selección de rango Personalizado"],
                            id="sj-toggle-custom-date",
                            color="link",
                            style={
                                'color': '#6c757d',
                                'textDecoration': 'none',
                                'fontSize': '13px',
                                'padding': '5px 10px'
                            },
                            size="sm"
                        )
                    ], width=12)
                ]),
                
                # Collapse para date pickers
                dbc.Collapse([
                    html.Hr(style={'margin': '10px 0', 'borderColor': '#e0e0e0'}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Fecha Inicio:", className="form-label", style={
                                'fontWeight': '500',
                                'fontSize': '12px',
                                'color': '#6c757d',
                                'marginBottom': '6px',
                                'display': 'block'
                            }),
                            dcc.DatePickerSingle(
                                id="sj-custom-start-date",
                                display_format="YYYY-MM-DD",
                                placeholder="Fecha inicio",
                                first_day_of_week=1
                            ),
                        ], width=12, lg=4, className="mb-2"),
                        dbc.Col([
                            html.Label("Fecha Fin:", className="form-label", style={
                                'fontWeight': '500',
                                'fontSize': '12px',
                                'color': '#6c757d',
                                'marginBottom': '6px',
                                'display': 'block'
                            }),
                            dcc.DatePickerSingle(
                                id="sj-custom-end-date",
                                display_format="YYYY-MM-DD",
                                placeholder="Fecha fin",
                                first_day_of_week=1
                            ),
                        ], width=12, lg=4, className="mb-2"),
                        dbc.Col([
                            dbc.Button("Aplicar Rango Personalizado", id="sj-apply-custom-date", style={
                                'backgroundColor': '#28a745',
                                'border': 'none',
                                'borderRadius': '8px',
                                'padding': '8px 16px',
                                'fontWeight': '600',
                                'fontSize': '13px',
                                'marginTop': '24px'
                            }, size="sm"),
                        ], width=12, lg=4, className="mb-2")
                    ])
                ], id="sj-custom-date-collapse", is_open=False),
                
                # Store para las fechas actuales (del microciclo o personalizadas)
                dcc.Store(id="sj-date-store", data={}),
                
                # Selector de jugadores (aparece dinámicamente)
                html.Div(id="sj-jugadores-container", style={'display': 'none'}, children=[
                    html.Hr(style={'margin': '20px 0', 'borderColor': '#e0e0e0'}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Selecciona jugadores (opcional):", className="form-label", style={
                                'fontWeight': '500',
                                'fontSize': '13px',
                                'color': '#6c757d',
                                'marginBottom': '8px'
                            }),
                            dcc.Dropdown(
                                id="sj-jugadores-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Todos los jugadores seleccionados por defecto...",
                                className="mb-2"
                            ),
                            dbc.Checklist(
                                id="sj-incluir-porteros",
                                options=[{'label': ' Incluir porteros', 'value': 'incluir'}],
                                value=[],
                                inline=True,
                                style={
                                    'fontSize': '12px',
                                    'color': '#6c757d',
                                    'marginTop': '5px'
                                }
                            ),
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Aplicar Filtro", id="sj-filtrar-btn", style={
                                'backgroundColor': '#28a745',
                                'border': 'none',
                                'borderRadius': '8px',
                                'padding': '8px 20px',
                                'fontWeight': '600',
                                'fontSize': '14px'
                            }, size="sm"),
                        ], width=12, className="text-end")
                    ], className="mt-2")
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # Card para gráfico
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Acumulado semanal por jugador", style={
                            'color': '#1e3d59',
                            'fontWeight': '600',
                            'fontSize': '18px',
                            'marginBottom': '20px'
                        }),
                        dcc.Loading(
                            id="sj-loading-chart",
                            type="circle",
                            children=[
                                dcc.Graph(id="sj-stacked-chart")
                            ]
                        )
                    ], width=12)
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        })
    ])

# Función para obtener el contenido de "Carga Jugadores"
def get_carga_jugadores_content(microciclos=None):
    """Contenido de la pestaña Carga Jugadores - Análisis de cargas máximas en MD"""
    
    # Asegurar que microciclos sea una lista
    if not microciclos:
        microciclos = []
    
    return html.Div([
        # Card de controles para análisis de máximos
        dbc.Card([
            dbc.CardBody([
                html.H6("Análisis de Cargas Máximas en Partidos (MD)", 
                        className="mb-3",
                        style={'color': '#1e3d59', 'fontWeight': '600'}),
                html.Div([
                    html.P([
                        "Estadísticas calculadas desde agosto 2025 sobre partidos donde el jugador jugó ",
                        html.Strong("+70 minutos"),
                        ". Valores estandarizados a 94 minutos."
                    ], className="mb-2",
                       style={'fontSize': '13px', 'color': '#6c757d'}),
                    html.P([
                        html.I(className="fas fa-info-circle me-2", style={'color': '#17a2b8'}),
                        html.Small("Nota: La velocidad máxima no se estandariza (es un valor puntual).", 
                                  style={'color': '#6c757d', 'fontSize': '11px'})
                    ], className="mb-3")
                ]),
                
                dbc.Button("Cargar Análisis", 
                          id="cj-cargar-btn", 
                          style={
                              'backgroundColor': '#1e3d59',
                              'border': 'none',
                              'borderRadius': '8px',
                              'padding': '10px 24px',
                              'fontWeight': '600',
                              'fontSize': '14px'
                          })
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # Card para tabla de resultados de máximos
        dbc.Card([
            dbc.CardBody([
                html.Div(id="cj-tabla-container", children=[
                    html.Div("Haz clic en 'Cargar Análisis' para ver las estadísticas", 
                            className="text-center text-muted p-4")
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # Card para visualización de barras de carga semanal
        dbc.Card([
            dbc.CardBody([
                html.H6("Carga Semanal vs Máximos de Competición", 
                        className="mb-3",
                        style={'color': '#1e3d59', 'fontWeight': '600'}),
                
                html.Div([
                    # Row para selectores
                    dbc.Row([
                        dbc.Col([
                            html.Label("Microciclo:", style={'fontWeight': '600', 'fontSize': '13px', 'color': '#1e3d59'}),
                            dcc.Dropdown(
                                id="cj-microciclo-dropdown",
                                options=[
                                    {'label': m['label'] if isinstance(m, dict) else m, 
                                     'value': m['label'] if isinstance(m, dict) else m} 
                                    for m in microciclos
                                ],
                                placeholder="Seleccionar microciclo",
                                style={'fontSize': '13px'}
                            )
                        ], md=5),
                        dbc.Col([
                            html.Label("Métrica:", style={'fontWeight': '600', 'fontSize': '13px', 'color': '#1e3d59'}),
                            dcc.Dropdown(
                                id="cj-metrica-dropdown",
                                options=[
                                    {'label': 'Distancia Total (m)', 'value': 'total_distance'},
                                    {'label': 'Distancia +21km/h (m)', 'value': 'distancia_+21_km/h_(m)'},
                                    {'label': 'Distancia +24km/h (m)', 'value': 'distancia_+24_km/h_(m)'},
                                    {'label': 'Distancia +28km/h (m)', 'value': 'distancia+28_(km/h)'},
                                    {'label': 'Aceleraciones', 'value': 'gen2_acceleration_band7plus_total_effort_count'},
                                    {'label': 'Player Load', 'value': 'average_player_load'},
                                    {'label': 'Velocidad Máxima (km/h)', 'value': 'max_vel'}
                                ],
                                placeholder="Seleccionar métrica",
                                style={'fontSize': '13px'}
                            )
                        ], md=5),
                        dbc.Col([
                            html.Label("\u00A0", style={'fontWeight': '600', 'fontSize': '13px'}),  # Espacio para alinear
                            dbc.Button("Generar Barras", 
                                      id="cj-generar-barras-btn",
                                      style={
                                          'backgroundColor': '#1e3d59',
                                          'border': 'none',
                                          'borderRadius': '8px',
                                          'padding': '10px 20px',
                                          'fontWeight': '600',
                                          'fontSize': '13px',
                                          'width': '100%'
                                      })
                        ], md=2)
                    ], className="mb-3"),
                    
                    # Contenedor para las barras de carga
                    html.Div(id="cj-barras-container", children=[
                        html.Div("Selecciona un microciclo y una métrica, luego haz clic en 'Generar Barras'", 
                                className="text-center text-muted p-4")
                    ])
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # Store para guardar los máximos calculados
        dcc.Store(id='cj-maximos-store', data={})
    ])

# Layout principal con pestañas
layout = standard_page([
    # Store global para cachear microciclos (se carga una sola vez)
    dcc.Store(id="microciclos-store", data=[]),
    
    # Título principal
    html.Div([
        html.H2("CONTROL PROCESO ENTRENAMIENTO - Sesiones y Microciclos", 
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
                    "Semana Equipo",
                    id="tab-cpe-equipo",
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
                        "width": "33.33%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Semana Jugadores",
                    id="tab-cpe-jugadores",
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
                        "width": "33.33%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Carga Jugadores",
                    id="tab-cpe-carga",
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
                        "width": "33.33%",
                        "textAlign": "center"
                    }
                )
            ], style={
                "display": "flex",
                "borderBottom": "1px solid #e9ecef",
                "marginBottom": "20px"
            })
        ]),
        
        # Contenedor del contenido de las pestañas
        html.Div(id="cpe-tab-content", children=[get_semana_equipo_content([])])
    ], style={
        "backgroundColor": "white",
        "borderRadius": "12px",
        "padding": "20px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"
    })
])

# ============================================
# CALLBACKS PARA MANEJO DE MICROCICLOS Y FECHAS
# ============================================

# Callback para cargar microciclos una sola vez al inicio
@callback(
    Output("microciclos-store", "data"),
    Input("microciclos-store", "data"),
    prevent_initial_call=False
)
def load_microciclos_once(current_data):
    """Carga los microciclos solo la primera vez (cuando data está vacío)"""
    if not current_data:
        microciclos = get_microciclos()
        return microciclos
    return current_data

# Callbacks para actualizar opciones de dropdowns cuando se cargan microciclos
@callback(
    Output("sc-microciclo-dropdown", "options"),
    Output("sc-microciclo-dropdown", "value"),
    Input("microciclos-store", "data"),
    prevent_initial_call=False
)
def update_sc_microciclo_options(microciclos):
    """Actualiza las opciones del dropdown de microciclos para Semana Equipo"""
    if not microciclos:
        return [], None
    options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos]
    default_value = microciclos[0]['id'] if microciclos else None
    return options, default_value

@callback(
    Output("sj-microciclo-dropdown", "options"),
    Output("sj-microciclo-dropdown", "value"),
    Input("microciclos-store", "data"),
    prevent_initial_call=False
)
def update_sj_microciclo_options(microciclos):
    """Actualiza las opciones del dropdown de microciclos para Semana Jugadores"""
    if not microciclos:
        return [], None
    options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos]
    default_value = microciclos[0]['id'] if microciclos else None
    return options, default_value

# Callback para toggle collapse de fechas personalizadas - Semana Equipo
@callback(
    Output("sc-custom-date-collapse", "is_open"),
    Input("sc-toggle-custom-date", "n_clicks"),
    State("sc-custom-date-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_sc_custom_date(n_clicks, is_open):
    return not is_open

# Callback para toggle collapse de fechas personalizadas - Semana Jugadores
@callback(
    Output("sj-custom-date-collapse", "is_open"),
    Input("sj-toggle-custom-date", "n_clicks"),
    State("sj-custom-date-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_sj_custom_date(n_clicks, is_open):
    return not is_open

# Callback para actualizar store de fechas desde microciclo - Semana Equipo
@callback(
    Output("sc-date-store", "data"),
    Input("sc-microciclo-dropdown", "value"),
    Input("sc-apply-custom-date", "n_clicks"),
    State("sc-custom-start-date", "date"),
    State("sc-custom-end-date", "date"),
    State("microciclos-store", "data"),
    prevent_initial_call=False
)
def update_sc_date_store(microciclo_id, apply_clicks, custom_start, custom_end, microciclos):
    """Actualiza el store de fechas desde microciclo o fechas personalizadas"""
    ctx = dash.callback_context
    
    # Si se aplicó rango personalizado
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'sc-apply-custom-date.n_clicks':
        if custom_start and custom_end:
            return {'start_date': custom_start, 'end_date': custom_end, 'source': 'custom'}
    
    # Si se seleccionó un microciclo
    if microciclo_id and microciclos:
        microciclo = next((mc for mc in microciclos if mc['id'] == microciclo_id), None)
        if microciclo:
            return {
                'start_date': microciclo['start_date'],
                'end_date': microciclo['end_date'],
                'source': 'microciclo'
            }
    
    return {}

# Callback para actualizar store de fechas desde microciclo - Semana Jugadores
@callback(
    Output("sj-date-store", "data"),
    Input("sj-microciclo-dropdown", "value"),
    Input("sj-apply-custom-date", "n_clicks"),
    State("sj-custom-start-date", "date"),
    State("sj-custom-end-date", "date"),
    State("microciclos-store", "data"),
    prevent_initial_call=False
)
def update_sj_date_store(microciclo_id, apply_clicks, custom_start, custom_end, microciclos):
    """Actualiza el store de fechas desde microciclo o fechas personalizadas"""
    ctx = dash.callback_context
    
    # Si se aplicó rango personalizado
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'sj-apply-custom-date.n_clicks':
        if custom_start and custom_end:
            return {'start_date': custom_start, 'end_date': custom_end, 'source': 'custom'}
    
    # Si se seleccionó un microciclo
    if microciclo_id and microciclos:
        microciclo = next((mc for mc in microciclos if mc['id'] == microciclo_id), None)
        if microciclo:
            return {
                'start_date': microciclo['start_date'],
                'end_date': microciclo['end_date'],
                'source': 'microciclo'
            }
    
    return {}

# ============================================
# CALLBACKS PARA SEMANA EQUIPO
# ============================================

# Callback para mostrar/ocultar datos detallados
@callback(
    Output("datos-detallados-container", "style"),
    Output("toggle-datos-btn", "children"),
    Input("toggle-datos-btn", "n_clicks"),
    State("datos-detallados-container", "style"),
    prevent_initial_call=True
)
def toggle_datos_detallados(n_clicks, current_style):
    if current_style.get("display") == "none":
        # Mostrar tabla
        return {"display": "block"}, [html.I(className="fas fa-table me-2"), "Ocultar datos de rendimiento detallado"]
    else:
        # Ocultar tabla
        return {"display": "none"}, [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"]

# Callback para cargar datos iniciales de Semana Equipo
@callback(
    Output("sc-jugadores-container", "style"),
    Output("sc-player-dropdown", "options"),
    Output("sc-player-dropdown", "value"),
    Output("sc-bar-chart", "figure"),
    Output("sc-table-container", "children"),
    Input("sc-cargar-btn", "n_clicks"),
    State("sc-date-store", "data"),
    State("sc-metric-dropdown", "value"),
    prevent_initial_call=True
)
def cargar_datos_semana_equipo(n_clicks, date_data, metric):
    """Carga datos iniciales y muestra selector de jugadores con los participantes del periodo (OPTIMIZADO)"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return {'display': 'none'}, [], [], {}, html.Div("Selecciona un microciclo o rango personalizado.")
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    if not start_date or not end_date:
        return {'display': 'none'}, [], [], {}, html.Div()
    
    # Convertir fechas a timestamps (manejar ambos formatos: solo fecha o fecha con hora)
    try:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    except:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    try:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    # Obtener actividades
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return {'display': 'none'}, [], [], {}, html.Div("No hay datos para el periodo seleccionado.")
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()
    
    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return {'display': 'none'}, [], [], {}, html.Div("No hay participantes en este periodo.")
    
    # Obtener jugadores únicos que participaron (usando cache)
    atleta_ids = participantes["athlete_id"].unique().tolist()
    atletas_df = get_cached_athletes()
    atletas_periodo = atletas_df[atletas_df["id"].isin(atleta_ids)]
    
    # Crear opciones del dropdown (todos los jugadores)
    jugadores_options = [{'label': row['full_name'], 'value': row['id']} for _, row in atletas_periodo.iterrows()]
    
    # Por defecto: EXCLUIR porteros
    atletas_sin_porteros = atletas_periodo[atletas_periodo['position_name'] != 'Goal Keeper']
    jugadores_ids = atletas_sin_porteros['id'].tolist()
    
    # Generar gráfico y tabla inicial sin porteros
    resultado = generar_tabla_y_grafico_equipo(start_date, end_date, metric, jugadores_ids)
    
    # Verificar si es una tupla (tabla, fig) o un error
    if isinstance(resultado, tuple) and len(resultado) == 2:
        tabla, fig = resultado
    else:
        # Error en la generación
        tabla = html.Div("Error al generar los datos.", className="text-center text-muted p-4")
        fig = {}
    
    # Mostrar selector de jugadores
    return {'display': 'block'}, jugadores_options, jugadores_ids, fig, tabla

# Callback para actualizar jugadores cuando se marca/desmarca "incluir porteros" en Semana Equipo
@callback(
    Output("sc-player-dropdown", "value", allow_duplicate=True),
    Output("sc-bar-chart", "figure", allow_duplicate=True),
    Output("sc-table-container", "children", allow_duplicate=True),
    Input("sc-incluir-porteros", "value"),
    State("sc-date-store", "data"),
    State("sc-metric-dropdown", "value"),
    State("sc-player-dropdown", "options"),
    prevent_initial_call=True
)
def toggle_porteros_equipo(incluir_porteros, date_data, metric, jugadores_options):
    """Incluye o excluye porteros según el checkbox en Semana Equipo"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return [], {}, html.Div()
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    # Obtener todos los atletas
    atletas_df = get_cached_athletes()
    
    # Si se debe incluir porteros
    if 'incluir' in incluir_porteros:
        # Seleccionar todos los jugadores disponibles
        jugadores_ids = [opt['value'] for opt in jugadores_options]
    else:
        # Excluir porteros
        ids_disponibles = [opt['value'] for opt in jugadores_options]
        atletas_disponibles = atletas_df[atletas_df['id'].isin(ids_disponibles)]
        atletas_sin_porteros = atletas_disponibles[atletas_disponibles['position_name'] != 'Goal Keeper']
        jugadores_ids = atletas_sin_porteros['id'].tolist()
    
    # Generar tabla y gráfico con la nueva selección
    resultado = generar_tabla_y_grafico_equipo(start_date, end_date, metric, jugadores_ids)
    
    if isinstance(resultado, tuple) and len(resultado) == 2:
        tabla, fig = resultado
    else:
        tabla = html.Div("Error al generar los datos.", className="text-center text-muted p-4")
        fig = {}
    
    return jugadores_ids, fig, tabla

# Callback para aplicar filtro de jugadores en Semana Equipo
@callback(
    Output("sc-table-container", "children", allow_duplicate=True),
    Output("sc-bar-chart", "figure", allow_duplicate=True),
    Input("sc-filtrar-btn", "n_clicks"),
    State("sc-date-store", "data"),
    State("sc-metric-dropdown", "value"),
    State("sc-player-dropdown", "value"),
    prevent_initial_call=True
)
def update_sc_table_and_chart(n_clicks, date_data, metric, selected_players):
    """Aplica filtro de jugadores seleccionados"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return html.Div("Selecciona un microciclo o rango personalizado.", className="text-center text-muted p-4"), {}
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    if not start_date or not end_date or not selected_players:
        return html.Div("Selecciona jugadores para filtrar.", className="text-center text-muted p-4"), {}
    
    resultado = generar_tabla_y_grafico_equipo(start_date, end_date, metric, selected_players)
    
    # Verificar si es una tupla (tabla, fig)
    if isinstance(resultado, tuple) and len(resultado) == 2:
        return resultado  # Retorna (tabla, fig)
    else:
        # Error
        return html.Div("Error al aplicar el filtro.", className="text-center text-muted p-4"), {}

# Función auxiliar para generar tabla y gráfico de Semana Equipo (OPTIMIZADA)
def generar_tabla_y_grafico_equipo(start_date, end_date, metric, atleta_ids_filtro):
    """Genera tabla y gráfico para Semana Equipo (OPTIMIZADO)"""
    if not start_date or not end_date:
        return html.Div("Selecciona un rango de fechas.", className="text-center text-muted p-4"), {}
    
    # Convertir fechas a timestamps (manejar ambos formatos)
    try:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    except:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    try:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return html.Div("No hay actividades en el rango seleccionado.", className="text-center text-muted p-4"), {}
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()

    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return html.Div("No hay participantes para las actividades seleccionadas.", className="text-center text-muted p-4"), {}
    
    atleta_ids = participantes["athlete_id"].unique().tolist()

    # Obtener métricas
    metricas = get_metrics_for_activities_and_athletes(actividad_ids, atleta_ids, metric)

    # Mapeos (usando cache para atletas)
    actividad_fecha = dict(zip(actividades["id"], actividades["start_time"]))
    actividad_grupo = dict(zip(actividades["id"], actividades["grupo_dia"]))
    actividad_nombre = dict(zip(actividades["id"], actividades["name"])) if "name" in actividades.columns else {}
    atletas_df = get_cached_athletes()
    atleta_nombre = dict(zip(atletas_df["id"], atletas_df["full_name"]))
    
    # Obtener la etiqueta de la métrica seleccionada
    parametros = get_available_parameters()
    metrica_label = next((p['label'] for p in parametros if p['value'] == metric), metric)

    # OPTIMIZACIÓN: Construir tabla usando merge de pandas (mucho más rápido)
    # Crear DataFrame base con participantes
    df_tabla = participantes.copy()
    
    # Merge con métricas
    df_tabla = df_tabla.merge(
        metricas[['activity_id', 'athlete_id', 'parameter_value']], 
        on=['activity_id', 'athlete_id'], 
        how='left'
    )
    
    # Añadir columnas adicionales usando map (vectorizado)
    df_tabla['fecha'] = df_tabla['activity_id'].map(
        lambda x: datetime.fromtimestamp(actividad_fecha[x]).strftime("%Y-%m-%d") if x in actividad_fecha else ""
    )
    df_tabla['grupo_dia'] = df_tabla['activity_id'].map(actividad_grupo)
    df_tabla['activity_name'] = df_tabla['activity_id'].map(actividad_nombre)
    df_tabla['jugador'] = df_tabla['athlete_id'].map(atleta_nombre)
    df_tabla['valor'] = df_tabla['parameter_value'].fillna(0.0)
    
    # Filtrar por jugadores seleccionados
    if atleta_ids_filtro:
        df_tabla = df_tabla[df_tabla['athlete_id'].isin(atleta_ids_filtro)]
    
    # Renombrar columna para consistencia
    df_tabla = df_tabla.rename(columns={'athlete_id': 'jugador_id'})
    
    # Ordenar
    df_tabla = df_tabla.sort_values(['fecha', 'grupo_dia', 'jugador'])
    
    # Convertir a lista de diccionarios solo para la tabla final
    tabla_filtrada = df_tabla[['fecha', 'grupo_dia', 'jugador', 'jugador_id', 'valor']].to_dict('records')
    
    # 6. Gráfico de barras acumuladas por grupo_dia
    df = pd.DataFrame(tabla_filtrada)
    
    if not df.empty:
        # Obtener todos los días únicos que realmente tienen datos
        dias_con_datos = df["grupo_dia"].unique().tolist()
        
        # Ordenar los días: MD, MD+X (ascendente), MD-X (descendente desde mayor)
        # Orden: MD, MD+1, MD+2, MD+3, MD-6, MD-5, MD-4, MD-3, MD-2, MD-1, Sin clasificar
        orden_dias = ["MD", "MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "Sin clasificar"]
        dias_ordenados = [d for d in orden_dias if d in dias_con_datos]
        
        # Añadir cualquier día que no esté en el orden predefinido
        dias_extra = [d for d in dias_con_datos if d not in orden_dias]
        dias_ordenados.extend(sorted(dias_extra))
        
        # Usar todos los días con datos (crear copia explícita para evitar SettingWithCopyWarning)
        # Necesitamos incluir activity_id para contar actividades
        df_grafico = df_tabla[['fecha', 'grupo_dia', 'jugador', 'jugador_id', 'valor', 'activity_id', 'activity_name']].copy()
        df_grafico.loc[:, "grupo_dia"] = pd.Categorical(df_grafico["grupo_dia"], categories=dias_ordenados, ordered=True)
        
        # OPTIMIZACIÓN: Calcular estadísticas incluyendo actividades y fechas
        df_bar = df_grafico.groupby("grupo_dia", observed=True).agg({
            'valor': 'mean',
            'jugador_id': 'nunique',
            'activity_id': lambda x: x.nunique(),  # Número de actividades únicas
            'fecha': lambda x: ', '.join(sorted(x.unique())),  # Fechas únicas
            'activity_name': lambda x: ', '.join(filter(None, x.unique()))  # Nombres de actividades (sin valores nulos)
        }).reset_index()
        
        df_bar.columns = ["grupo_dia", "valor", "num_jugadores", "num_actividades", "fechas", "nombres_actividades"]
        df_bar["jugadores"] = df_bar["num_jugadores"].astype(str)
        
        # Determinar la unidad de la métrica para las etiquetas
        unidad = ""
        if "(m)" in metrica_label:
            unidad = " m"
        
        # Obtener los umbrales para esta variable
        umbrales_df = get_variable_thresholds(metric)
        
        # Crear gráfico con go.Figure para control individual de barras
        fig = go.Figure()
        
        # Añadir cada día como una barra separada para control de visibilidad
        for idx, row in df_bar.iterrows():
            dia = row['grupo_dia']
            valor = row['valor']
            num_jugadores = row['num_jugadores']
            num_actividades = row['num_actividades']
            fechas = row['fechas']
            nombres_actividades = row['nombres_actividades'] if row['nombres_actividades'] else ""
            
            # Determinar si el día debe estar visible por defecto
            # Solo días MD-X (MD-6, MD-5, MD-4, MD-3, MD-2, MD-1) y MD están visibles por defecto
            es_dia_md = bool(re.match(r'^MD[-+]?\d*$', dia))  # MD, MD-1, MD+1, etc.
            visible_por_defecto = True if es_dia_md else 'legendonly'
            
            # Construir tooltip dinámicamente
            tooltip_lines = [
                f"<b>{dia}</b>",
                f"{metrica_label} (Media): <b>%{{y:.1f}}{unidad}</b>",
                f"Jugadores: {num_jugadores}",
                f"Actividades: {num_actividades}",
                f"Fechas: {fechas}"
            ]
            
            # Si es MD, añadir el nombre del partido
            if dia == "MD" and nombres_actividades:
                tooltip_lines.insert(1, f"<i>{nombres_actividades}</i>")
            
            hovertemplate_text = "<br>".join(tooltip_lines) + "<extra></extra>"
            
            fig.add_trace(go.Bar(
                name=dia,
                x=[dia],
                y=[valor],
                marker=dict(
                    color="#1e3d59",
                    line=dict(color="#0d3b66", width=1.5)
                ),
                text=[valor],
                texttemplate=f"%{{text:.1f}}{unidad}",
                textposition="outside",
                hovertemplate=hovertemplate_text,
                visible=visible_por_defecto,
                showlegend=True
            ))
        
        # Añadir los umbrales al gráfico SOLO si existen Y tienen datos válidos
        if not umbrales_df.empty:
            # Filtrar solo umbrales que tienen valores válidos
            umbrales_validos = umbrales_df[
                umbrales_df['min_value'].notna() & 
                umbrales_df['max_value'].notna()
            ].copy()
            
            if not umbrales_validos.empty:
                # Crear diccionario de umbrales por día para búsqueda rápida
                umbrales_por_dia = {}
                for _, row in umbrales_validos.iterrows():
                    umbrales_por_dia[row['dia']] = {
                        'min': float(row['min_value']),
                        'max': float(row['max_value'])
                    }
                
                # Contador para saber si realmente añadimos algún umbral
                umbrales_añadidos = False
                
                # Iterar por cada día en el gráfico y añadir umbral si existe
                for idx, dia in enumerate(dias_ordenados):
                    # Si este día tiene umbral definido en la BD, añadirlo
                    if dia in umbrales_por_dia:
                        min_val = umbrales_por_dia[dia]['min']
                        max_val = umbrales_por_dia[dia]['max']
                        
                        # Rectángulo para el rango recomendado
                        fig.add_shape(
                            type="rect",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=min_val, y1=max_val,
                            fillcolor="rgba(200, 255, 200, 0.3)",
                            line=dict(width=0),
                            layer="below"
                        )
                        
                        # Línea para valor máximo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=max_val, y1=max_val,
                            line=dict(color="rgba(0, 128, 0, 0.9)", width=3),
                        )
                        
                        # Línea para valor mínimo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=min_val, y1=min_val,
                            line=dict(color="rgba(255, 0, 0, 0.9)", width=3),
                        )
                        
                        umbrales_añadidos = True
                
                # Solo añadir leyenda si realmente se añadieron umbrales
                if umbrales_añadidos:
                    fig.add_trace(go.Scatter(
                        x=[None], y=[None],
                        mode='markers',
                        marker=dict(size=10, color='rgba(0, 128, 0, 0.9)'),
                        name='Máximo recomendado'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=[None], y=[None],
                        mode='markers',
                        marker=dict(size=10, color='rgba(255, 0, 0, 0.9)'),
                        name='Mínimo recomendado'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=[None], y=[None],
                        mode='markers',
                        marker=dict(size=10, color='rgba(200, 255, 200, 0.3)'),
                        name='Rango recomendado'
                    ))
        
        fig.update_layout(
            title=None,  # Sin título
            xaxis=dict(
                title=dict(
                    text="Día del microciclo",
                    font=dict(size=13, color="#1e3d59", family="Montserrat")
                ),
                tickfont=dict(size=11, family="Montserrat"),
                categoryorder='array',
                categoryarray=dias_ordenados  # Forzar el orden correcto
            ),
            yaxis=dict(
                title=dict(
                    text=metrica_label,
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
            barmode='group'  # Importante para que cada barra sea independiente
        )
        
        # OPTIMIZACIÓN: Tabla de datos completos (usando DataFrame directamente)
        formato = ".0f" if "Distance" in metrica_label or "(m)" in metrica_label else ".2f"
        
        columns = [
            {"name": "Fecha", "id": "fecha"},
            {"name": "Día", "id": "grupo_dia"},
            {"name": "Jugador", "id": "jugador"},
            {"name": metrica_label, "id": "valor", "type": "numeric", "format": {"specifier": formato}}
        ]
        
        # Usar DataFrame directamente (más rápido que list comprehension)
        data = df_tabla[['fecha', 'grupo_dia', 'jugador', 'valor']].to_dict('records')
        
        table = dash_table.DataTable(
            id="sc-results-table",
            columns=columns,
            data=data,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "10px", "fontFamily": "Montserrat"},
            style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "border": "1px solid #dee2e6", "fontFamily": "Montserrat"},
            style_data_conditional=[{
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9"
            }],
            filter_action="native",
            sort_action="native",
            page_size=15,
            page_action="native"  # Paginación nativa (más rápida)
        )
        return table, fig
    else:
        return html.Div("No hay datos para mostrar en la tabla ni en el gráfico.", className="text-center text-muted p-4"), {}

# Callback para cambiar entre pestañas
@callback(
    Output("cpe-tab-content", "children"),
    Output("tab-cpe-equipo", "style"),
    Output("tab-cpe-jugadores", "style"),
    Output("tab-cpe-carga", "style"),
    Input("tab-cpe-equipo", "n_clicks"),
    Input("tab-cpe-jugadores", "n_clicks"),
    Input("tab-cpe-carga", "n_clicks"),
    State("microciclos-store", "data"),
    prevent_initial_call=False
)
def cambiar_pestana(n_clicks_equipo, n_clicks_jugadores, n_clicks_carga, microciclos):
    """Cambia entre las pestañas de Semana Equipo, Semana Jugadores y Carga Jugadores (OPTIMIZADO)"""
    ctx = callback_context
    
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
        "width": "33.33%",
        "textAlign": "center"
    }
    
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
        "width": "33.33%",
        "textAlign": "center"
    }
    
    # Asegurar que microciclos sea una lista
    if not microciclos:
        microciclos = []
    
    # Por defecto mostrar Semana Equipo
    if not ctx.triggered:
        return get_semana_equipo_content(microciclos), style_active, style_inactive, style_inactive
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "tab-cpe-jugadores":
        return get_semana_jugadores_content(microciclos), style_inactive, style_active, style_inactive
    elif button_id == "tab-cpe-carga":
        return get_carga_jugadores_content(microciclos), style_inactive, style_inactive, style_active
    else:
        return get_semana_equipo_content(microciclos), style_active, style_inactive, style_inactive

# ============================================
# CALLBACKS PARA SEMANA JUGADORES
# ============================================

# Callback para cargar datos iniciales y mostrar selector de jugadores
@callback(
    Output("sj-jugadores-container", "style"),
    Output("sj-jugadores-dropdown", "options"),
    Output("sj-jugadores-dropdown", "value"),
    Output("sj-stacked-chart", "figure"),
    Input("sj-cargar-btn", "n_clicks"),
    State("sj-date-store", "data"),
    State("sj-metric-dropdown", "value"),
    prevent_initial_call=True
)
def cargar_datos_semana(n_clicks, date_data, metric):
    """Carga datos iniciales y muestra selector de jugadores con los participantes del periodo (OPTIMIZADO)"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return {'display': 'none'}, [], [], {}
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    if not start_date or not end_date:
        return {'display': 'none'}, [], [], {}
    
    # Convertir fechas a timestamps (manejar ambos formatos)
    try:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    except:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    try:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    # Obtener actividades
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return {'display': 'none'}, [], [], {}
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()
    
    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return {'display': 'none'}, [], [], {}
    
    # Obtener jugadores únicos que participaron (usando cache)
    atleta_ids = participantes["athlete_id"].unique().tolist()
    atletas_df = get_cached_athletes()
    atletas_periodo = atletas_df[atletas_df["id"].isin(atleta_ids)]
    
    # Crear opciones del dropdown (todos los jugadores)
    jugadores_options = [{'label': row['full_name'], 'value': row['id']} for _, row in atletas_periodo.iterrows()]
    
    # Por defecto: EXCLUIR porteros
    atletas_sin_porteros = atletas_periodo[atletas_periodo['position_name'] != 'Goal Keeper']
    jugadores_ids = atletas_sin_porteros['id'].tolist()
    
    # Generar gráfico inicial sin porteros
    fig = generar_grafico_semana_jugadores(start_date, end_date, metric, jugadores_ids)
    
    # Mostrar selector de jugadores
    return {'display': 'block'}, jugadores_options, jugadores_ids, fig

# Callback para actualizar jugadores cuando se marca/desmarca "incluir porteros"
@callback(
    Output("sj-jugadores-dropdown", "value", allow_duplicate=True),
    Output("sj-stacked-chart", "figure", allow_duplicate=True),
    Input("sj-incluir-porteros", "value"),
    State("sj-date-store", "data"),
    State("sj-metric-dropdown", "value"),
    State("sj-jugadores-dropdown", "options"),
    prevent_initial_call=True
)
def toggle_porteros(incluir_porteros, date_data, metric, jugadores_options):
    """Incluye o excluye porteros según el checkbox"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return [], {}
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    # Obtener todos los atletas
    atletas_df = get_cached_athletes()
    
    # Si se debe incluir porteros
    if 'incluir' in incluir_porteros:
        # Seleccionar todos los jugadores disponibles
        jugadores_ids = [opt['value'] for opt in jugadores_options]
    else:
        # Excluir porteros
        ids_disponibles = [opt['value'] for opt in jugadores_options]
        atletas_disponibles = atletas_df[atletas_df['id'].isin(ids_disponibles)]
        atletas_sin_porteros = atletas_disponibles[atletas_disponibles['position_name'] != 'Goal Keeper']
        jugadores_ids = atletas_sin_porteros['id'].tolist()
    
    # Generar gráfico con la nueva selección
    fig = generar_grafico_semana_jugadores(start_date, end_date, metric, jugadores_ids)
    
    return jugadores_ids, fig

# Callback para aplicar filtro de jugadores
@callback(
    Output("sj-stacked-chart", "figure", allow_duplicate=True),
    Input("sj-filtrar-btn", "n_clicks"),
    State("sj-date-store", "data"),
    State("sj-metric-dropdown", "value"),
    State("sj-jugadores-dropdown", "value"),
    prevent_initial_call=True
)
def update_semana_jugadores_chart(n_clicks, date_data, metric, jugadores_seleccionados):
    """Aplica filtro de jugadores seleccionados"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return {}
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    if not start_date or not end_date or not jugadores_seleccionados:
        return {}
    
    return generar_grafico_semana_jugadores(start_date, end_date, metric, jugadores_seleccionados)

# Cache para datos de atletas (evita consultas repetidas)
@lru_cache(maxsize=1)
def get_cached_athletes():
    """Obtiene y cachea la lista de atletas"""
    return get_all_athletes()

# Función auxiliar para generar el gráfico (optimizada)
def generar_grafico_semana_jugadores(start_date, end_date, metric, atleta_ids_filtro):
    """Genera el gráfico de barras apiladas por jugador con colores por día (OPTIMIZADO)"""
    if not start_date or not end_date:
        return {}
    
    # Convertir fechas a timestamps (manejar ambos formatos)
    try:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    except:
        start_ts = int(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    try:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except:
        end_ts = int(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").timestamp())
    
    # Obtener actividades
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return {}
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()
    
    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return {}
    
    # Filtrar por jugadores del filtro
    if atleta_ids_filtro:
        participantes = participantes[participantes["athlete_id"].isin(atleta_ids_filtro)]
        if participantes.empty:
            return {}
    
    atleta_ids = participantes["athlete_id"].unique().tolist()
    
    # Obtener métricas
    metricas = get_metrics_for_activities_and_athletes(actividad_ids, atleta_ids, metric)
    
    # Mapeos (usando cache para atletas)
    actividad_fecha = dict(zip(actividades["id"], actividades["start_time"]))
    actividad_grupo = dict(zip(actividades["id"], actividades["grupo_dia"]))
    actividad_nombre = dict(zip(actividades["id"], actividades["name"])) if "name" in actividades.columns else {}
    atletas_df = get_cached_athletes()
    atleta_nombre = dict(zip(atletas_df["id"], atletas_df["full_name"]))
    
    # Obtener la etiqueta de la métrica
    parametros = get_available_parameters()
    metrica_label = next((p['label'] for p in parametros if p['value'] == metric), metric)
    
    # Construir datos
    datos = []
    for _, row in participantes.iterrows():
        actividad_id = row["activity_id"]
        atleta_id = row["athlete_id"]
        fecha = datetime.fromtimestamp(actividad_fecha[actividad_id]).strftime("%Y-%m-%d")
        grupo_dia = actividad_grupo.get(actividad_id, "Sin clasificar")
        activity_name = actividad_nombre.get(actividad_id, "")
        nombre = atleta_nombre.get(atleta_id, str(atleta_id))
        
        valor = metricas[(metricas["activity_id"] == actividad_id) & (metricas["athlete_id"] == atleta_id)]["parameter_value"]
        valor_metrica = float(valor.values[0]) if not valor.empty else 0.0
        
        datos.append({
            "jugador": nombre,
            "jugador_id": atleta_id,
            "fecha": fecha,
            "grupo_dia": grupo_dia,
            "actividad_id": actividad_id,
            "activity_name": activity_name,
            "valor": valor_metrica
        })
    
    df = pd.DataFrame(datos)
    
    if df.empty:
        return {}
    
    # Crear gráfico con dos grupos de barras: Semana y Partido
    # Agrupar por jugador y grupo_dia, sumando valores y conservando activity_name
    df_grouped = df.groupby(["jugador", "grupo_dia", "fecha"]).agg({
        'valor': 'sum',
        'activity_name': 'first'  # Tomar el primer nombre de actividad
    }).reset_index()
    
    # Separar datos de entrenamiento (semana) y partido (MD)
    df_semana = df_grouped[~df_grouped["grupo_dia"].isin(["MD", "Sin clasificar"])]
    df_partido = df_grouped[df_grouped["grupo_dia"] == "MD"]
    df_sin_clasificar = df_grouped[df_grouped["grupo_dia"] == "Sin clasificar"]
    
    # Crear mapeo de jugador a posición
    jugador_posicion = dict(zip(atletas_df["full_name"], atletas_df["position_name"]))
    
    # Orden de posiciones deseado
    orden_posiciones = [
        "Goal Keeper",
        "Lateral",
        "Central",
        "Mediocentro",
        "Interior",
        "Extremo",
        "Delantero"
    ]
    
    # Crear diccionario de prioridad de posiciones
    prioridad_posicion = {pos: idx for idx, pos in enumerate(orden_posiciones)}
    
    # Obtener jugadores únicos y ordenarlos por posición
    jugadores_unicos = df_grouped["jugador"].unique()
    
    def get_orden_jugador(jugador):
        """Retorna tupla (prioridad_posicion, carga_total) para ordenar"""
        posicion = jugador_posicion.get(jugador, "Sin posición")
        prioridad = prioridad_posicion.get(posicion, 999)  # 999 para posiciones no definidas
        
        # Calcular carga total de semana para ordenar dentro de la misma posición
        carga = df_semana[df_semana["jugador"] == jugador]["valor"].sum()
        
        return (prioridad, -carga)  # Negativo para ordenar descendente por carga
    
    jugadores_ordenados = sorted(jugadores_unicos, key=get_orden_jugador)
    
    # Orden de días de entrenamiento: MD+X (ascendente), luego MD-X (descendente desde mayor)
    # Orden: MD+1, MD+2, MD+3, MD-6, MD-5, MD-4, MD-3, MD-2, MD-1
    orden_dias_semana = ["MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1"]
    
    # Paleta de colores profesional y moderna - AMPLIADA
    colores_dias = {
        "MD-6": "#2C3E50",  # Azul oscuro
        "MD-5": "#34495E",  # Azul grisáceo
        "MD-4": "#4A90E2",  # Azul cielo
        "MD-3": "#50C878",  # Verde esmeralda
        "MD-2": "#FFB84D",  # Naranja suave
        "MD-1": "#FF6B6B",  # Rojo coral
        "MD": "#9B59B6",    # Morado partido
        "MD+1": "#45B7D1",  # Turquesa
        "MD+2": "#5D6D7E",  # Gris azulado
        "MD+3": "#7F8C8D",  # Gris medio
        "Sin clasificar": "#BDC3C7"  # Gris claro
    }
    
    # Mapeo de nombres de posiciones a abreviaturas
    abrev_posiciones = {
        "Goal Keeper": "POR",
        "Lateral": "LAT",
        "Central": "CEN",
        "Mediocentro": "MCD",
        "Interior": "INT",
        "Extremo": "EXT",
        "Delantero": "DEL"
    }
    
    # Crear figura
    fig = go.Figure()
    
    # Obtener días únicos de semana y ordenarlos (TODOS los días que tengan datos)
    dias_semana_unicos = df_semana["grupo_dia"].unique()
    dias_semana_ordenados = [dia for dia in orden_dias_semana if dia in dias_semana_unicos]
    
    # Añadir días extra que no estén en el orden predefinido
    dias_extra = [dia for dia in dias_semana_unicos if dia not in orden_dias_semana]
    dias_semana_ordenados.extend(sorted(dias_extra))
    
    # GRUPO 1: Barras apiladas de SEMANA (entrenamientos)
    for dia in dias_semana_ordenados:
        df_dia = df_semana[df_semana["grupo_dia"] == dia]
        
        valores = []
        hover_data = []
        for jugador in jugadores_ordenados:
            df_jugador_dia = df_dia[df_dia["jugador"] == jugador]
            if not df_jugador_dia.empty:
                valor = df_jugador_dia["valor"].sum()
                fecha = df_jugador_dia["fecha"].iloc[0]
                posicion = jugador_posicion.get(jugador, "Sin posición")
                valores.append(valor)
                hover_data.append(f"{posicion}|{fecha}")
            else:
                valores.append(0)
                hover_data.append("||")
        
        # Determinar si el día debe estar oculto por defecto
        # Solo días MD-X (MD-6, MD-5, MD-4, MD-3, MD-2, MD-1) y MD+X están visibles por defecto
        es_dia_md = bool(re.match(r'^MD[-+]\d+$', dia))
        visible_por_defecto = True if es_dia_md else 'legendonly'
        
        fig.add_trace(go.Bar(
            name=dia,
            x=jugadores_ordenados,
            y=valores,
            marker=dict(
                color=colores_dias.get(dia, "#95a5a6"),
                line=dict(color='rgba(255,255,255,0.8)', width=1)
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<i>%{customdata[0]}</i><br>"
                f"<b>{dia}</b><br>"
                f"{metrica_label}: <b>%{{y:.1f}}</b><br>"
                "Fecha: %{customdata[1]}"
                "<extra></extra>"
            ),
            customdata=[[h.split('|')[0], h.split('|')[1]] for h in hover_data],
            offsetgroup=0,
            width=0.4,
            visible=visible_por_defecto  # Ocultar por defecto si no es MD-X o MD+X
        ))
    
    # GRUPO 2: Barra separada de PARTIDO (MD)
    if not df_partido.empty:
        valores_partido = []
        hover_partido = []
        for jugador in jugadores_ordenados:
            df_jugador_partido = df_partido[df_partido["jugador"] == jugador]
            if not df_jugador_partido.empty:
                valor = df_jugador_partido["valor"].sum()
                fecha = df_jugador_partido["fecha"].iloc[0]
                activity_name = df_jugador_partido["activity_name"].iloc[0] if "activity_name" in df_jugador_partido.columns else ""
                posicion = jugador_posicion.get(jugador, "Sin posición")
                
                # Calcular carga de semana para comparación
                carga_semana = df_semana[df_semana["jugador"] == jugador]["valor"].sum()
                porcentaje = (valor / carga_semana * 100) if carga_semana > 0 else 0
                
                valores_partido.append(valor)
                hover_partido.append(f"{posicion}|{fecha}|{carga_semana:.1f}|{porcentaje:.1f}|{activity_name}")
            else:
                valores_partido.append(0)
                hover_partido.append("|||0|0|")
        
        fig.add_trace(go.Bar(
            name="MD (Partido)",
            x=jugadores_ordenados,
            y=valores_partido,
            marker=dict(
                color=colores_dias["MD"],
                line=dict(color='rgba(255,255,255,0.8)', width=1),
                pattern=dict(shape="/", size=6, solidity=0.4)
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<i>%{customdata[0]}</i><br>"
                "<b>PARTIDO: %{customdata[4]}</b><br>"
                f"{metrica_label}: <b>%{{y:.1f}}</b><br>"
                "Carga Semana: %{customdata[2]}<br>"
                "% vs Semana: <b>%{customdata[3]}%</b><br>"
                "Fecha: %{customdata[1]}"
                "<extra></extra>"
            ),
            customdata=[[h.split('|')[0], h.split('|')[1], h.split('|')[2], h.split('|')[3], h.split('|')[4]] for h in hover_partido],
            offsetgroup=1,
            width=0.4
        ))
    
    # GRUPO 3: Sin clasificar (desactivado por defecto)
    if not df_sin_clasificar.empty:
        valores_sc = []
        fechas_sc = []
        for jugador in jugadores_ordenados:
            df_jugador_sc = df_sin_clasificar[df_sin_clasificar["jugador"] == jugador]
            if not df_jugador_sc.empty:
                valores_sc.append(df_jugador_sc["valor"].sum())
                fechas_sc.append(df_jugador_sc["fecha"].iloc[0])
            else:
                valores_sc.append(0)
                fechas_sc.append("")
        
        fig.add_trace(go.Bar(
            name="Sin clasificar",
            x=jugadores_ordenados,
            y=valores_sc,
            marker_color=colores_dias["Sin clasificar"],
            hovertemplate=f"<b>%{{x}}</b><br>Sin clasificar<br>{metrica_label}: %{{y:.1f}}<br>Fecha: %{{customdata}}<extra></extra>",
            customdata=fechas_sc,
            visible='legendonly',  # Desactivado por defecto
            offsetgroup=0  # Se apila con semana si se activa
        ))
    
    # Añadir líneas verticales y anotaciones discretas para separar posiciones
    posicion_anterior = None
    posiciones_indices = {}
    
    for idx, jugador in enumerate(jugadores_ordenados):
        posicion_actual = jugador_posicion.get(jugador, "Sin posición")
        
        if posicion_actual not in posiciones_indices:
            posiciones_indices[posicion_actual] = []
        posiciones_indices[posicion_actual].append(idx)
        
        # Línea separadora más sutil
        if posicion_anterior is not None and posicion_actual != posicion_anterior and idx > 0:
            fig.add_vline(
                x=idx - 0.5,
                line_width=1,
                line_dash="dot",
                line_color="rgba(150, 150, 150, 0.3)"
            )
        
        posicion_anterior = posicion_actual
    
    # Anotaciones discretas de posición (solo nombre, arriba dentro del área)
    for posicion, indices in posiciones_indices.items():
        if len(indices) > 0:
            centro = (min(indices) + max(indices)) / 2
            
            # Añadir anotación discreta arriba
            fig.add_annotation(
                x=centro,
                y=1.02,
                yref="paper",
                text=f"<i>{posicion}</i>",
                showarrow=False,
                font=dict(size=9, color="#aaaaaa", family="Montserrat"),
                xanchor='center'
            )
    
    # Configurar layout limpio y profesional
    # Manejar ambos formatos de fecha
    try:
        fecha_inicio = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        fecha_inicio = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
    
    try:
        fecha_fin = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        fecha_fin = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
    
    fig.update_layout(
        barmode='stack',
        title=None,  # Sin título para más espacio
        xaxis=dict(
            title=None,
            categoryorder='array',
            categoryarray=jugadores_ordenados,
            showgrid=False,
            tickfont=dict(size=10, family="Montserrat"),
            tickangle=-45,  # Rotados para evitar solapamiento
            tickmode='linear',
            automargin=True
        ),
        yaxis=dict(
            title=dict(
                text=f"{metrica_label}",
                font=dict(size=13, color="#1e3d59", family="Montserrat")
            ),
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.15)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='rgba(100, 100, 100, 0.3)',
            zerolinewidth=1,
            tickfont=dict(size=11, family="Montserrat"),
            rangemode='tozero'
        ),
        height=550,
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#e0e0e0",
            borderwidth=1,
            font=dict(size=11, family="Montserrat"),
            itemsizing='constant',
            tracegroupgap=15,
            itemwidth=30
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=60, b=150, l=80, r=40),
        font=dict(family="Montserrat"),
        bargap=0.2,
        bargroupgap=0.1
    )
    
    return fig

# ============================================
# CALLBACKS PARA CARGA JUGADORES
# ============================================

# Callback para cargar estadísticas MD de jugadores
@callback(
    Output("cj-tabla-container", "children"),
    Output("cj-maximos-store", "data"),
    Input("cj-cargar-btn", "n_clicks"),
    prevent_initial_call=True
)
def cargar_estadisticas_md(n_clicks):
    """Carga y muestra estadísticas de cargas máximas en partidos MD"""
    
    print("DEBUG: Callback cargar_estadisticas_md ejecutándose...")
    
    try:
        # Obtener datos (ahora desde agosto 2025)
        df = calcular_estadisticas_md_jugadores('2025-08-15')
        print(f"DEBUG: Datos obtenidos. Shape: {df.shape if not df.empty else 'EMPTY'}")
        
        if df.empty:
            return (html.Div("No hay datos disponibles para el análisis. Verifica que haya actividades MD desde agosto 2025.", 
                            className="text-center text-muted p-4"), {})
    except Exception as e:
        print(f"ERROR en calcular_estadisticas_md_jugadores: {e}")
        import traceback
        traceback.print_exc()
        return (html.Div(f"Error al cargar datos: {str(e)}", 
                        className="text-center text-danger p-4"), {})
    
    # Excluir porteros por defecto
    df = df[df['posicion'] != 'Goal Keeper'].copy()
    
    # Mapeo de nombres de métricas para display
    metric_labels = {
        'total_distance': 'Distancia Total (m)',
        'distancia_+21_km/h_(m)': 'Distancia +21km/h (m)',
        'distancia_+24_km/h_(m)': 'Distancia +24km/h (m)',
        'distancia+28_(km/h)': 'Distancia +28km/h (m)',
        'gen2_acceleration_band7plus_total_effort_count': 'Aceleraciones',
        'average_player_load': 'Player Load',
        'max_vel': 'Velocidad Máxima (km/h)'
    }
    
    df['metrica_label'] = df['metrica'].map(metric_labels)
    
    # Advertencia si algún jugador no tiene partidos con +70 mins
    jugadores_sin_datos = df[df['num_partidos_70min'] == 0]['jugador_nombre'].unique()
    if len(jugadores_sin_datos) > 0:
        print(f"WARNING: Jugadores sin partidos +70 mins: {', '.join(jugadores_sin_datos)}")
    
    # Crear tabla expandible por jugador
    jugadores = df['jugador_nombre'].unique()
    
    tabla_contenido = []
    
    for jugador in sorted(jugadores):
        df_jugador = df[df['jugador_nombre'] == jugador].sort_values('metrica')
        
        # Usar acordeón nativo HTML con details/summary
        tabla_jugador = html.Details([
            html.Summary([
                html.Strong(jugador, style={'fontSize': '14px', 'color': '#1e3d59'})
            ], style={
                'cursor': 'pointer',
                'padding': '12px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '8px',
                'marginBottom': '8px',
                'listStyle': 'none'
            }),
            
            # Contenido expandible
            html.Div([
                # Advertencia si el jugador no tiene partidos con +70 mins
                html.Div([
                    html.I(className="fas fa-exclamation-triangle me-2", style={'color': '#ffc107'}),
                    html.Span(f"Este jugador no tiene partidos con más de 70 minutos jugados", 
                             style={'fontSize': '12px', 'color': '#856404'})
                ], style={'padding': '8px', 'backgroundColor': '#fff3cd', 'borderRadius': '6px', 'marginBottom': '12px'}) 
                if df_jugador['num_partidos_70min'].iloc[0] == 0 else html.Div(),
                
                # Tabla de métricas (valores estandarizados a 94')
                dash_table.DataTable(
                    data=df_jugador[['metrica_label', 'num_partidos_70min', 'media_estandarizada', 'maximo_estandarizado', 'media_3_maximos', 'media_5_maximos']].to_dict('records'),
                    columns=[
                        {'name': 'Métrica', 'id': 'metrica_label'},
                        {'name': 'Nº Partidos (+70\')', 'id': 'num_partidos_70min', 'type': 'numeric'},
                        {'name': 'Media (94\')', 'id': 'media_estandarizada', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                        {'name': 'Máximo (94\')', 'id': 'maximo_estandarizado', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                        {'name': 'Media Top 3 (94\')', 'id': 'media_3_maximos', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                        {'name': 'Media Top 5 (94\')', 'id': 'media_5_maximos', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    ],
                    style_table={'overflowX': 'auto', 'marginTop': '12px'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '12px',
                        'fontFamily': 'Montserrat',
                        'fontSize': '12px'
                    },
                    style_header={
                        'backgroundColor': '#1e3d59',
                        'color': 'white',
                        'fontWeight': '600',
                        'fontSize': '13px'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#f8f9fa'
                        }
                    ]
                ),
                
                # Detalles de los partidos con máximos (top 5)
                html.Details([
                    html.Summary("Ver detalles de partidos con valores máximos", 
                                style={'cursor': 'pointer', 'marginTop': '16px', 'fontSize': '12px', 'color': '#1e3d59'}),
                    html.Div([
                        html.Div([
                            html.Strong(f"{row['metrica_label']}:", className="me-2"),
                            html.Ul([
                                html.Li(
                                    f"{partido['fecha']} - {partido['partido']} ({partido['minutos']}min): {partido['valor']:.2f}" +
                                    (f" (estandarizado a 94')" if partido['estandarizado'] else ""),
                                    style={'fontSize': '11px'}
                                )
                                for partido in row['partidos_maximos']
                            ], style={'marginTop': '4px', 'marginBottom': '8px'})
                        ], style={'marginBottom': '12px'})
                        for _, row in df_jugador.iterrows()
                    ], style={'padding': '12px', 'backgroundColor': '#ffffff', 'borderRadius': '8px', 'marginTop': '8px'})
                ], style={'marginBottom': '16px'})
            ], style={'paddingLeft': '12px', 'paddingRight': '12px', 'paddingBottom': '12px'})
        ], className="mb-3", style={
            'border': '1px solid #e9ecef',
            'borderRadius': '8px',
            'backgroundColor': 'white'
        })
        
        tabla_contenido.append(tabla_jugador)
    
    # Crear diccionario de máximos para el store
    maximos_dict = {}
    for _, row in df.iterrows():
        jugador = row['jugador_nombre']
        metrica = row['metrica']
        if jugador not in maximos_dict:
            maximos_dict[jugador] = {}
        maximos_dict[jugador][metrica] = {
            'maximo_estandarizado': row['maximo_estandarizado'],
            'athlete_id': row['athlete_id']
        }
    
    return html.Div(tabla_contenido), maximos_dict

# Callback para generar barras de carga semanal vs máximos de competición
@callback(
    Output("cj-barras-container", "children"),
    Input("cj-generar-barras-btn", "n_clicks"),
    State("cj-microciclo-dropdown", "value"),
    State("cj-metrica-dropdown", "value"),
    State("cj-maximos-store", "data"),
    prevent_initial_call=True
)
def generar_barras_carga(n_clicks, microciclo, metrica, maximos_dict):
    """
    Genera barras de progreso mostrando la carga semanal vs el máximo de competición.
    Cada barra representa: mínimo = 2x máximo, máximo = 4x máximo (solo para distancia total).
    """
    
    if not microciclo or not metrica:
        return html.Div("Por favor, selecciona un microciclo y una métrica", className="text-center text-muted p-4")
    
    if not maximos_dict:
        return html.Div("Primero debes cargar el análisis de máximos de competición en la sección superior", 
                       className="text-center text-warning p-4")
    
    print(f"DEBUG: Generando barras para microciclo={microciclo}, metrica={metrica}")
    
    try:
        # Obtener actividades del microciclo
        engine = get_db_connection()
        if engine is None:
            return html.Div("Error de conexión a BD", className="text-center text-danger p-4")
        
        # Obtener fechas del microciclo
        # Formato: "Semana J10 R SANTANDER Vs RCD (12/10/2025 - 18/10/2025)"
        # Extraer las fechas entre paréntesis
        import re
        match = re.search(r'\((\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})\)', microciclo)
        if not match:
            return html.Div("Formato de microciclo inválido", className="text-center text-danger p-4")
        
        fecha_inicio_str = match.group(1)
        fecha_fin_str = match.group(2)
        
        # Convertir a timestamps
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%d/%m/%Y')
        fecha_fin = datetime.strptime(fecha_fin_str, '%d/%m/%Y')
        ts_inicio = int(fecha_inicio.timestamp())
        ts_fin = int(fecha_fin.timestamp())
        
        # Obtener actividades del microciclo
        query_actividades = f'''
            SELECT id
            FROM activities
            WHERE start_time >= {ts_inicio}
            AND start_time <= {ts_fin}
            ORDER BY start_time ASC
        '''
        df_actividades = pd.read_sql(query_actividades, engine)
        
        if df_actividades.empty:
            return html.Div("No hay actividades en este microciclo", className="text-center text-muted p-4")
        
        activity_ids = df_actividades['id'].tolist()
        ids_str = ','.join([f"'{id}'" for id in activity_ids])
        
        # Obtener valores de la métrica para todos los jugadores en el microciclo
        query_metrica = f'''
            SELECT 
                athlete_id,
                SUM(CAST(parameter_value AS DECIMAL(10,2))) as carga_semanal
            FROM activity_athlete_metrics
            WHERE parameter_name = '{metrica}'
            AND activity_id IN ({ids_str})
            AND parameter_value IS NOT NULL
            AND parameter_value != ''
            GROUP BY athlete_id
        '''
        df_carga = pd.read_sql(query_metrica, engine)
        
        if df_carga.empty:
            return html.Div("No hay datos de carga para esta métrica en el microciclo", 
                           className="text-center text-muted p-4")
        
        # Añadir nombres de jugadores
        atletas = get_all_athletes()
        df_carga = df_carga.merge(
            atletas[['id', 'full_name', 'position_name']],
            left_on='athlete_id',
            right_on='id',
            how='left'
        )
        
        # Excluir porteros
        df_carga = df_carga[df_carga['position_name'] != 'Goal Keeper'].copy()
        
        # Definir multiplicadores para mínimo y máximo
        # Solo para distancia total usamos x2 y x4
        if metrica == 'total_distance':
            MULTIPLICADOR_MINIMO = 2
            MULTIPLICADOR_MAXIMO = 4
        else:
            # Para otras métricas, no usamos límites por ahora
            MULTIPLICADOR_MINIMO = None
            MULTIPLICADOR_MAXIMO = None
        
        # Crear barras para cada jugador
        barras_html = []
        
        for _, row in df_carga.sort_values('full_name').iterrows():
            jugador = row['full_name']
            carga_semanal = row['carga_semanal']
            
            # Buscar el máximo de competición para este jugador
            if jugador not in maximos_dict or metrica not in maximos_dict[jugador]:
                continue  # Skip si no tiene máximo calculado
            
            maximo_competicion = maximos_dict[jugador][metrica]['maximo_estandarizado']
            
            # Calcular límites de la barra
            if MULTIPLICADOR_MINIMO and MULTIPLICADOR_MAXIMO:
                minimo_barra = MULTIPLICADOR_MINIMO * maximo_competicion
                maximo_barra = MULTIPLICADOR_MAXIMO * maximo_competicion
                
                # Calcular porcentaje con respecto al máximo
                porcentaje = min((carga_semanal / maximo_barra) * 100, 100)
                
                # Calcular posición del mínimo en la barra (50%)
                posicion_minimo = 50  # El mínimo está a mitad de la barra
            else:
                # Sin límites definidos, usar solo el máximo de competición
                maximo_barra = maximo_competicion * 2  # Por defecto x2
                porcentaje = min((carga_semanal / maximo_barra) * 100, 100)
                minimo_barra = None
                posicion_minimo = None
            
            # Crear barra HTML
            barra = html.Div([
                # Nombre del jugador
                html.Div([
                    html.Strong(jugador, style={'fontSize': '13px', 'color': '#1e3d59'})
                ], style={
                    'width': '180px',
                    'paddingRight': '12px',
                    'display': 'inline-block',
                    'verticalAlign': 'middle'
                }),
                
                # Contenedor de la barra
                html.Div([
                    # Barra de fondo
                    html.Div([
                        # Barra de progreso
                        html.Div(style={
                            'width': f'{porcentaje}%',
                            'height': '100%',
                            'backgroundColor': '#1e3d59',
                            'borderRadius': '4px',
                            'transition': 'width 0.3s ease'
                        }),
                        
                        # Marcador de mínimo (si aplica)
                        html.Div([
                            html.Div(style={
                                'position': 'absolute',
                                'left': f'{posicion_minimo}%',
                                'top': '-5px',
                                'width': '2px',
                                'height': 'calc(100% + 10px)',
                                'backgroundColor': '#ffc107',
                                'zIndex': 1
                            }),
                            html.Span(f'{minimo_barra:.0f}', style={
                                'position': 'absolute',
                                'left': f'{posicion_minimo}%',
                                'bottom': '-20px',
                                'transform': 'translateX(-50%)',
                                'fontSize': '10px',
                                'color': '#ffc107',
                                'fontWeight': '600'
                            })
                        ], style={'position': 'relative'}) if minimo_barra else html.Div()
                    ], style={
                        'position': 'relative',
                        'width': '100%',
                        'height': '30px',
                        'backgroundColor': '#e9ecef',
                        'borderRadius': '4px',
                        'overflow': 'hidden'
                    })
                ], style={
                    'flex': '1',
                    'display': 'inline-block',
                    'verticalAlign': 'middle',
                    'marginRight': '12px'
                }),
                
                # Porcentaje
                html.Div([
                    html.Strong(f'{porcentaje:.1f}%', style={'fontSize': '13px', 'color': '#1e3d59'})
                ], style={
                    'width': '60px',
                    'textAlign': 'right',
                    'display': 'inline-block',
                    'verticalAlign': 'middle'
                }),
                
                # Valor absoluto
                html.Div([
                    html.Span(f'{carga_semanal:.0f}', style={'fontSize': '11px', 'color': '#6c757d'})
                ], style={
                    'width': '80px',
                    'textAlign': 'right',
                    'display': 'inline-block',
                    'verticalAlign': 'middle',
                    'paddingLeft': '8px'
                })
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'marginBottom': '16px',
                'padding': '8px',
                'backgroundColor': '#ffffff',
                'borderRadius': '8px',
                'border': '1px solid #e9ecef'
            })
            
            barras_html.append(barra)
        
        if not barras_html:
            return html.Div("No hay jugadores con datos disponibles", className="text-center text-muted p-4")
        
        # Añadir leyenda si hay límites
        if MULTIPLICADOR_MINIMO and MULTIPLICADOR_MAXIMO:
            leyenda = html.Div([
                html.Div([
                    html.I(className="fas fa-circle me-2", style={'color': '#1e3d59', 'fontSize': '10px'}),
                    html.Small(f"Carga acumulada del microciclo", style={'fontSize': '11px', 'color': '#6c757d'})
                ], style={'marginRight': '20px', 'display': 'inline-block'}),
                html.Div([
                    html.I(className="fas fa-minus me-2", style={'color': '#ffc107', 'fontSize': '10px'}),
                    html.Small(f"Mínimo recomendado ({MULTIPLICADOR_MINIMO}x máximo partido)", 
                              style={'fontSize': '11px', 'color': '#6c757d'})
                ], style={'marginRight': '20px', 'display': 'inline-block'}),
                html.Div([
                    html.I(className="fas fa-flag me-2", style={'color': '#dc3545', 'fontSize': '10px'}),
                    html.Small(f"Máximo recomendado ({MULTIPLICADOR_MAXIMO}x máximo partido)", 
                              style={'fontSize': '11px', 'color': '#6c757d'})
                ], style={'display': 'inline-block'})
            ], style={
                'padding': '12px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '8px',
                'marginBottom': '20px'
            })
            
            return html.Div([leyenda] + barras_html)
        
        return html.Div(barras_html)
        
    except Exception as e:
        print(f"ERROR generando barras: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Error: {str(e)}", className="text-center text-danger p-4")
