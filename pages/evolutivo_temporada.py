# pages/evolutivo_temporada.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("CONTROL PROCESO ENTRENAMIENTO - EVOLUTIVO-TEMPORADA", className="page-title"),
    html.P(
        "Sección en construcción. Aquí mostraremos análisis evolutivo de temporada: tendencias, acumulados y comparativas.",
        className="page-text"
    )
])
