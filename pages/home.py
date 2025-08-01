# pages/home.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2(
        "🏠 Bienvenido al Dashboard Catapult",
        className="page-title"
    ),

    html.P(
        "Este dashboard es la herramienta central para el seguimiento y análisis de datos de rendimiento de los jugadores. Aquí podrás consultar métricas de entrenamiento, carga de trabajo, y analizar la evolución de cada jugador.",
        className="page-text"
    ),

    html.Hr(),

    html.H4("📊 Seguimiento de Carga", className="page-section-title"),
    html.P(
        "Monitoriza la carga de entrenamiento de los jugadores: distancia total, velocidad, aceleraciones... Análisis por microciclo para optimizar la planificación y prevenir lesiones.",
        className="page-text"
    ),

    html.Hr(),

    html.P(
        "Selecciona una sección en el menú lateral para comenzar.",
        className="text-center mt-4",
        style={"fontSize": "1.2rem", "color": "#666"}
    )
])
