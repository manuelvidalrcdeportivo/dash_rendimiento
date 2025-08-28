# pages/contratos.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("📄 Contratos", className="page-title"),
    html.P(
        "Sección en construcción. Aquí se gestionarán los contratos, vigencias, cláusulas y alertas.",
        className="page-text"
    )
])
