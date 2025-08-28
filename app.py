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
# Nuevas secciones y subsecciones: CONTROL PROCESO ENTRENAMIENTO y páginas individuales
from pages.evolutivo_temporada import layout as cpe_evolutivo_layout
from pages.semaforo_control import layout as semaforo_layout
from pages.competicion_post_partido import layout as crc_post_layout
from pages.competicion_evolutivo_temporada import layout as crc_evolutivo_layout
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
                    html.Img(src="/assets/escudo_depor.png", style={"height": "100px"}),
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
    Input("url-login", "pathname"),
    State("global-session-store", "data")
)
def display_main_layout(pathname, session_data):
    if session_data.get("logged_in"):
        return dashboard_layout()
    return login_layout

# -------------------- 3) render subpáginas --------------------
@app.callback(
    Output("page-content", "children"),
    Input("subpage-url", "pathname"),
    State("global-session-store", "data")
)
def display_subpage(pathname, session_data):
    if not session_data.get("logged_in"):
        return html.Div(
            "Sesión expirada. Por favor, vuelve a iniciar sesión.",
            style={"textAlign": "center", "color": "red"}
        )

    # Mostrar la página correspondiente según la ruta
    if pathname in ["/", "/inicio"]:
        return home_layout
    elif pathname == "/ficha-jugador":
        return ficha_jugador_layout
    elif pathname == "/control-proceso-entrenamiento":
        # Compatibilidad: dirigir a SESIONES-MICROCICLOS
        return rendimiento_fisico_layout
    elif pathname in ["/rendimiento-fisico", "/seguimiento-carga"]:
        # Compatibilidad con la ruta anterior
        return rendimiento_fisico_layout
    elif pathname == "/control-proceso-entrenamiento/sesiones-microciclos":
        return rendimiento_fisico_layout
    elif pathname == "/control-proceso-entrenamiento/evolutivo-temporada":
        return cpe_evolutivo_layout
    elif pathname == "/chicha-jugador":
        # Alias de Ficha de Jugador
        return ficha_jugador_layout
    elif pathname == "/semaforo-control":
        return semaforo_layout
    elif pathname == "/rendimiento-competicion/post-partido":
        return crc_post_layout
    elif pathname == "/rendimiento-competicion/evolutivo-temporada":
        return crc_evolutivo_layout
    elif pathname == "/estado-funcional/capacidad":
        return ef_capacidad_layout
    elif pathname == "/estado-funcional/medico":
        return ef_medico_layout
    elif pathname == "/estado-funcional/psicologico":
        return ef_psico_layout
    elif pathname == "/admin":
        roles = session_data.get("roles", []) or []
        if "admin" in roles:
            return admin_layout
        return html.Div("No autorizado. Se requiere rol admin.", className="p-4 text-danger")
    else:  # Cualquier otra ruta
        return home_layout

# -------------------- 4) toggles de secciones colapsables --------------------
@app.callback(
    Output("collapse-cpe", "is_open"),
    Input("toggle-cpe", "n_clicks"),
    State("collapse-cpe", "is_open"),
    prevent_initial_call=True
)
def toggle_cpe(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-crc", "is_open"),
    Input("toggle-crc", "n_clicks"),
    State("collapse-crc", "is_open"),
    prevent_initial_call=True
)
def toggle_crc(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@app.callback(
    Output("collapse-cef", "is_open"),
    Input("toggle-cef", "n_clicks"),
    State("collapse-cef", "is_open"),
    prevent_initial_call=True
)
def toggle_cef(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

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