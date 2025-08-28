# pages/chicha_jugador.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("👤 Chicha Jugador", className="page-title"),
    html.P(
        "Sección en construcción. Aquí se mostrarán insights individuales del jugador (resumen, KPIs clave, comparativas).",
        className="page-text"
    )
])
