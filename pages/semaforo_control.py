# pages/semaforo_control.py

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from utils.layouts import standard_page
from utils.semaforo_utils import get_all_semaforo_status, get_estado_general


def create_circular_semaforo(estados_data):
    """
    Crea un gráfico circular tipo 'queso de trivial' dividido en 6 secciones
    """
    # Definir las 6 secciones en orden específico
    secciones = [
        {'name': 'COMPETICIÓN', 'key': 'competicion'},
        {'name': 'ENTRENAMIENTO', 'key': 'entrenamiento'},
        {'name': 'NUTRICIÓN', 'key': 'nutricion'},
        {'name': 'PSICOLÓGICO', 'key': 'psicologico'},
        {'name': 'MÉDICO', 'key': 'medico'},
        {'name': 'CAPACIDAD FUNCIONAL', 'key': 'capacidad'}
    ]
    
    # Preparar datos para el pie chart
    labels = []
    colors = []
    estados = []
    hover_texts = []
    
    for seccion in secciones:
        estado = estados_data.get(seccion['key'], {
            'color': '#6c757d',
            'estado': 'EN DESARROLLO',
            'detalle': 'Sección pendiente de implementar'
        })
        
        labels.append(seccion['name'])
        colors.append(estado['color'])
        estados.append(estado['estado'])
        hover_texts.append(f"<b>{seccion['name']}</b><br>Estado: {estado['estado']}<br>Detalle: {estado['detalle']}")
    
    # Crear el pie chart único con todas las secciones
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=[1, 1, 1, 1, 1, 1],  # Valores iguales para secciones uniformes
        marker=dict(
            colors=colors,
            line=dict(color='white', width=3)
        ),
        textinfo='label+text',
        texttemplate='<b>%{label}</b><br>%{text}',
        text=estados,
        textfont=dict(size=10, color='white', family='Montserrat, sans-serif', weight='bold'),
        textposition='inside',
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_texts,
        hole=0.4,  # Crear agujero en el centro para el escudo
        sort=False,  # Mantener orden de las secciones
        direction='clockwise',
        showlegend=False
    )])
    
    fig.update_layout(
        height=700,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat, sans-serif'),
        showlegend=False,
        images=[
            # Escudo del equipo en el centro
            dict(
                source="/assets/ESCUDO-AZUL_RGB-HD.png",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                xanchor="center", yanchor="middle",
                sizex=0.15, sizey=0.15,
                opacity=0.9,
                layer="above"
            )
        ]
    )
    
    return fig


def create_status_cards(estados_data, estado_general):
    """
    Crea tarjetas de resumen de estados
    """
    # Tarjeta de estado general
    general_card = dbc.Card([
        dbc.CardBody([
            html.H4("ESTADO GENERAL", className="text-center mb-3", 
                   style={"color": "#1e3d59", "fontWeight": "bold"}),
            html.Div([
                html.H2(estado_general['estado'], 
                       className="text-center mb-2",
                       style={"color": estado_general['color'], "fontWeight": "bold"}),
                html.P(estado_general['detalle'], 
                      className="text-center text-muted",
                      style={"fontSize": "14px"})
            ])
        ])
    ], style={"border": f"3px solid {estado_general['color']}", "backgroundColor": "#f8f9fa"})
    
    # Tarjetas individuales por sección (TODAS las secciones)
    section_cards = []
    display_names = {
        'competicion': 'COMPETICIÓN',
        'entrenamiento': 'ENTRENAMIENTO', 
        'nutricion': 'NUTRICIÓN',
        'psicologico': 'PSICOLÓGICO',
        'medico': 'MÉDICO',
        'capacidad': 'CAPACIDAD FUNCIONAL'
    }
    
    for seccion_name, estado in estados_data.items():
        display_name = display_names.get(seccion_name, seccion_name.upper())
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6(display_name, 
                           className="text-center mb-2",
                           style={"color": "#1e3d59", "fontWeight": "bold", "fontSize": "12px"}),
                    html.H6(estado['estado'], 
                           className="text-center mb-1",
                           style={"color": estado['color'], "fontWeight": "bold", "fontSize": "14px"}),
                    html.P(estado['detalle'], 
                          className="text-center text-muted small",
                          style={"fontSize": "10px", "lineHeight": "1.2"})
                ])
            ], style={"border": f"2px solid {estado['color']}", "height": "100px"})
        ], md=6, className="mb-2")
        section_cards.append(card)
    
    # Retornar un solo componente contenedor con todas las cards
    return html.Div([
        general_card,
        html.Hr(className="my-3"),
        html.H6("DETALLE POR SECCIÓN", className="mb-3", 
               style={"color": "#1e3d59", "fontWeight": "bold"}),
        dbc.Row(section_cards)
    ])


