# pages/evolutivo_temporada.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("Seguimiento Carga Jugadores", className="page-title"),
    html.P([
        "Esta sección está siendo refactorizada. ",
        "Por favor, usa la nueva página: ",
        html.A("Entrenamiento Jugadores", href="/entrenamiento-jugadores", className="fw-bold")
    ], className="page-text")
])
