# pages/home.py

from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    # Header principal
    dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Img(src="/assets/ESCUDO-AZUL_RGB-HD.png", className="me-3", style={"height": "68px"}),
                    html.Div([
                        html.H2("Departamento de Rendimiento Deportivo", className="mb-1", 
                               style={"color": "#1e3d59", "fontWeight": "600"}),
                        html.P("RC Deportivo - Sistema de gestión integral", className="mb-0 text-muted")
                    ])
                ], className="d-flex align-items-center"),
            ], className="text-center mb-4"),
        ]),
        className="shadow-sm mb-4",
        style={"background": "#fff", "borderLeft": "4px solid #1e3d59"}
    ),

    # Secciones principales organizadas en cards
    dbc.Row([
        # Control Estado Funcional
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-heartbeat me-2", style={"color": "#1e3d59"}),
                    html.H5("Control Estado Funcional", className="mb-0", style={"color": "#1e3d59", "fontWeight": "600"})
                ], style={"background": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}),
                dbc.CardBody([
                    html.P("Evaluación multidimensional del estado del jugador", className="text-muted small mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-dumbbell me-2", style={"color": "#6c757d"}),
                                "Capacidad Funcional"
                            ], href="/estado-funcional/capacidad", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-stethoscope me-2", style={"color": "#6c757d"}),
                                "Médico"
                            ], href="/estado-funcional/medico", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-brain me-2", style={"color": "#6c757d"}),
                                "Psicológico"
                            ], href="/estado-funcional/psicologico", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-ruler me-2", style={"color": "#6c757d"}),
                                "Antropométrico"
                            ], href="/estado-funcional/antropometrico", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                    ], flush=True)
                ])
            ], className="h-100 shadow-sm")
        ], md=6, className="mb-4"),

        # Control Proceso Entrenamiento
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-clipboard-list me-2", style={"color": "#1e3d59"}),
                    html.H5("Control Proceso Entrenamiento", className="mb-0", style={"color": "#1e3d59", "fontWeight": "600"})
                ], style={"background": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}),
                dbc.CardBody([
                    html.P("Monitorización y optimización del entrenamiento", className="text-muted small mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-calendar-week me-2", style={"color": "#6c757d"}),
                                "Sesiones-Microciclos"
                            ], href="/control-proceso-entrenamiento/sesiones-microciclos", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-chart-line me-2", style={"color": "#6c757d"}),
                                "Evolutivo Temporada"
                            ], href="/control-proceso-entrenamiento/evolutivo-temporada", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                    ], flush=True)
                ])
            ], className="h-100 shadow-sm")
        ], md=6, className="mb-4"),
    ]),

    dbc.Row([
        # Control Proceso Competición (consolidado)
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chess me-2", style={"color": "#1e3d59"}),
                    html.H5("Control Proceso Competición", className="mb-0", style={"color": "#1e3d59", "fontWeight": "600"})
                ], style={"background": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}),
                dbc.CardBody([
                    html.P("Control estratégico y análisis competitivo", className="text-muted small mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-clipboard-check me-2", style={"color": "#6c757d"}),
                                "Post-Partido"
                            ], href="/control-proceso-competicion/post-partido", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-chart-line me-2", style={"color": "#6c757d"}),
                                "Evolutivo Temporada"
                            ], href="/control-proceso-competicion/evolutivo-temporada", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-users me-2", style={"color": "#6c757d"}),
                                "Aprovechamiento de Plantilla"
                            ], href="/control-proceso-competicion/aprovechamiento-plantilla", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-map me-2", style={"color": "#6c757d"}),
                                "Mapas de estilo-rendimiento"
                            ], href="/control-proceso-competicion/mapas-estilo-rendimiento", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                    ], flush=True)
                ])
            ], className="h-100 shadow-sm")
        ], md=6, className="mb-4"),

        # Herramientas
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-tools me-2", style={"color": "#1e3d59"}),
                    html.H5("Herramientas", className="mb-0", style={"color": "#1e3d59", "fontWeight": "600"})
                ], style={"background": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}),
                dbc.CardBody([
                    html.P("Análisis individual y control general", className="text-muted small mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-user me-2", style={"color": "#6c757d"}),
                                "Ficha Jugador"
                            ], href="/ficha-jugador", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-traffic-light me-2", style={"color": "#6c757d"}),
                                "Semáforo Control"
                            ], href="/semaforo-control", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                    ], flush=True)
                ])
            ], className="h-100 shadow-sm")
        ], md=6, className="mb-4"),
    ]),

    # Mensaje final
    html.Hr(),
    html.P(
        "Selecciona una sección para comenzar el análisis.",
        className="text-center mt-3 text-muted",
        style={"fontSize": "1rem"}
    )
], className="py-3", fluid=True)
