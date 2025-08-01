# utils/layouts.py

from dash import html, dcc
import dash_bootstrap_components as dbc

def dashboard_layout():
    """
    Crea el layout principal del dashboard con una barra lateral de navegación.
    """
    return html.Div([
        # Contenedor con flexbox para mejor distribución del sidebar y contenido
        html.Div([
            # Barra lateral (sidebar)
            html.Div([
                html.Div([
                    html.Img(src="/assets/escudo_depor.png", style={"height": "60px"}),
                ], className="d-flex flex-column align-items-center mb-4"),
                
                # Elementos de navegación
                html.Div([
                    dbc.NavLink(
                        [html.I(className="fas fa-home me-2"), "🏠 Inicio"],
                        href="/inicio",
                        active="exact",
                        className="py-3 text-white"
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-chart-line me-2"), "📈 Seguimiento de Carga"],
                        href="/seguimiento-carga",
                        active="exact",
                        className="py-3 text-white"
                    ),
                ], className="nav flex-column")
            ], 
            className="sidebar",
            style={
                "background": "#0d3b66", 
                "height": "100vh",
                "position": "fixed",
                "top": 0,
                "left": 0,
                "padding": "1.5rem 1rem",
                "color": "white",
                "width": "250px",
                "zIndex": "1000"
            }),
            
            # Contenido principal
            html.Div([
                # Aquí va el contenido de cada página
                html.Div(id="page-content")
            ], 
            className="content-container",
            style={
                "padding": "1.5rem",
                "marginLeft": "250px",
                "width": "calc(100% - 250px)",
                "minHeight": "100vh"
            })
        ], style={"display": "flex", "width": "100%"})
    ], style={"width": "100%"})


def standard_page(content):
    """
    Formato estándar para las páginas.
    
    Args:
        content: Lista de elementos Dash para mostrar en la página
    """
    return html.Div([
        dbc.Container([
            dbc.Card(
                dbc.CardBody(content),
                className="shadow-sm mb-4",
                style={"background": "rgba(255, 255, 255, 0.95)"}  # Card blanco semi-transparente
            )
        ],
            className="py-3",
            fluid=True
        )
    ], id="page-content")
