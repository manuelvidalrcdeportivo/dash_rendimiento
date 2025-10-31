import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, callback_context, ALL
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
from functools import lru_cache
import re
from utils.db_manager import (
    get_db_connection,
    get_activities_by_date_range,
    get_participants_for_activities,
    get_metrics_for_activities_and_athletes,
    get_available_parameters,
    get_all_athletes,
    get_field_time_for_activities,
    add_grupo_dia_column,
    get_variable_thresholds,
    get_microciclos,
    # NUEVAS FUNCIONES OPTIMIZADAS:
    get_microciclos_from_processed_table,
    get_microciclo_data_processed,
    get_athletes_from_microciclo,
    get_microciclo_metrics_summary,
    get_microciclo_athlete_totals,
    get_ultimos_4_mds_promedios
)
from utils.layouts import standard_page
from utils.carga_jugadores import calcular_estadisticas_md_jugadores

# Función para obtener el contenido de "Microciclo Equipo" (contenido actual)
def get_microciclo_equipo_content(microciclos=None):
    """Contenido de la pestaña Microciclo Equipo - Vista con cacheo de datos"""
    # Usar microciclos pasados como parámetro o lista vacía
    if microciclos is None:
        microciclos = []
    microciclo_options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos]
    default_microciclo = microciclos[0]['id'] if microciclos else None
    
    # Definir métricas disponibles (similar a Control Proceso Competición)
    metricas_disponibles = [
        {'id': 'total_distance', 'label': 'Distancia Total (m)', 'icon': 'fa-route'},
        {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h (m)', 'icon': 'fa-running'},
        {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h (m)', 'icon': 'fa-bolt'},
        {'id': 'acc_dec_total', 'label': 'Aceleraciones/Deceleraciones +3', 'icon': 'fa-tachometer-alt'},
        {'id': 'ritmo_medio', 'label': 'Ritmo Medio (m/min)', 'icon': 'fa-stopwatch'}
    ]
    
    return html.Div([
        # Stores globales
        dcc.Store(id="sc-microciclo-cache", data={}),
        dcc.Store(id="sc-microciclo-loaded", data=False),  # Trigger único para barras
        dcc.Store(id="sc-date-store", data={}),
        dcc.Store(id="sc-part-rehab-store", data=[]),
        dcc.Store(id="sc-selected-metric", data="total_distance"),
        
        # PASO 1: Selector de Microciclo
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Selecciona Microciclo:", className="form-label", style={
                            'fontWeight': '500',
                            'fontSize': '14px',
                            'color': '#1e3d59',
                            'marginBottom': '8px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id="sc-microciclo-dropdown",
                            options=microciclo_options,
                            value=default_microciclo,
                            clearable=False,
                            placeholder="Selecciona un microciclo...",
                            style={'fontSize': '14px'}
                        ),
                    ], width=12, lg=9),
                    dbc.Col([
                        html.Div([
                            dcc.Loading(
                                id="sc-loading-microciclo",
                                type="circle",
                                color="#1e3d59",
                                children=[
                                    dbc.Button([
                                        html.I(className="fas fa-search me-2"),
                                        "Cargar Datos"
                                    ], id="sc-cargar-microciclo-btn", style={
                                        'backgroundColor': '#1e3d59',
                                        'border': 'none',
                                        'width': '100%',
                                        'padding': '10px'
                                    })
                                ]
                            )
                        ], style={'marginTop': '0'})
                    ], width=12, lg=3)
                ], className="mb-2", align="end"),
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # Loading general para TODO el contenido del microciclo
        dcc.Loading(
            id="sc-loading-general",
            type="default",
            color="#1e3d59",
            fullscreen=False,
            children=[
                # PASO 2: Seguimiento de Carga del Microciclo (TODAS LAS MÉTRICAS)
                html.Div(id="sc-progress-container", style={'display': 'none'}, children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Seguimiento de Carga del Microciclo", style={
                                'color': '#1e3d59',
                                'fontWeight': '600',
                                'fontSize': '18px',
                                'marginBottom': '20px'
                            }),
                            html.Div(id="sc-progress-bar-container", children=[
                                html.Div("Cargando seguimiento de carga...", className="text-center text-muted p-4")
                            ])
                        ])
                    ], className="mb-4", style={
                        'backgroundColor': 'white',
                        'borderRadius': '12px',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                        'border': 'none'
                    })
                ]),
        
        # PASO 3: Botones de métricas + Filtros
        html.Div(id="sc-metricas-container", style={'display': 'none'}, children=[
            dbc.Card([
                dbc.CardBody([
                    html.Label("Selecciona Métrica para Ver Detalle:", style={
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'color': '#1e3d59',
                        'marginBottom': '12px',
                        'display': 'block'
                    }),
                    # Primera fila: 3 botones
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                [html.I(className=f"fas {m['icon']} me-2"), m['label']],
                                id={'type': 'metric-btn', 'index': m['id']},
                                color="light",
                                style={
                                    'backgroundColor': '#f8f9fa' if idx != 0 else '#1e3d59',
                                    'color': '#1e3d59' if idx != 0 else 'white',
                                    'border': '1px solid #e0e0e0',
                                    'borderRadius': '8px',
                                    'padding': '12px 16px',
                                    'fontWeight': '600' if idx == 0 else '500',
                                    'fontSize': '13px',
                                    'marginBottom': '10px',
                                    'transition': 'all 0.2s ease',
                                    'width': '100%',
                                    'textAlign': 'left'
                                },
                                className="metric-button"
                            )
                        ], width=12, md=6, lg=4, className="mb-2")
                        for idx, m in enumerate(metricas_disponibles[:3])  # Primeros 3 botones
                    ]),
                    # Segunda fila: 2 botones centrados
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                [html.I(className=f"fas {m['icon']} me-2"), m['label']],
                                id={'type': 'metric-btn', 'index': m['id']},
                                color="light",
                                style={
                                    'backgroundColor': '#f8f9fa',
                                    'color': '#1e3d59',
                                    'border': '1px solid #e0e0e0',
                                    'borderRadius': '8px',
                                    'padding': '12px 16px',
                                    'fontWeight': '500',
                                    'fontSize': '13px',
                                    'marginBottom': '10px',
                                    'transition': 'all 0.2s ease',
                                    'width': '100%',
                                    'textAlign': 'left'
                                },
                                className="metric-button"
                            )
                        ], width=12, md=6, lg=4, className="mb-2")
                        for idx, m in enumerate(metricas_disponibles[3:], start=3)  # Últimos 2 botones
                    ], justify="center"),
                    
                    html.Hr(style={'margin': '20px 0', 'borderColor': '#e0e0e0'}),
                    
                    # Filtro de jugadores
                    html.Label("Filtro de Jugadores (opcional):", style={
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'color': '#1e3d59',
                        'marginBottom': '10px',
                        'display': 'block'
                    }),
                    html.Div(id="sc-jugadores-container", children=[
                        dbc.Row([
                            dbc.Col([
                                dcc.Dropdown(
                                    id="sc-player-dropdown",
                                    options=[],
                                    value=[],
                                    multi=True,
                                    placeholder="Todos los jugadores seleccionados por defecto...",
                                    className="mb-2"
                                ),
                                html.Div([
                                    dbc.Checklist(
                                        id="sc-incluir-porteros",
                                        options=[{'label': ' Incluir porteros', 'value': 'incluir'}],
                                        value=[],
                                        inline=True,
                                        style={
                                            'fontSize': '12px',
                                            'color': '#6c757d',
                                            'marginTop': '5px',
                                            'display': 'inline-block',
                                            'marginRight': '20px'
                                        }
                                    ),
                                    dbc.Checklist(
                                        id="sc-incluir-part-rehab",
                                        options=[{'label': ' Incluir Part/Rehab', 'value': 'incluir'}],
                                        value=[],
                                        inline=True,
                                        style={
                                            'fontSize': '12px',
                                            'color': '#6c757d',
                                            'marginTop': '5px',
                                            'display': 'inline-block'
                                        }
                                    ),
                                ]),
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
            })
        ]),
    
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
            ]
        )  # Cierre del dcc.Loading general
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
                
                # Store para IDs de jugadores con Part/Rehab
                dcc.Store(id="sj-part-rehab-store", data=[]),
                
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
                            html.Div([
                                dbc.Checklist(
                                    id="sj-incluir-porteros",
                                    options=[{'label': ' Incluir porteros', 'value': 'incluir'}],
                                    value=[],
                                    inline=True,
                                    style={
                                        'fontSize': '12px',
                                        'color': '#6c757d',
                                        'marginTop': '5px',
                                        'display': 'inline-block',
                                        'marginRight': '20px'
                                    }
                                ),
                                dbc.Checklist(
                                    id="sj-incluir-part-rehab",
                                    options=[{'label': ' Incluir Part/Rehab', 'value': 'incluir'}],
                                    value=[],
                                    inline=True,
                                    style={
                                        'fontSize': '12px',
                                        'color': '#6c757d',
                                        'marginTop': '5px',
                                        'display': 'inline-block'
                                    }
                                ),
                            ]),
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
                                    {'label': 'Distancia +21km/h (m)', 'value': 'distancia_21_kmh'},
                                    {'label': 'Distancia +24km/h (m)', 'value': 'distancia_24_kmh'},
                                    {'label': 'Aceleraciones/Deceleraciones +3', 'value': 'acc_dec_total'},
                                    {'label': 'Ritmo Medio', 'value': 'ritmo_medio'}
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
                    "Microciclo Equipo",
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
                        "width": "50%",
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
                        "width": "50%",
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
        html.Div(id="cpe-tab-content", children=[get_microciclo_equipo_content([])])
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
        # OPTIMIZACIÓN: Usar tabla intermedia en lugar de procesar en tiempo real
        try:
            microciclos = get_microciclos_from_processed_table()
            if microciclos:
                print(f"✅ Microciclos cargados desde tabla intermedia: {len(microciclos)}")
                return microciclos
        except Exception as e:
            print(f"⚠️ Error cargando desde tabla intermedia, usando método antiguo: {e}")
        
        # Fallback al método antiguo si falla
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

