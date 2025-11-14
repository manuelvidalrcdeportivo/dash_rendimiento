# pages/rendimiento_fisico.py
# TEMPORALMENTE DESHABILITADO: Reutiliza el layout existente de seguimiento de carga
# Comentado para evitar conflicto de callbacks con entrenamiento_equipo.py
# from pages.seguimiento_carga import layout as layout

# Layout temporal mientras se completa la refactorización
from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H3("Microciclo Equipo", className="mb-4", style={'color': '#1e3d59', 'fontWeight': '600'}),
    html.Div([
        html.P("Esta sección está siendo refactorizada.", className="text-muted"),
        html.P([
            "Por favor, usa la nueva página: ",
            html.A("Entrenamiento Equipo", href="/entrenamiento-equipo", className="fw-bold")
        ], className="text-info")
    ], className="p-4 bg-light rounded")
], fluid=True, className="py-4")
