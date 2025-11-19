"""Antropométrico: dashboard con pestañas Estado y Evolutivo
"""

from dash import html, dcc, callback, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from functools import lru_cache
from utils.layouts import standard_page
from utils.soccersystem_data import (
    get_team_anthropometry_timeseries,
    get_team_anthropometry,
)


ALL_VAL = "__ALL__"


def get_estado_antropometrico_content():
    """Contenido de la pestaña Estado Antropométrico Actual"""
    return html.Div([
        
        # Dashboard de métricas clave
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div(id="antropo-estado-cards", style={"marginBottom": "20px"})
                ], md=12)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading-composicion",
                        type="default", 
                        children=[
                            dcc.Graph(
                                id="antropo-actual-composicion", 
                                style={"height": "900px", "backgroundColor": "transparent"},
                                config={'displayModeBar': False}
                            )
                        ]
                    )
                ], md=6),
                dbc.Col([
                    dcc.Loading(
                        id="loading-peso-grasa",
                        type="default", 
                        children=[
                            html.Div(
                                id="antropo-actual-peso-grasa"
                            )
                        ]
                    )
                ], md=6)
            ], className="mb-3")
        ], style={"padding": "20px"})
    ])

# Colores para jugadores resaltados
COLORES_JUGADORES = [
    '#e74c3c',  # Rojo
    '#3498db',  # Azul
    '#2ecc71',  # Verde
    '#f39c12',  # Naranja
    '#9b59b6',  # Morado
    '#1abc9c',  # Turquesa
    '#e67e22',  # Naranja oscuro
    '#34495e',  # Gris oscuro
]

FONT_FAMILY = "Montserrat, sans-serif"

def get_evolutivo_antropometrico_content():
    """Contenido de la pestaña Evolutivo Antropométrico"""
    return html.Div([
        
        # Controles de filtrado (solo selector de jugadores)
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("SELECCIONAR JUGADORES PARA RESALTAR:", 
                              style={"fontWeight": "bold", "color": "#1e3d59", "fontSize": "16px", "fontFamily": FONT_FAMILY}),
                    dcc.Dropdown(
                        id="antropo-player-multi-dd", 
                        placeholder="Selecciona hasta 8 jugadores para resaltar",
                        multi=True,
                        style={"fontFamily": FONT_FAMILY}
                    ),
                    html.Div([
                        html.Small("Los jugadores no seleccionados aparecerán en gris tenue. La línea azul oscuro representa la media del equipo.",
                                  style={"color": "#6c757d", "fontStyle": "italic", "fontFamily": FONT_FAMILY})
                    ], style={"marginTop": "8px"})
                ], md=12)
            ], className="mb-3")
        ], style={"padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "8px", "margin": "20px", "border": "2px solid #1e3d59"}),
        
        # Botones de selección de métrica (estilo discreto)
        html.Div([
            html.Div([
                html.Button(
                    "% Grasa Corporal",
                    id="btn-metrica-grasa",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#1e3d59",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "padding": "12px 30px",
                        "fontWeight": "600",
                        "fontSize": "14px",
                        "fontFamily": FONT_FAMILY,
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                        "minWidth": "200px"
                    }
                ),
                html.Button(
                    "Peso Muscular (Lee)",
                    id="btn-metrica-peso-muscular",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 30px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "fontFamily": FONT_FAMILY,
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "marginRight": "10px",
                        "minWidth": "200px"
                    }
                ),
                html.Button(
                    "Σ 6 Pliegues",
                    id="btn-metrica-pliegues",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#f8f9fa",
                        "color": "#6c757d",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "6px",
                        "padding": "12px 30px",
                        "fontWeight": "500",
                        "fontSize": "14px",
                        "fontFamily": FONT_FAMILY,
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "minWidth": "200px"
                    }
                )
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "padding": "20px 0",
                "borderBottom": "1px solid #e9ecef"
            })
        ], style={
            "backgroundColor": "white",
            "marginBottom": "20px"
        }),
        
        # Gráfico evolutivo (un solo gráfico que cambia según selección)
        html.Div([
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        id="loading-evolucion",
                        type="default",
                        color="#1e3d59",
                        children=[
                            html.Div(id="antropo-grafico-evolutivo")
                        ]
                    )
                ], md=12)
            ], className="mb-3")
        ], style={"padding": "20px"})
    ])

