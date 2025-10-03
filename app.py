# app.py

import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from core import app               # instanciado con suppress_callback_exceptions=True
from utils.auth_db import validate_user_db, get_user_roles, get_user_id
from utils.layouts import dashboard_layout

# Importar layouts de páginas
from pages.home import layout as home_layout
# Importación eliminada: from pages.jugadores import layout as jugadores_layout
from pages.ficha_jugador import layout as ficha_jugador_layout
from pages.rendimiento_fisico import layout as rendimiento_fisico_layout
from pages.admin import layout as admin_layout
# Nuevas subsecciones: CONTROL ESTADO FUNCIONAL
from pages.estado_funcional_capacidad import layout as ef_capacidad_layout
from pages.estado_funcional_medico import layout as ef_medico_layout
from pages.estado_funcional_psicologico import layout as ef_psico_layout
from pages.estado_funcional_antropometrico import layout as ef_antropo_layout
# Nuevas secciones y subsecciones: CONTROL PROCESO ENTRENAMIENTO y páginas individuales
from pages.evolutivo_temporada import layout as cpe_evolutivo_layout
from pages.semaforo_control import layout as semaforo_layout
# Nuevas páginas para CONTROL PROCESO COMPETICIÓN
from pages.rendimiento_colectivo import layout as rendimiento_colectivo_layout
from pages.rendimiento_individual import layout as rendimiento_individual_layout
# Comentamos las páginas que no usaremos por ahora
# from pages.ficha_jugador import layout as ficha_jugador_layout
# from pages.postpartido import layout as postpartido_layout
# from pages.evolutivo import layout as evolutivo_layout
# from pages.rubricas import layout as rubricas_layout
# from pages.rubricas_porteros import layout as rubricas_porteros_layout
# from pages.proyecciones import layout as proyecciones_layout

# -------------------- Layout de login simplificado --------------------
login_layout = html.Div(
    dbc.Container(
        dbc.Card(
            dbc.CardBody([
                html.Div(
                    html.Img(src="/assets/ESCUDO-AZUL_RGB-HD.png", style={"height": "100px"}),
                    className="text-center mb-4"
                ),
                html.H2("Iniciar sesión", className="text-center mb-4"),
                dbc.Input(id="username", placeholder="Usuario", type="text", className="mb-3"),
                dbc.Input(id="password", placeholder="Contraseña", type="password", className="mb-3"),
                html.Div(id="login-output", style={"color": "red", "marginBottom": "10px"}),
                dbc.Button("Entrar", id="login-button", color="primary", className="w-100")
            ]),
            className="shadow p-4"
        ),
        className="d-flex justify-content-center align-items-center",
        style={"height": "100vh"}
    )
)

# -------------------- Layout principal --------------------
app.layout = html.Div([
    dcc.Location(id='url-login', refresh=False),
    dcc.Location(id='subpage-url', refresh=False),

    dcc.Store(id='global-session-store', storage_type='session', data={'logged_in': False}),
    dcc.Store(id='user-id-store', storage_type='session'),

    html.Div(id='main-layout', children=login_layout)
], id="app-container")

