# pages/lesiones.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("⛑️ Lesiones", className="page-title"),
    html.P(
        "Sección en construcción. Aquí se registrarán y seguirán las lesiones, tiempos de recuperación y readaptaciones.",
        className="page-text"
    )
])
