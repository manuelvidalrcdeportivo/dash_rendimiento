"""
Evolutivo Temporada (Competición): Visualización tipo ranking por métrica.
- Lee tabla indicadores_rendimiento (metrica, valor, ranking)
- Dibuja un grid (22 filas = rangos 1..22, columnas = métricas)
- Para cada métrica, rellena desde abajo hasta 'ranking' (ranking=1 rellena toda la columna)
- Colores: 1-6 verde, 7-16 amarillo, 17-22 rojo. Celdas vacías gris claro.
"""

from dash import html, dcc
from utils.layouts import standard_page
from utils.db_manager import get_db_connection
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import inspect


def fetch_indicadores_rendimiento():
    """Obtiene metrica, valor, ranking desde la BD o devuelve datos de ejemplo si no existe la tabla."""
    try:
        engine = get_db_connection()
        if engine is None:
            raise RuntimeError("Sin conexión a BD")
        insp = inspect(engine)
        if 'indicadores_rendimiento' not in insp.get_table_names():
            raise RuntimeError("Tabla indicadores_rendimiento no existe")
        df = pd.read_sql("SELECT metrica, valor, ranking FROM indicadores_rendimiento", engine)
        # Limpieza mínima
        df['ranking'] = pd.to_numeric(df['ranking'], errors='coerce').astype('Int64')
        df = df.dropna(subset=['metrica', 'ranking'])
        return df
    except Exception:
        # Datos de ejemplo (del enunciado)
        data = [
            ("Iniciativa de juego (puntos)", "55.62", 9),
            ("Posesión del balón (% tiempo)", "52 %", 11),
            ("Centroide colectivo global", "46 m", 10),
            ("Recuperaciones en campo contrario (% total)", "38 %", 12),
            ("Eficacia construcción ofensiva (%)", "17.3 %", 10),
            ("Expected Goals (xG)", "2.64", 6),
            ("Eficacia finalización (%)", "9.4 %", 8),
            ("Goles a favor", "3", 9),
            ("Eficacia de contención defensiva (%)", "82.4 %", 13),
            ("Expected goals en contra", "1.37", 7),
            ("Eficacia evitación (%)", "97.8 %", 3),
            ("Goles en contra totales", "1", 2),
            ("Distancia total recorrida", "113309 m", 14),
            ("Distancia Recorrida > 21 km/h (m.)", "6216 m", 17),
            ("Distancia High Sprint > 24 km/h (m.)", "2808 m", 13),
        ]
        return pd.DataFrame(data, columns=["metrica", "valor", "ranking"])


def _band_for_rank(rank: int) -> int:
    """Devuelve banda de color: 1=verde(1-6), 2=amarillo(7-16), 3=rojo(17-22)."""
    if 1 <= rank <= 6:
        return 1
    if 7 <= rank <= 16:
        return 2
    if 17 <= rank <= 22:
        return 3
    return 0


# Definición de grupos y orden objetivo
GROUPS = [
    ("Estilo", [
        "Iniciativa de juego (puntos)",
        "Posesión del balón (% tiempo)",
        "Centroide colectivo global",
        "Recuperaciones en campo contrario (% total)",
    ]),
    ("Rendimiento ofensivo", [
        "Eficacia construcción ofensiva (%)",
        "Expected Goals (xG)",
        "Eficacia finalización (%)",
        "Goles a favor",
    ]),
    ("Rendimiento defensivo", [
        "Eficacia de contención defensiva (%)",
        "Expected goals en contra",
        "Eficacia evitación (%)",
        "Goles en contra totales",
    ]),
    ("Rendimiento físico", [
        "Distancia total recorrida",
        "Distancia Recorrida > 21 km/h (m.)",
        "Distancia High Sprint > 24 km/h (m.)",
    ]),
]


def _band_to_color(band: int) -> str:
    if band == 1:
        return '#2ecc71'  # verde
    if band == 2:
        return '#f1c40f'  # amarillo
    if band == 3:
        return '#e74c3c'  # rojo
    return '#f5f6fa'      # vacío


def _order_metrics_by_groups(df: pd.DataFrame):
    """
    Devuelve la lista de métricas ordenadas según GROUPS y un diccionario con
    posiciones por grupo: {group_name: (start_idx, end_idx, present_metric_list)}
    """
    all_metrics = df['metrica'].tolist()
    ordered = []
    group_pos = {}
    for gname, metrics in GROUPS:
        present = [m for m in metrics if m in all_metrics]
        if present:
            start = len(ordered)
            ordered.extend(present)
            end = len(ordered) - 1
            group_pos[gname] = (start, end, present)
    # Añadir cualquier métrica sobrante que no esté en los grupos
    leftovers = [m for m in all_metrics if m not in ordered]
    ordered.extend(leftovers)
    return ordered, group_pos