layout = standard_page([
    html.Div([
        html.H2("CONTROL ESTADO FUNCIONAL - Antropométrico", 
                className="mb-4", 
                style={
                    "color": "#1e3d59", 
                    "backgroundColor": "transparent",
                    "fontWeight": "600",
                    "textAlign": "center",
                    "padding": "1rem 0"
                })
    ], style={"backgroundColor": "transparent"}),
    
    # Pestañas
    html.Div([
        html.Div([
            html.Button(
                "Estado Antropométrico Actual",
                id="tab-antropo-estado-actual",
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
                "Evolutivo Antropométrico",
                id="tab-antropo-evolutivo",
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
    
    # Contenido de pestañas
    html.Div([
        html.Div([
            html.Div(id="tab-antropo-content", children=get_estado_antropometrico_content()),
            dcc.Store(id="antropo-data-store"),
            dcc.Store(id="antropo-tab-store", data="estado-actual")
        ], style={
            "backgroundColor": "white",
            "borderRadius": "0 0 8px 8px",
            "minHeight": "400px"
        })
    ], className="shadow-sm", style={"border": "1px solid #e9ecef", "borderRadius": "8px"})
])


def _empty_fig(title: str):
    """Crear figura vacía con mensaje profesional"""
    fig = go.Figure()
    fig.update_layout(
        title={"text": title, "x": 0.5, "font": {"size": 16, "color": "#1e3d59"}},
        template="plotly_white",
        height=350,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor='rgba(248,249,250,0.8)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text="📊 Sin datos disponibles",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16, color="#6c757d"),
                align="center"
            )
        ]
    )
    return fig


# Callbacks para navegación entre pestañas
@callback(
    [Output("tab-antropo-content", "children"),
     Output("tab-antropo-estado-actual", "style"),
     Output("tab-antropo-evolutivo", "style"),
     Output("antropo-tab-store", "data")],
    [Input("tab-antropo-estado-actual", "n_clicks"),
     Input("tab-antropo-evolutivo", "n_clicks")],
    [State("antropo-tab-store", "data")],
    prevent_initial_call=False
)
def cambiar_tab_antropo(estado_clicks, evolutivo_clicks, current_tab):
    ctx = callback_context
    
    # Estilos para pestañas
    style_active = {
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
    
    style_inactive = {
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
    
    # Carga inicial: mostrar Estado Actual como activo por defecto
    if not ctx.triggered:
        return get_estado_antropometrico_content(), style_active, style_inactive, "estado-actual"
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "tab-antropo-estado-actual":
        return (get_estado_antropometrico_content(), 
                style_active, style_inactive, "estado-actual")
    elif button_id == "tab-antropo-evolutivo":
        return (get_evolutivo_antropometrico_content(), 
                style_inactive, style_active, "evolutivo")
    
    return get_estado_antropometrico_content(), style_active, style_inactive, "estado-actual"

# Callbacks para la pestaña Estado Antropométrico
@lru_cache(maxsize=32)
def get_cached_anthropometry_data(category, cache_key):
    """Cache para datos antropométricos - se actualiza cada minuto"""
    return get_team_anthropometry_timeseries(category=category)

@callback(
    [Output("antropo-estado-cards", "children"),
     Output("antropo-actual-composicion", "figure"),
     Output("antropo-actual-peso-grasa", "children")],
    [Input("antropo-tab-store", "data")],
    prevent_initial_call=False
)
def update_antropo_dashboard(current_tab):
    """Actualiza el dashboard visual solo cuando está en la pestaña Estado"""
    if current_tab != "estado-actual":
        return html.Div(), _empty_fig("Ranking % Grasa"), html.Div()
    
    try:
        # Obtener datos antropométricos con caché (se renueva cada minuto)
        cache_key = datetime.now().strftime('%Y%m%d%H%M')
        df_current = get_cached_anthropometry_data("Primer Equipo", cache_key)
        
        if df_current is None or df_current.empty:
            return (
                html.Div([
                    dbc.Alert("No hay datos disponibles", color="warning", className="text-center")
                ]),
                _empty_fig("Ranking % Grasa"),
                html.Div()
            )
        
        # Optimizar conversión de fecha y filtrado
        df_current['fecha'] = pd.to_datetime(df_current['fecha'], format='%Y-%m-%d', errors='coerce')
        fecha_ultima_medicion = df_current['fecha'].max()
        
        # Filtrado optimizado en una sola operación
        mask = ((df_current['fecha'] == fecha_ultima_medicion) & 
                ((df_current["pct_grasa"].notna()) | 
                 (df_current["kg_a_bajar"].notna()) | 
                 (df_current["sum_pliegues"].notna())))
        df_display = df_current[mask].copy()
        
        # Verificar si hay datos válidos
        if df_display.empty:
            return (
                html.Div([
                    dbc.Alert("No hay datos para la fecha más reciente", color="warning", className="text-center")
                ]),
                _empty_fig("Ranking % Grasa"),
                html.Div()
            )
        
        # Calcular estadísticas de forma más eficiente
        total_jugadores = len(df_display)
        
        # Usar .loc para evitar warnings y mejorar rendimiento
        peso_col = df_display.loc[df_display["peso"].notna(), "peso"]
        grasa_col = df_display.loc[df_display["pct_grasa"].notna(), "pct_grasa"]
        pliegues_col = df_display.loc[df_display["sum_pliegues"].notna(), "sum_pliegues"]
        kg_col = df_display.loc[df_display["kg_a_bajar"].notna(), "kg_a_bajar"]
        
        peso_promedio = peso_col.mean() if not peso_col.empty else 0
        grasa_promedio = grasa_col.mean() if not grasa_col.empty else 0
        pliegues_promedio = pliegues_col.mean() if not pliegues_col.empty else 0
        kg_bajar_promedio = kg_col.mean() if not kg_col.empty else 0
        
        # Determinar colores según los umbrales
        if grasa_promedio <= 10.0:
            color_grasa = "#28a745"  # Verde - Óptimo
            estado_grasa = "ÓPTIMO"
        elif grasa_promedio <= 10.5:
            color_grasa = "#ffc107"  # Amarillo - Aceptable
            estado_grasa = "ACEPTABLE"
        else:
            color_grasa = "#dc3545"  # Rojo - Alto
            estado_grasa = "ALTO"
            
        # Color para kg a bajar (negativo = debe ganar peso = verde, positivo = sobrepeso = rojo)
        if kg_bajar_promedio <= 0:
            color_kg = "#28a745"  # Verde - peso adecuado o debe ganar
        else:
            color_kg = "#dc3545"  # Rojo - sobrepeso promedio
        
        # Crear cards superiores con la nueva información
        cards = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{fecha_ultima_medicion.strftime('%d/%m/%Y')}", className="text-center mb-1", style={"fontSize": "14px", "fontWeight": "bold", "color": "#6c757d"}),
                        html.H4(f"{total_jugadores}", className="text-center mb-0", style={"fontSize": "32px", "fontWeight": "bold", "color": "#007bff"}),
                        html.P("Jugadores Evaluados", className="text-center text-muted mb-0", style={"fontSize": "13px"})
                    ])
                ], className="h-100", style={"backgroundColor": "#f8f9fa", "border": "2px solid #007bff"})
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{peso_promedio:.1f} kg", className="text-center mb-1", style={"fontSize": "14px", "fontWeight": "bold", "color": "#6c757d"}),
                        html.H4(f"{grasa_promedio:.1f}%", className="text-center mb-0", style={"fontSize": "32px", "fontWeight": "bold", "color": color_grasa}),
                        html.P(f"% Grasa Promedio ({estado_grasa})", className="text-center text-muted mb-0", style={"fontSize": "13px"})
                    ])
                ], className="h-100", style={"backgroundColor": "#f8f9fa", "border": f"2px solid {color_grasa}"})
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"{pliegues_promedio:.1f} mm", className="text-center mb-1", style={"fontSize": "14px", "fontWeight": "bold", "color": "#6c757d"}),
                        html.H4(f"{kg_bajar_promedio:.1f} kg", className="text-center mb-0", style={"fontSize": "32px", "fontWeight": "bold", "color": color_kg}),
                        html.P("Kg Promedio a Bajar", className="text-center text-muted mb-0", style={"fontSize": "13px"})
                    ])
                ], className="h-100", style={"backgroundColor": "#f8f9fa", "border": f"2px solid {color_kg}"})
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Última Medición", className="text-center mb-1", style={"fontSize": "14px", "fontWeight": "bold", "color": "#6c757d"}),
                        html.H4(f"{fecha_ultima_medicion.strftime('%d/%m')}", className="text-center mb-0", style={"fontSize": "32px", "fontWeight": "bold", "color": "#17a2b8"}),
                        html.P(f"{fecha_ultima_medicion.strftime('%Y')}", className="text-center text-muted mb-0", style={"fontSize": "13px"})
                    ])
                ], className="h-100", style={"backgroundColor": "#f8f9fa", "border": "2px solid #17a2b8"})
            ], width=3)
        ], className="mb-4")
        
        # ===== GRÁFICO RANKING % GRASA CORPORAL =====
        # Filtrar jugadores con datos de % grasa válidos
        grasa_data = df_display[df_display["pct_grasa"].notna()].copy()
        
        if len(grasa_data) > 0:
            # Ordenar por % grasa (menor a mayor es mejor)
            grasa_data = grasa_data.sort_values("pct_grasa", ascending=True)
            
            # Función para asignar colores según % grasa
            def get_grasa_color(pct_grasa):
                if 8 <= pct_grasa <= 10:
                    return '#28a745'  # Verde
                elif 10 < pct_grasa <= 10.5:
                    return '#ffc107'  # Amarillo
                else:
                    return '#dc3545'  # Rojo
            
            colors = [get_grasa_color(x) for x in grasa_data["pct_grasa"]]
            
            fig_composicion = go.Figure(data=[
                go.Bar(
                    y=grasa_data["player_name"],
                    x=grasa_data["pct_grasa"],
                    orientation='h',
                    marker=dict(
                        color=colors,
                        line=dict(color='white', width=1)
                    ),
                    text=[f"{x:.1f}%" for x in grasa_data["pct_grasa"]],
                    textposition='auto',
                    textfont=dict(size=15, color="#1e3d59", weight="bold", family="Montserrat, sans-serif"),
                    hovertemplate='<b>%{y}</b><br>% Grasa: %{x:.1f}%<extra></extra>'
                )
            ])
            
            fig_composicion.update_layout(
                title={"text": "RANKING COMPOSICIÓN CORPORAL (% GRASA)", "x": 0.5, "font": {"size": 22, "color": "#1e3d59", "weight": "bold", "family": "Montserrat, sans-serif"}},
                height=900,
                margin=dict(l=160, r=80, t=90, b=50),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                font=dict(family="Montserrat, sans-serif"),
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='rgba(128,128,128,0.3)', 
                    tickfont=dict(size=14, weight="bold", family="Montserrat, sans-serif"),
                    title=dict(text="% GRASA CORPORAL", font=dict(color="#1e3d59", size=16, weight="bold", family="Montserrat, sans-serif")),
                    range=[6, max(grasa_data["pct_grasa"]) * 1.1]
                ),
                yaxis=dict(
                    showgrid=False, 
                    tickfont=dict(size=13, weight="bold", family="Montserrat, sans-serif"),
                    title=dict(text="JUGADORES", font=dict(color="#1e3d59", size=16, weight="bold", family="Montserrat, sans-serif")),
                    categoryorder='array',
                    categoryarray=grasa_data["player_name"].tolist()
                )
            )
        else:
            fig_composicion = _empty_fig("Ranking % Grasa Corporal")
        
        # ===== CARD JUGADORES CON SOBREPESO =====
        # Filtrar jugadores con kg_a_bajar positivos (sobrepeso)
        sobrepeso_data = df_display[(df_display["kg_a_bajar"].notna()) & (df_display["kg_a_bajar"] > 0)].copy()
        
        if len(sobrepeso_data) > 0:
            sobrepeso_data = sobrepeso_data.sort_values("kg_a_bajar", ascending=False)
            
            # Crear tabla de forma más eficiente usando list comprehension
            tabla_data = [
                {
                    "Jugador": row["player_name"],
                    "Kg a Bajar": f"{row['kg_a_bajar']:.1f} kg"
                }
                for _, row in sobrepeso_data.iterrows()
            ]
            
            sobrepeso_card = dbc.Card([
                dbc.CardHeader([
                    html.H4("⚠️ JUGADORES CON SOBREPESO", 
                           className="text-center mb-0", 
                           style={"color": "#dc3545", "fontWeight": "bold"})
                ], style={"backgroundColor": "#fff5f5", "border": "1px solid #fed7d7"}),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=tabla_data,
                        columns=[
                            {"name": "Jugador", "id": "Jugador", "type": "text"},
                            {"name": "Kg a Bajar", "id": "Kg a Bajar", "type": "text"}
                        ],
                        style_cell={
                            'textAlign': 'center',
                            'fontWeight': 'bold',
                            'fontSize': '15px',
                            'fontFamily': 'Montserrat, sans-serif',
                            'padding': '12px',
                            'border': '1px solid #e2e8f0',
                            'backgroundColor': 'white'
                        },
                        style_header={
                            'backgroundColor': '#dc3545',
                            'color': 'white',
                            'fontWeight': 'bold',
                            'fontSize': '17px',
                            'fontFamily': 'Montserrat, sans-serif',
                            'textAlign': 'center',
                            'border': '1px solid #dc3545'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#f8f9fa'
                            }
                        ],
                        page_size=10,
                        sort_action="native"
                    )
                ], style={"height": "620px", "overflowY": "auto"})
            ], style={"height": "720px", "border": "2px solid #dc3545"})
        else:
            # Card verde si no hay jugadores con sobrepeso
            sobrepeso_card = dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H3("✅ EXCELENTE", 
                               className="text-center mb-3", 
                               style={"color": "#28a745", "fontWeight": "bold", "fontSize": "32px"}),
                        html.H5("NO HAY JUGADORES CON SOBREPESO", 
                               className="text-center mb-4",
                               style={"color": "#28a745", "fontWeight": "bold"}),
                        html.P("Todos los jugadores mantienen un peso corporal adecuado según los estándares establecidos.",
                               className="text-center",
                               style={"color": "#155724", "fontSize": "16px"})
                    ], className="d-flex flex-column justify-content-center align-items-center", 
                       style={"height": "100%"})
                ], style={"height": "620px", "backgroundColor": "#d4edda"})
            ], style={"height": "720px", "border": "3px solid #28a745", "backgroundColor": "#d4edda"})
        
        return cards, fig_composicion, sobrepeso_card
        
    except Exception as e:
        print(f"[ERROR] Dashboard antropométrico: {str(e)}")
        error_card = dbc.Alert(
            [
                html.I(className="fas fa-exclamation-circle me-2"),
                f"Error al cargar el dashboard: {str(e)}"
            ],
            color="danger",
            className="text-center"
        )
        return (error_card, 
               _empty_fig("Ranking % Grasa"), 
               html.Div())