layout = standard_page([
    # Título principal
    html.Div([
        html.H2("SEMÁFORO DE CONTROL", 
                className="mb-4", 
                style={
                    "color": "#1e3d59", 
                    "backgroundColor": "transparent",
                    "fontWeight": "600",
                    "textAlign": "center",
                    "padding": "1rem 0"
                })
    ], style={"backgroundColor": "transparent"}),
    
    # Store para almacenar datos 
    dcc.Store(id='semaforo-data-store', data=None),
    
    # Intervalo para carga inicial (2 segundos) y luego cada 5 minutos
    dcc.Interval(
        id='semaforo-interval',
        interval=2000,  # 2 segundos inicial
        n_intervals=0,
        max_intervals=1  # Solo dispara una vez inicialmente
    ),
    
    # Intervalo para actualización automática cada 5 minutos
    dcc.Interval(
        id='semaforo-interval-periodic',
        interval=5*60*1000,  # 5 minutos en milisegundos
        n_intervals=0
    ),
    
    # Container principal con loading inicial
    html.Div([
        # Fila con gráfico circular y tarjetas
        dbc.Row([
            # Columna del gráfico circular
            dbc.Col([
                html.Div([
                    # Spinner de carga inicial visible por defecto
                    html.Div([
                        html.Div([
                            dbc.Spinner(
                                color="primary", 
                                size="xl",
                                spinnerClassName="mb-4"
                            ),
                            html.H4("🚦 Cargando Semáforo de Control", 
                                   className="text-primary fw-bold mb-3"),
                            html.P("Obteniendo indicadores del estado del equipo...", 
                                   className="text-muted")
                        ], className="text-center")
                    ], style={
                        "height": "700px", 
                        "display": "flex", 
                        "alignItems": "center", 
                        "justifyContent": "center",
                        "backgroundColor": "#f8f9fa",
                        "borderRadius": "10px",
                        "border": "2px dashed #dee2e6"
                    })
                ], id="semaforo-chart-container")
            ], md=8),
            
            # Columna de tarjetas de estado
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Spinner(color="primary", size="lg", spinnerClassName="mb-3"),
                            html.H5("Cargando estados...", className="text-center text-muted")
                        ])
                    ])
                ], id="status-cards-container")
            ], md=4)
        ], className="mb-4"),
        
        # Solo mostrar última actualización sin card innecesaria
        dbc.Row([
            dbc.Col([
                html.P([
                    "Última actualización: ",
                    html.Span(id="ultima-actualizacion", style={"fontWeight": "bold", "color": "#1e3d59"})
                ], className="text-center text-muted small mt-3 mb-0")
            ])
        ])
    ], className="p-3")
])


# Callback para controlar el indicador de carga
@callback(
    Output('loading-indicator-container', 'style'),
    Input('semaforo-data-store', 'data')
)
def update_loading_indicator(data):
    """Controla la visibilidad del spinner de carga"""
    
    if data is None or not data or not data.get('estados'):
        return {"display": "block"}
    else:
        return {"display": "none"}


# Callback para cargar datos iniciales y actualizaciones periódicas
@callback(
    Output('semaforo-data-store', 'data'),
    [Input('semaforo-interval', 'n_intervals'),
     Input('semaforo-interval-periodic', 'n_intervals')]
)
def load_semaforo_data(n_intervals_initial, n_intervals_periodic):
    """Carga los datos del semáforo"""
    try:
        estados = get_all_semaforo_status()
        
        estado_general = get_estado_general()
        
        return {
            'estados': estados,
            'estado_general': estado_general,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"ERROR cargando datos del semáforo: {e}")
        return {
            'estados': {},
            'estado_general': {'color': '#6c757d', 'estado': 'ERROR', 'detalle': str(e)},
            'timestamp': datetime.now().isoformat()
        }


# Callback para actualizar visualización
@callback(
    [Output('semaforo-chart-container', 'children'),
     Output('status-cards-container', 'children'),
     Output('ultima-actualizacion', 'children')],
    [Input('semaforo-data-store', 'data')]
)
def update_semaforo_display(data):
    """Actualiza la visualización del semáforo"""
    
    # Si data es None o vacío, mostrar spinner completo
    if data is None or not data or not data.get('estados'):
        
        # Spinner para el gráfico completo
        loading_chart = html.Div([
            html.Div([
                dbc.Spinner(
                    color="primary", 
                    size="xl",
                    spinner_style={"width": "5rem", "height": "5rem"},
                    className="mb-4"
                ),
                html.H3("🚦 Cargando Semáforo de Control", 
                       className="text-primary fw-bold mb-3"),
                html.P("Obteniendo indicadores del estado del equipo...", 
                       className="text-muted fs-5")
            ], className="text-center")
        ], style={
            "height": "700px", 
            "display": "flex", 
            "alignItems": "center", 
            "justifyContent": "center",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "10px",
            "border": "2px dashed #dee2e6"
        })
        
        # Cards de carga
        loading_cards = html.Div([
            dbc.Card([
                dbc.CardBody([
                    dbc.Spinner(color="primary", size="lg", spinnerClassName="mb-3"),
                    html.H5("Cargando estados...", className="text-center text-muted")
                ])
            ])
        ])
        
        return loading_chart, loading_cards, "Cargando..."
    
    try:
        estados = data['estados']
        estado_general = data['estado_general']
        timestamp = datetime.fromisoformat(data['timestamp'])
        
        
        # Verificar que tenemos estados válidos
        if not estados or len(estados) == 0:
            raise Exception("Estados vacíos recibidos")
        
        # Crear gráfico circular
        fig = create_circular_semaforo(estados)
        
        # Envolver el gráfico en un componente dcc.Graph
        chart_component = dcc.Graph(
            figure=fig,
            style={"height": "700px", "backgroundColor": "transparent"},
            config={'displayModeBar': False}
        )
        
        # Crear tarjetas de estado
        cards = create_status_cards(estados, estado_general)
        
        # Formatear timestamp
        timestamp_str = timestamp.strftime("%d/%m/%Y a las %H:%M")
        
        return chart_component, cards, timestamp_str
        
    except Exception as e:
        print(f"Error actualizando visualización: {e}")
        
        # Componente de error
        error_component = html.Div([
            html.Div([
                html.H4("⚠️ Error", className="text-danger mb-3"),
                html.P(f"No se pudo cargar el semáforo: {str(e)}", 
                       className="text-muted")
            ], className="text-center py-5")
        ], style={
            "height": "700px", 
            "display": "flex", 
            "alignItems": "center", 
            "justifyContent": "center",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "10px",
            "border": "2px solid #dc3545"
        })
        
        return error_component, html.Div(f"Error: {str(e)}"), "Error"
