# pages/estado_funcional_capacidad.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("CONTROL ESTADO FUNCIONAL - Capacidad Funcional", className="page-title"),
    html.P(
        "Sección en construcción. Aquí mostraremos indicadores de capacidad funcional (tests físicos, fuerza, movilidad, etc.). Pendientes de documentos inicio temporada.",
        className="page-text"
    )
])