# Callback para toggle collapse de fechas personalizadas - Semana Jugadores
@callback(
    Output("sj-custom-date-collapse", "is_open"),
    Input("sj-toggle-custom-date", "n_clicks"),
    State("sj-custom-date-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_sj_custom_date(n_clicks, is_open):
    return not is_open

# Callback para actualizar store de fechas desde microciclo - Microciclo Equipo
@callback(
    Output("sc-date-store", "data"),
    Input("sc-microciclo-dropdown", "value"),
    State("microciclos-store", "data"),
    prevent_initial_call=False
)
def update_sc_date_store(microciclo_id, microciclos):
    """Actualiza el store de fechas desde microciclo seleccionado"""
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

# ============================================
# FUNCIÓN ULTRA-OPTIMIZADA PARA GENERAR GRÁFICOS
# ============================================

def generar_grafico_optimizado_precargado(df_summary, metric, metrica_label, maximos_historicos, umbrales_df, nombre_partido):
    """
    Versión ultra-optimizada que genera gráficos directamente desde datos ya procesados.
    NO hace ninguna query adicional. Umbrales hardcodeados.
    """
    import re
    
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
        
        # Tooltip
        hovertemplate = f"<b>{dia}</b>" + \
                      fecha_str + \
                      f"<br>{metrica_label} (Media): <b>{valor:.1f}{unidad}</b>" + \
                      porcentaje_md + \
                      f"<br>Jugadores: {num_jugadores}<br>" + \
                      "<extra></extra>"
        
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
    umbrales_multiplicadores = {
        'total_distance': {
            'MD-4': {'min': 0.45, 'max': 0.6},  # 65-85% del máximo
            'MD-3': {'min': 0.65, 'max': 0.80},  # 50-70% del máximo
            'MD-2': {'min': 0.35, 'max': 0.5},  # 35-55% del máximo
            'MD-1': {'min': 0.25, 'max': 0.4}   # 20-40% del máximo
        },
        'distancia_21_kmh': {
            'MD-4': {'min': 0.20, 'max': 0.30},
            'MD-3': {'min': 0.5, 'max': 0.8},
            'MD-2': {'min': 0.15, 'max': 0.3},
            'MD-1': {'min': 0.15, 'max': 0.3}
        },
        'distancia_24_kmh': {
            'MD-4': {'min': 0.10, 'max': 0.2},
            'MD-3': {'min': 0.40, 'max': 0.60},
            'MD-2': {'min': 0.2, 'max': 0.3},
            'MD-1': {'min': 0.10, 'max': 0.30}
        },
        'acc_dec_total': {
            'MD-4': {'min': 0.75, 'max': 1},
            'MD-3': {'min': 0.5, 'max': 0.7},
            'MD-2': {'min': 0.35, 'max': 0.65},
            'MD-1': {'min': 0.3, 'max': 0.55}
        },
        'ritmo_medio': {
            'MD-4': {'min': 0.50, 'max': 0.80},
            'MD-3': {'min': 0.5, 'max': 0.8},
            'MD-2': {'min': 0.5, 'max': 0.70},
            'MD-1': {'min': 0.4, 'max': 0.6}
        }
    }
    
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
                
                # Línea máximo (verde)
                fig.add_shape(
                    type="line",
                    x0=idx-0.4, x1=idx+0.4,
                    y0=max_val, y1=max_val,
                    line=dict(color="rgba(0, 128, 0, 0.9)", width=3),
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
                marker=dict(size=10, color='rgba(0, 128, 0, 0.9)'),
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
    
    # Añadir línea naranja del máximo SOBRE el MD
    if max_historico_md and 'MD' in dias_ordenados:
        try:
            idx_md = dias_ordenados.index('MD')
            partido_max_label = "Máx últimos 4 MDs (100%)"
            if maximos_historicos and maximos_historicos.get('partido_max'):
                partido_max_label = f"Referencia: {maximos_historicos['partido_max']} (100%)"
            
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
                hovertemplate=f"<b>Máximo de últimos 4 MDs</b><br>" +
                             (f"Partido: <b>{maximos_historicos.get('partido_max')}</b><br>" if maximos_historicos and maximos_historicos.get('partido_max') else "") +
                             f"Valor: <b>{max_historico_md:.1f}{unidad}</b><br>" +
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

# ============================================
# NUEVO CALLBACK PARA MICROCICLO EQUIPO - CACHEO DE DATOS
# ============================================

# Callback principal: Cargar y cachear TODAS las métricas del microciclo
@callback(
    Output("sc-microciclo-cache", "data"),
    Output("sc-microciclo-loaded", "data"),
    Output("sc-metricas-container", "style"),
    Output("sc-jugadores-container", "style"),
    Output("sc-player-dropdown", "options"),
    Output("sc-player-dropdown", "value"),
    Output("sc-part-rehab-store", "data"),
    Input("sc-cargar-microciclo-btn", "n_clicks"),
    State("sc-microciclo-dropdown", "value"),
    State("sc-date-store", "data"),
    prevent_initial_call=True
)
def cargar_microciclo_completo(n_clicks, microciclo_id, date_data):
    """
    OPTIMIZADO: Carga datos desde tabla intermedia.
    Fallback a método antiguo si la tabla no está disponible.
    """
    if not microciclo_id:
        return {}, False, {'display': 'none'}, {'display': 'none'}, [], [], []
    
    print(f"🔄 Cargando microciclo: {microciclo_id}")
    
    # MÉTODO OPTIMIZADO: Usar tabla intermedia
    try:
        # Obtener atletas del microciclo desde tabla procesada
        atletas_df = get_athletes_from_microciclo(microciclo_id)
        
        if atletas_df.empty:
            print(f"⚠️ No hay datos en tabla intermedia para {microciclo_id}, usando método antiguo")
            raise Exception("Tabla intermedia vacía")
        
        # Identificar jugadores con Part/Rehab
        jugadores_con_part_rehab = atletas_df[atletas_df['has_part_rehab']]['athlete_id'].tolist()
        
        # Filtrar porteros
        atletas_sin_porteros = atletas_df[atletas_df['athlete_position'] != 'Goal Keeper']
        
        # Crear opciones dropdown
        jugadores_options = [
            {'label': row['athlete_name'], 'value': row['athlete_id']} 
            for _, row in atletas_df.iterrows()
        ]
        
        # Selección inicial: jugadores de campo
        jugadores_ids = atletas_sin_porteros['athlete_id'].tolist()
        
        print(f"⚡⚡⚡ ULTRA-OPTIMIZACIÓN: Cargando con solo 2 queries masivas...")
        
        # Importar función ULTRA-optimizada (2 queries totales)
        from pages.seguimiento_carga_ultra_optimizado import cargar_microciclo_ultrarapido_v2
        
        # Cargar todo con 2 queries masivas
        resultado_raw = cargar_microciclo_ultrarapido_v2(microciclo_id, jugadores_ids)
        
        if not resultado_raw:
            print("❌ Error cargando microciclo")
            raise Exception("No se pudieron cargar los datos")
        
        datos_por_metrica = resultado_raw['datos_por_metrica']
        ultimos_4_mds_por_metrica = resultado_raw['maximos_historicos']
        nombre_partido = resultado_raw.get('nombre_partido')
        
        # Generar gráficos de forma ultra-optimizada
        print("🎨 Generando 6 gráficos (umbrales hardcodeados, 0 queries)...")
        
        # Obtener parámetros una sola vez (no 6 veces)
        parametros = get_available_parameters()
        parametros_dict = {p['value']: p['label'] for p in parametros}
        
        graficos_metricas = {}
        for metrica, df_resumen in datos_por_metrica.items():
            try:
                # Generar gráfico con función optimizada (umbrales hardcodeados)
                fig = generar_grafico_optimizado_precargado(
                    df_resumen,
                    metrica,
                    parametros_dict.get(metrica, metrica),
                    ultimos_4_mds_por_metrica.get(metrica),
                    None,  # umbrales_df no necesario (hardcodeados)
                    nombre_partido
                )
                graficos_metricas[metrica] = fig
            except Exception as e:
                print(f"  ⚠️ Error con {metrica}: {e}")
        
        print(f"✅ {len(graficos_metricas)} gráficos generados")
        
        # Cache optimizado CON TODAS LAS MÉTRICAS PRE-CARGADAS
        cache_optimizado = {
            'microciclo_id': microciclo_id,
            'jugadores_ids': jugadores_ids,
            'cargado': True,
            'graficos': graficos_metricas,  # ← TODAS las figuras listas
            'maximos_historicos': ultimos_4_mds_por_metrica  # ← Máximos precalculados
        }
        
        print(f"✅ Microciclo cargado: {len(atletas_df)} atletas, {len(graficos_metricas)} métricas")
        
        # Generar timestamp único para trigger
        import time
        timestamp = time.time()
        
        return (
            cache_optimizado,
            timestamp,  # Trigger para cargar barras
            {'display': 'block'},
            {'display': 'block'},
            jugadores_options,
            jugadores_ids,
            jugadores_con_part_rehab
        )
        
    except Exception as e:
        print(f"❌ Error cargando microciclo desde tabla intermedia: {e}")
        import traceback
        traceback.print_exc()
        return {}, False, {'display': 'none'}, {'display': 'none'}, [], [], []

# Callback para cargar y mostrar métrica inicial
@callback(
    Output("sc-bar-chart", "figure"),
    Output("sc-selected-metric", "data"),
    Output("sc-progress-container", "style"),
    Input("sc-microciclo-loaded", "data"),
    State("sc-microciclo-cache", "data"),
    prevent_initial_call=True
)
def cargar_metrica_inicial(loaded_timestamp, cache_data):
    """Muestra el gráfico de la primera métrica (Distancia Total) desde el cache
    
    Los datos YA están cargados en cache_data['graficos']
    """
    if not loaded_timestamp or not cache_data or not cache_data.get('cargado'):
        return {}, "total_distance", {'display': 'none'}
    
    # Obtener figura desde el cache (ya está cargada)
    graficos = cache_data.get('graficos', {})
    fig = graficos.get('total_distance', {})
    
    if fig:
        print(f"📊 Mostrando métrica inicial: Distancia Total (desde cache)")
        return fig, "total_distance", {'display': 'block'}
    
    print(f"⚠️ No se encontró total_distance en cache")
    return {}, "total_distance", {'display': 'none'}

# Callback para cambiar entre métricas usando botones (carga on-demand con cache inteligente)
@callback(
    Output("sc-bar-chart", "figure", allow_duplicate=True),
    Output("sc-selected-metric", "data", allow_duplicate=True),
    Input({'type': 'metric-btn', 'index': ALL}, 'n_clicks'),
    State("sc-microciclo-cache", "data"),
    State("sc-player-dropdown", "value"),
    State("sc-incluir-part-rehab", "value"),
    prevent_initial_call=True
)
def cambiar_metrica(n_clicks_list, cache_data, jugadores_seleccionados, incluir_part_rehab):
    """Cambia la métrica mostrada leyendo desde el cache
    
    Los datos YA están cargados en cache_data['graficos']
    NO hace queries adicionales = INSTANTÁNEO
    """
    ctx = dash.callback_context
    
    if not ctx.triggered or not cache_data or not cache_data.get('cargado'):
        raise PreventUpdate
    
    # Identificar qué botón fue presionado
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == '':
        raise PreventUpdate
    
    # Extraer el index del botón (nombre de la métrica)
    import json
    button_dict = json.loads(button_id)
    metrica_seleccionada = button_dict['index']
    
    # Obtener figura desde el cache (ya está cargada)
    graficos = cache_data.get('graficos', {})
    fig = graficos.get(metrica_seleccionada)
    
    if fig:
        print(f"⚡ Mostrando {metrica_seleccionada} (desde cache)")
        return fig, metrica_seleccionada
    
    print(f"⚠️ No se encontró {metrica_seleccionada} en cache")
    raise PreventUpdate

# Callback para actualizar estilos de botones de métricas
@callback(
    Output({'type': 'metric-btn', 'index': ALL}, 'style'),
    Input("sc-selected-metric", "data")
)
def actualizar_estilos_botones(metrica_actual):
    """Actualiza los estilos de los botones según la métrica seleccionada"""
    # Orden exacto de las métricas como aparecen en el layout
    metricas_list = [
        'total_distance',
        'distancia_21_kmh',
        'distancia_24_kmh',
        'acc_dec_total',
        'ritmo_medio'
    ]
    
    print(f"🎨 Actualizando estilos botones. Métrica actual: {metrica_actual}")
    
    estilos = []
    for metrica in metricas_list:
        if metrica == metrica_actual:
            # Estilo activo
            estilos.append({
                'backgroundColor': '#1e3d59',
                'color': 'white',
                'border': '1px solid #1e3d59',
                'borderRadius': '8px',
                'padding': '12px 16px',
                'fontWeight': '600',
                'fontSize': '13px',
                'marginBottom': '10px',
                'transition': 'all 0.2s ease',
                'width': '100%',
                'textAlign': 'left'
            })
        else:
            # Estilo inactivo
            estilos.append({
                'backgroundColor': '#f8f9fa',
                'color': '#1e3d59',
                'border': '1px solid #e0e0e0',
                'borderRadius': '8px',
                'padding': '12px 16px',
                'fontWeight': '500',
                'fontSize': '13px',
                'marginBottom': '10px',
                'transition': 'all 0.2s ease',
                'width': '100%',
                'textAlign': 'left'
            })
    
    return estilos

# Callback para generar barras de progreso de TODAS las métricas
@callback(
    Output("sc-progress-bar-container", "children"),
    Input("sc-microciclo-loaded", "data"),
    State("sc-microciclo-cache", "data"),
    prevent_initial_call=True
)
def generar_barras_todas_metricas(loaded_timestamp, cache_data):
    """Genera barras de progreso para TODAS las métricas del microciclo
    
    USA DATOS DEL CACHE - NO HACE QUERIES ADICIONALES
    """
    if not loaded_timestamp or not cache_data or not cache_data.get('cargado'):
        return html.Div()
    
    print(f"🎯 Generando barras desde cache (SIN queries adicionales)")
    
    # Configuración de métricas con umbrales
    metricas_config = [
        {'id': 'total_distance', 'label': 'Distancia Total', 'min': 170, 'max': 230},
        {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h', 'min': 100, 'max': 170},
        {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h', 'min': 80, 'max': 140},
        {'id': 'acc_dec_total', 'label': 'Aceleraciones/Deceleraciones +3', 'min': 190, 'max': 290},
        {'id': 'ritmo_medio', 'label': 'Ritmo Medio', 'min': 100, 'max': 140}
    ]
    
    # Colores para días
    colores_dias = {
        'MD-5': '#b3cde3',
        'MD-4': '#6baed6', 
        'MD-3': '#4292c6',
        'MD-2': '#2171b5',
        'MD-1': '#08519c'
    }
    
    # Obtener datos del cache (ya cargados)
    graficos = cache_data.get('graficos', {})
    maximos_historicos = cache_data.get('maximos_historicos', {})
    
    if not graficos:
        return html.Div("No hay datos disponibles", className="text-center text-muted p-4")
    
    barras_html = []
    
    # Generar barra para cada métrica
    for config in metricas_config:
        metric_id = config['id']
        
        # Obtener figura del cache
        fig = graficos.get(metric_id)
        if not fig:
            continue
        
        try:
            # Extraer datos de la figura (ya están procesados)
            entrenamientos_con_porcentaje = []
            acumulado_total = 0
            
            # Obtener máximo histórico del cache
            max_historico = maximos_historicos.get(metric_id, {}).get('max')
            
            # Extraer valores de las barras del gráfico
            for trace in fig.get('data', []):
                dia = trace.get('name', '').split(' ')[0]  # Quitar porcentaje si existe
                if dia and dia.startswith('MD-'):
                    valor = trace.get('y', [0])[0] if trace.get('y') else 0
                    # Solo procesar si tenemos valor y máximo histórico válidos
                    if valor and valor > 0 and max_historico and max_historico > 0:
                        porcentaje = (valor / max_historico) * 100
                        acumulado_total += porcentaje
                        entrenamientos_con_porcentaje.append({
                            'nombre': dia,
                            'porcentaje': porcentaje,
                            'color': colores_dias.get(dia, '#6c757d')
                        })
            
            # Ordenar días correctamente (MD-4, MD-3, MD-2, MD-1)
            entrenamientos_con_porcentaje.sort(key=lambda x: x['nombre'], reverse=True)
            
            # 4. Determinar color del acumulado
            if acumulado_total < config['min']:
                color_acumulado = '#dc3545'  # Rojo - Por debajo del mínimo
            elif acumulado_total <= config['max']:
                color_acumulado = '#28a745'  # Verde - En rango óptimo
            else:
                color_acumulado = '#dc3545'  # Rojo - Por encima del máximo
            
            # 5. Crear barra HTML para esta métrica
            # Calcular posición del mínimo
            pos_min = (config['min'] / config['max']) * 100 if config['max'] > 0 else 0
            
            barra_metrica = html.Div([
                dbc.Row([
                    # Columna izquierda: Nombre de la métrica
                    dbc.Col([
                        html.Div(config['label'], style={
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#1e3d59',
                            'lineHeight': '40px'
                        })
                    ], width=2),
                    
                    # Columna central: Barra de progreso
                    dbc.Col([
                        html.Div([
                            # Barra con segmentos de días
                            html.Div(
                                [
                                    html.Div(
                                        f"{e['porcentaje']:.0f}%",
                                        style={
                                            'width': f"{min(100, (e['porcentaje'] / config['max']) * 100)}%",
                                            'backgroundColor': e['color'],
                                            'color': 'white',
                                            'fontSize': '11px',
                                            'fontWeight': '600',
                                            'textAlign': 'center',
                                            'lineHeight': '40px',
                                            'textShadow': '0 0 3px rgba(0,0,0,0.5)',
                                            'display': 'inline-block',
                                            'height': '100%'
                                        }
                                    )
                                    for e in entrenamientos_con_porcentaje
                                ],
                                style={
                                    'height': '40px',
                                    'backgroundColor': '#e9ecef',
                                    'borderRadius': '6px',
                                    'display': 'flex',
                                    'position': 'relative'
                                }
                            ),
                            # Línea del mínimo
                            html.Div(style={
                                'position': 'absolute',
                                'left': f'{pos_min}%',
                                'top': '0',
                                'width': '2px',
                                'height': '40px',
                                'backgroundColor': '#1e3d59',
                                'zIndex': '5'
                            }),
                            # Línea del máximo
                            html.Div(style={
                                'position': 'absolute',
                                'right': '0',
                                'top': '0',
                                'width': '2px',
                                'height': '40px',
                                'backgroundColor': '#dc3545',
                                'zIndex': '5'
                            }),
                            # Label del mínimo debajo
                            html.Div(f"Mín: {config['min']}%", style={
                                'position': 'absolute',
                                'left': f'{pos_min}%',
                                'top': '48px',
                                'transform': 'translateX(-50%)',
                                'fontSize': '9px',
                                'fontWeight': '600',
                                'color': '#1e3d59',
                                'whiteSpace': 'nowrap'
                            }),
                            # Label del máximo debajo
                            html.Div(f"Máx: {config['max']}%", style={
                                'position': 'absolute',
                                'right': '0',
                                'top': '48px',
                                'transform': 'translateX(50%)',
                                'fontSize': '9px',
                                'fontWeight': '600',
                                'color': '#dc3545',
                                'whiteSpace': 'nowrap'
                            })
                        ], style={'position': 'relative', 'paddingBottom': '25px'})
                    ], width=8),
                    
                    # Columna derecha: Acumulado total
                    dbc.Col([
                        html.Div(f"{acumulado_total:.0f}%", style={
                            'fontWeight': '700',
                            'fontSize': '16px',
                            'color': color_acumulado,
                            'lineHeight': '40px',
                            'textAlign': 'right'
                        })
                    ], width=2)
                ])
            ], style={'marginBottom': '35px'})
            
            # Añadir barra a la lista
            barras_html.append(barra_metrica)
            print(f"  ✓ Barra creada para {config['label']} - Acumulado: {acumulado_total:.0f}%")
            
        except Exception as e:
            print(f"  ✗ Error con {config['label']}: {e}")
            continue
    
    print(f"✅ {len(barras_html)} barras generadas desde cache")
    
    # Retornar todas las barras
    if barras_html:
        return html.Div(barras_html)
    else:
        return html.Div("No hay datos suficientes para mostrar el seguimiento de carga", 
                       className="text-muted text-center p-3")

# Callback para añadir/quitar porteros y actualizar indicadores (Microciclo Equipo)
@callback(
    Output("sc-player-dropdown", "options", allow_duplicate=True),
    Output("sc-player-dropdown", "value", allow_duplicate=True),
    Input("sc-incluir-porteros", "value"),
    Input("sc-incluir-part-rehab", "value"),
    State("sc-player-dropdown", "options"),
    State("sc-player-dropdown", "value"),
    State("sc-part-rehab-store", "data"),
    prevent_initial_call=True
)
def toggle_filtros_equipo(incluir_porteros, incluir_part_rehab, current_options, current_value, part_rehab_ids):
    """Añade/quita porteros y actualiza indicadores visuales para Part/Rehab - NO ACTUALIZA GRÁFICO"""
    print(f"\n🔘 TOGGLE CHECKBOXES (NO recalcula gráfico, solo dropdown)")
    print(f"  Porteros: {incluir_porteros}")
    print(f"  Part/Rehab: {incluir_part_rehab}")
    
    if not current_options:
        return current_options, current_value or []
    
    # Obtener todos los atletas disponibles
    atletas_df = get_cached_athletes()
    ids_disponibles = [opt['value'] for opt in current_options]
    atletas_disponibles = atletas_df[atletas_df['id'].isin(ids_disponibles)].copy()
    
    # IDs con Part/Rehab
    rehab_ids = set(part_rehab_ids) if part_rehab_ids else set()
    
    # Crear opciones con indicadores si Part/Rehab está marcado
    nuevas_options = []
    for _, row in atletas_disponibles.iterrows():
        label = row['full_name']
        
        # Solo mostrar indicador si checkbox Part/Rehab está marcado Y el jugador tiene Part/Rehab
        if 'incluir' in incluir_part_rehab and row['id'] in rehab_ids:
            label = f"⚠️ {label} (incluyendo entrenamientos rehab)"
        
        nuevas_options.append({'label': label, 'value': row['id']})
    
    # Empezar con la selección actual
    seleccion_actual = set(current_value) if current_value else set()
    
    # Obtener IDs de porteros
    porteros_ids = set(atletas_disponibles[atletas_disponibles['position_name'] == 'Goal Keeper']['id'].tolist())
    
    # Aplicar lógica de añadir/quitar SOLO PORTEROS
    if 'incluir' in incluir_porteros:
        # AÑADIR porteros a la selección actual
        seleccion_actual = seleccion_actual.union(porteros_ids)
    else:
        # QUITAR porteros de la selección actual
        seleccion_actual = seleccion_actual - porteros_ids
    
    # Part/Rehab NO modifica la selección, solo los indicadores y el filtrado en "Aplicar Filtro"
    
    return nuevas_options, list(seleccion_actual)

# Callback para aplicar filtro de jugadores en Microciclo Equipo
@callback(
    Output("sc-bar-chart", "figure", allow_duplicate=True),
    Output("sc-selected-metric", "data", allow_duplicate=True),
    Output("sc-microciclo-cache", "data", allow_duplicate=True),
    Input("sc-filtrar-btn", "n_clicks"),
    State("sc-selected-metric", "data"),
    State("sc-microciclo-cache", "data"),
    State("sc-player-dropdown", "value"),
    State("sc-incluir-part-rehab", "value"),
    prevent_initial_call=True
)
def aplicar_filtro_microciclo(n_clicks, metrica_actual, cache_data, jugadores_seleccionados, incluir_part_rehab):
    """Aplica filtro de jugadores seleccionados y regenera gráfico"""
    if not cache_data or not cache_data.get('cargado'):
        raise PreventUpdate
    
    if not jugadores_seleccionados:
        raise PreventUpdate
    
    # Determinar si excluir Part/Rehab según checkbox
    excluir_part_rehab = 'incluir' not in (incluir_part_rehab or [])
    
    print(f"\n{'='*60}")
    print(f"🔧 APLICAR FILTRO - DEBUG")
    print(f"{'='*60}")
    print(f"Métrica: {metrica_actual}")
    print(f"Jugadores seleccionados: {len(jugadores_seleccionados)} -> {jugadores_seleccionados}")
    print(f"Excluir Part/Rehab: {excluir_part_rehab}")
    
    # Limpiar cache de métricas (ya que cambiaron los filtros)
    cache_data['metricas_cargadas'] = {}
    
    # OPTIMIZACIÓN: Usar tabla intermedia si está disponible
    if cache_data.get('usa_tabla_intermedia'):
        microciclo_id = cache_data.get('microciclo_id')
        try:
            print(f"⚡ Aplicando filtro desde tabla intermedia (microciclo: {microciclo_id})")
            tabla, fig = generar_grafico_desde_tabla_intermedia(
                microciclo_id, 
                metrica_actual, 
                jugadores_seleccionados, 
                excluir_part_rehab
            )
            
            # Guardar en cache con nueva key
            cache_key = f"{metrica_actual}_{','.join(map(str, sorted(jugadores_seleccionados)))}_{excluir_part_rehab}"
            cache_data['metricas_cargadas'][cache_key] = fig
            
            print(f"✅ Filtro aplicado: {len(jugadores_seleccionados)} jugadores, Part/Rehab={'incluido' if not excluir_part_rehab else 'excluido'}")
            
            return fig, metrica_actual, cache_data
            
        except Exception as e:
            print(f"⚠️ Error con tabla intermedia: {e}")
            import traceback
            traceback.print_exc()
            print("  Intentando método antiguo...")
    
    # FALLBACK: Método antiguo
    start_date = cache_data.get('start_date')
    end_date = cache_data.get('end_date')
    
    if not start_date or not end_date:
        raise PreventUpdate
    
    try:
        resultado = generar_tabla_y_grafico_equipo(start_date, end_date, metrica_actual, jugadores_seleccionados, excluir_part_rehab)
        if isinstance(resultado, tuple) and len(resultado) == 2:
            tabla, fig = resultado
            
            # Guardar en cache con nueva key
            cache_key = f"{metrica_actual}_{','.join(map(str, sorted(jugadores_seleccionados)))}_{excluir_part_rehab}"
            cache_data['metricas_cargadas'][cache_key] = fig
            
            print(f"✅ Filtro aplicado: {len(jugadores_seleccionados)} jugadores, Part/Rehab={'incluido' if not excluir_part_rehab else 'excluido'}")
            
            return fig, metrica_actual, cache_data
    except Exception as e:
        print(f"Error aplicando filtro: {e}")
    
    raise PreventUpdate

# Función SÚPER OPTIMIZADA usando tabla intermedia
def generar_grafico_desde_tabla_intermedia(microciclo_id, metric, atleta_ids_filtro, excluir_part_rehab=True, maximos_precalculados=None, df_summary_precargado=None, umbrales_precargados=None, nombre_partido=None):
    """
    Genera gráfico desde tabla intermedia con TODAS las funcionalidades del método original.
    
    Args:
        maximos_precalculados: Dict opcional con máximos ya calculados {metric: {'max': X, 'min': Y}}
        df_summary_precargado: DataFrame opcional con resumen ya cargado (evita query)
        umbrales_precargados: DataFrame opcional con umbrales ya cargados (evita query)
        nombre_partido: Nombre del partido (para hover del MD)
    """
    try:
        # Usar resumen precargado si está disponible, sino hacer query
        if df_summary_precargado is not None:
            df_summary = df_summary_precargado
        else:
            # Obtener resumen por día desde tabla intermedia
            df_summary = get_microciclo_metrics_summary(
                microciclo_id=microciclo_id,
                metric_name=metric,
                athlete_ids=atleta_ids_filtro,
                exclude_part_rehab=excluir_part_rehab,
                exclude_goalkeepers=True
            )
        
        if df_summary.empty:
            return html.Div("No hay datos disponibles.", className="text-center text-muted p-4"), {}
        
        # Ordenar días según lógica MD
        orden_dias = ["MD", "MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "Sin clasificar"]
        dias_con_datos = df_summary['activity_tag'].unique().tolist()
        dias_ordenados = [d for d in orden_dias if d in dias_con_datos]
        dias_extra = [d for d in dias_con_datos if d not in orden_dias]
        dias_ordenados.extend(sorted(dias_extra))
        
        # Ordenar DataFrame
        df_summary['activity_tag'] = pd.Categorical(df_summary['activity_tag'], categories=dias_ordenados, ordered=True)
        df_summary = df_summary.sort_values('activity_tag')
        
        # Obtener etiqueta de la métrica
        parametros = get_available_parameters()
        metrica_label = next((p['label'] for p in parametros if p['value'] == metric), metric)
        
        # Determinar unidad
        unidad = " m" if "(m)" in metrica_label else ""
        
        # Obtener umbrales (usar precargados si están disponibles)
        if umbrales_precargados is not None:
            umbrales_df = umbrales_precargados
        else:
            umbrales_df = get_variable_thresholds(metric)
        
        # Crear gráfico
        fig = go.Figure()
        
        # COLORES EN ESCALA DE AZULES (de claro a oscuro)
        colores_azules = {
            'MD-6': '#A8DADC',  # Azul muy claro
            'MD-5': '#86C5D8',  # Azul claro
            'MD-4': '#64B0D4',  # Azul medio-claro
            'MD-3': '#479FCD',  # Azul medio
            'MD-2': '#2B8DC6',  # Azul medio-oscuro
            'MD-1': '#1E78B4',  # Azul oscuro
            'MD': '#0d3b66'     # Azul marino (más oscuro)
        }
        
        # Para métricas que requieren filtro +70 mins en MD (distancias, aceleraciones, ritmo)
        max_historico_md = None
        if 'MD' in dias_con_datos and metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total', 'ritmo_medio']:
            # Obtener datos MD con filtro de field_time desde tabla intermedia
            df_md_raw = get_microciclo_data_processed(
                microciclo_id=microciclo_id,
                metric_name=metric,
                athlete_ids=atleta_ids_filtro,
                exclude_part_rehab=excluir_part_rehab,
                exclude_goalkeepers=True
            )
            
            if not df_md_raw.empty:
                # Filtrar solo actividades MD
                df_md_filtered = df_md_raw[df_md_raw['activity_tag'] == 'MD'].copy()
                
                if not df_md_filtered.empty and 'field_time' in df_md_filtered.columns:
                    # Filtrar jugadores con +70 minutos (4200 segundos)
                    MIN_FIELD_TIME = 4200
                    df_md_filtered = df_md_filtered[df_md_filtered['field_time'] >= MIN_FIELD_TIME].copy()
                    
                    if not df_md_filtered.empty:
                        # Estandarizar a 94 minutos (5640 segundos) SOLO para distancias y aceleraciones
                        # Ritmo medio NO se estandariza (ya es relativo al minuto)
                        if metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
                            STANDARIZATION_TIME = 5640
                            df_md_filtered['metric_value_std'] = df_md_filtered['metric_value'] * (STANDARIZATION_TIME / df_md_filtered['field_time'])
                            md_actual_promedio = df_md_filtered['metric_value_std'].mean()
                        else:
                            # Para ritmo_medio: solo filtrar +70 mins, no estandarizar
                            md_actual_promedio = df_md_filtered['metric_value'].mean()
                        
                        md_count_filtered = len(df_md_filtered)  # Número de jugadores +70 mins
                        
                        # Actualizar el valor Y el count en df_summary para el MD
                        df_summary.loc[df_summary['activity_tag'] == 'MD', 'avg_metric'] = md_actual_promedio
                        df_summary.loc[df_summary['activity_tag'] == 'MD', 'count_athletes'] = md_count_filtered
        
        # OBTENER MÁX/MÍN HISTÓRICO DE ÚLTIMOS 4 MDs (para porcentajes y líneas naranjas)
        # Siempre usar los precalculados que vienen de cargar_microciclo_ultrarapido_v2()
        max_historico_md = None
        min_historico_md = None
        
        if 'MD' in dias_ordenados and metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
            if maximos_precalculados and metric in maximos_precalculados:
                max_historico_md = maximos_precalculados[metric]['max']
                min_historico_md = maximos_precalculados[metric]['min']
                print(f"✅ Usando máximos precalculados: MAX={max_historico_md:.1f}, MIN={min_historico_md:.1f}")
        
        # Añadir cada día como barra
        for idx, row in df_summary.iterrows():
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
            
            # Determinar visibilidad por defecto (solo días MD-X y MD)
            es_dia_md = bool(re.match(r'^MD[-+]?\d*$', dia))
            visible_por_defecto = True if es_dia_md else 'legendonly'
            
            # Color según el día
            color = colores_azules.get(dia, '#6c757d')  # Gris para otros días
            
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
            
            # Tooltip
            hovertemplate = f"<b>{dia}</b>" + \
                          fecha_str + \
                          f"<br>{metrica_label} (Media): <b>{valor:.1f}{unidad}</b>" + \
                          porcentaje_md + \
                          f"<br>Jugadores: {num_jugadores}<br>" + \
                          "<extra></extra>"
            
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
        
        # AÑADIR UMBRALES POR DÍA (rectángulos verdes con líneas)
        if not umbrales_df.empty:
            umbrales_validos = umbrales_df[
                umbrales_df['min_value'].notna() & 
                umbrales_df['max_value'].notna()
            ].copy()
            
            if not umbrales_validos.empty:
                umbrales_por_dia = {}
                for _, row in umbrales_validos.iterrows():
                    umbrales_por_dia[row['dia']] = {
                        'min': float(row['min_value']),
                        'max': float(row['max_value'])
                    }
                
                umbrales_añadidos = False
                for idx, dia in enumerate(dias_ordenados):
                    if dia in umbrales_por_dia:
                        min_val = umbrales_por_dia[dia]['min']
                        max_val = umbrales_por_dia[dia]['max']
                        
                        # Rectángulo de rango recomendado
                        fig.add_shape(
                            type="rect",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=min_val, y1=max_val,
                            fillcolor="rgba(200, 255, 200, 0.3)",
                            line=dict(width=0),
                            layer="below"
                        )
                        
                        # Línea máximo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=max_val, y1=max_val,
                            line=dict(color="rgba(0, 128, 0, 0.9)", width=3),
                        )
                        
                        # Línea mínimo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=min_val, y1=min_val,
                            line=dict(color="rgba(255, 0, 0, 0.9)", width=3),
                        )
                        
                        umbrales_añadidos = True
                
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
        
        # AÑADIR LÍNEA NARANJA MÁXIMO DE ÚLTIMOS 4 MDs (referencia para %)
        # Solo mostrar el máximo, no el mínimo
        if max_historico_md and 'MD' in dias_ordenados:
            try:
                idx_md = dias_ordenados.index('MD')
                
                # Obtener información del partido del máximo
                partido_max_label = "Máx últimos 4 MDs (100%)"
                if maximos_precalculados and metric in maximos_precalculados:
                    partido_max = maximos_precalculados[metric].get('partido_max')
                    if partido_max:
                        partido_max_label = f"Referencia: {partido_max} (100%)"
                
                # Línea MÁXIMO (naranja) con hover - Esta es la referencia para los porcentajes
                # Añadir línea invisible con hover para mostrar info del partido
                fig.add_trace(go.Scatter(
                    x=['MD'],
                    y=[max_historico_md],
                    mode='lines',
                    line=dict(color="rgba(255, 150, 0, 0.9)", width=3),
                    name=partido_max_label,
                    hovertemplate=f"<b>Máximo de últimos 4 MDs</b><br>" +
                                 (f"Partido: <b>{maximos_precalculados[metric].get('partido_max')}</b><br>" if maximos_precalculados and metric in maximos_precalculados and maximos_precalculados[metric].get('partido_max') else "") +
                                 f"Valor: <b>{max_historico_md:.1f}{unidad}</b><br>" +
                                 "Referencia para los % (100%)<extra></extra>",
                    showlegend=True
                ))
                
            except Exception as e:
                print(f"⚠️ Error añadiendo línea naranja: {e}")
        
        # Layout
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
            barmode='group'
        )
        
        return None, fig
        
    except Exception as e:
        print(f"❌ Error generando gráfico desde tabla intermedia: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"Error: {str(e)}", className="text-center text-danger p-4"), {}

# Función auxiliar para generar tabla y gráfico de Semana Equipo (OPTIMIZADA)
def generar_tabla_y_grafico_equipo(start_date, end_date, metric, atleta_ids_filtro, excluir_part_rehab=True):
    """Genera tabla y gráfico para Semana Equipo (OPTIMIZADO)
    
    Args:
        excluir_part_rehab: Si True, excluye actividades donde participation_type es 'Part' o 'Rehab'
    """
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

    # Obtener participantes CON tags de participación
    participantes = get_participants_for_activities(actividad_ids, include_participation_tags=True)
    if participantes.empty:
        return html.Div("No hay participantes para las actividades seleccionadas.", className="text-center text-muted p-4"), {}
    
    # Filtrar actividades Part/Rehab si corresponde
    if excluir_part_rehab:
        participantes = participantes[
            (participantes['participation_type'].isna()) | 
            (~participantes['participation_type'].isin(['Part', 'Rehab']))
        ]
    
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
        
        # ===== LÓGICA ESPECIAL PARA DÍAS MD (PARTIDOS) =====
        # Identificar actividades MD y aplicar filtrado por field_time + estandarización
        actividades_md = actividades[actividades['grupo_dia'] == 'MD']
        
        if not actividades_md.empty and metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total', 'ritmo_medio']:
            # Obtener activity_ids de MD
            md_activity_ids = actividades_md['id'].tolist()
            
            # Obtener field_time para estos partidos
            field_time_df = get_field_time_for_activities(md_activity_ids, atleta_ids)
            
            if not field_time_df.empty:
                # Filtrar jugadores con más de 70 minutos (4200 segundos)
                MIN_FIELD_TIME = 4200  # 70 minutos en segundos
                field_time_df = field_time_df[field_time_df['field_time'] >= MIN_FIELD_TIME].copy()
                
                # Merge con df_grafico para obtener valores de MD
                df_md = df_grafico[df_grafico['grupo_dia'] == 'MD'].copy()
                df_md = df_md.merge(
                    field_time_df[['activity_id', 'athlete_id', 'field_time']],
                    left_on=['activity_id', 'jugador_id'],
                    right_on=['activity_id', 'athlete_id'],
                    how='inner'  # Solo mantener jugadores con +70 mins
                )
                
                # Estandarizar a 94 minutos (5640 segundos) SOLO para distancias y aceleraciones
                # Ritmo medio NO se estandariza (ya es relativo al minuto)
                if metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
                    STANDARIZATION_TIME = 5640
                    df_md['valor'] = df_md['valor'] * (STANDARIZATION_TIME / df_md['field_time'])
                
                # Actualizar df_grafico: remover MD originales y añadir MD filtrados/estandarizados
                df_grafico = df_grafico[df_grafico['grupo_dia'] != 'MD']
                df_grafico = pd.concat([df_grafico, df_md[['fecha', 'grupo_dia', 'jugador', 'jugador_id', 'valor', 'activity_id', 'activity_name']]], ignore_index=True)
        
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
            
            # Si es MD, añadir el nombre del partido y nota de estandarización
            if dia == "MD":
                if nombres_actividades:
                    tooltip_lines.insert(1, f"<i>{nombres_actividades}</i>")
                # Si es métrica de distancia, indicar que está estandarizado
                if metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
                    tooltip_lines.append("<i>Titulares (+70 mins) estandarizado a 94'</i>")
                elif metric == 'ritmo_medio':
                    tooltip_lines.append("<i>Titulares (+70 mins)</i>")
            
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
        
        # ===== AÑADIR BARRAS DE MÁX/MÍN PARA ÚLTIMOS 4 PARTIDOS MD =====
        if 'MD' in dias_ordenados and metric in ['total_distance', 'distancia_21_kmh', 'distancia_24_kmh', 'acc_dec_total']:
            try:
                # Obtener índice de MD en el eje X
                idx_md = dias_ordenados.index('MD')
                
                # Buscar los últimos 4 partidos MD (incluido el actual) en un rango amplio
                # Extender la búsqueda hacia atrás (ej: 90 días)
                start_historico_ts = start_ts - (90 * 24 * 3600)  # 90 días antes
                actividades_historicas = get_activities_by_date_range(start_historico_ts, end_ts)
                
                if not actividades_historicas.empty:
                    actividades_historicas = add_grupo_dia_column(actividades_historicas)
                    partidos_md = actividades_historicas[actividades_historicas['grupo_dia'] == 'MD'].copy()
                    
                    # Ordenar por fecha descendente y tomar últimos 4
                    partidos_md = partidos_md.sort_values('start_time', ascending=False).head(4)
                    
                    if len(partidos_md) >= 2:  # Al menos 2 partidos para tener máx/mín
                        md_ids_historicos = partidos_md['id'].tolist()
                        
                        # Obtener field_time para estos partidos
                        field_time_hist = get_field_time_for_activities(md_ids_historicos, atleta_ids)
                        
                        if not field_time_hist.empty:
                            MIN_FIELD_TIME = 4200
                            field_time_hist = field_time_hist[field_time_hist['field_time'] >= MIN_FIELD_TIME].copy()
                            
                            # Obtener métricas para estos partidos
                            metricas_hist = get_metrics_for_activities_and_athletes(md_ids_historicos, atleta_ids, metric)
                            
                            # Merge y estandarizar
                            df_hist = metricas_hist.merge(
                                field_time_hist[['activity_id', 'athlete_id', 'field_time']],
                                on=['activity_id', 'athlete_id'],
                                how='inner'
                            )
                            
                            if not df_hist.empty:
                                STANDARIZATION_TIME = 5640
                                df_hist['valor_std'] = df_hist['parameter_value'] * (STANDARIZATION_TIME / df_hist['field_time'])
                                
                                # Calcular promedio por partido
                                promedios_por_partido = df_hist.groupby('activity_id')['valor_std'].mean()
                                
                                # Calcular máx y mín de estos promedios
                                max_valor = promedios_por_partido.max()
                                min_valor = promedios_por_partido.min()
                                
                                # Añadir barras de error (máx/mín) en la barra MD
                                # Rectángulo para rango máx/mín
                                fig.add_shape(
                                    type="rect",
                                    x0=idx_md-0.35, x1=idx_md+0.35,
                                    y0=min_valor, y1=max_valor,
                                    fillcolor="rgba(255, 200, 100, 0.25)",
                                    line=dict(color="rgba(255, 150, 0, 0.6)", width=2),
                                    layer="below"
                                )
                                
                                # Línea de máximo
                                fig.add_shape(
                                    type="line",
                                    x0=idx_md-0.35, x1=idx_md+0.35,
                                    y0=max_valor, y1=max_valor,
                                    line=dict(color="rgba(255, 100, 0, 0.9)", width=3),
                                )
                                
                                # Línea de mínimo
                                fig.add_shape(
                                    type="line",
                                    x0=idx_md-0.35, x1=idx_md+0.35,
                                    y0=min_valor, y1=min_valor,
                                    line=dict(color="rgba(255, 100, 0, 0.9)", width=3),
                                )
                                
                                # Añadir leyenda
                                fig.add_trace(go.Scatter(
                                    x=[None], y=[None],
                                    mode='markers',
                                    marker=dict(size=10, color='rgba(255, 150, 0, 0.8)', symbol='diamond'),
                                    name=f'Máx/Mín últimos {len(promedios_por_partido)} MDs'
                                ))
            except Exception as e:
                print(f"Error calculando máx/mín histórico: {e}")
        
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
    Input("tab-cpe-equipo", "n_clicks"),
    Input("tab-cpe-jugadores", "n_clicks"),
    State("microciclos-store", "data"),
    prevent_initial_call=False
)
def cambiar_pestana(n_clicks_equipo, n_clicks_jugadores, microciclos):
    """Cambia entre las pestañas de Microciclo Equipo y Semana Jugadores (OPTIMIZADO)"""
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
        "width": "50%",
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
        "width": "50%",
        "textAlign": "center"
    }
    
    # Asegurar que microciclos sea una lista
    if not microciclos:
        microciclos = []
    
    # Por defecto mostrar Microciclo Equipo
    if not ctx.triggered:
        return get_microciclo_equipo_content(microciclos), style_active, style_inactive
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "tab-cpe-jugadores":
        return get_semana_jugadores_content(microciclos), style_inactive, style_active
    else:
        return get_microciclo_equipo_content(microciclos), style_active, style_inactive

# ============================================
# CALLBACKS PARA SEMANA JUGADORES
# ============================================

# Callback para cargar datos iniciales y mostrar selector de jugadores
@callback(
    Output("sj-jugadores-container", "style"),
    Output("sj-jugadores-dropdown", "options"),
    Output("sj-jugadores-dropdown", "value"),
    Output("sj-stacked-chart", "figure"),
    Output("sj-part-rehab-store", "data"),
    Input("sj-cargar-btn", "n_clicks"),
    State("sj-date-store", "data"),
    State("sj-metric-dropdown", "value"),
    prevent_initial_call=True
)
def cargar_datos_semana(n_clicks, date_data, metric):
    """Carga datos iniciales y muestra selector de jugadores con los participantes del periodo (OPTIMIZADO)"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return {'display': 'none'}, [], [], {}, []
    
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
    
    # Obtener participantes CON tags de participación
    participantes = get_participants_for_activities(actividad_ids, include_participation_tags=True)
    if participantes.empty:
        return {'display': 'none'}, [], [], {}
    
    # Identificar jugadores que tienen AL MENOS UNA actividad Part/Rehab
    jugadores_con_part_rehab = set()
    for athlete_id in participantes['athlete_id'].unique():
        athlete_participations = participantes[participantes['athlete_id'] == athlete_id]['participation_type'].tolist()
        if 'Rehab' in athlete_participations or 'Part' in athlete_participations:
            jugadores_con_part_rehab.add(athlete_id)
    
    # Obtener jugadores únicos que participaron (usando cache)
    atleta_ids = participantes["athlete_id"].unique().tolist()
    atletas_df = get_cached_athletes()
    atletas_periodo = atletas_df[atletas_df["id"].isin(atleta_ids)].copy()
    
    # Crear opciones del dropdown SIN indicadores por defecto
    jugadores_options = [{'label': row['full_name'], 'value': row['id']} for _, row in atletas_periodo.iterrows()]
    
    # Por defecto: EXCLUIR porteros
    atletas_sin_porteros = atletas_periodo[atletas_periodo['position_name'] != 'Goal Keeper']
    jugadores_ids = atletas_sin_porteros['id'].tolist()
    
    # Generar gráfico inicial sin porteros, excluyendo actividades Part/Rehab
    fig = generar_grafico_semana_jugadores(start_date, end_date, metric, jugadores_ids, excluir_part_rehab=True)
    
    # Mostrar selector de jugadores
    return {'display': 'block'}, jugadores_options, jugadores_ids, fig, list(jugadores_con_part_rehab)

# Callback para añadir/quitar porteros y actualizar indicadores (Semana Jugadores)
@callback(
    Output("sj-jugadores-dropdown", "options", allow_duplicate=True),
    Output("sj-jugadores-dropdown", "value", allow_duplicate=True),
    Input("sj-incluir-porteros", "value"),
    Input("sj-incluir-part-rehab", "value"),
    State("sj-jugadores-dropdown", "options"),
    State("sj-jugadores-dropdown", "value"),
    State("sj-part-rehab-store", "data"),
    prevent_initial_call=True
)
def toggle_filtros_jugadores(incluir_porteros, incluir_part_rehab, current_options, current_value, part_rehab_ids):
    """Añade/quita porteros y actualiza indicadores visuales para Part/Rehab"""
    if not current_options:
        return current_options, current_value or []
    
    # Obtener todos los atletas disponibles
    atletas_df = get_cached_athletes()
    ids_disponibles = [opt['value'] for opt in current_options]
    atletas_disponibles = atletas_df[atletas_df['id'].isin(ids_disponibles)].copy()
    
    # IDs con Part/Rehab
    rehab_ids = set(part_rehab_ids) if part_rehab_ids else set()
    
    # Crear opciones con indicadores si Part/Rehab está marcado
    nuevas_options = []
    for _, row in atletas_disponibles.iterrows():
        label = row['full_name']
        
        # Solo mostrar indicador si checkbox Part/Rehab está marcado Y el jugador tiene Part/Rehab
        if 'incluir' in incluir_part_rehab and row['id'] in rehab_ids:
            label = f"⚠️ {label} (incluyendo entrenamientos rehab)"
        
        nuevas_options.append({'label': label, 'value': row['id']})
    
    # Empezar con la selección actual
    seleccion_actual = set(current_value) if current_value else set()
    
    # Obtener IDs de porteros
    porteros_ids = set(atletas_disponibles[atletas_disponibles['position_name'] == 'Goal Keeper']['id'].tolist())
    
    # Aplicar lógica de añadir/quitar SOLO PORTEROS
    if 'incluir' in incluir_porteros:
        # AÑADIR porteros a la selección actual
        seleccion_actual = seleccion_actual.union(porteros_ids)
    else:
        # QUITAR porteros de la selección actual
        seleccion_actual = seleccion_actual - porteros_ids
    
    # Part/Rehab NO modifica la selección, solo los indicadores y el filtrado en "Aplicar Filtro"
    
    return nuevas_options, list(seleccion_actual)

# Callback para aplicar filtro de jugadores
@callback(
    Output("sj-stacked-chart", "figure", allow_duplicate=True),
    Input("sj-filtrar-btn", "n_clicks"),
    State("sj-date-store", "data"),
    State("sj-metric-dropdown", "value"),
    State("sj-jugadores-dropdown", "value"),
    State("sj-incluir-part-rehab", "value"),
    prevent_initial_call=True
)
def update_semana_jugadores_chart(n_clicks, date_data, metric, jugadores_seleccionados, incluir_part_rehab):
    """Aplica filtro de jugadores seleccionados y regenera gráfico"""
    if not date_data or 'start_date' not in date_data or 'end_date' not in date_data:
        return {}
    
    start_date = date_data['start_date']
    end_date = date_data['end_date']
    
    if not start_date or not end_date or not jugadores_seleccionados:
        return {}
    
    # Determinar si excluir Part/Rehab según checkbox
    excluir_part_rehab = 'incluir' not in incluir_part_rehab
    
    return generar_grafico_semana_jugadores(start_date, end_date, metric, jugadores_seleccionados, excluir_part_rehab=excluir_part_rehab)

# Cache para datos de atletas (evita consultas repetidas)
@lru_cache(maxsize=1)
def get_cached_athletes():
    """Obtiene y cachea la lista de atletas"""
    return get_all_athletes()

# Función auxiliar para generar el gráfico (optimizada)
def generar_grafico_semana_jugadores(start_date, end_date, metric, atleta_ids_filtro, excluir_part_rehab=True):
    """Genera el gráfico de barras apiladas por jugador con colores por día (OPTIMIZADO)
    
    Args:
        excluir_part_rehab: Si True, excluye actividades donde participation_type es 'Part' o 'Rehab'
    """
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
    
    # Obtener participantes CON tags de participación
    participantes = get_participants_for_activities(actividad_ids, include_participation_tags=True)
    if participantes.empty:
        return {}
    
    # Filtrar actividades Part/Rehab si corresponde
    if excluir_part_rehab:
        participantes = participantes[
            (participantes['participation_type'].isna()) | 
            (~participantes['participation_type'].isin(['Part', 'Rehab']))
        ]
    
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
    # Orden: MD, MD+1, MD+2, MD+3, MD-6, MD-5, MD-4, MD-3, MD-2, MD-1, Sin clasificar
    orden_dias_semana = ["MD", "MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "Sin clasificar"]
    dias_ordenados = [d for d in orden_dias_semana if d in df_grouped["grupo_dia"].unique()]
    
    # Añadir cualquier día que no esté en el orden predefinido
    dias_extra = [d for d in df_grouped["grupo_dia"].unique() if d not in orden_dias_semana]
    dias_ordenados.extend(sorted(dias_extra))
    
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
    dias_semana_unicos = df_grouped["grupo_dia"].unique()
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
        'distancia_21_kmh': 'Distancia +21km/h (m)',
        'distancia_24_kmh': 'Distancia +24km/h (m)',
        'acc_dec_total': 'Aceleraciones/Deceleraciones +3',
        'ritmo_medio': 'Ritmo Medio',
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
