"""
Página de Entrenamiento Jugadores (Microciclo Jugadores).
Código extraído de seguimiento_carga.py manteniendo funcionalidad exacta.
"""

from dash import dcc, html, Input, Output, State, callback, dash_table, callback_context, ALL
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash
import plotly.graph_objects as go
import pandas as pd
import json
import re
from datetime import datetime

# Importaciones de utilidades compartidas (NUEVAS)
from utils.entrenamiento_metricas import (
    detectar_tipo_microciclo,
    get_metricas_disponibles,
    get_metricas_config_por_tipo,
    get_cached_athletes
)
from utils.entrenamiento_tablas import generar_tabla_evolutiva
from utils.entrenamiento_graficos import generar_grafico_optimizado_precargado

# Importaciones originales de db_manager
from utils.db_manager import (
    get_db_connection,
    get_all_athletes,
    get_athletes_from_microciclo,
    get_microciclos_from_processed_table,
    get_microciclos,
    get_available_parameters
)

# Importar funciones ultra-optimizadas
from pages.seguimiento_carga_ultra_optimizado import (
    cargar_microciclo_ultrarapido_v2, 
    cargar_tabla_evolutiva_microciclos
)



# Función para obtener el contenido de "Microciclo Jugadores" (contenido actual)
def get_microciclo_jugadores_content(microciclos=None, jugadores=None):
    """Contenido de la pestaña Microciclo Jugadores - Vista individual por jugador"""
    # Usar microciclos y jugadores pasados como parámetro o listas vacías
    if microciclos is None:
        microciclos = []
    if jugadores is None:
        jugadores = []
    
    # Opciones reales (ya no necesitamos placeholders)
    microciclo_options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos] if microciclos else []
    default_microciclo = microciclos[0]['id'] if microciclos else None
    
    jugador_options = [{'label': j['nombre'], 'value': j['id']} for j in jugadores] if jugadores else []
    default_jugador = jugadores[0]['id'] if jugadores else None
    
    # USAR FUNCIÓN CENTRALIZADA PARA MÉTRICAS
    metricas_disponibles = get_metricas_disponibles()
    
    return html.Div([
        # Stores globales
        dcc.Store(id="scj-microciclo-cache", data={}),
        dcc.Store(id="scj-microciclo-loaded", data=False),  # Trigger único para barras
        dcc.Store(id="scj-date-store", data={}),
        dcc.Store(id="scj-part-rehab-store", data=[]),
        dcc.Store(id="scj-selected-metric", data="total_distance"),
        dcc.Store(id="scj-tabla-evolutiva-data", data={}),  # Store para datos de tabla evolutiva
        dcc.Store(id="scj-tabla-evolutiva-cache", data={}),  # Caché de datos evolutivos por jugador
        dcc.Store(id="scj-maximos-jugador-cache", data={}),  # Caché de máximos por jugador (absolutos)
        dcc.Store(id="scj-jugador-seleccionado", data=default_jugador),  # Store para jugador seleccionado,
        
        # SELECTOR DE JUGADOR (PRIMERO - Filtra toda la vista)
        dbc.Card([
            dbc.CardBody([
                html.Label("Selecciona Jugador:", className="form-label", style={
                    'fontWeight': '600',
                    'fontSize': '16px',
                    'color': '#1e3d59',
                    'marginBottom': '12px',
                    'display': 'block'
                }),
                dcc.Dropdown(
                    id="scj-jugador-selector",
                    options=jugador_options,
                    value=default_jugador,
                    clearable=False,
                    placeholder="Selecciona un jugador...",
                    style={'fontSize': '14px'}
                ),
            ])
        ], className="mb-4", style={
            'backgroundColor': '#f0f7ff',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(30,61,89,0.15)',
            'border': '2px solid #1e3d59'
        }),
        
        # TABLA EVOLUTIVA (filtrada por jugador seleccionado)
        dbc.Card([
            dbc.CardBody([
                dcc.Loading(
                    id="scj-loading-tabla-evolutiva",
                    type="default",
                    color="#1e3d59",
                    children=html.Div(id="scj-tabla-evolutiva-container", children=[
                        html.Div("Cargando tabla evolutiva...", className="text-center text-muted p-4")
                    ])
                )
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # PASO 1: Selector de Microciclo (ahora más pequeño)
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
                            id="scj-microciclo-dropdown",
                            options=microciclo_options,
                            value=default_microciclo,
                            clearable=False,
                            placeholder="Selecciona un microciclo...",
                            style={'fontSize': '14px'}
                        ),
                    ], width=12, lg=10),
                    dbc.Col([
                        html.Div([
                            dcc.Loading(
                                id="scj-loading-microciclo",
                                type="circle",
                                color="#1e3d59",
                                children=[
                                    dbc.Button([
                                        html.I(className="fas fa-search me-2"),
                                        "Cargar Datos"
                                    ], id="scj-cargar-microciclo-btn", style={
                                        'backgroundColor': '#1e3d59',
                                        'border': 'none',
                                        'width': '100%',
                                        'padding': '10px'
                                    })
                                ]
                            )
                        ], style={'marginTop': '0'})
                    ], width=12, lg=2)
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
            id="scj-loading-general",
            type="default",
            color="#1e3d59",
            fullscreen=False,
            children=[
                # PASO 2: Seguimiento de Carga del Jugador (TODAS LAS MÉTRICAS)
                html.Div(id="scj-progress-container", style={'display': 'none'}, children=[
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Seguimiento de Carga del Jugador", style={
                                'color': '#1e3d59',
                                'fontWeight': '600',
                                'fontSize': '18px',
                                'marginBottom': '20px'
                            }),
                            html.Div(id="scj-progress-bar-container", children=[
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
        
        # PASO 3: Botones de métricas (sin filtros)
        html.Div(id="scj-metricas-container", style={'display': 'none'}, children=[
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
                                id={'type': 'metric-btn-jugador', 'index': m['id']},
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
                                id={'type': 'metric-btn-jugador', 'index': m['id']},
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
                    ], justify="center")
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
                        id="scj-loading-bar",
                        type="circle",
                        children=[
                            dcc.Graph(id="scj-bar-chart")
                        ]
                    ),
                    # Info del partido del máximo
                    html.Div(id="scj-max-info", className="mt-3", style={
                        'padding': '12px',
                        'backgroundColor': '#f8f9fa',
                        'borderRadius': '8px',
                        'border': '1px solid #dee2e6'
                    })
                ], width=12)
            ])
        ])
    ], className="mb-4", style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'border': 'none'
    }),
    
    # Card con explicación y tabla de partidos (SIEMPRE VISIBLE)
    dbc.Card([
        dbc.CardBody([
            # Sección explicativa
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H5([
                            html.I(className="fas fa-info-circle me-2"),
                            "Cálculo de Máximos Individuales"
                        ], style={'fontSize': '16px', 'fontWeight': '600', 'marginBottom': '15px'}),
                        
                        html.Div([
                            html.P([
                                html.Strong("📊 Referencia 100% = "),
                                "Mejor marca personal de la temporada (partidos +70')"
                            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
                            
                            html.P([
                                html.Strong("⏱️ Partidos considerados: "),
                                html.Span(id="scj-info-partidos", style={'fontStyle': 'italic', 'color': '#0066cc'})
                            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
                            
                            html.P([
                                html.Strong("📈 Valor máximo: "),
                                html.Span(id="scj-info-maximo", style={'fontStyle': 'italic', 'color': '#0066cc'})
                            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
                            
                            html.P([
                                html.Strong("🔄 Estandarización: "),
                                "Todos los valores → 94 minutos"
                            ], style={'marginBottom': '8px', 'fontSize': '14px'}),
                            
                            html.P([
                                html.Strong("📉 Carga semanal: "),
                                "Entrenamientos = % del máximo (sin Part/Rehab)"
                            ], style={'marginBottom': '0', 'fontSize': '14px'}),
                        ])
                    ], color="info", style={
                        'marginBottom': '20px',
                        'borderLeft': '4px solid #17a2b8'
                    })
                ], width=12)
            ]),
            
            # Tabla de partidos considerados
            dbc.Row([
                dbc.Col([
                    html.Div(id="scj-tabla-partidos-container")
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
                id="scj-toggle-datos-btn",
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
    
    # Card para datos detallados (OCULTA por defecto)
    html.Div(
        dbc.Card([
            dbc.CardBody([
                # Datos detallados
                dbc.Row([
                    dbc.Col([
                        html.H5("Datos detallados de rendimiento", style={
                            'color': '#1e3d59',
                            'fontWeight': '600',
                            'fontSize': '18px',
                            'marginBottom': '20px'
                        }),
                        dcc.Loading(
                            id="scj-loading-table",
                            type="circle",
                            children=[
                                html.Div(id="scj-table-container")
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
        id="scj-datos-detallados-container",
        style={"display": "none"}  # Oculto por defecto
    )
        ]
    )  # Cierre del dcc.Loading general
])



# CALLBACK ELIMINADO: microciclos-store es compartido globalmente
# y ya se carga en otras páginas. No necesitamos duplicar este callback.


# CALLBACKS ELIMINADOS para romper dependencia circular
# La carga de jugadores se hará de forma estática en el layout


# Callback para cargar tabla evolutiva CON CACHÉ
@callback(
    Output("scj-tabla-evolutiva-container", "children"),
    Output("scj-tabla-evolutiva-data", "data"),
    Output("scj-tabla-evolutiva-cache", "data"),
    Input("scj-jugador-selector", "value"),
    State("scj-tabla-evolutiva-cache", "data"),
    prevent_initial_call=True  # Evitar carga automática innecesaria
)
def cargar_tabla_evolutiva_jugador(jugador_id, cache_evolutivo):
    """
    Carga la tabla evolutiva de UN SOLO JUGADOR con caché.
    Se ejecuta al cargar la página y cuando el usuario cambia de jugador.
    """
    if not jugador_id or jugador_id == '':
        return (
            html.Div("Selecciona un jugador para ver su evolución", 
                    className="text-muted text-center p-4"),
            {},
            cache_evolutivo or {}
        )
    
    # Verificar caché primero
    cache_evolutivo = cache_evolutivo or {}
    
    if jugador_id in cache_evolutivo:
        datos_cached = cache_evolutivo[jugador_id]
        tabla = generar_tabla_evolutiva(datos_cached)
        return tabla, datos_cached, cache_evolutivo
    
    # Caché MISS: cargar desde BD
    
    try:
        datos_evolutivos = cargar_tabla_evolutiva_microciclos(jugadores_ids=[jugador_id])
        
        if not datos_evolutivos:
            return (
                html.Div("No hay datos disponibles", className="text-muted text-center p-4"),
                {},
                cache_evolutivo
            )
        
        # Generar tabla
        tabla = generar_tabla_evolutiva(datos_evolutivos)
        
        # Guardar en caché
        cache_evolutivo[jugador_id] = datos_evolutivos
        
        return tabla, datos_evolutivos, cache_evolutivo
        
    except Exception as e:
        return (
            html.Div(f"Error al cargar tabla evolutiva: {str(e)}", 
                    className="text-danger text-center p-4"),
            {},
            cache_evolutivo or {}
        )


# CALLBACK ELIMINADO: cargar_tabla_inicial
# Era redundante y causaba cargas innecesarias. 
# El callback principal cargar_tabla_evolutiva_jugador ya maneja la carga inicial.


# Callback para cambiar microciclo desde tabla evolutiva (click en celdas)
@callback(
    Output("scj-microciclo-dropdown", "value", allow_duplicate=True),
    Output("scj-cargar-microciclo-btn", "n_clicks", allow_duplicate=True),
    Input({'type': 'tabla-evolutiva-celda', 'microciclo_id': ALL, 'metrica_id': ALL}, 'n_clicks'),
    Input({'type': 'tabla-evolutiva-header', 'microciclo_id': ALL}, 'n_clicks'),
    State({'type': 'tabla-evolutiva-celda', 'microciclo_id': ALL, 'metrica_id': ALL}, 'id'),
    State({'type': 'tabla-evolutiva-header', 'microciclo_id': ALL}, 'id'),
    State("scj-cargar-microciclo-btn", "n_clicks"),
    prevent_initial_call=True
)
def cambiar_microciclo_desde_tabla(clicks_celdas, clicks_headers, ids_celdas, ids_headers, current_n_clicks):
    """Permite cambiar el microciclo seleccionado haciendo click en la tabla evolutiva"""
    ctx = dash.callback_context
    
    if not ctx.triggered:
        raise PreventUpdate
    
    # Obtener el ID del elemento que disparó el callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if triggered_id == '':
        raise PreventUpdate
    
    try:
        # Parsear el ID (es un JSON string)
        triggered_dict = json.loads(triggered_id)
        microciclo_id = triggered_dict.get('microciclo_id')
        
        if microciclo_id:
            # Incrementar n_clicks para forzar recarga automática
            new_n_clicks = (current_n_clicks or 0) + 1
            return microciclo_id, new_n_clicks
    
    except Exception as e:
        raise PreventUpdate
    
    raise PreventUpdate


def generar_info_maximo(metrica, cache_data):
    """
    Genera el componente visual con la información del partido que fija el máximo.
    """
    maximos = cache_data.get('maximos_historicos', {})
    max_info = maximos.get(metrica, {})
    
    # Validar que tiene datos
    if not max_info:
        return html.Div("Sin datos de máximo histórico", style={'color': '#6c757d', 'fontSize': '14px'})
    
    # Verificar si tiene_datos existe y es True
    tiene_datos = max_info.get('tiene_datos', True)  # Por defecto True si no existe (para compatibilidad)
    if not tiene_datos:
        return html.Div("Sin datos de máximo histórico para este jugador", style={'color': '#6c757d', 'fontSize': '14px'})
    
    partido_max = max_info.get('partido_max', 'N/A')
    fecha_max = max_info.get('fecha_max')
    num_partidos = max_info.get('num_partidos', 0)
    max_valor = max_info.get('max')
    warning = max_info.get('warning')
    
    # Formatear fecha
    if fecha_max:
        from datetime import datetime
        try:
            if isinstance(fecha_max, str):
                fecha_obj = datetime.strptime(str(fecha_max)[:10], '%Y-%m-%d')
            else:
                fecha_obj = fecha_max
            fecha_str = fecha_obj.strftime('%d/%m/%Y')
        except:
            fecha_str = str(fecha_max)
    else:
        fecha_str = 'N/A'
    
    # Nombres de métricas
    nombres_metricas = {
        'total_distance': 'Distancia Total',
        'distancia_21_kmh': 'Distancia +21 km/h',
        'distancia_24_kmh': 'Distancia +24 km/h',
        'acc_dec_total': 'Aceleraciones +3',
        'ritmo_medio': 'Ritmo Medio'
    }
    
    return html.Div([
        html.Div([
            html.I(className="fas fa-trophy me-2", style={'color': '#ffc107'}),
            html.Strong("Máximo Histórico:", style={'color': '#495057'}),
            html.Span(f" {max_valor:.1f}" if max_valor else " N/A", style={'color': '#1e3d59', 'fontWeight': '600', 'marginLeft': '8px'})
        ], style={'marginBottom': '8px'}),
        html.Div([
            html.I(className="fas fa-futbol me-2", style={'color': '#28a745'}),
            html.Strong("Partido:", style={'color': '#495057'}),
            html.Span(f" {partido_max}", style={'marginLeft': '8px'})
        ], style={'marginBottom': '8px'}),
        html.Div([
            html.I(className="fas fa-calendar me-2", style={'color': '#17a2b8'}),
            html.Strong("Fecha:", style={'color': '#495057'}),
            html.Span(f" {fecha_str}", style={'marginLeft': '8px'})
        ], style={'marginBottom': '8px'}),
        html.Div([
            html.I(className="fas fa-info-circle me-2", style={'color': '#6c757d'}),
            html.Span(f"Basado en {num_partidos} partido(s) +70' desde inicio temporada (10/08/2025)", style={'color': '#6c757d', 'fontSize': '13px'})
        ]) if num_partidos > 0 else None,
        dbc.Alert(warning, color="warning", className="mt-2 mb-0", style={'fontSize': '13px'}) if warning else None
    ], style={'fontSize': '14px'})


# Callback principal: Cargar y cachear TODAS las métricas del jugador en el microciclo
@callback(
    Output("scj-microciclo-cache", "data"),
    Output("scj-microciclo-loaded", "data"),
    Output("scj-metricas-container", "style"),
    Output("scj-maximos-jugador-cache", "data"),
    Input("scj-cargar-microciclo-btn", "n_clicks"),
    State("scj-microciclo-dropdown", "value"),
    State("scj-jugador-selector", "value"),
    State("scj-tabla-evolutiva-data", "data"),  # ✅ Datos de la tabla
    State("scj-maximos-jugador-cache", "data"),  # Caché de máximos
    State("scj-date-store", "data"),
    prevent_initial_call=True
)
def cargar_microciclo_jugador(n_clicks, microciclo_id, jugador_id, datos_tabla, cache_maximos, date_data):
    """
    Carga datos de UN SOLO JUGADOR en el microciclo seleccionado.
    ♻️ REUTILIZA máximos ya calculados en la tabla (optimizado).
    """
    if not microciclo_id or not jugador_id:
        return {}, False, {'display': 'none'}, cache_maximos or {}
    
    try:
        # Cargar datos del microciclo (actividades por día)
        resultado_raw = cargar_microciclo_ultrarapido_v2(microciclo_id, [jugador_id])
        
        if not resultado_raw:
            raise Exception("No se pudieron cargar los datos")
        
        datos_por_metrica = resultado_raw['datos_por_metrica']
        nombre_partido = resultado_raw.get('nombre_partido')
        
        # 🎯 REUTILIZAR MÁXIMOS del caché (si existen)
        # Los máximos son absolutos, no cambian por microciclo
        from pages.seguimiento_carga_ultra_optimizado import calcular_maximo_individual_jugador
        
        cache_maximos = cache_maximos or {}
        
        # Verificar si ya tenemos los máximos en caché
        if jugador_id in cache_maximos:
            ultimos_4_mds_por_metrica = cache_maximos[jugador_id]
        else:
            # Caché MISS: Calcular máximos
            ultimos_4_mds_por_metrica = {}
            metricas_a_calcular = {
                'total_distance': 'total_distance',
                'distancia_21_kmh': 'distancia_+21_km/h_(m)',
                'distancia_24_kmh': 'distancia_+24_km/h_(m)',
                'acc_dec_total': 'gen2_acceleration_band7plus_total_effort_count',
                'ritmo_medio': 'average_player_load'
            }
            
            # Calcular todos los máximos
            for metrica_dash, metrica_bd in metricas_a_calcular.items():
                max_individual = calcular_maximo_individual_jugador(
                    jugador_id, 
                    metrica_bd, 
                    None  # Sin fecha = máximo absoluto
                )
                ultimos_4_mds_por_metrica[metrica_dash] = max_individual
            
            # Guardar en caché
            cache_maximos[jugador_id] = ultimos_4_mds_por_metrica
        
        # Generar gráficos de forma ultra-optimizada
        
        # Detectar tipo de microciclo ANTES de generar gráficos (1 sola vez)
        dias_presentes = []
        for metrica, df_resumen in datos_por_metrica.items():
            if not df_resumen.empty:
                dias_presentes = df_resumen['activity_tag'].unique().tolist()
                break
        
        tipo_microciclo = detectar_tipo_microciclo(dias_presentes)
        
        # Añadir tipo al diccionario de máximos históricos para pasarlo a los gráficos
        ultimos_4_mds_con_tipo = {}
        for metrica, datos in ultimos_4_mds_por_metrica.items():
            if datos:
                ultimos_4_mds_con_tipo[metrica] = {**datos, 'tipo_microciclo': tipo_microciclo}
            else:
                ultimos_4_mds_con_tipo[metrica] = {'tipo_microciclo': tipo_microciclo}
        
        # Obtener parámetros una sola vez (no 6 veces)
        parametros = get_available_parameters()
        parametros_dict = {p['value']: p['label'] for p in parametros}
        
        graficos_metricas = {}
        for metrica, df_resumen in datos_por_metrica.items():
            try:
                # Generar gráfico con función optimizada (tipo ya incluido en máximos)
                fig = generar_grafico_optimizado_precargado(
                    df_resumen,
                    metrica,
                    parametros_dict.get(metrica, metrica),
                    ultimos_4_mds_con_tipo.get(metrica),
                    None,  # umbrales_df no necesario (hardcodeados)
                    nombre_partido
                )
                graficos_metricas[metrica] = fig
            except Exception as e:
                pass
        
        # Cache optimizado CON TODAS LAS MÉTRICAS PRE-CARGADAS DEL JUGADOR
        cache_optimizado = {
            'microciclo_id': microciclo_id,
            'jugador_id': jugador_id,  # ← Jugador individual
            'cargado': True,
            'graficos': graficos_metricas,  # ← TODAS las figuras listas
            'maximos_historicos': ultimos_4_mds_por_metrica,  # ← Máximos precalculados
            'tipo_microciclo': tipo_microciclo,  # ← Tipo detectado
            'dias_presentes': dias_presentes  # ← Días disponibles
        }
        
        # Generar timestamp único para trigger
        import time
        timestamp = time.time()
        
        return (
            cache_optimizado,
            timestamp,  # Trigger para cargar barras
            {'display': 'block'},
            cache_maximos  # Devolver caché actualizado
        )
        
    except Exception as e:
        return {}, False, {'display': 'none'}, cache_maximos or {}

# Callback para cargar y mostrar métrica inicial
@callback(
    Output("scj-bar-chart", "figure"),
    Output("scj-selected-metric", "data"),
    Output("scj-progress-container", "style"),
    Output("scj-max-info", "children"),
    Input("scj-microciclo-loaded", "data"),
    State("scj-microciclo-cache", "data"),
    prevent_initial_call=True
)
def cargar_metrica_inicial(loaded_timestamp, cache_data):
    """Muestra el gráfico de la primera métrica (Distancia Total) desde el cache
    
    Los datos YA están cargados en cache_data['graficos']
    """
    if not loaded_timestamp or not cache_data or not cache_data.get('cargado'):
        return {}, "total_distance", {'display': 'none'}, None
    
    # Obtener figura desde el cache (ya está cargada)
    graficos = cache_data.get('graficos', {})
    fig = graficos.get('total_distance', {})
    
    # Obtener info del máximo
    max_info = generar_info_maximo('total_distance', cache_data)
    
    if fig:
        return fig, "total_distance", {'display': 'block'}, max_info
    return {}, "total_distance", {'display': 'none'}, None

# Callback para cambiar entre métricas usando botones (carga on-demand con cache inteligente)
@callback(
    Output("scj-bar-chart", "figure", allow_duplicate=True),
    Output("scj-selected-metric", "data", allow_duplicate=True),
    Output("scj-max-info", "children", allow_duplicate=True),
    Input({'type': 'metric-btn-jugador', 'index': ALL}, 'n_clicks'),
    State("scj-microciclo-cache", "data"),
    prevent_initial_call=True
)
def cambiar_metrica(n_clicks_list, cache_data):
    """Cambia la métrica mostrada leyendo desde el cache
    
    Los datos YA están cargados en cache_data['graficos']
    NO hace queries adicionales = INSTANTÁNEO
    Sin filtros de usuario - usa datos pre-cargados
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
    
    # Obtener info del máximo
    max_info = generar_info_maximo(metrica_seleccionada, cache_data)
    
    if fig:
        return fig, metrica_seleccionada, max_info
    
    raise PreventUpdate

# Callback para actualizar estilos de botones de métricas
@callback(
    Output({'type': 'metric-btn-jugador', 'index': ALL}, 'style'),
    Input("scj-selected-metric", "data")
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


# Callback para generar tabla de partidos considerados
@callback(
    Output("scj-tabla-partidos-container", "children"),
    Input("scj-microciclo-loaded", "data"),
    State("scj-microciclo-cache", "data"),
    State("scj-selected-metric", "data"),
    prevent_initial_call=True
)
def generar_tabla_partidos(loaded_timestamp, cache_data, metrica_actual):
    """Genera tabla con todos los partidos considerados para el cálculo de máximos"""
    if not loaded_timestamp or not cache_data or not cache_data.get('cargado'):
        return html.Div()
    
    # Obtener máximos históricos del cache
    maximos_historicos = cache_data.get('maximos_historicos', {})
    
    # Usar la métrica actual o la primera disponible
    metrica_key = metrica_actual if metrica_actual else 'total_distance'
    
    if metrica_key not in maximos_historicos:
        return html.Div()
    
    maximo_info = maximos_historicos[metrica_key]
    partidos_detalle = maximo_info.get('partidos_detalle', [])
    
    if not partidos_detalle:
        return html.Div([
            html.P([
                html.I(className="fas fa-info-circle me-2"),
                "No hay información de partidos disponible para este jugador."
            ], style={
                'color': '#6c757d',
                'fontStyle': 'italic',
                'marginTop': '10px'
            })
        ])
    
    # Crear tabla
    from datetime import datetime
    
    tabla_rows = []
    for partido in partidos_detalle:
        fecha = partido['fecha']
        nombre = partido['partido']
        minutos = partido['minutos']
        valor_metrica = partido.get('valor_metrica', 0)
        candidato = partido['candidato']
        
        # Formatear fecha
        try:
            if isinstance(fecha, str):
                fecha_obj = datetime.strptime(str(fecha).split()[0], '%Y-%m-%d')
                fecha_formatted = fecha_obj.strftime('%d/%m')
            else:
                fecha_formatted = str(fecha)
        except:
            fecha_formatted = str(fecha)
        
        # Determinar estado y color
        if minutos >= 70:
            estado = "✅ SÍ"
            color_fondo = "#d4edda"  # Verde claro
            color_texto = "#155724"
            valor_std = valor_metrica * (5640 / (minutos * 60)) if minutos > 0 else 0
        elif minutos > 0:
            estado = "❌ NO"
            color_fondo = "#fff3cd"  # Amarillo claro
            color_texto = "#856404"
            valor_std = 0
        else:
            estado = "❌ NO"
            color_fondo = "#f8d7da"  # Rojo claro
            color_texto = "#721c24"
            valor_std = 0
        
        tabla_rows.append(
            html.Tr([
                html.Td(fecha_formatted, style={'padding': '10px', 'borderBottom': '1px solid #dee2e6', 'fontSize': '13px'}),
                html.Td(nombre, style={'padding': '10px', 'borderBottom': '1px solid #dee2e6', 'fontWeight': '500', 'fontSize': '13px'}),
                html.Td(f"{minutos:.0f}'", style={'padding': '10px', 'borderBottom': '1px solid #dee2e6', 'textAlign': 'center', 'fontSize': '13px', 'fontWeight': '600'}),
                html.Td(f"{valor_std:.0f}m" if valor_std > 0 else "-", style={
                    'padding': '10px',
                    'borderBottom': '1px solid #dee2e6',
                    'textAlign': 'center',
                    'fontSize': '13px',
                    'fontWeight': '600',
                    'color': '#0066cc' if valor_std > 0 else '#999'
                }),
                html.Td(estado, style={
                    'padding': '10px',
                    'borderBottom': '1px solid #dee2e6',
                    'textAlign': 'center',
                    'backgroundColor': color_fondo,
                    'color': color_texto,
                    'fontWeight': '600',
                    'fontSize': '13px'
                })
            ])
        )
    
    tabla = html.Table([
        html.Thead(
            html.Tr([
                html.Th("Fecha", style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6', 'fontWeight': '600', 'fontSize': '13px'}),
                html.Th("Partido", style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6', 'fontWeight': '600', 'fontSize': '13px'}),
                html.Th("Min", style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6', 'fontWeight': '600', 'textAlign': 'center', 'fontSize': '13px'}),
                html.Th("Valor (94')", style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6', 'fontWeight': '600', 'textAlign': 'center', 'fontSize': '13px'}),
                html.Th("Usado", style={'padding': '10px', 'backgroundColor': '#f8f9fa', 'borderBottom': '2px solid #dee2e6', 'fontWeight': '600', 'textAlign': 'center', 'fontSize': '13px'})
            ])
        ),
        html.Tbody(tabla_rows)
    ], style={
        'width': '100%',
        'borderCollapse': 'collapse',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'borderRadius': '8px',
        'overflow': 'hidden',
        'fontSize': '13px'
    })
    
    return html.Div([
        html.H6([
            html.I(className="fas fa-calculator me-2"),
            "Cálculo del Máximo Individual"
        ], style={
            'color': '#1e3d59',
            'fontWeight': '600',
            'marginBottom': '12px',
            'fontSize': '15px'
        }),
        tabla
    ])


# Callback para actualizar información de máximos individuales
@callback(
    Output("scj-info-partidos", "children"),
    Output("scj-info-maximo", "children"),
    Input("scj-microciclo-loaded", "data"),
    State("scj-microciclo-cache", "data"),
    State("scj-selected-metric", "data"),
    prevent_initial_call=True
)
def actualizar_info_maximos(loaded_timestamp, cache_data, metrica_actual):
    """Actualiza la información sobre cómo se calculan los máximos del jugador"""
    if not loaded_timestamp or not cache_data or not cache_data.get('cargado'):
        return "Cargando...", "Cargando..."
    
    # Obtener máximos históricos del cache
    maximos_historicos = cache_data.get('maximos_historicos', {})
    
    # Usar la métrica actual o la primera disponible
    metrica_key = metrica_actual if metrica_actual else 'total_distance'
    
    if metrica_key in maximos_historicos:
        maximo_info = maximos_historicos[metrica_key]
        partido_max = maximo_info.get('partido_max', 'N/A')
        fecha_max = maximo_info.get('fecha_max', 'N/A')
        max_val = maximo_info.get('max', 0)
        num_partidos = maximo_info.get('num_partidos', 0)
        warning = maximo_info.get('warning', '')
        
        # Formatear fecha
        try:
            from datetime import datetime
            if isinstance(fecha_max, str):
                fecha_obj = datetime.strptime(str(fecha_max).split()[0], '%Y-%m-%d')
                fecha_formatted = fecha_obj.strftime('%d/%m/%Y')
            else:
                fecha_formatted = str(fecha_max)
        except:
            fecha_formatted = str(fecha_max)
        
        # Información de partidos según el número encontrado
        if num_partidos >= 4:
            info_partidos = f"✅ {num_partidos} partidos con +70' encontrados en las últimas 4 jornadas del equipo."
        elif num_partidos > 0:
            info_partidos = f"⚠️ Solo {num_partidos} partido(s) con +70' en las últimas 4 jornadas. Se buscó hacia atrás en la temporada."
        else:
            info_partidos = "🔴 Sin partidos +70'. Se usa el partido donde jugó más minutos."
        
        # Información del máximo
        if max_val and max_val > 0:
            info_maximo = f"{max_val:.1f}m en {partido_max} ({fecha_formatted})"
            
            # Añadir información adicional si hay warning
            if warning and '🔴' in warning:
                info_maximo += " - ⚠️ Referencia limitada: sin partidos +70'"
            elif num_partidos < 4:
                info_maximo += f" - ⚠️ Solo {num_partidos} partido(s) +70'"
        else:
            info_maximo = "No disponible - Jugador sin datos de partidos"
        
        return info_partidos, info_maximo
    
    return "Datos no disponibles", "Datos no disponibles"


# Callback para mostrar/ocultar tabla detallada
@callback(
    Output("scj-datos-detallados-container", "style"),
    Output("scj-toggle-datos-btn", "children"),
    Input("scj-toggle-datos-btn", "n_clicks"),
    State("scj-datos-detallados-container", "style"),
    prevent_initial_call=True
)
def toggle_tabla_detallada_jugador(n_clicks, current_style):
    """Muestra u oculta la tabla de datos detallados"""
    if current_style.get("display") == "none":
        return {"display": "block"}, [html.I(className="fas fa-eye-slash me-2"), "Ocultar datos detallados"]
    else:
        return {"display": "none"}, [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"]


# Callback para cargar tabla detallada
@callback(
    Output("scj-table-container", "children"),
    Input("scj-selected-metric", "data"),
    State("scj-microciclo-cache", "data"),
    prevent_initial_call=True
)
def cargar_tabla_detallada(metrica_seleccionada, cache_data):
    """Carga la tabla detallada de la métrica seleccionada desde el cache"""
    if not cache_data or not cache_data.get('cargado') or not metrica_seleccionada:
        return html.Div("No hay datos disponibles", className="text-muted text-center p-4")
    
    # Obtener figura desde el cache
    graficos = cache_data.get('graficos', {})
    fig = graficos.get(metrica_seleccionada)
    
    if not fig:
        return html.Div("No hay datos disponibles para esta métrica", className="text-muted text-center p-4")
    
    # Extraer datos de la figura para crear tabla
    try:
        datos_tabla = []
        for trace in fig.get('data', []):
            dia = trace.get('name', '').split(' ')[0]
            valor = trace.get('y', [0])[0] if trace.get('y') else 0
            if dia and dia.startswith('MD-'):
                datos_tabla.append({'Día': dia, 'Valor': f"{valor:.1f}"})
        
        if not datos_tabla:
            return html.Div("No hay datos disponibles", className="text-muted text-center p-4")
        
        # Crear tabla con dash_table
        import pandas as pd
        df_tabla = pd.DataFrame(datos_tabla)
        
        return dash_table.DataTable(
            data=df_tabla.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df_tabla.columns],
            style_cell={
                'textAlign': 'center',
                'padding': '12px',
                'fontSize': '14px'
            },
            style_header={
                'backgroundColor': '#1e3d59',
                'color': 'white',
                'fontWeight': '600',
                'fontSize': '14px'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )
    except Exception as e:
        print(f"❌ Error generando tabla: {e}")
        return html.Div("Error al generar tabla", className="text-danger text-center p-4")


# Callback para generar barras de progreso de TODAS las métricas
@callback(
    Output("scj-progress-bar-container", "children"),
    Input("scj-microciclo-loaded", "data"),
    State("scj-microciclo-cache", "data"),
    prevent_initial_call=True
)
def generar_barras_todas_metricas(loaded_timestamp, cache_data):
    """Genera barras de progreso para TODAS las métricas del microciclo
    
    USA DATOS DEL CACHE - NO HACE QUERIES ADICIONALES
    """
    if not loaded_timestamp or not cache_data or not cache_data.get('cargado'):
        return html.Div()
    
    # Obtener tipo de microciclo del cache
    tipo_microciclo = cache_data.get('tipo_microciclo', 'estandar')
    
    # Configuración de métricas con umbrales según tipo de microciclo
    metricas_config = get_metricas_config_por_tipo(tipo_microciclo)
    
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
            
            # Determinar si es métrica de suma o media
            es_media = config.get('tipo') == 'media'
            
            # Extraer valores de las barras del gráfico
            valores_entrenamientos = []
            valores_absolutos = []  # Para logging
            for trace in fig.get('data', []):
                dia = trace.get('name', '').split(' ')[0]  # Quitar porcentaje si existe
                if dia and dia.startswith('MD-'):
                    valor = trace.get('y', [0])[0] if trace.get('y') else 0
                    # Solo procesar si tenemos valor y máximo histórico válidos
                    if valor and valor > 0 and max_historico and max_historico > 0:
                        porcentaje = (valor / max_historico) * 100
                        valores_entrenamientos.append(porcentaje)
                        valores_absolutos.append(valor)
                        entrenamientos_con_porcentaje.append({
                            'nombre': dia,
                            'porcentaje': porcentaje,
                            'color': colores_dias.get(dia, '#6c757d')
                        })
            
            # Ordenar días correctamente (MD-4, MD-3, MD-2, MD-1)
            entrenamientos_con_porcentaje.sort(key=lambda x: x['nombre'], reverse=True)
            
            # Calcular acumulado según tipo de métrica
            if es_media and valores_entrenamientos:
                acumulado_total = sum(valores_entrenamientos) / len(valores_entrenamientos)
            else:
                acumulado_total = sum(valores_entrenamientos)
            
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
            
            # Para métricas de MEDIA: mostrar barra única sin segmentos
            if es_media:
                barra_contenido = html.Div(
                    f"{acumulado_total:.0f}%",
                    style={
                        'width': f"{min(100, (acumulado_total / config['max']) * 100)}%",
                        'backgroundColor': '#1e3d59',  # Azul marino siempre
                        'color': 'white',
                        'fontSize': '13px',
                        'fontWeight': '600',
                        'textAlign': 'center',
                        'lineHeight': '40px',
                        'textShadow': '0 0 3px rgba(0,0,0,0.5)',
                        'height': '100%',
                        'borderRadius': '6px 0 0 6px'
                    }
                )
            else:
                # Para métricas de SUMA: mostrar segmentos por día
                barra_contenido = [
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
                ]
            
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
                            # Barra (única para media, segmentada para suma)
                            html.Div(
                                barra_contenido,
                                style={
                                    'height': '40px',
                                    'backgroundColor': '#e9ecef',
                                    'borderRadius': '6px',
                                    'display': 'flex' if not es_media else 'block',
                                    'position': 'relative'
                                }
                            ),
                            # Línea del mínimo (roja)
                            html.Div(style={
                                'position': 'absolute',
                                'left': f'{pos_min}%',
                                'top': '0',
                                'width': '2px',
                                'height': '40px',
                                'backgroundColor': '#dc3545',
                                'zIndex': '5'
                            }),
                            # Línea del máximo (roja)
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
                                'color': '#dc3545',
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
            
        except Exception as e:
            continue
    
    # Retornar todas las barras
    if barras_html:
        return html.Div(barras_html)
    else:
        return html.Div("No hay datos suficientes para mostrar el seguimiento de carga", 
                       className="text-muted text-center p-3")


# ============================================
# LAYOUT DE LA PÁGINA
# ============================================

# Función para cargar datos estáticamente
def cargar_datos_iniciales():
    """Carga microciclos y jugadores de forma estática"""
    try:
        # Cargar microciclos
        microciclos = get_microciclos_from_processed_table()
        if not microciclos:
            microciclos = get_microciclos()
        
        # Cargar jugadores
        engine = get_db_connection()
        query = '''
            SELECT DISTINCT athlete_id, athlete_name, athlete_position
            FROM microciclos_metricas_procesadas
            WHERE activity_date >= '2024-08-01'
              AND athlete_position != 'Goal Keeper'
            ORDER BY athlete_name
        '''
        df_jugadores = pd.read_sql(query, engine)
        engine.dispose()
        
        jugadores = []
        if not df_jugadores.empty:
            jugadores = [
                {
                    'id': row['athlete_id'],
                    'nombre': f"{row['athlete_name']} ({row['athlete_position']})",
                    'posicion': row['athlete_position']
                }
                for _, row in df_jugadores.iterrows()
            ]
        
        return microciclos, jugadores
    except Exception as e:
        return [], []

# Cargar datos al importar el módulo
MICROCICLOS_ESTATICOS, JUGADORES_ESTATICOS = cargar_datos_iniciales()

layout = html.Div([
    # Stores globales con datos precargados
    dcc.Store(id='microciclos-store', data=MICROCICLOS_ESTATICOS),
    dcc.Store(id='jugadores-store', data=JUGADORES_ESTATICOS),
    dcc.Store(id='scj-date-store', data={}),
    
    dbc.Container([
        # Card contenedor principal con fondo blanco
        dbc.Card([
            dbc.CardBody([
                # Título de la sección
                html.H3("CONTROL PROCESO ENTRENAMIENTO - Entrenamiento Jugadores", 
                       className="mb-4", 
                       style={
                           'color': '#1e3d59',
                           'fontWeight': '700',
                           'fontSize': '24px',
                           'textAlign': 'center',
                           'borderBottom': '2px solid #1e3d59',
                           'paddingBottom': '15px',
                           'marginBottom': '25px'
                       }),
                
                # Contenido estático (sin loading dinámico)
                get_microciclo_jugadores_content(MICROCICLOS_ESTATICOS, JUGADORES_ESTATICOS)
            ], style={'padding': '30px'})
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '15px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
            'border': 'none',
            'marginTop': '20px'
        })
    ], fluid=True, className="py-4", style={'backgroundColor': '#f8f9fa'})
])