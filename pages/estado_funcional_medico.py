# pages/estado_funcional_medico.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("CONTROL ESTADO FUNCIONAL - Médico", className="page-title"),
    html.P(
        "Sección en construcción. Aquí integraremos indicadores/valoraciones médicas (lesiones activas, historial, aptitud).",
        className="page-text"
    )
])
