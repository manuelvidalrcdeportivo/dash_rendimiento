# pages/home.py

from dash import html
import dash_bootstrap_components as dbc

layout = dbc.Container([
    # Card 1: Introducción (más importante)
    dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div([
                    html.Img(src="/assets/escudo_depor.png", className="me-3", style={"height": "68px"}),
                    html.Div([
                        html.H2("Departamento de Rendimiento Deportivo", className="mb-1"),
                        html.P("Evaluación integral del rendimiento para una identidad deportiva sostenible.", className="mb-0")
                    ])
                ], className="d-flex align-items-center"),
            ], className="home-hero mb-3 fade-in"),

            html.P(
                "El R.C. Deportivo se plantea desarrollar la implantación de un Departamento de Rendimiento Deportivo vanguardista, con el fin de estar en disposición de evaluar adecuadamente la calidad-pertinencia de los modelos de juego y entrenamiento de sus equipos.",
                className="page-text"
            ),
            html.P(
                "En una primera fase, posteriormente extensible a otros equipos de la estructura deportiva del Club, el Departamento de Rendimiento Deportivo tendrá como principal misión evaluar, desde una perspectiva multidimensional (colectiva e individual: física, técnico-táctica, médica y psico-social), la eficacia-adecuación de los procesos que caracterizan la forma de competir y entrenar de su 1º equipo masculino; todo ello con la finalidad de colaborar con el Área Deportiva del Club (dirección deportiva y cuerpo técnico del 1º equipo), en la construcción-modelación de una identidad deportiva propia generadora de patrimonio y competitividad deportiva sostenible, focalizada en un óptimo aprovechamiento de la Cantera.",
                className="page-text"
            ),
        ]),
        className="shadow-sm mb-4",
        style={"background": "rgba(255, 255, 255, 0.95)"}
    ),

    # Sección: Impactos positivos (un solo card con intro + 3 subsecciones)
    dbc.Card(
        dbc.CardBody([
            html.H4("IMPACTOS POSITIVOS IMPLANTACIÓN DEPARTAMENTO RENDIMIENTO DEPORTIVO", className="page-section-title mb-3"),
            html.P(
                "Bajo la supervisión global de la Dirección Deportiva, se pretende definir-instaurar de forma consensuada una sistemática de trabajo eficaz y vanguardista que permita interactuar de forma sinérgica y alineada a las distintas áreas del Club, generando flujos de información de calidad válidos para:",
                className="text-muted",
                style={"fontSize": "0.95rem"}
            ),

            html.Hr(),

            html.H5("1º CONSEJO ADMINISTRACIÓN – DIRECCIÓN GENERAL", className="mb-2"),
            html.P(
                "Trazar una estrategia deportiva eficaz y ambiciosa, que permita definir una identidad deportiva propia generadora de patrimonio y competitividad deportiva sostenible, focalizada en un óptimo aprovechamiento de la Cantera.",
                className="page-text"
            ),
            html.Ul([
                html.Li("Asesoramiento para la implantación de un desarrollo deportivo coherente del 1º equipo (establecimiento de una planificación deportiva adecuada y corrección anticipada de desviaciones que puedan condicionar su evolución)."),
                html.Li("Propuesta de un conjunto de rasgos identitarios claros, con aplicación flexible atendiendo a los contextos particulares de cada momento-situación, caracterizadores de la forma de jugar-competir (ADN Depor COMPETICIÓN) y de entrenar (ADN Depor ENTRENAMIENTO) de los diferentes equipos que conforman la estructura deportiva del Club."),
            ], className="page-text estilizado"),

            html.Hr(),

            html.H5("2º DIRECCIÓN DEPORTIVA Y CUERPO TÉCNICO 1º EQUIPO", className="mb-2"),
            html.P(
                "Instaurar criterios-procedimientos de monitorización y optimización de los procesos de entrenamiento-competición del 1º equipo, ajustándolos a sus necesidades particulares y respetando la autonomía técnica del entrenador, que permitan desarrollar una evaluación compartida del rendimiento del equipo (revisión cruzada de datos-comentarios técnicos dirección deportiva – departamento rendimiento deportivo – cuerpo técnico), propiciadora de una competitividad deportiva positiva y sostenible.",
                className="page-text"
            ),
            html.Ul([
                html.Li("Control físico-funcional jugador → evaluación del estado funcional del jugador y de su potencial de rendimiento."),
                html.Li("Control competición → evaluación sincrónica/diacrónica del perfil de rendimiento competitivo del equipo y jugadores."),
                html.Li("Control entrenamiento → evaluación de metodologías de trabajo para la mejora del rendimiento individual y colectivo (contenidos y cargas de entrenamiento)."),
                html.Li("Prescripción de líneas de actuación para la mejora del modelo de juego y de entrenamiento del equipo."),
            ], className="page-text estilizado"),

            html.Hr(),

            html.H5("3º DIRECCIÓN Y TÉCNICOS FÚTBOL FORMATIVO", className="mb-2"),
            html.P(
                "Instaurar progresivamente procedimientos de trabajo validados en 1º equipo que, convenientemente adaptados, permitan obtener un máximo desarrollo-aprovechamiento de la Cantera.",
                className="page-text"
            ),
        ]),
        className="shadow-sm mb-4",
        style={"background": "rgba(255, 255, 255, 0.98)"}
    ),

    html.Hr(),
    html.P(
        "Selecciona una sección en el menú lateral para comenzar.",
        className="text-center mt-3",
        style={"fontSize": "1.1rem", "color": "#666"}
    )
], className="py-3", fluid=True)