# -------------------- 1) login simplificado --------------------
@app.callback(
    Output("global-session-store", "data", allow_duplicate=True),
    Output("user-id-store", "data", allow_duplicate=True),
    Output("login-output", "children"),
    Output("url-login", "pathname", allow_duplicate=True),
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def do_login(n_clicks, username, password):
    # Login seguro: validar usuario y contraseña usando bcrypt y archivo seguro
    if username and password and validate_user_db(username, password):
        roles = get_user_roles(username)
        user_id = get_user_id(username)
        session = {
            "logged_in": True,
            "user": username,
            "roles": roles
        }
        return session, user_id, "", "/inicio"
    return {"logged_in": False}, None, "Credenciales incorrectas", no_update

# -------------------- 2) mostrar login o dashboard --------------------
@app.callback(
    Output("main-layout", "children"),
    Input("global-session-store", "data")
)
def display_main_layout(session_data):
    if session_data.get("logged_in"):
        return dashboard_layout()
    return login_layout

# -------------------- 3) render subpáginas --------------------
@app.callback(
    Output("page-content", "children"),
    [Input("subpage-url", "pathname"),
     Input("global-session-store", "data")],
    prevent_initial_call=False
)
def display_subpage(pathname, session_data):
    if not session_data or not session_data.get("logged_in"):
        return html.Div(
            "Sesión expirada. Por favor, vuelve a iniciar sesión.",
            style={"textAlign": "center", "color": "red"}
        )

    roles = session_data.get("roles", []) or []
    
    # Helper function to check role access
    def has_access(required_roles):
        if "admin" in roles or "direccion" in roles:
            return True
        return any(role in roles for role in required_roles)

    # Mostrar la página correspondiente según la ruta
    if pathname in ["/", "/inicio"]:
        return home_layout
    elif pathname == "/ficha-jugador":
        if has_access(["admin", "direccion", "analista"]):
            return ficha_jugador_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/control-proceso-entrenamiento":
        # Compatibilidad: dirigir a SESIONES-MICROCICLOS
        if has_access(["admin", "direccion", "analista"]):
            return rendimiento_fisico_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname in ["/rendimiento-fisico", "/seguimiento-carga"]:
        # Compatibilidad con la ruta anterior
        if has_access(["admin", "direccion", "analista"]):
            return rendimiento_fisico_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/control-proceso-entrenamiento/sesiones-microciclos":
        if has_access(["admin", "direccion", "analista"]):
            return rendimiento_fisico_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/control-proceso-entrenamiento/evolutivo-temporada":
        if has_access(["admin", "direccion", "analista"]):
            return cpe_evolutivo_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/chicha-jugador":
        # Alias de Ficha de Jugador
        if has_access(["admin", "direccion", "analista"]):
            return ficha_jugador_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/semaforo-control":
        if has_access(["admin", "direccion", "analista"]):
            return semaforo_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/control-proceso-competicion/rendimiento-colectivo":
        if has_access(["admin", "direccion", "analista"]):
            return rendimiento_colectivo_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/control-proceso-competicion/rendimiento-individual":
        if has_access(["admin", "direccion", "analista"]):
            return rendimiento_individual_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/estado-funcional/capacidad":
        if has_access(["admin", "direccion", "preparador"]):
            return ef_capacidad_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/estado-funcional/medico":
        if has_access(["admin", "direccion", "medico"]):
            return ef_medico_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/estado-funcional/psicologico":
        if has_access(["admin", "direccion", "psicologo"]):
            return ef_psico_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/estado-funcional/antropometrico":
        if has_access(["admin", "direccion", "nutricion"]):
            return ef_antropo_layout
        return html.Div("No tienes permisos para acceder a esta sección.", className="p-4 text-danger")
    elif pathname == "/admin":
        # Solo admin puede acceder a la sección de administración/configuración
        if "admin" in roles:
            return admin_layout
        return html.Div("No autorizado. Se requiere rol admin.", className="p-4 text-danger")
    else:  # Cualquier otra ruta
        return home_layout

# -------------------- 4) toggles de secciones colapsables --------------------
@app.callback(
    Output("collapse-cpe", "is_open"),
    Input("toggle-cpe", "n_clicks"),
    Input("subpage-url", "pathname"),
    State("collapse-cpe", "is_open"),
)
def toggle_cpe(n_clicks, pathname, is_open):
    # Mantener abierta si la URL pertenece a CPE
    if pathname and pathname.startswith("/control-proceso-entrenamiento"):
        return True
    # Toggle manual por botón
    triggered_prop = (
        dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if dash.callback_context.triggered else None
    )
    if triggered_prop == "toggle-cpe" and n_clicks:
        return not is_open
    # Cerrar si cambiamos a otra sección
    if pathname:
        return False
    return is_open

# -------------------- 4b) resaltar cabeceras de secciones según URL --------------------
@app.callback(
    Output("toggle-crc", "className"),
    Output("toggle-cpe", "className"),
    Output("toggle-cef", "className"),
    Input("subpage-url", "pathname"),
)
def highlight_section_headers(pathname):
    base_class = "text-start text-uppercase fw-bold small w-100 text-white"
    active_class = base_class + " active-group"
    crc_class = base_class
    cpe_class = base_class
    cef_class = base_class
    if pathname and pathname.startswith("/rendimiento-competicion"):
        crc_class = active_class
    if pathname and pathname.startswith("/control-proceso-entrenamiento"):
        cpe_class = active_class
    if pathname and pathname.startswith("/estado-funcional"):
        cef_class = active_class
    return crc_class, cpe_class, cef_class

@app.callback(
    Output("collapse-crc", "is_open"),
    Input("toggle-crc", "n_clicks"),
    Input("subpage-url", "pathname"),
    State("collapse-crc", "is_open"),
)
def toggle_crc(n_clicks, pathname, is_open):
    # Mantener abierta si la URL pertenece a CRC (competición)
    if pathname and pathname.startswith("/control-proceso-competicion"):
        return True
    # Toggle manual por botón
    triggered_prop = (
        dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if dash.callback_context.triggered else None
    )
    if triggered_prop == "toggle-crc" and n_clicks:
        return not is_open
    # Cerrar si cambiamos a otra sección
    if pathname:
        return False
    return is_open

@app.callback(
    Output("collapse-cef", "is_open"),
    Input("toggle-cef", "n_clicks"),
    Input("subpage-url", "pathname"),
    State("collapse-cef", "is_open"),
)
def toggle_cef(n_clicks, pathname, is_open):
    # Mantener abierta si la URL pertenece a CEF (estado funcional)
    if pathname and pathname.startswith("/estado-funcional"):
        return True
    # Toggle manual por botón
    triggered_prop = (
        dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if dash.callback_context.triggered else None
    )
    if triggered_prop == "toggle-cef" and n_clicks:
        return not is_open
    # Cerrar si cambiamos a otra sección
    if pathname:
        return False
    return is_open

# -------------------- 4c) Control de visibilidad del sidebar por roles --------------------
@app.callback(
    [Output("nav-section-crc", "style"),
     Output("nav-section-cpe", "style"),
     Output("nav-section-cef", "style"),
     Output("nav-section-ficha", "style"),
     Output("nav-section-semaforo", "style"),
     Output("nav-section-admin", "style")],
    Input("global-session-store", "data")
)
def control_sidebar_visibility(session_data):
    default_style = {"display": "block"}
    hidden_style = {"display": "none"}
    
    if not session_data or not session_data.get("logged_in"):
        return [hidden_style] * 6
    
    roles = session_data.get("roles", []) or []
    
    # Control Proceso Competición - acceso: admin, direccion, analista
    crc_style = default_style if any(role in roles for role in ["admin", "direccion", "analista"]) else hidden_style
    
    # Control Proceso Entrenamiento - acceso: admin, direccion, analista
    cpe_style = default_style if any(role in roles for role in ["admin", "direccion", "analista"]) else hidden_style
    
    # Control Estado Funcional - acceso: admin, direccion, medico, nutricion, psicologo, preparador
    cef_style = default_style if any(role in roles for role in ["admin", "direccion", "medico", "nutricion", "psicologo", "preparador"]) else hidden_style
    
    # Ficha Jugador - acceso: admin, direccion, analista
    ficha_style = default_style if any(role in roles for role in ["admin", "direccion", "analista"]) else hidden_style
    
    # Semáforo Control - acceso: admin, direccion, analista
    semaforo_style = default_style if any(role in roles for role in ["admin", "direccion", "analista"]) else hidden_style
    
    # Administración - acceso: solo admin
    admin_style = default_style if "admin" in roles else hidden_style
    
    return crc_style, cpe_style, cef_style, ficha_style, semaforo_style, admin_style

# -------------------- 4d) Control de visibilidad de subsecciones Estado Funcional --------------------
@app.callback(
    [Output("nav-subsection-medico", "style"),
     Output("nav-subsection-antropometrico", "style"),
     Output("nav-subsection-psicologico", "style"),
     Output("nav-subsection-capacidad", "style")],
    Input("global-session-store", "data")
)
def control_cef_subsections_visibility(session_data):
    default_style = {"display": "block"}
    hidden_style = {"display": "none"}
    
    if not session_data or not session_data.get("logged_in"):
        return [hidden_style] * 4
    
    roles = session_data.get("roles", []) or []
    
    # Médico - acceso: admin, direccion, medico
    medico_style = default_style if any(role in roles for role in ["admin", "direccion", "medico"]) else hidden_style
    
    # Antropométrico - acceso: admin, direccion, nutricion
    antropometrico_style = default_style if any(role in roles for role in ["admin", "direccion", "nutricion"]) else hidden_style
    
    # Psicológico - acceso: admin, direccion, psicologo
    psicologico_style = default_style if any(role in roles for role in ["admin", "direccion", "psicologo"]) else hidden_style
    
    # Capacidad - acceso: admin, direccion, preparador
    capacidad_style = default_style if any(role in roles for role in ["admin", "direccion", "preparador"]) else hidden_style
    
    return medico_style, antropometrico_style, psicologico_style, capacidad_style

# -------------------- 5) info de usuario en sidebar + logout --------------------
@app.callback(
    Output("sidebar-user", "children"),
    Input("global-session-store", "data")
)
def sidebar_user_info(session_data):
    if session_data and session_data.get("logged_in"):
        username = session_data.get("user", "")
        roles = session_data.get("roles", []) or []
        return dbc.Container([
            html.Div([
                html.I(className="fas fa-user me-2"),
                html.Span(f"Usuario: {username}")
            ]),
            html.Div(html.Small(", ".join(roles)), className="text-white-50 mt-1"),
            dbc.Button("Cerrar sesión", id="logout-button", color="secondary", size="sm", className="w-100 mt-2")
        ], fluid=True)
    return ""

@app.callback(
    Output("global-session-store", "data", allow_duplicate=True),
    Output("user-id-store", "data", allow_duplicate=True),
    Output("url-login", "pathname", allow_duplicate=True),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def do_logout(n_clicks):
    if n_clicks:
        return {"logged_in": False}, None, "/"
    return dash.no_update, dash.no_update, dash.no_update

# -------------------- Export WSGI --------------------
server = app.server

if __name__ == "__main__":
    import os
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8050)),
        debug=True,
        use_reloader=True
    )
#e