# pages/admin.py

from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from utils.layouts import standard_page
from utils.auth_db import create_user, list_roles

# Opciones de roles (si la BD no está inicializada, se usan valores por defecto)
ROLE_OPTIONS = [{"label": r.title(), "value": r} for r in list_roles()]

layout = standard_page([
    html.H2("🛠️ Administración", className="page-title"),
    html.P("Alta de usuarios y asignación de roles.", className="page-text"),

    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Usuario"),
                    dbc.Input(id="adm-username", type="text", placeholder="Nombre de usuario"),
                ], md=6),
                dbc.Col([
                    dbc.Label("Contraseña"),
                    dbc.Input(id="adm-password", type="password", placeholder="Contraseña"),
                ], md=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Nombre completo (opcional)"),
                    dbc.Input(id="adm-fullname", type="text", placeholder="Nombre y apellidos"),
                ], md=6),
                dbc.Col([
                    dbc.Label("Email (opcional)"),
                    dbc.Input(id="adm-email", type="email", placeholder="correo@club.es"),
                ], md=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Roles"),
                    dcc.Dropdown(id="adm-roles", options=ROLE_OPTIONS, multi=True, placeholder="Selecciona roles"),
                ], md=12),
            ], className="mb-3"),
            dbc.Button("Crear usuario", id="adm-create-btn", color="primary"),
            html.Div(id="adm-msg", className="mt-3")
        ])
    ], className="shadow-sm", style={"background": "rgba(255, 255, 255, 0.95)"}),
])


@callback(
    Output("adm-msg", "children"),
    Input("adm-create-btn", "n_clicks"),
    State("adm-username", "value"),
    State("adm-password", "value"),
    State("adm-fullname", "value"),
    State("adm-email", "value"),
    State("adm-roles", "value"),
    prevent_initial_call=True
)
def admin_create_user(n_clicks, username, password, full_name, email, roles):
    if not username or not password:
        return dbc.Alert("Usuario y contraseña son obligatorios.", color="warning")
    roles = roles or []
    created = create_user(username, password, full_name, email, roles)
    if created:
        return dbc.Alert(f"Usuario '{username}' creado con roles: {', '.join(roles) if roles else 'sin roles'}.", color="success")
    else:
        return dbc.Alert(f"El usuario '{username}' ya existe.", color="danger")
