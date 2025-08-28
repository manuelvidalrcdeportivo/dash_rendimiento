# pages/semaforo_control.py

from dash import html
from utils.layouts import standard_page

layout = standard_page([
    html.H2("🚦 SEMÁFORO DE CONTROL", className="page-title"),
    html.P(
        "Sección en construcción. Aquí mostraremos alertas y estados tipo semáforo sobre el control del proceso.",
        className="page-text"
    )
])
