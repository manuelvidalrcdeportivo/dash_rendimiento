# pages/ficha_jugador.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("🧾 FICHA DE JUGADOR", className="page-title"),
    html.P(
        "Sección en construcción. Aquí se mostrará la ficha integral del jugador (datos personales, posición, histórico, etc.).",
        className="page-text"
    )
])
