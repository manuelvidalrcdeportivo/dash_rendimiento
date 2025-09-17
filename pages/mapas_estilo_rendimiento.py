# pages/mapas_estilo_rendimiento.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("CONTROL PROCESO COMPETICIÓN - Mapas de estilo-rendimiento", className="page-title"),
    html.P(
        "Sección en construcción. Aquí mostraremos mapas visuales que correlacionan el estilo de juego del equipo con los resultados de rendimiento (patrones estratégicos, análisis de correlaciones estilo-resultado, etc.). Pendientes de desarrollo completo.",
        className="page-text"
    )
])
