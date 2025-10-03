# pages/rendimiento_individual.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.Div([
        html.H2("CONTROL PROCESO COMPETICIÓN - Rendimiento Individual", 
                className="mb-4", 
                style={
                    "color": "#1e3d59", 
                    "fontWeight": "600",
                    "textAlign": "center"
                })
    ]),
    
    html.Div([
        html.Div([
            html.I(className="fas fa-hard-hat fa-5x mb-4", style={"color": "#ffc107"}),
            html.H3("Sección en Desarrollo", style={"color": "#1e3d59", "fontWeight": "600"}),
            html.P(
                "Estamos trabajando en el análisis de rendimiento individual de los jugadores.",
                className="text-muted mt-3",
                style={"fontSize": "16px"}
            ),
            html.P(
                "Esta funcionalidad estará disponible próximamente.",
                className="text-muted",
                style={"fontSize": "14px"}
            )
        ], style={
            "textAlign": "center", 
            "padding": "100px 20px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"
        })
    ], className="mt-4")
])