def build_ranking_heatmap(df: pd.DataFrame) -> go.Figure:
    # Ordenar métricas por grupos
    ordered_metrics, group_pos = _order_metrics_by_groups(df)
    # Mapeos por métrica
    df_by_metric = {row['metrica']: row for _, row in df.iterrows()}
    values = [df_by_metric[m]['valor'] for m in ordered_metrics]
    ranks = [int(df_by_metric[m]['ranking']) for m in ordered_metrics]

    # Preparar etiquetas envueltas en varias líneas para el eje X
    def wrap_label(text: str, max_line_len: int = 16) -> str:
        words = str(text).split()
        if not words:
            return ""
        lines, line = [], ""
        for w in words:
            if len(line) + (1 if line else 0) + len(w) <= max_line_len:
                line = (line + " " + w).strip()
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)
        return "<br>".join(lines)

    metrics_wrapped = [wrap_label(m) for m in ordered_metrics]

    n_rows = 22
    y_vals = list(range(1, n_rows + 1))  # 1 (arriba) -> 22 (abajo)

    # Matrices z y customdata
    z = []  # 0=vacio, 1=verde, 2=amarillo, 3=rojo
    customdata = []  # por celda: [rank, valor]

    # Precalcular banda por columna
    bands = [_band_for_rank(rk) for rk in ranks]

    for y in y_vals:
        row_vals = []
        row_custom = []
        for col_idx, rk in enumerate(ranks):
            # Relleno desde abajo hasta 'rk': con y >= rk la celda se considera rellena
            filled = 1 if y >= rk else 0
            val = bands[col_idx] if filled else 0
            row_vals.append(val)
            row_custom.append([rk, values[col_idx]])
        z.append(row_vals)
        customdata.append(row_custom)

    # Colorscale discreta basada en zmin=0, zmax=3
    colorscale = [
        [0.0, '#f5f6fa'],  # vacío
        [0.24, '#f5f6fa'],
        [0.25, '#2ecc71'],  # verde
        [0.49, '#2ecc71'],
        [0.50, '#f1c40f'],  # amarillo
        [0.74, '#f1c40f'],
        [0.75, '#e74c3c'],  # rojo
        [1.0, '#e74c3c'],
    ]

    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        row_heights=[0.74, 0.14, 0.08, 0.04], vertical_spacing=0.03
    )

    fig.add_trace(
        go.Heatmap(
            z=z,
            x=ordered_metrics,
            y=y_vals,
            colorscale=colorscale,
            zmin=0,
            zmax=3,
            showscale=False,
            xgap=5,
            ygap=4,
            hoverinfo='x+y+z',
            customdata=customdata,
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Ranking: %{customdata[0]}<br>" +
                "Valor: %{customdata[1]}<extra></extra>"
            ),
        ),
        row=1, col=1
    )

    # Layout general
    fig.update_layout(
        height=960,
        margin=dict(l=50, r=40, t=40, b=160),
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    # Fila 1 (heatmap): ocultar etiquetas del eje X para que queden solo en la fila 2
    fig.update_xaxes(
        row=1, col=1,
        title='', type='category', tickangle=0,
        tickfont=dict(size=16),
        showticklabels=False,
        automargin=True, showgrid=False, zeroline=False,
        categoryorder='array', categoryarray=ordered_metrics,
    )
    # Eje Y principal (fila 1)
    fig.update_yaxes(
        row=1, col=1,
        title='Ranking',
        tickmode='linear', tick0=1, dtick=1,
        tickfont=dict(size=14), showgrid=False, zeroline=False,
        autorange='reversed'
    )
    # Fila 2: mostrar etiquetas de métricas (bajo el heatmap)
    # Añadimos una traza invisible para forzar render de los ticks del eje X
    fig.add_trace(
        go.Scatter(x=ordered_metrics, y=[0]*len(ordered_metrics), mode='markers',
                    marker=dict(opacity=0), hoverinfo='skip', showlegend=False),
        row=2, col=1
    )
    fig.update_xaxes(
        row=2, col=1,
        title='', type='category', tickangle=0,
        tickfont=dict(size=12),
        tickvals=ordered_metrics, ticktext=metrics_wrapped,
        automargin=True, showgrid=False, zeroline=False, showticklabels=True,
        categoryorder='array', categoryarray=ordered_metrics,
        matches='x', side='top', ticklabelposition='inside', ticks='outside', ticklen=0, ticklabelstandoff=6
    )
    fig.update_yaxes(row=2, col=1, visible=False, range=[0, 1])

    # No annotations needed on row 2; tick labels are shown directly on x2

    # Fila 3: banda de grupos (sin etiquetas X)
    fig.update_xaxes(row=3, col=1, showticklabels=False, categoryorder='array', categoryarray=ordered_metrics, showgrid=False, zeroline=False, matches='x')
    fig.update_yaxes(row=3, col=1, visible=False, range=[0, 1])

    # Dibujar recuadros de grupo coloreados por la media de ranking y etiqueta centrada
    rank_map = {m: int(df_by_metric[m]['ranking']) for m in ordered_metrics}
    cat_pos = {m: i for i, m in enumerate(ordered_metrics)}
    group_avgs = []
    for gname, (start_idx, end_idx, present) in group_pos.items():
        if not present:
            continue
        # Usar posiciones numéricas en el eje categórico para abarcar columnas completas
        x0 = cat_pos[present[0]] - 0.5
        x1 = cat_pos[present[-1]] + 0.5
        avg_rank = float(np.mean([rank_map[m] for m in present]))
        group_avgs.append(avg_rank)
        band = _band_for_rank(int(round(avg_rank)))
        color = _band_to_color(band)
        # Rectángulo
        n_total = len(ordered_metrics)
        eps = 0.001
        start_frac = start_idx / n_total
        end_frac = (end_idx + 1) / n_total
        start_frac = max(0.0, start_frac - eps)
        end_frac = min(1.0, end_frac + eps)
        fig.add_shape(
            type='rect', xref='x3 domain', yref='y3',
            x0=start_frac, x1=end_frac, y0=0.0, y1=1.0,
            fillcolor=color, line=dict(color='black', width=1),
            layer='above'
        )
        # Etiqueta del grupo (centrada aproximadamente en la métrica del medio)
        mid_idx = (len(present) - 1) // 2
        mid_metric = present[mid_idx]
        avg_text = f"{gname} ({avg_rank:.1f})"
        fig.add_annotation(
            x=(start_idx + end_idx + 1) / (2 * len(ordered_metrics)),
            y=0.5,
            xref='x3 domain', yref='y3',
            text=avg_text,
            font=dict(size=18, color='black'),
            showarrow=False, align='center',
            xanchor='center', yanchor='middle'
        )

    # Fila 4: bloque resumen "Rendimiento competición"
    fig.update_xaxes(row=4, col=1, showticklabels=False, showgrid=False, zeroline=False, matches='x')
    fig.update_yaxes(row=4, col=1, visible=False, range=[0, 1])
    if group_avgs:
        overall_avg = float(np.mean(group_avgs))
    else:
        # Fallback: media de todas las métricas si no hay grupos
        overall_avg = float(np.mean(ranks)) if len(ranks) > 0 else np.nan
    if not np.isnan(overall_avg):
        band_overall = _band_for_rank(int(round(overall_avg)))
        color_overall = _band_to_color(band_overall)
        fig.add_shape(
            type='rect', xref='x4 domain', yref='y4',
            x0=0.0, x1=1.0, y0=0.0, y1=1.0,
            fillcolor=color_overall, line=dict(color='black', width=1),
            layer='above'
        )
        fig.add_annotation(
            x=0.5, y=0.5,
            xref='x4 domain', yref='y4',
            text=f"Rendimiento competición ({overall_avg:.1f})",
            font=dict(size=18, color='black'),
            showarrow=False, align='center',
            xanchor='center', yanchor='middle'
        )

    return fig


def legend_block():
    # Leyenda estilizada
    box_style = {
        'display': 'inline-block',
        'width': '14px',
        'height': '14px',
        'marginRight': '8px',
        'borderRadius': '2px',
        'border': '1px solid #000',
    }
    return html.Div([
        html.Span([
            html.Span(style={**box_style, 'background': '#2ecc71'}),
            html.Span('Rendimiento alto (1–6)', className='text-muted')
        ], className='me-3'),
        html.Span([
            html.Span(style={**box_style, 'background': '#f1c40f'}),
            html.Span('Rendimiento medio (7–16)', className='text-muted')
        ], className='me-3'),
        html.Span([
            html.Span(style={**box_style, 'background': '#e74c3c'}),
            html.Span('Rendimiento bajo (17–22)', className='text-muted')
        ])
    ], className='mb-2', style={'display': 'flex', 'gap': '16px', 'alignItems': 'center', 'flexWrap': 'wrap'})

def description_block():
    return html.Div([
        html.P(
            [
                html.Span('Cada columna representa una métrica; las filas muestran el ranking que ocupa el equipo en la competición (1 arriba → 22 abajo). '),
                html.Span('El color refleja la banda de rendimiento por métrica y por grupo.'),
            ],
            className='text-muted', style={'fontStyle': 'italic'}
        )
    ], className='mb-2')


def build_layout():
    df = fetch_indicadores_rendimiento()
    fig = build_ranking_heatmap(df)
    return standard_page([
        html.H2("Control Rendimiento Competición - Evolutivo Temporada", className="page-title", style={'textTransform': 'none', 'fontWeight': 600}),
        description_block(),
        legend_block(),
        dcc.Graph(id='evolutivo-ranking', figure=fig, config={'displayModeBar': False})
    ])


layout = build_layout()
