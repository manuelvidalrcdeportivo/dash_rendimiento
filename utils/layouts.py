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
                    # INICIO (cabecera clicable, sin subtítulo)
                    dbc.NavLink(
                        [html.I(className="fas fa-home me-2"), "INICIO"],
                        href="/inicio",
                        active="exact",
                        className="py-3 text-white text-uppercase fw-bold small"
                    ),

                    # FICHA DE JUGADOR (cabecera clicable, sin subtítulo)
                    dbc.NavLink(
                        [html.I(className="fas fa-id-card me-2"), "FICHA DE JUGADOR"],
                        href="/ficha-jugador",
                        active="exact",
                        className="py-3 text-white text-uppercase fw-bold small",
                        style={
                            "borderTop": "1px solid rgba(255,255,255,0.2)",
                            "paddingTop": "0.75rem"
                        }
                    ),

                    # SEMÁFORO DE CONTROL (cabecera clicable, sin subtítulo)
                    dbc.NavLink(
                        [html.I(className="fas fa-traffic-light me-2"), "SEMÁFORO DE CONTROL"],
                        href="/semaforo-control",
                        active="exact",
                        className="py-3 text-white text-uppercase fw-bold small",
                        style={
                            "borderTop": "1px solid rgba(255,255,255,0.2)",
                            "paddingTop": "0.75rem"
                        }
                    ),

                    # Sección agrupada colapsable: CONTROL PROCESO ENTRENAMIENTO
                    dbc.Button(
                        [html.I(className="fas fa-dumbbell me-2"), "CONTROL PROCESO ENTRENAMIENTO"],
                        id="toggle-cpe",
                        color="link",
                        className="text-start text-uppercase fw-bold small w-100 text-white",
                        style={
                            "borderTop": "1px solid rgba(255,255,255,0.2)",
                            "paddingTop": "0.75rem",
                            "textDecoration": "none"
                        }
                    ),
                    dbc.Collapse([
                        dbc.NavLink(
                            [html.I(className="fas fa-calendar-day me-2"), "Sesiones Microciclos"],
                            href="/control-proceso-entrenamiento/sesiones-microciclos",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                        dbc.NavLink(
                            [html.I(className="fas fa-chart-area me-2"), "Evolutivo temporada"],
                            href="/control-proceso-entrenamiento/evolutivo-temporada",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                    ], id="collapse-cpe", is_open=False),

                    # Sección agrupada colapsable: CONTROL RENDIMIENTO COMPETICION
                    dbc.Button(
                        [html.I(className="fas fa-trophy me-2"), "CONTROL RENDIMIENTO COMPETICION"],
                        id="toggle-crc",
                        color="link",
                        className="text-start text-uppercase fw-bold small w-100 text-white",
                        style={
                            "borderTop": "1px solid rgba(255,255,255,0.2)",
                            "paddingTop": "0.75rem",
                            "textDecoration": "none"
                        }
                    ),
                    dbc.Collapse([
                        dbc.NavLink(
                            [html.I(className="fas fa-clipboard-check me-2"), "Post Partido"],
                            href="/rendimiento-competicion/post-partido",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                        dbc.NavLink(
                            [html.I(className="fas fa-chart-line me-2"), "Evolutivo Temporada"],
                            href="/rendimiento-competicion/evolutivo-temporada",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                    ], id="collapse-crc", is_open=False),

                    # Sección agrupada colapsable: CONTROL ESTADO FUNCIONAL
                    dbc.Button(
                        [html.I(className="fas fa-heartbeat me-2"), "CONTROL ESTADO FUNCIONAL"],
                        id="toggle-cef",
                        color="link",
                        className="text-start text-uppercase fw-bold small w-100 text-white",
                        style={
                            "borderTop": "1px solid rgba(255,255,255,0.2)",
                            "paddingTop": "0.75rem",
                            "textDecoration": "none"
                        }
                    ),
                    dbc.Collapse([
                        dbc.NavLink(
                            [html.I(className="fas fa-running me-2"), "Capacidad Funcional"],
                            href="/estado-funcional/capacidad",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                        dbc.NavLink(
                            [html.I(className="fas fa-user-md me-2"), "Médico"],
                            href="/estado-funcional/medico",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                        dbc.NavLink(
                            [html.I(className="fas fa-brain me-2"), "Psicológico"],
                            href="/estado-funcional/psicologico",
                            active="exact",
                            className="py-2 text-white-50 ps-4 small"
                        ),
                    ], id="collapse-cef", is_open=False),
                    dbc.NavLink(
                        [html.I(className="fas fa-tools me-2"), "🛠️ Administración"],
                        href="/admin",
                        active="exact",
                        className="py-3 text-white"
                    ),
                ], className="nav flex-column", style={"flex": "1 1 auto"}),

                # Información de usuario + Logout (anclado abajo)
                html.Div(id="sidebar-user",
                    className="mt-3",
                    style={
                        "borderTop": "1px solid rgba(255,255,255,0.2)",
                        "paddingTop": "0.75rem",
                        "color": "rgba(255,255,255,0.85)",
                        "fontSize": "0.9rem"
                    }
                )
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
                "zIndex": "1000",
                "display": "flex",
                "flexDirection": "column"
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
    ])
