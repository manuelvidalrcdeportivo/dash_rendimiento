import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
from utils.db_manager import (
    get_activities_by_date_range,
    get_participants_for_activities,
    get_metrics_for_activities_and_athletes,
    get_available_parameters,
    get_variable_thresholds,
    add_grupo_dia_column
)
from utils.db_manager import get_all_athletes

# Layout principal de la sección Seguimiento de Carga
layout = dbc.Container([
    html.H2("📈 CONTROL PROCESO ENTRENAMIENTO - SESIONES-MICROCICLOS", className="page-title mb-4", style={"color": "white"}),
    
    # Card para filtros
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Selecciona un periodo:", className="form-label"),
                    dcc.DatePickerRange(
                        id="sc-date-range",
                        display_format="YYYY-MM-DD",
                        start_date_placeholder_text="Fecha inicio",
                        end_date_placeholder_text="Fecha fin",
                        className="mb-2"
                    ),
                ], width=12, lg=3),
                dbc.Col([
                    html.Label("Selecciona una métrica:", className="form-label"),
                    dcc.Dropdown(
                        id="sc-metric-dropdown",
                        options=get_available_parameters(),
                        value="total_distance",
                        clearable=False,
                        className="mb-2"
                    ),
                ], width=12, lg=3),
                dbc.Col([
                    html.Label("Selecciona jugadores:", className="form-label"),
                    dcc.Dropdown(
                        id="sc-player-dropdown",
                        multi=True,
                        placeholder="Todos los jugadores",
                        options=[], # Se llenará dinámicamente
                        value=['ALL'],   # Por defecto opción 'Todos'
                        className="mb-2"
                    ),
                ], width=12, lg=4),
                dbc.Col([
                    dbc.Button("Filtrar", id="sc-filtrar-btn", color="primary", className="mt-4 w-100"),
                ], width=12, lg=2)
            ])
        ])
    ], className="mb-4 shadow-sm", style={"background": "rgba(255, 255, 255, 0.95)"}),
    
    # Card para gráfico (ahora primero)
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5("Visualización de carga microciclo (MD-4 a MD)", className="mb-3"),
                    dcc.Loading(
                        id="sc-loading-bar",
                        type="circle",
                        children=[
                            dcc.Graph(id="sc-bar-chart")
                        ]
                    )
                ], width=12)
            ])
        ])
    ], className="mb-4 shadow-sm", style={"background": "rgba(255, 255, 255, 0.95)"}),
    
    # Botón para mostrar/ocultar datos detallados
    dbc.Row([
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"],
                id="toggle-datos-btn",
                color="secondary",
                outline=True,
                className="mb-3 w-100"
            ),
        ], width=12)
    ]),
    
    # Card para tabla (ahora oculta por defecto)
    html.Div(
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Datos detallados de rendimiento", className="mb-3"),
                        dcc.Loading(
                            id="sc-loading-table",
                            type="circle",
                            children=[
                                html.Div(id="sc-table-container")
                            ]
                        )
                    ], width=12)
                ])
            ])
        ], className="shadow-sm", style={"background": "rgba(255, 255, 255, 0.95)"}),
        id="datos-detallados-container",
        style={"display": "none"} # Oculto por defecto
    )
], fluid=True)