# Callback para cargar opciones de jugadores (multi-select)
@callback(
    Output("antropo-player-multi-dd", "options"),
    Input("antropo-tab-store", "data"),
    prevent_initial_call=False
)
def load_evolutivo_players(current_tab):
    if current_tab != "evolutivo":
        return []
        
    # Obtener datos de jugadores de primer equipo
    ts = get_cached_anthropometry_data("Primer Equipo", datetime.now().strftime('%Y%m%d%H%M'))
    
    if ts is None or ts.empty:
        return []
    
    # Obtener jugadores únicos
    players = sorted(ts["player_name"].dropna().unique().tolist())
    opts = [{"label": p, "value": p} for p in players]
    
    return opts


@callback(
    [
        Output("antropo-grafico-evolutivo", "children"),
        Output("btn-metrica-grasa", "style"),
        Output("btn-metrica-peso-muscular", "style"),
        Output("btn-metrica-pliegues", "style")
    ],
    [
        Input("btn-metrica-grasa", "n_clicks"),
        Input("btn-metrica-peso-muscular", "n_clicks"),
        Input("btn-metrica-pliegues", "n_clicks"),
        Input("antropo-player-multi-dd", "value"),
        Input("antropo-tab-store", "data")
    ],
    prevent_initial_call=False
)
def update_antropo_evolution_chart(n_grasa, n_peso, n_pliegues, selected_players, current_tab):
    """Actualiza el gráfico evolutivo según la métrica seleccionada"""
    # Estilos para botones
    style_active = {
        "backgroundColor": "#1e3d59",
        "color": "white",
        "border": "none",
        "borderRadius": "6px",
        "padding": "12px 30px",
        "fontWeight": "600",
        "fontSize": "14px",
        "fontFamily": FONT_FAMILY,
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "minWidth": "200px"
    }
    style_inactive = {
        "backgroundColor": "#f8f9fa",
        "color": "#6c757d",
        "border": "1px solid #e9ecef",
        "borderRadius": "6px",
        "padding": "12px 30px",
        "fontWeight": "500",
        "fontSize": "14px",
        "fontFamily": FONT_FAMILY,
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "marginRight": "10px",
        "minWidth": "200px"
    }
    
    if current_tab != "evolutivo":
        empty_msg = html.Div("Carga la pestaña Evolutivo para ver los gráficos", 
                            style={"textAlign": "center", "padding": "20px", "fontFamily": FONT_FAMILY})
        return empty_msg, style_active, style_inactive, style_inactive
    
    # Determinar qué botón fue presionado
    ctx = callback_context
    if not ctx.triggered:
        metrica_seleccionada = 'pct_grasa'  # Por defecto grasa
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'btn-metrica-peso-muscular':
            metrica_seleccionada = 'peso_muscular'
        elif button_id == 'btn-metrica-pliegues':
            metrica_seleccionada = 'sum_pliegues'
        else:
            metrica_seleccionada = 'pct_grasa'
    
    # Actualizar estilos de botones
    style_grasa = style_active if metrica_seleccionada == 'pct_grasa' else style_inactive
    style_peso = style_active if metrica_seleccionada == 'peso_muscular' else style_inactive
    style_pliegues = style_active if metrica_seleccionada == 'sum_pliegues' else style_inactive
    
    try:
        # Obtener datos evolutivos
        df = get_cached_anthropometry_data("Primer Equipo", datetime.now().strftime('%Y%m%d%H%M'))
        
        if df is None or df.empty:
            empty_msg = html.Div("Sin datos disponibles", 
                                style={"textAlign": "center", "padding": "20px", "fontFamily": FONT_FAMILY})
            return empty_msg, style_grasa, style_peso, style_pliegues
        
        # Convertir fecha
        df['fecha'] = pd.to_datetime(df['fecha'])
        
        # Renombrar columna para consistencia
        if 'player_name' in df.columns:
            df = df.rename(columns={'player_name': 'nombre'})
        
        # Crear diccionario de jugadores resaltados con colores
        jugadores_resaltados = {}
        if selected_players:
            for i, jugador in enumerate(selected_players[:8]):  # Máximo 8 jugadores
                jugadores_resaltados[jugador] = COLORES_JUGADORES[i % len(COLORES_JUGADORES)]
        
        # Generar el gráfico según la métrica seleccionada
        fig = crear_grafico_evolutivo(df, jugadores_resaltados, metrica_seleccionada)
        
        return fig, style_grasa, style_peso, style_pliegues
        
    except Exception as e:
        print(f"[ERROR] Gráfico evolutivo: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = html.Div(f"Error al cargar gráfico: {str(e)}", 
                            style={"textAlign": "center", "padding": "20px", "color": "red", "fontFamily": FONT_FAMILY})
        return error_msg, style_grasa, style_peso, style_pliegues


