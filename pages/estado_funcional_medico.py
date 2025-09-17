# pages/estado_funcional_medico.py

from dash import html, dcc, callback, Input, Output, State
import dash
import dash_bootstrap_components as dbc
from utils.layouts import standard_page
from utils.db_manager import (get_fechas_entrenamiento_disponibles, get_evaluaciones_medicas, 
                             get_estadisticas_por_jugador, get_evolucion_jugador, get_lista_jugadores)
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Función para obtener el color según la evaluación
def get_evaluation_color(evaluacion):
    """Retorna el estilo completo según la evaluación"""
    style_map = {
        'Normal': {
            'backgroundColor': '#d4edda',  # Verde claro
            'color': '#155724'             # Verde oscuro
        },
        'Precaución': {
            'backgroundColor': '#fff3cd',  # Amarillo claro
            'color': '#856404'             # Amarillo oscuro
        },
        'Fisio/RTP': {
            'backgroundColor': '#f8d7da',  # Rojo claro
            'color': '#721c24'             # Rojo oscuro
        }
    }
    return style_map.get(evaluacion, {
        'backgroundColor': '#f8f9fa', 
        'color': '#495057'
    })  # Gris por defecto

def format_date(date_obj):
    """Formatea la fecha para mostrar en español"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except:
            return date_obj
    
    if not hasattr(date_obj, 'strftime'):
        return str(date_obj)
    
    # Mapeo de meses en español
    meses_es = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
        'April': 'abril', 'May': 'mayo', 'June': 'junio',
        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    
    # Obtener fecha en inglés y convertir
    fecha_en = date_obj.strftime('%d de %B de %Y')
    for mes_en, mes_es in meses_es.items():
        fecha_en = fecha_en.replace(mes_en, mes_es)
    
    return fecha_en

# Contenido de las pestañas
def get_estado_actual_content():
    return html.Div([
        # Navegador de fechas con flechas
        html.Div([
            html.Div([
                # Flecha izquierda
                html.Button(
                    "‹",
                    id='fecha-anterior',
                    className="btn",
                    style={
                        "backgroundColor": "transparent",
                        "border": "2px solid #1e3d59",
                        "color": "#1e3d59",
                        "width": "40px",
                        "height": "40px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "fontSize": "24px",
                        "fontWeight": "bold"
                    }
                ),
                
                # Fecha actual
                html.Div(
                    id='fecha-actual-display',
                    style={
                        "color": "#1e3d59",
                        "fontWeight": "600",
                        "fontSize": "18px",
                        "textAlign": "center",
                        "minWidth": "250px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center"
                    }
                ),
                
                # Flecha derecha  
                html.Button(
                    "›",
                    id='fecha-siguiente',
                    className="btn",
                    style={
                        "backgroundColor": "transparent",
                        "border": "2px solid #1e3d59",
                        "color": "#1e3d59",
                        "width": "40px",
                        "height": "40px",
                        "borderRadius": "50%",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "fontSize": "24px",
                        "fontWeight": "bold"
                    }
                )
            ], style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "gap": "20px",
                "marginBottom": "30px"
            }),
            
            # Store para manejar el índice de fecha actual y lista de fechas
            dcc.Store(id='fechas-disponibles-store', data=[]),
            dcc.Store(id='fecha-index-store', data=0)
        ]),
        
        # Contenedor para la tabla
        html.Div(id='tabla-evaluaciones-container')
    ], className="p-4")

def get_evolutivo_content():
    return html.Div([
        # Sección 1: Estadísticas por jugador
        html.Div([
            html.H5("Estadísticas por Jugador", 
                   style={"color": "#1e3d59", "fontWeight": "600", "marginBottom": "20px"}),
            html.P("Porcentaje de días en cada estado médico por jugador", 
                   className="text-muted mb-3"),
            
            # Store para el ordenamiento y datos
            dcc.Store(id='sort-column-store', data='nombre_jugador'),
            dcc.Store(id='sort-order-store', data='asc'),
            dcc.Store(id='estadisticas-data-store', data={}),
            
            html.Div(id='tabla-estadisticas-container')
        ], className="mb-5"),
        
        # Separador
        html.Hr(style={"border": "1px solid #e9ecef", "margin": "40px 0"}),
        
        # Sección 2: Evolución temporal
        html.Div([
            html.H5("Evolución Temporal", 
                   style={"color": "#1e3d59", "fontWeight": "600", "marginBottom": "20px"}),
            html.P("Seguimiento del estado médico de un jugador a lo largo del tiempo", 
                   className="text-muted mb-3"),
            
            # Selector de jugador
            html.Div([
                html.Label("Seleccionar Jugador:", 
                          style={"fontWeight": "600", "color": "#495057", "marginBottom": "8px"}),
                dcc.Dropdown(
                    id='jugador-selector',
                    placeholder="Selecciona un jugador...",
                    style={"minWidth": "300px"}
                )
            ], className="mb-4"),
            
            # Contenedor del gráfico
            html.Div(id='grafico-evolucion-container')
        ])
    ], className="p-4")

layout = standard_page([
    # Título con fondo transparente
    html.Div([
        html.H2("CONTROL ESTADO FUNCIONAL - Médico", 
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
        # Header de pestañas estilo imagen
        html.Div([
            html.Div([
                html.Button(
                    "Estado Médico Actual",
                    id="tab-estado-actual",
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
                        "width": "50%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Evolutivo Médico",
                    id="tab-evolutivo",
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
                        "width": "50%",
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
            html.Div(id="tab-content", children=get_estado_actual_content())
        ], style={
            "backgroundColor": "white",
            "borderRadius": "0 0 8px 8px",
            "minHeight": "400px"
        })
    ], className="shadow-sm", style={"border": "1px solid #e9ecef", "borderRadius": "8px"})
])

# Callback para manejar el cambio de pestañas
@callback(
    [Output("tab-estado-actual", "style"),
     Output("tab-evolutivo", "style"),
     Output("tab-content", "children")],
    [Input("tab-estado-actual", "n_clicks"),
     Input("tab-evolutivo", "n_clicks")]
)
def update_tabs(n_clicks_actual, n_clicks_evolutivo):
    # Determinar cuál pestaña está activa
    if n_clicks_evolutivo and n_clicks_evolutivo > (n_clicks_actual or 0):
        # Pestaña evolutivo activa
        style_actual = {
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
            "width": "50%",
            "textAlign": "center"
        }
        style_evolutivo = {
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
            "width": "50%",
            "textAlign": "center"
        }
        content = get_evolutivo_content()
    else:
        # Pestaña estado actual activa (por defecto)
        style_actual = {
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
            "width": "50%",
            "textAlign": "center"
        }
        style_evolutivo = {
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
            "width": "50%",
            "textAlign": "center"
        }
        content = get_estado_actual_content()
    
    return style_actual, style_evolutivo, content

# Callback para cargar las fechas disponibles inicialmente
@callback(
    Output('fechas-disponibles-store', 'data'),
    Output('fecha-index-store', 'data'),
    Output('fecha-actual-display', 'children'),
    Input('tab-content', 'children')  # Se ejecuta al cargar la pestaña
)
def load_fechas_disponibles(_):
    """Carga las fechas de entrenamiento disponibles"""
    try:
        fechas = get_fechas_entrenamiento_disponibles()
        if not fechas:
            return [], 0, "No hay fechas disponibles"
        
        # Convertir fechas a strings para el store
        fechas_str = [str(fecha) for fecha in fechas]
        fecha_actual = format_date(fechas[0]) if fechas else "No hay fechas disponibles"
        
        return fechas_str, 0, fecha_actual
        
    except Exception as e:
        print(f"Error cargando fechas: {e}")
        return [], 0, "Error cargando fechas"

# Callback para navegación con flechas
@callback(
    Output('fecha-index-store', 'data', allow_duplicate=True),
    Output('fecha-actual-display', 'children', allow_duplicate=True),
    [Input('fecha-anterior', 'n_clicks'),
     Input('fecha-siguiente', 'n_clicks')],
    [State('fechas-disponibles-store', 'data'),
     State('fecha-index-store', 'data')],
    prevent_initial_call=True
)
def navigate_fechas(n_anterior, n_siguiente, fechas_disponibles, index_actual):
    """Navega entre fechas usando las flechas"""
    if not fechas_disponibles:
        return 0, "No hay fechas disponibles"
    
    triggered = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if triggered == 'fecha-anterior' and n_anterior:
        # Ir a fecha anterior (índice mayor, fecha más antigua)
        nuevo_index = min(index_actual + 1, len(fechas_disponibles) - 1)
    elif triggered == 'fecha-siguiente' and n_siguiente:
        # Ir a fecha siguiente (índice menor, fecha más reciente)
        nuevo_index = max(index_actual - 1, 0)
    else:
        nuevo_index = index_actual
    
    fecha_actual = format_date(fechas_disponibles[nuevo_index])
    return nuevo_index, fecha_actual

# Callback para mostrar la tabla de evaluaciones
@callback(
    Output('tabla-evaluaciones-container', 'children'),
    [Input('fecha-index-store', 'data'),
     Input('fechas-disponibles-store', 'data')]
)
def update_tabla_evaluaciones(index_actual, fechas_disponibles):
    """Actualiza la tabla de evaluaciones según la fecha seleccionada"""
    if not fechas_disponibles or index_actual >= len(fechas_disponibles):
        return html.Div("No hay fecha seleccionada.", 
                       className="text-muted text-center p-4")
    
    fecha_seleccionada = fechas_disponibles[index_actual]
    
    try:
        # Obtener evaluaciones de la base de datos
        df = get_evaluaciones_medicas(fecha_seleccionada)
        
        if df.empty:
            return html.Div("No hay evaluaciones para la fecha seleccionada.", 
                           className="text-muted text-center p-4")
        
        # Crear filas de la tabla
        filas = []
        for _, row in df.iterrows():
            # Definir colores según evaluación
            color_evaluacion = get_evaluation_color(row['evaluacion'])
            
            # Construir contenido de evaluación con comentarios
            evaluacion_content = [
                html.Span(row['evaluacion'], style={"fontWeight": "600"})
            ]
            
            if pd.notna(row['comentarios_evaluacion']) and row['comentarios_evaluacion'].strip():
                evaluacion_content.append(html.Br())
                evaluacion_content.append(
                    html.Span(row['comentarios_evaluacion'], 
                             style={"fontStyle": "italic", "fontSize": "0.9em", "color": "#6c757d"})
                )
            
            # Observaciones (mostrar "—" si está vacío)
            observaciones = row['observaciones'] if pd.notna(row['observaciones']) and row['observaciones'].strip() else "—"
            observaciones_style = {"fontStyle": "italic", "color": "#6c757d"} if observaciones == "—" else {}
            
            fila = html.Tr([
                html.Td(row['nombre_jugador'], 
                       style={
                           "fontWeight": "bold", 
                           "color": "#1e3d59",
                           "padding": "12px", 
                           "width": "20%", 
                           "minWidth": "120px",
                           "textAlign": "center"
                       }),
                html.Td(evaluacion_content, 
                       style={**color_evaluacion, "padding": "12px", "width": "50%", "textAlign": "center"}),
                html.Td(observaciones, 
                       style={**observaciones_style, "padding": "12px", "width": "30%", "textAlign": "center"})
            ], style={"borderBottom": "1px solid #dee2e6"})
            filas.append(fila)
        
        # Crear la tabla completa
        tabla = html.Div([
            # Tabla
            html.Table([
                # Encabezados
                html.Thead([
                    html.Tr([
                        html.Th("Jugador", 
                               style={
                                   "backgroundColor": "#1e3d59", 
                                   "color": "white", 
                                   "padding": "15px", 
                                   "fontWeight": "600",
                                   "width": "20%",
                                   "minWidth": "120px",
                                   "textAlign": "center"
                               }),
                        html.Th("Evaluación", 
                               style={
                                   "backgroundColor": "#1e3d59", 
                                   "color": "white", 
                                   "padding": "15px", 
                                   "fontWeight": "600",
                                   "width": "50%",
                                   "textAlign": "center"
                               }),
                        html.Th("Observaciones", 
                               style={
                                   "backgroundColor": "#1e3d59", 
                                   "color": "white", 
                                   "padding": "15px", 
                                   "fontWeight": "600",
                                   "width": "30%",
                                   "textAlign": "center"
                               })
                    ])
                ]),
                # Cuerpo de la tabla
                html.Tbody(filas)
            ], className="table table-hover", style={
                "marginBottom": "0",
                "border": "1px solid #e9ecef"
            })
        ], style={
            "border": "1px solid #e9ecef",
            "borderRadius": "8px",
            "overflow": "hidden",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        })
        
        return tabla
        
    except Exception as e:
        print(f"Error actualizando tabla: {e}")
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2", style={"color": "#dc3545"}),
            f"Error cargando evaluaciones: {str(e)}"
        ], className="text-danger text-center p-4")

# Callback para manejar ordenamiento de tabla
@callback(
    Output('sort-column-store', 'data'),
    Output('sort-order-store', 'data'),
    [Input('sort-jugador', 'n_clicks'),
     Input('sort-normal', 'n_clicks'),
     Input('sort-precaucion', 'n_clicks'),
     Input('sort-fisio', 'n_clicks')],
    [State('sort-column-store', 'data'),
     State('sort-order-store', 'data')],
    prevent_initial_call=True
)
def handle_sort(n_jugador, n_normal, n_precaucion, n_fisio, current_column, current_order):
    """Maneja el ordenamiento de la tabla"""
    triggered = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if triggered == 'sort-jugador':
        new_column = 'nombre_jugador'
    elif triggered == 'sort-normal':
        new_column = 'Normal'
    elif triggered == 'sort-precaucion':
        new_column = 'Precaución'
    elif triggered == 'sort-fisio':
        new_column = 'Fisio/RTP'
    else:
        return current_column, current_order
    
    # Si es la misma columna, cambiar orden; si es diferente, empezar con ascendente
    if new_column == current_column:
        new_order = 'desc' if current_order == 'asc' else 'asc'
    else:
        new_order = 'asc'
    
    return new_column, new_order

# Callback para cargar datos (solo cuando se abre la pestaña)
@callback(
    Output('estadisticas-data-store', 'data'),
    Input('tab-content', 'children')
)
def load_estadisticas_data(_):
    """Carga los datos de estadísticas una sola vez"""
    try:
        df_stats = get_estadisticas_por_jugador()
        if df_stats.empty:
            return {}
        return df_stats.to_dict('records')
    except Exception as e:
        print(f"Error cargando datos de estadísticas: {e}")
        return {}

# Callback para renderizar tabla (rápido, solo ordena datos en memoria)
@callback(
    Output('tabla-estadisticas-container', 'children'),
    [Input('estadisticas-data-store', 'data'),
     Input('sort-column-store', 'data'),
     Input('sort-order-store', 'data')]
)
def render_tabla_estadisticas(data, sort_column, sort_order):
    """Renderiza la tabla con los datos ya cargados"""
    try:
        if not data:
            return html.Div("No hay datos de estadísticas disponibles.", 
                           className="text-muted text-center p-4")
        
        # Convertir de vuelta a DataFrame para facilitar el ordenamiento
        df_stats = pd.DataFrame(data)
        
        # Aplicar ordenamiento
        ascending = sort_order == 'asc'
        if sort_column == 'nombre_jugador':
            df_stats = df_stats.sort_values('nombre_jugador', ascending=ascending)
        else:
            df_stats = df_stats.sort_values(sort_column, ascending=ascending)
        
        # Función para obtener indicador de ordenamiento
        def get_sort_indicator(column_name):
            if sort_column == column_name:
                return " ↑" if sort_order == 'asc' else " ↓"
            return ""
        
        # Crear filas de la tabla
        filas = []
        for _, row in df_stats.iterrows():
            fila = html.Tr([
                html.Td(row['nombre_jugador'], 
                       style={
                           "fontWeight": "bold", 
                           "color": "#1e3d59",
                           "padding": "12px", 
                           "textAlign": "center"
                       }),
                html.Td(f"{row['Normal']:.1f}%", 
                       style={
                           "padding": "12px", 
                           "textAlign": "center",
                           "backgroundColor": "#d4edda",
                           "color": "#155724",
                           "fontWeight": "600"
                       }),
                html.Td(f"{row['Precaución']:.1f}%", 
                       style={
                           "padding": "12px", 
                           "textAlign": "center",
                           "backgroundColor": "#fff3cd",
                           "color": "#856404",
                           "fontWeight": "600"
                       }),
                html.Td(f"{row['Fisio/RTP']:.1f}%", 
                       style={
                           "padding": "12px", 
                           "textAlign": "center",
                           "backgroundColor": "#f8d7da",
                           "color": "#721c24",
                           "fontWeight": "600"
                       })
            ], style={"borderBottom": "1px solid #dee2e6"})
            filas.append(fila)
        
        # Crear tabla con headers clickeables
        tabla = html.Table([
            html.Thead([
                html.Tr([
                    html.Th(
                        html.Button(
                            f"Jugador{get_sort_indicator('nombre_jugador')}",
                            id='sort-jugador',
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "color": "white",
                                "fontWeight": "600",
                                "cursor": "pointer",
                                "width": "100%",
                                "padding": "0"
                            }
                        ),
                        style={
                            "backgroundColor": "#1e3d59", 
                            "color": "white", 
                            "padding": "15px", 
                            "textAlign": "center",
                            "width": "25%"
                        }
                    ),
                    html.Th(
                        html.Button(
                            f"Normal{get_sort_indicator('Normal')}",
                            id='sort-normal',
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "color": "white",
                                "fontWeight": "600",
                                "cursor": "pointer",
                                "width": "100%",
                                "padding": "0"
                            }
                        ),
                        style={
                            "backgroundColor": "#1e3d59", 
                            "color": "white", 
                            "padding": "15px", 
                            "textAlign": "center",
                            "width": "25%"
                        }
                    ),
                    html.Th(
                        html.Button(
                            f"Precaución{get_sort_indicator('Precaución')}",
                            id='sort-precaucion',
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "color": "white",
                                "fontWeight": "600",
                                "cursor": "pointer",
                                "width": "100%",
                                "padding": "0"
                            }
                        ),
                        style={
                            "backgroundColor": "#1e3d59", 
                            "color": "white", 
                            "padding": "15px", 
                            "textAlign": "center",
                            "width": "25%"
                        }
                    ),
                    html.Th(
                        html.Button(
                            f"Fisio/RTP{get_sort_indicator('Fisio/RTP')}",
                            id='sort-fisio',
                            style={
                                "backgroundColor": "transparent",
                                "border": "none",
                                "color": "white",
                                "fontWeight": "600",
                                "cursor": "pointer",
                                "width": "100%",
                                "padding": "0"
                            }
                        ),
                        style={
                            "backgroundColor": "#1e3d59", 
                            "color": "white", 
                            "padding": "15px", 
                            "textAlign": "center",
                            "width": "25%"
                        }
                    )
                ])
            ]),
            html.Tbody(filas)
        ], style={
            "width": "100%",
            "borderCollapse": "collapse",
            "border": "1px solid #dee2e6",
            "borderRadius": "8px",
            "overflow": "hidden",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
            "tableLayout": "fixed"
        })
        
        return tabla
        
    except Exception as e:
        print(f"Error cargando estadísticas: {e}")
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2", style={"color": "#dc3545"}),
            f"Error cargando estadísticas: {str(e)}"
        ], className="text-danger text-center p-4")

# Callback para cargar lista de jugadores
@callback(
    Output('jugador-selector', 'options'),
    Output('jugador-selector', 'value'),
    Input('tab-content', 'children')
)
def load_jugadores_dropdown(_):
    """Carga la lista de jugadores en el dropdown"""
    try:
        jugadores = get_lista_jugadores()
        if not jugadores:
            return [], None
        
        options = [{'label': jugador, 'value': jugador} for jugador in jugadores]
        return options, jugadores[0] if jugadores else None
        
    except Exception as e:
        print(f"Error cargando jugadores: {e}")
        return [], None

# Callback para mostrar gráfico de evolución
@callback(
    Output('grafico-evolucion-container', 'children'),
    Input('jugador-selector', 'value')
)
def update_grafico_evolucion(jugador_seleccionado):
    """Actualiza el gráfico de evolución del jugador seleccionado"""
    if not jugador_seleccionado:
        return html.Div("Selecciona un jugador para ver su evolución.", 
                       className="text-muted text-center p-4")
    
    try:
        df_evolucion = get_evolucion_jugador(jugador_seleccionado)
        if df_evolucion.empty:
            return html.Div(f"No hay datos de evolución para {jugador_seleccionado}.", 
                           className="text-muted text-center p-4")
        
        # Crear gráfico de línea
        fig = go.Figure()
        
        # Agregar bandas de colores de fondo para cada estado
        # Banda Fisio/RTP (roja)
        fig.add_shape(
            type="rect",
            x0=df_evolucion['fecha_entrenamiento'].min(),
            x1=df_evolucion['fecha_entrenamiento'].max(),
            y0=0.5, y1=1.5,
            fillcolor="rgba(220, 53, 69, 0.1)",
            line=dict(width=0),
            layer="below"
        )
        
        # Banda Precaución (amarilla)
        fig.add_shape(
            type="rect",
            x0=df_evolucion['fecha_entrenamiento'].min(),
            x1=df_evolucion['fecha_entrenamiento'].max(),
            y0=1.5, y1=2.5,
            fillcolor="rgba(255, 193, 7, 0.1)",
            line=dict(width=0),
            layer="below"
        )
        
        # Banda Normal (verde)
        fig.add_shape(
            type="rect",
            x0=df_evolucion['fecha_entrenamiento'].min(),
            x1=df_evolucion['fecha_entrenamiento'].max(),
            y0=2.5, y1=3.5,
            fillcolor="rgba(40, 167, 69, 0.1)",
            line=dict(width=0),
            layer="below"
        )
        
        # Preparar datos para hover con observaciones
        hover_data = []
        for _, row in df_evolucion.iterrows():
            observaciones = row['observaciones'] if pd.notna(row['observaciones']) and row['observaciones'].strip() else "Sin observaciones"
            comentarios = row['comentarios_evaluacion'] if pd.notna(row['comentarios_evaluacion']) and row['comentarios_evaluacion'].strip() else ""
            
            hover_text = f"<b>{jugador_seleccionado}</b><br>"
            hover_text += f"📅 {row['fecha_entrenamiento']}<br>"
            hover_text += f"🏥 {row['evaluacion']}<br>"
            if comentarios:
                hover_text += f"💬 {comentarios}<br>"
            hover_text += f"📝 {observaciones}"
            
            hover_data.append(hover_text)
        
        # Agregar línea de evolución con colores dinámicos por punto
        colores_puntos = []
        for evaluacion in df_evolucion['evaluacion']:
            if evaluacion == 'Normal':
                colores_puntos.append('#28a745')
            elif evaluacion == 'Precaución':
                colores_puntos.append('#ffc107')
            else:  # Fisio/RTP
                colores_puntos.append('#dc3545')
        
        fig.add_trace(go.Scatter(
            x=df_evolucion['fecha_entrenamiento'],
            y=df_evolucion['valor_numerico'],
            mode='lines+markers',
            name=jugador_seleccionado,
            line=dict(color='#1e3d59', width=3),
            marker=dict(size=10, color=colores_puntos, line=dict(width=2, color='white')),
            hovertemplate='%{text}<extra></extra>',
            text=hover_data
        ))
        
        # Personalizar layout sin título
        fig.update_layout(
            xaxis=dict(
                title=dict(text='Fecha de Entrenamiento', font=dict(size=14, color='#495057', family='Montserrat')),
                tickfont=dict(size=12, color='#495057', family='Montserrat'),
                gridcolor='rgba(233, 236, 239, 0.5)',
                showgrid=True
            ),
            yaxis=dict(
                tickfont=dict(size=16, family='Montserrat'),
                tickmode='array',
                tickvals=[1, 2, 3],
                ticktext=['<span style="color:#dc3545; font-weight:bold;">Fisio/RTP</span>', 
                         '<span style="color:#ffc107; font-weight:bold;">Precaución</span>', 
                         '<span style="color:#28a745; font-weight:bold;">Normal</span>'],
                gridcolor='rgba(233, 236, 239, 0.3)',
                showgrid=False,
                range=[0.5, 3.5]
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400,
            margin=dict(l=100, r=40, t=20, b=60),
            showlegend=False,
            hovermode='closest',
            font=dict(family='Montserrat')
        )
        
        return dcc.Graph(
            figure=fig,
            style={'height': '400px'},
            config={'displayModeBar': False}
        )
        
    except Exception as e:
        print(f"Error creando gráfico de evolución: {e}")
        return html.Div([
            html.I(className="fas fa-exclamation-triangle me-2", style={"color": "#dc3545"}),
            f"Error cargando evolución: {str(e)}"
        ], className="text-danger text-center p-4")
