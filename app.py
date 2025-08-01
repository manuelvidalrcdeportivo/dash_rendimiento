# app.py

import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from core import app               # instanciado con suppress_callback_exceptions=True
from utils.auth import validate_user
from utils.layouts import dashboard_layout

# Importar layouts de páginas
from pages.home import layout as home_layout
# Importación eliminada: from pages.jugadores import layout as jugadores_layout
from pages.seguimiento_carga import layout as seguimiento_carga_layout
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
    Output("global-session-store", "data"),
    Output("user-id-store", "data"),
    Output("login-output", "children"),
    Output("url-login", "pathname"),
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def do_login(n_clicks, username, password):
    # Login seguro: validar usuario y contraseña usando bcrypt y archivo seguro
    if username and password and validate_user(username, password):
        session = {
            "logged_in": True,
            "user": username,
            "nivel": 1,  # Nivel básico
            "categorias": ["todas"]  # Acceso a todas las categorías
        }
        return session, 1, "", "/inicio"
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
    if pathname == "/jugadores":
        return html.Div("La sección de jugadores ha sido eliminada", className="p-4")
    elif pathname == "/seguimiento-carga":
        from pages.seguimiento_carga import layout as seguimiento_carga_layout
        return seguimiento_carga_layout
    else:  # Para "/", "/inicio" y cualquier otra ruta no especificada
        return home_layout

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