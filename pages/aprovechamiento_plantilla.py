# pages/aprovechamiento_plantilla.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("CONTROL PROCESO COMPETICIÓN - Aprovechamiento de Plantilla", className="page-title"),
    html.P(
        "Sección en construcción. Aquí mostraremos indicadores de aprovechamiento de plantilla (utilización de jugadores, rotaciones, optimización del rendimiento colectivo, etc.). Pendientes de desarrollo completo.",
        className="page-text"
    )
])
