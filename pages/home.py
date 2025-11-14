# pages/home.py

from dash import html, dcc
import dash_bootstrap_components as dbc

def get_layout(roles=None):
    """
    Genera el layout de inicio dinámicamente según los roles del usuario.
    Solo muestra los cards y enlaces a los que el usuario tiene acceso.
    """
    if roles is None:
        roles = []
    
    # Helper para verificar acceso
    def has_access(required_roles):
        if "admin" in roles or "direccion" in roles:
            return True
        return any(role in roles for role in required_roles)
    
    # Construir cards según permisos
    cards = []
    
    # Primera fila
    first_row_cards = []
    
    # Control Estado Funcional - visible si tiene acceso a alguna subsección
    if has_access(["admin", "direccion", "medico", "nutricion", "psicologo"]):
        subsections = []
        if has_access(["admin", "direccion"]):
            subsections.append(
                dbc.ListGroupItem([
                    dcc.Link([
                        html.I(className="fas fa-dumbbell me-2", style={"color": "#6c757d"}),
                        "Capacidad Funcional"
                    ], href="/estado-funcional/capacidad", className="text-decoration-none", style={"color": "#495057"})
                ], action=True)
            )
        if has_access(["admin", "direccion", "medico"]):
            subsections.append(
                dbc.ListGroupItem([
                    dcc.Link([
                        html.I(className="fas fa-stethoscope me-2", style={"color": "#6c757d"}),
                        "Médico"
                    ], href="/estado-funcional/medico", className="text-decoration-none", style={"color": "#495057"})
                ], action=True)
            )
        if has_access(["admin", "direccion", "psicologo"]):
            subsections.append(
                dbc.ListGroupItem([
                    dcc.Link([
                        html.I(className="fas fa-brain me-2", style={"color": "#6c757d"}),
                        "Psicológico"
                    ], href="/estado-funcional/psicologico", className="text-decoration-none", style={"color": "#495057"})
                ], action=True)
            )
        if has_access(["admin", "direccion", "nutricion"]):
            subsections.append(
                dbc.ListGroupItem([
                    dcc.Link([
                        html.I(className="fas fa-ruler me-2", style={"color": "#6c757d"}),
                        "Antropométrico"
                    ], href="/estado-funcional/antropometrico", className="text-decoration-none", style={"color": "#495057"})
                ], action=True)
            )
        
        if subsections:
            first_row_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="fas fa-heartbeat me-2", style={"color": "#1e3d59"}),
                            html.H5("Control Estado Funcional", className="mb-0", style={"color": "#1e3d59", "fontWeight": "600"})
                        ], style={"background": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}),
                        dbc.CardBody([
                            html.P("Evaluación multidimensional del estado del jugador", className="text-muted small mb-3"),
                            dbc.ListGroup(subsections, flush=True)
                        ])
                    ], className="h-100 shadow-sm")
                ], md=6, className="mb-4")
            )
    
    # Control Proceso Entrenamiento
    if has_access(["admin", "direccion", "analista", "preparador"]):
        first_row_cards.append(
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
                                    html.I(className="fas fa-users me-2", style={"color": "#6c757d"}),
                                    "Entrenamiento Equipo"
                                ], href="/entrenamiento-equipo", className="text-decoration-none", style={"color": "#495057"})
                            ], action=True),
                            dbc.ListGroupItem([
                                dcc.Link([
                                    html.I(className="fas fa-user me-2", style={"color": "#6c757d"}),
                                    "Entrenamiento Jugadores"
                                ], href="/entrenamiento-jugadores", className="text-decoration-none", style={"color": "#495057"})
                            ], action=True),
                        ], flush=True)
                    ])
                ], className="h-100 shadow-sm")
            ], md=6, className="mb-4")
        )
    
    if first_row_cards:
        cards.append(dbc.Row(first_row_cards))
    
    # Segunda fila
    second_row_cards = []
    
    # Control Proceso Competición
    if has_access(["admin", "direccion", "analista"]):
        second_row_cards.append(
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
                                    html.I(className="fas fa-users-cog me-2", style={"color": "#6c757d"}),
                                    "Rendimiento Colectivo"
                                ], href="/control-proceso-competicion/rendimiento-colectivo", className="text-decoration-none", style={"color": "#495057"})
                            ], action=True),
                            dbc.ListGroupItem([
                                dcc.Link([
                                    html.I(className="fas fa-user-chart me-2", style={"color": "#6c757d"}),
                                    "Rendimiento Individual"
                                ], href="/control-proceso-competicion/rendimiento-individual", className="text-decoration-none", style={"color": "#495057"})
                            ], action=True),
                        ], flush=True)
                    ])
                ], className="h-100 shadow-sm")
            ], md=6, className="mb-4")
        )
    
    # Herramientas
    if has_access(["admin", "direccion", "analista"]):
        herramientas_items = []
        herramientas_items.append(
            dbc.ListGroupItem([
                dcc.Link([
                    html.I(className="fas fa-user me-2", style={"color": "#6c757d"}),
                    "Ficha Jugador"
                ], href="/ficha-jugador", className="text-decoration-none", style={"color": "#495057"})
            ], action=True)
        )
        herramientas_items.append(
            dbc.ListGroupItem([
                dcc.Link([
                    html.I(className="fas fa-traffic-light me-2", style={"color": "#6c757d"}),
                    "Semáforo Control"
                ], href="/semaforo-control", className="text-decoration-none", style={"color": "#495057"})
            ], action=True)
        )
        
        second_row_cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-tools me-2", style={"color": "#1e3d59"}),
                        html.H5("Herramientas", className="mb-0", style={"color": "#1e3d59", "fontWeight": "600"})
                    ], style={"background": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}),
                    dbc.CardBody([
                        html.P("Análisis individual y control general", className="text-muted small mb-3"),
                        dbc.ListGroup(herramientas_items, flush=True)
                    ])
                ], className="h-100 shadow-sm")
            ], md=6, className="mb-4")
        )
    
    if second_row_cards:
        cards.append(dbc.Row(second_row_cards))
    
    # Si no hay cards (no debería pasar), mostrar mensaje
    if not cards:
        cards = [
            html.Div([
                html.H4("Bienvenido al Sistema de Rendimiento Deportivo", className="text-center text-muted"),
                html.P("Contacta con el administrador para obtener permisos.", className="text-center text-muted")
            ], className="py-5")
        ]
    
    return dbc.Container([
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
        
        # Cards dinámicos
        *cards,
        
        # Mensaje final
        html.Hr(),
        html.P(
            "Selecciona una sección para comenzar el análisis.",
            className="text-center mt-3 text-muted",
            style={"fontSize": "1rem"}
        )
    ], className="py-3", fluid=True)

# Layout por defecto (para compatibilidad)
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
                                html.I(className="fas fa-users me-2", style={"color": "#6c757d"}),
                                "Entrenamiento Equipo"
                            ], href="/entrenamiento-equipo", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-user me-2", style={"color": "#6c757d"}),
                                "Entrenamiento Jugadores"
                            ], href="/entrenamiento-jugadores", className="text-decoration-none", style={"color": "#495057"})
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
                                html.I(className="fas fa-users-cog me-2", style={"color": "#6c757d"}),
                                "Rendimiento Colectivo"
                            ], href="/control-proceso-competicion/rendimiento-colectivo", className="text-decoration-none", style={"color": "#495057"})
                        ], action=True),
                        dbc.ListGroupItem([
                            dcc.Link([
                                html.I(className="fas fa-user-chart me-2", style={"color": "#6c757d"}),
                                "Rendimiento Individual"
                            ], href="/control-proceso-competicion/rendimiento-individual", className="text-decoration-none", style={"color": "#495057"})
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
