# pages/competicion_post_partido.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("CONTROL RENDIMIENTO COMPETICION - POST PARTIDO", className="page-title"),
    html.P(
        "Sección en construcción. Informe post partido con métricas de carga, rendimiento y comparativas.",
        className="page-text"
    )
])