def create_grasa_evolution_chart(df, player):
    """Crea gráfico de evolución de grasa corporal con bandas"""
    if player == ALL_VAL:
        # Promedio del equipo
        df_grasa = df.groupby('fecha')['pct_grasa'].mean().reset_index()
        title = "Evolución Promedio % Grasa Corporal del Equipo"
    else:
        # Jugador individual
        df_grasa = df[df['pct_grasa'].notna()].copy()
        title = f"Evolución % Grasa Corporal - {player if player else 'Jugador'}"
    
    if df_grasa.empty:
        return _empty_fig("Sin datos de grasa")
    
    fig = go.Figure()
    
    # Ordenar datos por fecha para evitar líneas que van hacia atrás
    df_grasa = df_grasa.sort_values('fecha')
    
    # Bandas de referencia (estilo médico)
    fig.add_hrect(
        y0=7, y1=8, 
        fillcolor="rgba(220, 53, 69, 0.1)", line_width=0,
        annotation_text="Muy Bajo", annotation_position="left",
        annotation=dict(font_size=12, font_color="#dc3545", font_family="Montserrat, sans-serif")
    )
    fig.add_hrect(
        y0=8, y1=10, 
        fillcolor="rgba(40, 167, 69, 0.15)", line_width=0,
        annotation_text="Óptimo", annotation_position="left",
        annotation=dict(font_size=12, font_color="#28a745", font_family="Montserrat, sans-serif")
    )
    fig.add_hrect(
        y0=10, y1=10.5, 
        fillcolor="rgba(255, 193, 7, 0.15)", line_width=0,
        annotation_text="Aceptable", annotation_position="left",
        annotation=dict(font_size=12, font_color="#ffc107", font_family="Montserrat, sans-serif")
    )
    fig.add_hrect(
        y0=10.5, y1=12, 
        fillcolor="rgba(220, 53, 69, 0.1)", line_width=0,
        annotation_text="Alto", annotation_position="left",
        annotation=dict(font_size=12, font_color="#dc3545", font_family="Montserrat, sans-serif")
    )
    
    # Línea de evolución
    fig.add_trace(go.Scatter(
        x=df_grasa['fecha'],
        y=df_grasa['pct_grasa'],
        mode='lines+markers',
        line=dict(color='#1e3d59', width=4),
        marker=dict(color='#1e3d59', size=8, line=dict(color='white', width=2)),
        name='% Grasa',
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>% Grasa: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'font': {'size': 20, 'color': '#1e3d59', 'weight': 'bold', 'family': 'Montserrat, sans-serif'}
        },
        xaxis=dict(
            title=dict(text='Fecha', font=dict(color='#1e3d59', size=14, weight='bold', family='Montserrat, sans-serif')),
            tickfont=dict(size=12, family='Montserrat, sans-serif'),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title=dict(text='% Grasa Corporal', font=dict(color='#1e3d59', size=14, weight='bold', family='Montserrat, sans-serif')),
            tickfont=dict(size=12, family='Montserrat, sans-serif'),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            range=[7, 12]
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat, sans-serif'),
        showlegend=False,
        height=500
    )
    
    return fig


def calcular_media_equipo_temporal(df, metrica):
    """Calcula la media del equipo agrupando por fecha"""
    df_media = df.groupby('fecha')[metrica].mean().reset_index()
    df_media.columns = ['fecha_medicion', 'media']
    return df_media


def crear_grafico_evolutivo(df_evolutivo, jugadores_resaltados, metrica):
    """
    Crea gráfico evolutivo con:
    - Líneas individuales de jugadores en gris tenue
    - Líneas de jugadores resaltados en sus colores específicos
    - Línea de media del equipo en azul oscuro destacada
    """
    if df_evolutivo.empty or metrica not in df_evolutivo.columns:
        return html.Div("Sin datos disponibles", style={"textAlign": "center", "padding": "20px", "fontFamily": FONT_FAMILY})
    
    # Renombrar columna para consistencia
    if 'player_name' in df_evolutivo.columns and 'nombre' not in df_evolutivo.columns:
        df_evolutivo = df_evolutivo.rename(columns={'player_name': 'nombre'})
    
    # Asegurar que las fechas sean datetime y filtrar NaT/None
    df_evolutivo['fecha'] = pd.to_datetime(df_evolutivo['fecha'], errors='coerce')
    df_evolutivo = df_evolutivo[df_evolutivo['fecha'].notna()]
    
    if df_evolutivo.empty:
        return html.Div("Sin fechas válidas", style={"textAlign": "center", "padding": "20px", "fontFamily": FONT_FAMILY})
    
    jugadores_resaltados = jugadores_resaltados or {}
    
    fig = go.Figure()
    
    # Añadir líneas individuales de jugadores
    for jugador in sorted(df_evolutivo['nombre'].unique()):
        df_jugador = df_evolutivo[df_evolutivo['nombre'] == jugador].sort_values('fecha')
        
        # Filtrar valores válidos
        df_jugador_valido = df_jugador[df_jugador[metrica].notna()]
        
        # Filtrar valores de 0 en Peso Muscular (Lee)
        if metrica == 'peso_muscular':
            df_jugador_valido = df_jugador_valido[df_jugador_valido[metrica] > 0]
        
        if not df_jugador_valido.empty:
            # Verificar si el jugador está resaltado
            if jugador in jugadores_resaltados:
                color = jugadores_resaltados[jugador]
                line_width = 3
                opacity = 1
                show_legend = True
                marker_size = 8
            else:
                color = 'rgba(150, 150, 150, 0.3)'  # Gris muy tenue
                line_width = 1
                opacity = 1
                show_legend = False
                marker_size = 5
            
            # Preparar hover text
            hover_texts = []
            for _, row in df_jugador_valido.iterrows():
                fecha_str = pd.to_datetime(row['fecha']).strftime('%d/%m/%Y')
                
                # Determinar título de métrica para hover
                if metrica == 'pct_grasa':
                    titulo_metrica = '% Grasa Corporal'
                    valor_str = f"{row[metrica]:.2f}%"
                elif metrica == 'peso_muscular':
                    titulo_metrica = 'Peso Muscular (Lee)'
                    valor_str = f"{row[metrica]:.2f} kg"
                elif metrica == 'sum_pliegues':
                    titulo_metrica = 'Σ 6 Pliegues'
                    valor_str = f"{row[metrica]:.2f} mm"
                else:
                    titulo_metrica = metrica
                    valor_str = f"{row[metrica]:.2f}"
                
                hover_texts.append(
                    f"<b>{jugador}</b><br>" +
                    f"Fecha: {fecha_str}<br>" +
                    f"{titulo_metrica}: {valor_str}"
                )
            
            fig.add_trace(go.Scatter(
                x=df_jugador_valido['fecha'],
                y=df_jugador_valido[metrica],
                mode='lines+markers',  # Añadir markers (puntos)
                name=jugador,
                line=dict(color=color, width=line_width),
                marker=dict(size=marker_size, color=color),
                opacity=opacity,
                hovertemplate='%{customdata}<extra></extra>',
                customdata=hover_texts,
                showlegend=show_legend
            ))
    
    # Calcular y añadir línea de media del equipo (azul oscuro destacada)
    df_media = calcular_media_equipo_temporal(df_evolutivo, metrica)
    
    if not df_media.empty:
        # Determinar título de métrica para hover de media
        if metrica == 'pct_grasa':
            titulo_metrica = '% Grasa Corporal'
            unidad = '%'
        elif metrica == 'peso_muscular':
            titulo_metrica = 'Peso Muscular (Lee)'
            unidad = 'kg'
        elif metrica == 'sum_pliegues':
            titulo_metrica = 'Σ 6 Pliegues'
            unidad = 'mm'
        else:
            titulo_metrica = metrica
            unidad = ''
        
        fig.add_trace(go.Scatter(
            x=df_media['fecha_medicion'],
            y=df_media['media'],
            mode='lines+markers',
            name='Media del Equipo',
            line=dict(color='#0d3b66', width=4),  # Azul oscuro, línea gruesa
            marker=dict(size=8, color='#0d3b66'),
            hovertemplate=f'<b>Media del Equipo</b><br>Fecha: %{{x|%d/%m/%Y}}<br>{titulo_metrica}: %{{y:.2f}}{unidad}<extra></extra>',
            showlegend=True
        ))
    
    # Configurar layout y añadir bandas de color para grasa corporal
    if metrica == 'pct_grasa':
        titulo_metrica = '% Grasa Corporal'
        titulo_eje = '% Grasa Corporal'
        unidad = '%'
        
        # Añadir bandas de color (verde: <10%, amarillo: 10-12%, rojo: >12%)
        # Obtener rango de fechas
        all_dates = df_evolutivo['fecha'].dropna()
        if not all_dates.empty:
            x0 = all_dates.min()
            x1 = all_dates.max()
            
            # Banda verde (< 10%)
            fig.add_shape(
                type="rect",
                x0=x0, x1=x1,
                y0=0, y1=10,
                fillcolor="rgba(46, 204, 113, 0.15)",  # Verde tenue
                line=dict(width=0),
                layer="below"
            )
            
            # Banda amarilla (10-12%)
            fig.add_shape(
                type="rect",
                x0=x0, x1=x1,
                y0=10, y1=12,
                fillcolor="rgba(241, 196, 15, 0.15)",  # Amarillo tenue
                line=dict(width=0),
                layer="below"
            )
            
            # Banda roja (> 12%)
            fig.add_shape(
                type="rect",
                x0=x0, x1=x1,
                y0=12, y1=25,  # Límite superior arbitrario
                fillcolor="rgba(231, 76, 60, 0.15)",  # Rojo tenue
                line=dict(width=0),
                layer="below"
            )
            
    elif metrica == 'peso_muscular':
        titulo_metrica = 'Peso Muscular'
        titulo_eje = 'Peso Muscular (Lee)'
        unidad = 'kg'
    elif metrica == 'sum_pliegues':
        titulo_metrica = 'Suma de 6 Pliegues'
        titulo_eje = 'Suma de 6 Pliegues'
        unidad = 'mm'
    else:
        titulo_metrica = metrica
        titulo_eje = metrica
        unidad = ''
    
    # Configurar eje Y según métrica
    yaxis_config = dict(
        title=dict(text=f"{titulo_eje} ({unidad})" if unidad else titulo_eje, font=dict(family=FONT_FAMILY)),
        showgrid=True,
        gridcolor='#f0f0f0',
        tickfont=dict(family=FONT_FAMILY)
    )
    
    # Ajustar rango del eje Y según métrica
    if metrica == 'pct_grasa':
        # Grasa corporal: de 8 a 14 (invertido, 8 arriba)
        yaxis_config['range'] = [8, 14]
        yaxis_config['autorange'] = False
    elif metrica == 'peso_muscular':
        # Peso muscular: rango automático con margen
        yaxis_config['autorange'] = True
        yaxis_config['rangemode'] = 'tozero'
    elif metrica == 'sum_pliegues':
        # Suma de pliegues: rango automático
        yaxis_config['autorange'] = True
    
    fig.update_layout(
        title=dict(
            text=f"Evolución: {titulo_metrica}",
            font=dict(family=FONT_FAMILY, size=18, color='#0d3b66'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text="Fecha", font=dict(family=FONT_FAMILY)),
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(family=FONT_FAMILY)
        ),
        yaxis=yaxis_config,
        height=600,
        template="plotly_white",
        font=dict(family=FONT_FAMILY),
        hovermode='closest',
        margin=dict(l=80, r=40, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(family=FONT_FAMILY, size=12)
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return dcc.Graph(figure=fig, config={"displayModeBar": False})


def create_peso_vs_ideal_chart(df, player):
    """Crea gráfico peso actual vs peso ideal de toda la plantilla"""
    if player == ALL_VAL:
        # Promedio del equipo
        df_peso = df.groupby('fecha').agg({
            'peso': 'mean',
            'kg_a_bajar': 'mean'
        }).reset_index()
        title = "Evolución Peso Actual vs Peso Ideal - Promedio Equipo"
    else:
        # Jugador individual
        df_peso = df[df['peso'].notna()].copy()
        title = f"Evolución Peso Actual vs Peso Ideal - {player if player else 'Jugador'}"
    
    if df_peso.empty:
        return _empty_fig("Sin datos de peso")
    
    # Ordenar por fecha
    df_peso = df_peso.sort_values('fecha')
    
    # Calcular peso ideal correctamente: peso - kg_a_bajar
    df_peso['peso_ideal'] = df_peso['peso'] - df_peso['kg_a_bajar'].fillna(0)
    
    fig = go.Figure()
    
    # Línea peso actual
    fig.add_trace(go.Scatter(
        x=df_peso['fecha'],
        y=df_peso['peso'],
        mode='lines+markers',
        line=dict(color='#007bff', width=3),
        marker=dict(color='#007bff', size=7),
        name='Peso Actual',
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Peso Actual: %{y:.1f} kg<extra></extra>'
    ))
    
    # Línea peso ideal
    fig.add_trace(go.Scatter(
        x=df_peso['fecha'],
        y=df_peso['peso_ideal'],
        mode='lines+markers',
        line=dict(color='#28a745', width=3, dash='dash'),
        marker=dict(color='#28a745', size=7),
        name='Peso Ideal',
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Peso Ideal: %{y:.1f} kg<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'font': {'size': 18, 'color': '#1e3d59', 'weight': 'bold', 'family': 'Montserrat, sans-serif'}
        },
        xaxis=dict(
            title=dict(text='Fecha', font=dict(color='#1e3d59', size=12, weight='bold', family='Montserrat, sans-serif')),
            tickfont=dict(size=11, family='Montserrat, sans-serif')
        ),
        yaxis=dict(
            title=dict(text='Peso (kg)', font=dict(color='#1e3d59', size=12, weight='bold', family='Montserrat, sans-serif')),
            tickfont=dict(size=11, family='Montserrat, sans-serif')
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Montserrat, sans-serif'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=450
    )
    
    return fig


# Función eliminada - ahora se usa create_peso_pliegues_combined_chart
