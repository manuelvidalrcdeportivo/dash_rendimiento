# pages/nutricion.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("🥗 Nutrición", className="page-title"),
    html.P(
        "Sección en construcción. Aquí se planificarán menús, seguimiento de composición corporal y pautas nutricionales.",
        className="page-text"
    )
])
