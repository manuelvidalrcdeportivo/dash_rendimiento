"""
Página de Entrenamiento Equipo (Microciclo Equipo).
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

# Importar función ultra-optimizada (MANTENER IGUAL)
from pages.seguimiento_carga_ultra_optimizado import cargar_microciclo_ultrarapido_v2, cargar_tabla_evolutiva_microciclos



# Función para obtener el contenido de "Microciclo Equipo" (contenido actual)
def get_microciclo_equipo_content(microciclos=None):
    """Contenido de la pestaña Microciclo Equipo - Vista con cacheo de datos"""
    # Usar microciclos pasados como parámetro o lista vacía
    if microciclos is None:
        microciclos = []
    microciclo_options = [{'label': mc['label'], 'value': mc['id']} for mc in microciclos]
    default_microciclo = microciclos[0]['id'] if microciclos else None
    
    # USAR FUNCIÓN CENTRALIZADA PARA MÉTRICAS
    metricas_disponibles = get_metricas_disponibles()
    
    return html.Div([
        # Stores globales
        dcc.Store(id="sc-microciclo-cache", data={}),
        dcc.Store(id="sc-microciclo-loaded", data=False),  # Trigger único para barras
        dcc.Store(id="sc-date-store", data={}),
        dcc.Store(id="sc-part-rehab-store", data=[]),
        dcc.Store(id="sc-selected-metric", data="total_distance"),
        dcc.Store(id="sc-tabla-evolutiva-data", data={}),  # Store para datos de tabla evolutiva
        
        # TABLA EVOLUTIVA (al inicio, antes del selector)
        dbc.Card([
            dbc.CardBody([
                html.Div(id="sc-tabla-evolutiva-container", children=[
                    html.Div([
                        dcc.Loading(
                            type="circle",
                            color="#1e3d59",
                            children=html.Div("Cargando tabla evolutiva...", className="text-center text-muted p-4")
                        )
                    ])
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
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
        
        # PASO 3: Botones de métricas (sin filtros)
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
        style={"display": "none"}  # Oculto por defecto
    )
        ]
    )  # Cierre del dcc.Loading general
])



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
                return microciclos
        except Exception as e:
            pass
        
        # Fallback al método antiguo si falla
        microciclos = get_microciclos()
        return microciclos
    return current_data


# Callback para actualizar el contenido con los microciclos cargados
@callback(
    Output("microciclo-equipo-container", "children"),
    Input("microciclos-store", "data"),
    prevent_initial_call=False
)
def update_content_with_microciclos(microciclos):
    """Actualiza el contenido del contenedor con los microciclos cargados"""
    if microciclos:
        return get_microciclo_equipo_content(microciclos)
    return get_microciclo_equipo_content([])

    
# Callback para cargar tabla evolutiva al inicio
@callback(
    Output("sc-tabla-evolutiva-container", "children"),
    Output("sc-tabla-evolutiva-data", "data"),
    Input("sc-microciclo-dropdown", "value"),  # Trigger cuando se selecciona microciclo
    State("sc-date-store", "data"),
    prevent_initial_call=False  # Permitir carga cuando dropdown recibe valor por defecto
)
def cargar_tabla_evolutiva_inicial(microciclo_id, date_data):
    """
    Carga la tabla evolutiva de todos los microciclos al inicio.
    Usa la misma lógica de jugadores que Seguimiento de Carga:
    - Excluye porteros
    - Solo jugadores Full (participation_type)
    """
    # Evitar carga si no hay microciclo seleccionado
    if not microciclo_id:
        return html.Div("Selecciona un microciclo para ver la tabla evolutiva", 
                       className="text-muted text-center p-4"), {}
    
    try:
        from pages.seguimiento_carga_ultra_optimizado import cargar_tabla_evolutiva_microciclos
        from utils.db_manager import get_db_connection
        import pandas as pd
        
        print("🔄 Cargando tabla evolutiva de microciclos...")
        
        # Obtener jugadores REALES que participaron en microciclos (sin porteros)
        # IMPORTANTE: Usar los mismos jugadores que usa el gráfico (df_raw['athlete_id'].unique())
        engine = get_db_connection()
        
        query_jugadores_activos = '''
            SELECT DISTINCT athlete_id
            FROM microciclos_metricas_procesadas
            WHERE athlete_position != 'Goal Keeper'
              AND activity_date >= '2024-08-01'
        '''
        
        df_jugadores = pd.read_sql(query_jugadores_activos, engine)
        engine.dispose()
        
        if df_jugadores.empty:
            return (
                html.Div("No hay jugadores disponibles", 
                        className="text-muted text-center p-4"),
                {}
            )
        
        jugadores_ids = df_jugadores['athlete_id'].tolist()
        
        print(f"🎯 Jugadores ACTIVOS sin porteros: {len(jugadores_ids)}")
        print(f"🎯 (Solo jugadores que realmente participaron en entrenamientos)")
        
        # Cargar datos de todos los microciclos con los mismos jugadores
        datos_evolutivos = cargar_tabla_evolutiva_microciclos(jugadores_ids=jugadores_ids)
        
        if not datos_evolutivos:
            return (
                html.Div("No se pudieron cargar los datos evolutivos", 
                        className="text-muted text-center p-4"),
                {}
            )
        
        # Generar componente visual
        tabla = generar_tabla_evolutiva(datos_evolutivos)
        
        return tabla, datos_evolutivos
        
    except Exception as e:
        print(f"❌ Error cargando tabla evolutiva: {e}")
        import traceback
        traceback.print_exc()
        return (
            html.Div(f"Error al cargar tabla evolutiva: {str(e)}", 
                    className="text-danger text-center p-4"),
            {}
        )


# Callback para cambiar microciclo desde tabla evolutiva (click en celdas)
@callback(
    Output("sc-microciclo-dropdown", "value", allow_duplicate=True),
    Output("sc-cargar-microciclo-btn", "n_clicks", allow_duplicate=True),
    Input({'type': 'tabla-evolutiva-celda', 'microciclo_id': ALL, 'metrica_id': ALL}, 'n_clicks'),
    Input({'type': 'tabla-evolutiva-header', 'microciclo_id': ALL}, 'n_clicks'),
    State({'type': 'tabla-evolutiva-celda', 'microciclo_id': ALL, 'metrica_id': ALL}, 'id'),
    State({'type': 'tabla-evolutiva-header', 'microciclo_id': ALL}, 'id'),
    State("sc-cargar-microciclo-btn", "n_clicks"),
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
            print(f"🖱️ Click en tabla: Cambiando a microciclo {microciclo_id}")
            # Incrementar n_clicks para forzar recarga automática
            new_n_clicks = (current_n_clicks or 0) + 1
            return microciclo_id, new_n_clicks
    
    except Exception as e:
        print(f"⚠️ Error procesando click en tabla: {e}")
        raise PreventUpdate
    
    raise PreventUpdate


# Callback principal: Cargar y cachear TODAS las métricas del microciclo
@callback(
    Output("sc-microciclo-cache", "data"),
    Output("sc-microciclo-loaded", "data"),
    Output("sc-metricas-container", "style"),
    Input("sc-cargar-microciclo-btn", "n_clicks"),
    State("sc-microciclo-dropdown", "value"),
    State("sc-date-store", "data"),
    prevent_initial_call=True
)
def cargar_microciclo_completo(n_clicks, microciclo_id, date_data):
    """
    OPTIMIZADO: Carga datos desde tabla intermedia.
    Fallback a método antiguo si la tabla no está disponible.
    Sin filtros de jugadores - usa lógica fija (sin porteros, sin Part/Rehab)
    """
    if not microciclo_id:
        return {}, False, {'display': 'none'}
    
    print(f"🔄 Cargando microciclo: {microciclo_id}")
    
    # MÉTODO OPTIMIZADO: Usar tabla intermedia
    try:
        # Obtener atletas del microciclo desde tabla procesada
        atletas_df = get_athletes_from_microciclo(microciclo_id)
        
        if atletas_df.empty:
            print(f"⚠️ No hay datos en tabla intermedia para {microciclo_id}, usando método antiguo")
            raise Exception("Tabla intermedia vacía")
        
        # Filtrar porteros - lógica fija (sin filtros de usuario)
        atletas_sin_porteros = atletas_df[atletas_df['athlete_position'] != 'Goal Keeper']
        
        # Selección fija: jugadores de campo (sin porteros, sin Part/Rehab)
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
        
        # Detectar tipo de microciclo ANTES de generar gráficos (1 sola vez)
        dias_presentes = []
        for metrica, df_resumen in datos_por_metrica.items():
            if not df_resumen.empty:
                dias_presentes = df_resumen['activity_tag'].unique().tolist()
                break
        
        tipo_microciclo = detectar_tipo_microciclo(dias_presentes)
        print(f"   Días presentes: {dias_presentes}")
        
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
        
        # Cache optimizado CON TODAS LAS MÉTRICAS PRE-CARGADAS
        cache_optimizado = {
            'microciclo_id': microciclo_id,
            'jugadores_ids': jugadores_ids,
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
            {'display': 'block'}
        )
        
    except Exception as e:
        print(f"❌ Error cargando microciclo desde tabla intermedia: {e}")
        import traceback
        traceback.print_exc()
        return {}, False, {'display': 'none'}

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
        return fig, "total_distance", {'display': 'block'}
    return {}, "total_distance", {'display': 'none'}

# Callback para cambiar entre métricas usando botones (carga on-demand con cache inteligente)
@callback(
    Output("sc-bar-chart", "figure", allow_duplicate=True),
    Output("sc-selected-metric", "data", allow_duplicate=True),
    Input({'type': 'metric-btn', 'index': ALL}, 'n_clicks'),
    State("sc-microciclo-cache", "data"),
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


# Callback para mostrar/ocultar tabla detallada
@callback(
    Output("datos-detallados-container", "style"),
    Output("toggle-datos-btn", "children"),
    Input("toggle-datos-btn", "n_clicks"),
    State("datos-detallados-container", "style"),
    prevent_initial_call=True
)
def toggle_tabla_detallada(n_clicks, current_style):
    """Muestra u oculta la tabla de datos detallados"""
    if current_style.get("display") == "none":
        return {"display": "block"}, [html.I(className="fas fa-eye-slash me-2"), "Ocultar datos detallados"]
    else:
        return {"display": "none"}, [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"]


# Callback para cargar tabla detallada
@callback(
    Output("sc-table-container", "children"),
    Input("sc-selected-metric", "data"),
    State("sc-microciclo-cache", "data"),
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

layout = html.Div([
    # Stores globales
    dcc.Store(id='microciclos-store', data=[]),
    dcc.Store(id='sc-date-store', data={}),
    
    dbc.Container([
        # Card contenedor principal con fondo blanco
        dbc.Card([
            dbc.CardBody([
                # Título de la sección
                html.H3("CONTROL PROCESO ENTRENAMIENTO - Entrenamiento Equipo", 
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
                
                # Contenedor del contenido dinámico
                html.Div(id='microciclo-equipo-container', children=[
                    get_microciclo_equipo_content([])  # Contenido inicial vacío
                ])
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