# Callback para mostrar/ocultar datos detallados
@callback(
    Output("datos-detallados-container", "style"),
    Output("toggle-datos-btn", "children"),
    Input("toggle-datos-btn", "n_clicks"),
    State("datos-detallados-container", "style"),
    prevent_initial_call=True
)
def toggle_datos_detallados(n_clicks, current_style):
    if current_style.get("display") == "none":
        # Mostrar tabla
        return {"display": "block"}, [html.I(className="fas fa-table me-2"), "Ocultar datos de rendimiento detallado"]
    else:
        # Ocultar tabla
        return {"display": "none"}, [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"]

# Callback para llenar el dropdown de jugadores solo cuando se inicia la aplicación
@callback(
    Output("sc-player-dropdown", "options"),
    Output("sc-player-dropdown", "value"),
    Input("sc-filtrar-btn", "n_clicks"),
    State("sc-date-range", "start_date"),
    State("sc-date-range", "end_date"),
    State("sc-player-dropdown", "value"),
    prevent_initial_call=False
)
def fill_players_dropdown(n_clicks, start_date, end_date, current_value):
    atletas_df = get_all_athletes()
    options = [{"label": "Todos los jugadores", "value": "ALL"}] + [
        {"label": row["full_name"], "value": row["id"]} for _, row in atletas_df.iterrows()
    ]
    
    # Si es la primera carga (current_value es None o lista vacía), usar valor por defecto
    if current_value is None or (isinstance(current_value, list) and len(current_value) == 0):
        return options, ["ALL"]
    # De lo contrario, mantener la selección actual
    return options, current_value

# Callback para filtrar y mostrar la tabla y el gráfico
@callback(
    Output("sc-table-container", "children"),
    Output("sc-bar-chart", "figure"),
    Input("sc-filtrar-btn", "n_clicks"),
    State("sc-date-range", "start_date"),
    State("sc-date-range", "end_date"),
    State("sc-metric-dropdown", "value"),
    State("sc-player-dropdown", "value"),
    prevent_initial_call=True
)
def update_sc_table_and_chart(n_clicks, start_date, end_date, metric, selected_players):
    if not start_date or not end_date:
        # Mensaje de error y gráfico vacío
        return html.Div("Selecciona un rango de fechas y filtra para ver datos.", className="text-center text-muted p-4"), {}
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return html.Div("No hay actividades en el rango seleccionado.", className="text-center text-muted p-4"), {}
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()

    # 2. Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return html.Div("No hay participantes para las actividades seleccionadas.", className="text-center text-muted p-4"), {}
    atleta_ids = participantes["athlete_id"].unique().tolist()

    # 3. Obtener métricas
    metricas = get_metrics_for_activities_and_athletes(actividad_ids, atleta_ids, metric)

    # 4. Mapeos
    actividad_fecha = dict(zip(actividades["id"], actividades["start_time"]))
    actividad_grupo = dict(zip(actividades["id"], actividades["grupo_dia"]))
    atletas_df = get_all_athletes()
    atleta_nombre = dict(zip(atletas_df["id"], atletas_df["full_name"]))
    
    # Obtener la etiqueta de la métrica seleccionada
    parametros = get_available_parameters()
    metrica_label = next((p['label'] for p in parametros if p['value'] == metric), metric)

    # 5. Construir tabla completa
    tabla = []
    for _, row in participantes.iterrows():
        actividad_id = row["activity_id"]
        atleta_id = row["athlete_id"]
        fecha = datetime.fromtimestamp(actividad_fecha[actividad_id]).strftime("%Y-%m-%d")
        grupo_dia = actividad_grupo.get(actividad_id, "Sin clasificar")
        nombre = atleta_nombre.get(atleta_id, str(atleta_id))
        valor = metricas[(metricas["activity_id"] == actividad_id) & (metricas["athlete_id"] == atleta_id)]["parameter_value"]
        if not valor.empty:
            valor_metrica = float(valor.values[0])
        else:
            valor_metrica = 0.0
        tabla.append({
            "fecha": fecha,
            "grupo_dia": grupo_dia,
            "jugador": nombre,
            "jugador_id": atleta_id,
            "valor": valor_metrica  # Campo genérico para cualquier métrica
        })
    # Filtrado por jugadores seleccionados
    if "ALL" not in selected_players:
        tabla_filtrada = [row for row in tabla if row["jugador_id"] in selected_players]
    else:
        tabla_filtrada = tabla  # Todos los jugadores
    # Ordenar por fecha, grupo_dia y jugador
    tabla_filtrada = sorted(tabla_filtrada, key=lambda x: (x["fecha"], x["grupo_dia"], x["jugador"]))
    
    # 6. Gráfico de barras acumuladas por grupo_dia
    df = pd.DataFrame(tabla_filtrada)
    # Días del microciclo que queremos mostrar (MD-4 a MD)
    dias_microciclo = ["MD-4", "MD-3", "MD-2", "MD-1", "MD"]
    
    if not df.empty:
        # Filtrar para el gráfico solo los días del microciclo
        df_grafico = df[df["grupo_dia"].isin(dias_microciclo)]
        # Si no hay datos tras el filtrado, mostrar mensaje
        if df_grafico.empty:
            fig = {}
        else:
            df_grafico["grupo_dia"] = pd.Categorical(df_grafico["grupo_dia"], categories=dias_microciclo, ordered=True)
            
            # Calcular la suma total por día
            # Primero agrupamos por grupo_dia y contamos jugadores
            df_count = df_grafico.groupby("grupo_dia")["jugador_id"].nunique().reset_index()
            df_count.columns = ["grupo_dia", "num_jugadores"]
            
            # Luego sumamos los valores por día
            df_sum = df_grafico.groupby("grupo_dia")["valor"].sum().reset_index()
            
            # Combinamos para mostrar la suma total
            df_bar = pd.merge(df_sum, df_count, on="grupo_dia")
            # df_bar["valor"] = df_bar["valor"] / df_bar["num_jugadores"]  # Comentado para mostrar la suma total
            
            # Añadimos columna para mostrar número de jugadores en tooltip
            df_bar["jugadores"] = df_bar["num_jugadores"].astype(str)
            
            # Determinar la unidad de la métrica para las etiquetas
            unidad = ""
            if "(m)" in metrica_label:
                unidad = " m"
            
            # Obtener los umbrales para esta variable
            umbrales_df = get_variable_thresholds(metric)
            
            # Mejorar visualización del gráfico
            fig = px.bar(
                df_bar, 
                x="grupo_dia", 
                y="valor", 
                labels={"grupo_dia": "Día del microciclo", "valor": metrica_label},
                title=f"{metrica_label} por día del microciclo (MD-4 a MD)",
                color_discrete_sequence=["#0d3b66"],
                text="valor"  # Mostrar valores en las barras
            )
            
            # Añadir los umbrales al gráfico si existen
            if not umbrales_df.empty:
                # Crear DataFrame para todos los días del microciclo
                dias_completos = pd.DataFrame({"dia": dias_microciclo})
                # Unir con los umbrales disponibles
                umbrales_completos = dias_completos.merge(umbrales_df, left_on="dia", right_on="dia", how="left")
                
                # Calcular el número de jugadores para ajustar los umbrales
                # Si se seleccionan todos los jugadores, usar el número real de participantes
                if "ALL" in selected_players:
                    # Contar jugadores únicos por día para ajustar umbrales
                    jugadores_por_dia = df_grafico.groupby("grupo_dia")["jugador_id"].nunique().to_dict()
                else:
                    # Si se seleccionan jugadores específicos, contar solo esos
                    df_filtrado = df_grafico[df_grafico["jugador_id"].isin(selected_players)]
                    jugadores_por_dia = df_filtrado.groupby("grupo_dia")["jugador_id"].nunique().to_dict()
                
                # Iterar por cada día y añadir marcas independientes para min y max
                for idx, row in umbrales_completos.iterrows():
                    dia = row['dia']
                    # Obtener el número de jugadores para este día
                    num_jugadores = jugadores_por_dia.get(dia, 1) if dia in jugadores_por_dia else 1
                    
                    if pd.notna(row['min_value']) and pd.notna(row['max_value']):
                        min_val = row['min_value'] * num_jugadores  # Ajustar por número de jugadores
                        max_val = row['max_value'] * num_jugadores  # Ajustar por número de jugadores
                        
                        # Rectángulo para cada día que represente el rango recomendado
                        fig.add_shape(
                            type="rect", 
                            x0=idx-0.3, x1=idx+0.3,  # Posición en el eje X (ancho del rectángulo)
                            y0=min_val, y1=max_val,   # Rango del rectángulo
                            fillcolor="rgba(200, 255, 200, 0.3)",
                            line=dict(width=0),
                            layer="below"
                        )
                        
                        # Línea para valor máximo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.3, x1=idx+0.3,
                            y0=max_val, y1=max_val,
                            line=dict(color="rgba(0, 128, 0, 0.9)", width=2),
                        )
                        
                        # Línea para valor mínimo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.3, x1=idx+0.3,
                            y0=min_val, y1=min_val,
                            line=dict(color="rgba(255, 0, 0, 0.9)", width=2),
                        )
                
                # Añadir elementos a la leyenda (puntos invisibles pero con leyenda)
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color='rgba(0, 128, 0, 0.9)'),
                    name='Máximo recomendado'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color='rgba(255, 0, 0, 0.9)'),
                    name='Mínimo recomendado'
                ))
                
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    marker=dict(size=10, color='rgba(200, 255, 200, 0.3)'),
                    name='Rango recomendado'
                ))
            
            fig.update_layout(
                xaxis_title="Día del microciclo",
                yaxis_title=metrica_label,
                bargap=0.4,
                plot_bgcolor="rgba(0,0,0,0)",  # Fondo transparente
                title_font_size=20,
                title_x=0.5,  # Centrar título
                height=500,   # Altura fija
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5
                )
            )
            
            # Ajustar texto en las barras
            fig.update_traces(
                selector=dict(type="bar"),
                texttemplate=f"%{{y:.0f}}{unidad}",
                textposition="inside",
                marker_line_width=1,
                marker_line_color="#003366",
                hovertemplate=f"%{{x}}<br>{metrica_label}: %{{y:.1f}}{unidad}<extra></extra>"
            )
        
        # Tabla de datos completos (todos los días)
        # Determinar el formato adecuado para la métrica
        formato = ".0f" if "Distance" in metrica_label or "(m)" in metrica_label else ".2f"
        
        columns = [
            {"name": "Fecha", "id": "fecha"},
            {"name": "Día", "id": "grupo_dia"},
            {"name": "Jugador", "id": "jugador"},
            {"name": metrica_label, "id": "valor", "type": "numeric", "format": {"specifier": formato}}
        ]
        data = [{k: v for k, v in row.items() if k != "jugador_id"} for row in tabla_filtrada]
        table = dash_table.DataTable(
            id="sc-results-table",
            columns=columns,
            data=data,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "10px"},
            style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "border": "1px solid #dee2e6"},
            style_data_conditional=[{
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9"
            }],
            filter_action="native",  # Permitir filtrado
            sort_action="native",    # Permitir ordenamiento
            page_size=15            # Más compacto
        )
        return table, fig
    else:
        return html.Div("No hay datos para mostrar en la tabla ni en el gráfico.", className="text-center text-muted p-4"), {}
