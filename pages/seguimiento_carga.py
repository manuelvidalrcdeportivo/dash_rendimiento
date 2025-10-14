import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime
from functools import lru_cache
import re
from utils.db_manager import (
    get_activities_by_date_range,
    get_participants_for_activities,
    get_metrics_for_activities_and_athletes,
    get_available_parameters,
    get_variable_thresholds,
    add_grupo_dia_column,
    get_all_athletes
)
from utils.layouts import standard_page

# Función para obtener el contenido de "Semana Equipo" (contenido actual)
def get_semana_equipo_content():
    """Contenido de la pestaña Semana Equipo - Vista actual del microciclo"""
    return html.Div([
        # Card para filtros
    dbc.Card([
        dbc.CardBody([
            # Fila única: Periodo, Métrica y Botón
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Label("Periodo:", className="form-label", style={
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#1e3d59',
                            'marginBottom': '6px',
                            'display': 'block'
                        }),
                        dcc.DatePickerRange(
                            id="sc-date-range",
                            display_format="YYYY-MM-DD",
                            start_date_placeholder_text="Inicio",
                            end_date_placeholder_text="Fin"
                        ),
                    ])
                ], width=12, lg=4, className="mb-2"),
                dbc.Col([
                    html.Div([
                        html.Label("Métrica:", className="form-label", style={
                            'fontWeight': '600',
                            'fontSize': '13px',
                            'color': '#1e3d59',
                            'marginBottom': '6px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id="sc-metric-dropdown",
                            options=get_available_parameters(),
                            value="total_distance",
                            clearable=False
                        ),
                    ])
                ], width=12, lg=6, className="mb-2"),
                dbc.Col([
                    dbc.Button("Cargar Datos", id="sc-cargar-btn", style={
                        'backgroundColor': '#1e3d59',
                        'border': 'none',
                        'borderRadius': '8px',
                        'padding': '10px 20px',
                        'fontWeight': '600',
                        'marginTop': '28px'
                    }, className="w-100"),
                ], width=12, lg=2, className="mb-2")
            ]),
            
            # Selector de jugadores (aparece dinámicamente)
            html.Div(id="sc-jugadores-container", style={'display': 'none'}, children=[
                html.Hr(style={'margin': '20px 0', 'borderColor': '#e0e0e0'}),
                dbc.Row([
                    dbc.Col([
                        html.Label("Selecciona jugadores (opcional):", className="form-label", style={
                            'fontWeight': '500',
                            'fontSize': '13px',
                            'color': '#6c757d',
                            'marginBottom': '8px'
                        }),
                        dcc.Dropdown(
                            id="sc-player-dropdown",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Todos los jugadores seleccionados por defecto...",
                            className="mb-2"
                        ),
                    ], width=12)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Aplicar Filtro", id="sc-filtrar-btn", style={
                            'backgroundColor': '#28a745',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '8px 20px',
                            'fontWeight': '600',
                            'fontSize': '14px'
                        }, size="sm"),
                    ], width=12, className="text-end")
                ], className="mt-2")
            ])
        ])
    ], className="mb-4", style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'border': 'none'
    }),
    
    # Card para gráfico
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H5("Visualización de carga microciclo (MD-4 a MD)", style={
                        'color': '#1e3d59',
                        'fontWeight': '600',
                        'fontSize': '18px',
                        'marginBottom': '20px'
                    }),
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
    ], className="mb-4", style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'border': 'none'
    }),
    
    # Botón para mostrar/ocultar datos detallados
    dbc.Row([
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-table me-2"), "Ver datos de rendimiento detallado"],
                id="toggle-datos-btn",
                style={
                    'backgroundColor': 'transparent',
                    'border': '2px solid #1e3d59',
                    'color': '#1e3d59',
                    'borderRadius': '8px',
                    'padding': '10px 20px',
                    'fontWeight': '600'
                },
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
                        html.H5("Datos detallados de rendimiento", style={
                            'color': '#1e3d59',
                            'fontWeight': '600',
                            'fontSize': '18px',
                            'marginBottom': '20px'
                        }),
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
        ], style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none',
            'padding': '20px'
        }),
        id="datos-detallados-container",
        style={"display": "none"} # Oculto por defecto
    )
    ])

# Función para obtener el contenido de "Semana Jugadores"
def get_semana_jugadores_content():
    """Contenido de la pestaña Semana Jugadores - Acumulado por jugador con colores por día"""
    return html.Div([
        # Card para filtros
        dbc.Card([
            dbc.CardBody([
                # Fila única: Periodo, Métrica y Botón
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Label("Periodo:", className="form-label", style={
                                'fontWeight': '600',
                                'fontSize': '13px',
                                'color': '#1e3d59',
                                'marginBottom': '6px',
                                'display': 'block'
                            }),
                            dcc.DatePickerRange(
                                id="sj-date-range",
                                display_format="YYYY-MM-DD",
                                start_date_placeholder_text="Inicio",
                                end_date_placeholder_text="Fin"
                            ),
                        ])
                    ], width=12, lg=4, className="mb-2"),
                    dbc.Col([
                        html.Div([
                            html.Label("Métrica:", className="form-label", style={
                                'fontWeight': '600',
                                'fontSize': '13px',
                                'color': '#1e3d59',
                                'marginBottom': '6px',
                                'display': 'block'
                            }),
                            dcc.Dropdown(
                                id="sj-metric-dropdown",
                                options=get_available_parameters(),
                                value="total_distance",
                                clearable=False
                            ),
                        ])
                    ], width=12, lg=6, className="mb-2"),
                    dbc.Col([
                        dbc.Button("Cargar Datos", id="sj-cargar-btn", style={
                            'backgroundColor': '#1e3d59',
                            'border': 'none',
                            'borderRadius': '8px',
                            'padding': '10px 20px',
                            'fontWeight': '600',
                            'marginTop': '28px'
                        }, className="w-100"),
                    ], width=12, lg=2, className="mb-2")
                ]),
                
                # Selector de jugadores (aparece dinámicamente)
                html.Div(id="sj-jugadores-container", style={'display': 'none'}, children=[
                    html.Hr(style={'margin': '20px 0', 'borderColor': '#e0e0e0'}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Selecciona jugadores (opcional):", className="form-label", style={
                                'fontWeight': '500',
                                'fontSize': '13px',
                                'color': '#6c757d',
                                'marginBottom': '8px'
                            }),
                            dcc.Dropdown(
                                id="sj-jugadores-dropdown",
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Todos los jugadores seleccionados por defecto...",
                                className="mb-2"
                            ),
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Aplicar Filtro", id="sj-filtrar-btn", style={
                                'backgroundColor': '#28a745',
                                'border': 'none',
                                'borderRadius': '8px',
                                'padding': '8px 20px',
                                'fontWeight': '600',
                                'fontSize': '14px'
                            }, size="sm"),
                        ], width=12, className="text-end")
                    ], className="mt-2")
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        }),
        
        # Card para gráfico
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Acumulado semanal por jugador", style={
                            'color': '#1e3d59',
                            'fontWeight': '600',
                            'fontSize': '18px',
                            'marginBottom': '20px'
                        }),
                        dcc.Loading(
                            id="sj-loading-chart",
                            type="circle",
                            children=[
                                dcc.Graph(id="sj-stacked-chart")
                            ]
                        )
                    ], width=12)
                ])
            ])
        ], className="mb-4", style={
            'backgroundColor': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'border': 'none'
        })
    ])

# Layout principal con pestañas
layout = standard_page([
    # Título principal
    html.Div([
        html.H2("CONTROL PROCESO ENTRENAMIENTO - Sesiones y Microciclos", 
                className="mb-4", 
                style={
                    "color": "#1e3d59", 
                    "backgroundColor": "transparent",
                    "fontWeight": "600",
                    "textAlign": "center",
                    "padding": "1rem 0"
                })
    ], style={"backgroundColor": "transparent"}),
    
    # Container principal con pestañas
    html.Div([
        # Header de pestañas
        html.Div([
            html.Div([
                html.Button(
                    "Semana Equipo",
                    id="tab-cpe-equipo",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#1e3d59",
                        "border": "none",
                        "borderBottom": "3px solid #1e3d59",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "600",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "50%",
                        "textAlign": "center"
                    }
                ),
                html.Button(
                    "Semana Jugadores",
                    id="tab-cpe-jugadores",
                    className="tab-button",
                    style={
                        "backgroundColor": "transparent",
                        "color": "#6c757d",
                        "border": "none",
                        "borderBottom": "3px solid transparent",
                        "borderRadius": "0",
                        "padding": "15px 0",
                        "fontWeight": "500",
                        "fontSize": "15px",
                        "cursor": "pointer",
                        "transition": "all 0.2s ease",
                        "width": "50%",
                        "textAlign": "center"
                    }
                )
            ], style={
                "display": "flex",
                "borderBottom": "1px solid #e9ecef",
                "marginBottom": "20px"
            })
        ]),
        
        # Contenedor del contenido de las pestañas
        html.Div(id="cpe-tab-content", children=[get_semana_equipo_content()])
    ], style={
        "backgroundColor": "white",
        "borderRadius": "12px",
        "padding": "20px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"
    })
])

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

# Callback para cargar datos iniciales de Semana Equipo
@callback(
    Output("sc-jugadores-container", "style"),
    Output("sc-player-dropdown", "options"),
    Output("sc-player-dropdown", "value"),
    Output("sc-bar-chart", "figure"),
    Output("sc-table-container", "children"),
    Input("sc-cargar-btn", "n_clicks"),
    State("sc-date-range", "start_date"),
    State("sc-date-range", "end_date"),
    State("sc-metric-dropdown", "value"),
    prevent_initial_call=True
)
def cargar_datos_semana_equipo(n_clicks, start_date, end_date, metric):
    """Carga datos iniciales y muestra selector de jugadores con los participantes del periodo (OPTIMIZADO)"""
    if not start_date or not end_date:
        return {'display': 'none'}, [], [], {}, html.Div()
    
    # Convertir fechas a timestamps
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    
    # Obtener actividades
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return {'display': 'none'}, [], [], {}, html.Div("No hay datos para el periodo seleccionado.")
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()
    
    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return {'display': 'none'}, [], [], {}, html.Div("No hay participantes en este periodo.")
    
    # Obtener jugadores únicos que participaron (usando cache)
    atleta_ids = participantes["athlete_id"].unique().tolist()
    atletas_df = get_cached_athletes()
    atletas_periodo = atletas_df[atletas_df["id"].isin(atleta_ids)]
    
    # Crear opciones del dropdown
    jugadores_options = [{'label': row['full_name'], 'value': row['id']} for _, row in atletas_periodo.iterrows()]
    jugadores_ids = atleta_ids  # Todos seleccionados por defecto
    
    # Generar gráfico y tabla inicial con todos los jugadores
    resultado = generar_tabla_y_grafico_equipo(start_date, end_date, metric, atleta_ids)
    
    # Verificar si es una tupla (tabla, fig) o un error
    if isinstance(resultado, tuple) and len(resultado) == 2:
        tabla, fig = resultado
    else:
        # Error en la generación
        tabla = html.Div("Error al generar los datos.", className="text-center text-muted p-4")
        fig = {}
    
    # Mostrar selector de jugadores
    return {'display': 'block'}, jugadores_options, jugadores_ids, fig, tabla

# Callback para aplicar filtro de jugadores en Semana Equipo
@callback(
    Output("sc-table-container", "children", allow_duplicate=True),
    Output("sc-bar-chart", "figure", allow_duplicate=True),
    Input("sc-filtrar-btn", "n_clicks"),
    State("sc-date-range", "start_date"),
    State("sc-date-range", "end_date"),
    State("sc-metric-dropdown", "value"),
    State("sc-player-dropdown", "value"),
    prevent_initial_call=True
)
def update_sc_table_and_chart(n_clicks, start_date, end_date, metric, selected_players):
    """Aplica filtro de jugadores seleccionados"""
    if not start_date or not end_date or not selected_players:
        return html.Div("Selecciona jugadores para filtrar.", className="text-center text-muted p-4"), {}
    
    resultado = generar_tabla_y_grafico_equipo(start_date, end_date, metric, selected_players)
    
    # Verificar si es una tupla (tabla, fig)
    if isinstance(resultado, tuple) and len(resultado) == 2:
        return resultado  # Retorna (tabla, fig)
    else:
        # Error
        return html.Div("Error al aplicar el filtro.", className="text-center text-muted p-4"), {}

# Función auxiliar para generar tabla y gráfico de Semana Equipo (OPTIMIZADA)
def generar_tabla_y_grafico_equipo(start_date, end_date, metric, atleta_ids_filtro):
    """Genera tabla y gráfico para Semana Equipo (OPTIMIZADO)"""
    if not start_date or not end_date:
        return html.Div("Selecciona un rango de fechas.", className="text-center text-muted p-4"), {}
    
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return html.Div("No hay actividades en el rango seleccionado.", className="text-center text-muted p-4"), {}
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()

    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return html.Div("No hay participantes para las actividades seleccionadas.", className="text-center text-muted p-4"), {}
    
    atleta_ids = participantes["athlete_id"].unique().tolist()

    # Obtener métricas
    metricas = get_metrics_for_activities_and_athletes(actividad_ids, atleta_ids, metric)

    # Mapeos (usando cache para atletas)
    actividad_fecha = dict(zip(actividades["id"], actividades["start_time"]))
    actividad_grupo = dict(zip(actividades["id"], actividades["grupo_dia"]))
    atletas_df = get_cached_athletes()
    atleta_nombre = dict(zip(atletas_df["id"], atletas_df["full_name"]))
    
    # Obtener la etiqueta de la métrica seleccionada
    parametros = get_available_parameters()
    metrica_label = next((p['label'] for p in parametros if p['value'] == metric), metric)

    # OPTIMIZACIÓN: Construir tabla usando merge de pandas (mucho más rápido)
    # Crear DataFrame base con participantes
    df_tabla = participantes.copy()
    
    # Merge con métricas
    df_tabla = df_tabla.merge(
        metricas[['activity_id', 'athlete_id', 'parameter_value']], 
        on=['activity_id', 'athlete_id'], 
        how='left'
    )
    
    # Añadir columnas adicionales usando map (vectorizado)
    df_tabla['fecha'] = df_tabla['activity_id'].map(
        lambda x: datetime.fromtimestamp(actividad_fecha[x]).strftime("%Y-%m-%d") if x in actividad_fecha else ""
    )
    df_tabla['grupo_dia'] = df_tabla['activity_id'].map(actividad_grupo)
    df_tabla['jugador'] = df_tabla['athlete_id'].map(atleta_nombre)
    df_tabla['valor'] = df_tabla['parameter_value'].fillna(0.0)
    
    # Filtrar por jugadores seleccionados
    if atleta_ids_filtro:
        df_tabla = df_tabla[df_tabla['athlete_id'].isin(atleta_ids_filtro)]
    
    # Renombrar columna para consistencia
    df_tabla = df_tabla.rename(columns={'athlete_id': 'jugador_id'})
    
    # Ordenar
    df_tabla = df_tabla.sort_values(['fecha', 'grupo_dia', 'jugador'])
    
    # Convertir a lista de diccionarios solo para la tabla final
    tabla_filtrada = df_tabla[['fecha', 'grupo_dia', 'jugador', 'jugador_id', 'valor']].to_dict('records')
    
    # 6. Gráfico de barras acumuladas por grupo_dia
    df = pd.DataFrame(tabla_filtrada)
    
    if not df.empty:
        # Obtener todos los días únicos que realmente tienen datos
        dias_con_datos = df["grupo_dia"].unique().tolist()
        
        # Ordenar los días: MD, MD+X (ascendente), MD-X (descendente desde mayor)
        # Orden: MD, MD+1, MD+2, MD+3, MD-6, MD-5, MD-4, MD-3, MD-2, MD-1, Sin clasificar
        orden_dias = ["MD", "MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1", "Sin clasificar"]
        dias_ordenados = [d for d in orden_dias if d in dias_con_datos]
        
        # Añadir cualquier día que no esté en el orden predefinido
        dias_extra = [d for d in dias_con_datos if d not in orden_dias]
        dias_ordenados.extend(sorted(dias_extra))
        
        # Usar todos los días con datos (crear copia explícita para evitar SettingWithCopyWarning)
        df_grafico = df[['fecha', 'grupo_dia', 'jugador', 'jugador_id', 'valor']].copy()
        df_grafico.loc[:, "grupo_dia"] = pd.Categorical(df_grafico["grupo_dia"], categories=dias_ordenados, ordered=True)
        
        # OPTIMIZACIÓN: Calcular estadísticas en una sola operación
        df_bar = df_grafico.groupby("grupo_dia", observed=True).agg({
            'valor': 'mean',
            'jugador_id': 'nunique'
        }).reset_index()
        
        df_bar.columns = ["grupo_dia", "valor", "num_jugadores"]
        df_bar["jugadores"] = df_bar["num_jugadores"].astype(str)
        
        # Determinar la unidad de la métrica para las etiquetas
        unidad = ""
        if "(m)" in metrica_label:
            unidad = " m"
        
        # Obtener los umbrales para esta variable
        umbrales_df = get_variable_thresholds(metric)
        
        # Crear gráfico con go.Figure para control individual de barras
        fig = go.Figure()
        
        # Añadir cada día como una barra separada para control de visibilidad
        for idx, row in df_bar.iterrows():
            dia = row['grupo_dia']
            valor = row['valor']
            num_jugadores = row['num_jugadores']
            
            # Determinar si el día debe estar visible por defecto
            # Solo días MD-X (MD-6, MD-5, MD-4, MD-3, MD-2, MD-1) y MD están visibles por defecto
            es_dia_md = bool(re.match(r'^MD[-+]?\d*$', dia))  # MD, MD-1, MD+1, etc.
            visible_por_defecto = True if es_dia_md else 'legendonly'
            
            fig.add_trace(go.Bar(
                name=dia,
                x=[dia],
                y=[valor],
                marker=dict(
                    color="#1e3d59",
                    line=dict(color="#0d3b66", width=1.5)
                ),
                text=[valor],
                texttemplate=f"%{{text:.1f}}{unidad}",
                textposition="outside",
                hovertemplate=f"{dia}<br>{metrica_label} (Media): %{{y:.1f}}{unidad}<br>Jugadores: {num_jugadores}<extra></extra>",
                visible=visible_por_defecto,
                showlegend=True
            ))
        
        # Añadir los umbrales al gráfico SOLO si existen Y tienen datos válidos
        if not umbrales_df.empty:
            # Filtrar solo umbrales que tienen valores válidos
            umbrales_validos = umbrales_df[
                umbrales_df['min_value'].notna() & 
                umbrales_df['max_value'].notna()
            ].copy()
            
            if not umbrales_validos.empty:
                # Crear diccionario de umbrales por día para búsqueda rápida
                umbrales_por_dia = {}
                for _, row in umbrales_validos.iterrows():
                    umbrales_por_dia[row['dia']] = {
                        'min': float(row['min_value']),
                        'max': float(row['max_value'])
                    }
                
                # Contador para saber si realmente añadimos algún umbral
                umbrales_añadidos = False
                
                # Iterar por cada día en el gráfico y añadir umbral si existe
                for idx, dia in enumerate(dias_ordenados):
                    # Si este día tiene umbral definido en la BD, añadirlo
                    if dia in umbrales_por_dia:
                        min_val = umbrales_por_dia[dia]['min']
                        max_val = umbrales_por_dia[dia]['max']
                        
                        # Rectángulo para el rango recomendado
                        fig.add_shape(
                            type="rect",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=min_val, y1=max_val,
                            fillcolor="rgba(200, 255, 200, 0.3)",
                            line=dict(width=0),
                            layer="below"
                        )
                        
                        # Línea para valor máximo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=max_val, y1=max_val,
                            line=dict(color="rgba(0, 128, 0, 0.9)", width=3),
                        )
                        
                        # Línea para valor mínimo
                        fig.add_shape(
                            type="line",
                            x0=idx-0.4, x1=idx+0.4,
                            y0=min_val, y1=min_val,
                            line=dict(color="rgba(255, 0, 0, 0.9)", width=3),
                        )
                        
                        umbrales_añadidos = True
                
                # Solo añadir leyenda si realmente se añadieron umbrales
                if umbrales_añadidos:
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
            title=None,  # Sin título
            xaxis=dict(
                title=dict(
                    text="Día del microciclo",
                    font=dict(size=13, color="#1e3d59", family="Montserrat")
                ),
                tickfont=dict(size=11, family="Montserrat"),
                categoryorder='array',
                categoryarray=dias_ordenados  # Forzar el orden correcto
            ),
            yaxis=dict(
                title=dict(
                    text=metrica_label,
                    font=dict(size=13, color="#1e3d59", family="Montserrat")
                ),
                tickfont=dict(size=11, family="Montserrat"),
                rangemode='tozero'
            ),
            bargap=0.3,
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=550,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#e0e0e0",
                borderwidth=1,
                font=dict(size=11, family="Montserrat")
            ),
            margin=dict(t=40, b=120, l=80, r=40),
            font=dict(family="Montserrat"),
            barmode='group'  # Importante para que cada barra sea independiente
        )
        
        # OPTIMIZACIÓN: Tabla de datos completos (usando DataFrame directamente)
        formato = ".0f" if "Distance" in metrica_label or "(m)" in metrica_label else ".2f"
        
        columns = [
            {"name": "Fecha", "id": "fecha"},
            {"name": "Día", "id": "grupo_dia"},
            {"name": "Jugador", "id": "jugador"},
            {"name": metrica_label, "id": "valor", "type": "numeric", "format": {"specifier": formato}}
        ]
        
        # Usar DataFrame directamente (más rápido que list comprehension)
        data = df_tabla[['fecha', 'grupo_dia', 'jugador', 'valor']].to_dict('records')
        
        table = dash_table.DataTable(
            id="sc-results-table",
            columns=columns,
            data=data,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "10px", "fontFamily": "Montserrat"},
            style_header={"backgroundColor": "#f8f9fa", "fontWeight": "bold", "border": "1px solid #dee2e6", "fontFamily": "Montserrat"},
            style_data_conditional=[{
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9"
            }],
            filter_action="native",
            sort_action="native",
            page_size=15,
            page_action="native"  # Paginación nativa (más rápida)
        )
        return table, fig
    else:
        return html.Div("No hay datos para mostrar en la tabla ni en el gráfico.", className="text-center text-muted p-4"), {}

# Callback para cambiar entre pestañas
@callback(
    Output("cpe-tab-content", "children"),
    Output("tab-cpe-equipo", "style"),
    Output("tab-cpe-jugadores", "style"),
    Input("tab-cpe-equipo", "n_clicks"),
    Input("tab-cpe-jugadores", "n_clicks"),
    prevent_initial_call=False
)
def switch_tab(equipo_clicks, jugadores_clicks):
    """Cambia entre las pestañas Semana Equipo y Semana Jugadores"""
    ctx = dash.callback_context
    
    # Estilos base
    style_active = {
        "backgroundColor": "transparent",
        "color": "#1e3d59",
        "border": "none",
        "borderBottom": "3px solid #1e3d59",
        "borderRadius": "0",
        "padding": "15px 0",
        "fontWeight": "600",
        "fontSize": "15px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "width": "50%",
        "textAlign": "center"
    }
    
    style_inactive = {
        "backgroundColor": "transparent",
        "color": "#6c757d",
        "border": "none",
        "borderBottom": "3px solid transparent",
        "borderRadius": "0",
        "padding": "15px 0",
        "fontWeight": "500",
        "fontSize": "15px",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "width": "50%",
        "textAlign": "center"
    }
    
    # Por defecto mostrar Semana Equipo
    if not ctx.triggered:
        return get_semana_equipo_content(), style_active, style_inactive
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "tab-cpe-jugadores":
        return get_semana_jugadores_content(), style_inactive, style_active
    else:
        return get_semana_equipo_content(), style_active, style_inactive

# Callback para cargar datos iniciales y mostrar selector de jugadores
@callback(
    Output("sj-jugadores-container", "style"),
    Output("sj-jugadores-dropdown", "options"),
    Output("sj-jugadores-dropdown", "value"),
    Output("sj-stacked-chart", "figure"),
    Input("sj-cargar-btn", "n_clicks"),
    State("sj-date-range", "start_date"),
    State("sj-date-range", "end_date"),
    State("sj-metric-dropdown", "value"),
    prevent_initial_call=True
)
def cargar_datos_semana(n_clicks, start_date, end_date, metric):
    """Carga datos iniciales y muestra selector de jugadores con los participantes del periodo (OPTIMIZADO)"""
    if not start_date or not end_date:
        return {'display': 'none'}, [], [], {}
    
    # Convertir fechas a timestamps
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    
    # Obtener actividades
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return {'display': 'none'}, [], [], {}
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()
    
    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return {'display': 'none'}, [], [], {}
    
    # Obtener jugadores únicos que participaron (usando cache)
    atleta_ids = participantes["athlete_id"].unique().tolist()
    atletas_df = get_cached_athletes()
    atletas_periodo = atletas_df[atletas_df["id"].isin(atleta_ids)]
    
    # Crear opciones del dropdown
    jugadores_options = [{'label': row['full_name'], 'value': row['id']} for _, row in atletas_periodo.iterrows()]
    jugadores_ids = atleta_ids  # Todos seleccionados por defecto
    
    # Generar gráfico inicial con todos los jugadores
    fig = generar_grafico_semana_jugadores(start_date, end_date, metric, atleta_ids)
    
    # Mostrar selector de jugadores
    return {'display': 'block'}, jugadores_options, jugadores_ids, fig

# Callback para aplicar filtro de jugadores
@callback(
    Output("sj-stacked-chart", "figure", allow_duplicate=True),
    Input("sj-filtrar-btn", "n_clicks"),
    State("sj-date-range", "start_date"),
    State("sj-date-range", "end_date"),
    State("sj-metric-dropdown", "value"),
    State("sj-jugadores-dropdown", "value"),
    prevent_initial_call=True
)
def update_semana_jugadores_chart(n_clicks, start_date, end_date, metric, jugadores_seleccionados):
    """Aplica filtro de jugadores seleccionados"""
    if not start_date or not end_date or not jugadores_seleccionados:
        return {}
    
    return generar_grafico_semana_jugadores(start_date, end_date, metric, jugadores_seleccionados)

# Cache para datos de atletas (evita consultas repetidas)
@lru_cache(maxsize=1)
def get_cached_athletes():
    """Obtiene y cachea la lista de atletas"""
    return get_all_athletes()

# Función auxiliar para generar el gráfico (optimizada)
def generar_grafico_semana_jugadores(start_date, end_date, metric, atleta_ids_filtro):
    """Genera el gráfico de barras apiladas por jugador con colores por día (OPTIMIZADO)"""
    if not start_date or not end_date:
        return {}
    
    # Convertir fechas a timestamps
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    
    # Obtener actividades
    actividades = get_activities_by_date_range(start_ts, end_ts)
    if actividades.empty:
        return {}
    
    actividades = add_grupo_dia_column(actividades)
    actividad_ids = actividades["id"].tolist() if "id" in actividades.columns else actividades["activity_id"].tolist()
    
    # Obtener participantes
    participantes = get_participants_for_activities(actividad_ids)
    if participantes.empty:
        return {}
    
    # Filtrar por jugadores del filtro
    if atleta_ids_filtro:
        participantes = participantes[participantes["athlete_id"].isin(atleta_ids_filtro)]
        if participantes.empty:
            return {}
    
    atleta_ids = participantes["athlete_id"].unique().tolist()
    
    # Obtener métricas
    metricas = get_metrics_for_activities_and_athletes(actividad_ids, atleta_ids, metric)
    
    # Mapeos (usando cache para atletas)
    actividad_fecha = dict(zip(actividades["id"], actividades["start_time"]))
    actividad_grupo = dict(zip(actividades["id"], actividades["grupo_dia"]))
    atletas_df = get_cached_athletes()
    atleta_nombre = dict(zip(atletas_df["id"], atletas_df["full_name"]))
    
    # Obtener la etiqueta de la métrica
    parametros = get_available_parameters()
    metrica_label = next((p['label'] for p in parametros if p['value'] == metric), metric)
    
    # Construir datos
    datos = []
    for _, row in participantes.iterrows():
        actividad_id = row["activity_id"]
        atleta_id = row["athlete_id"]
        fecha = datetime.fromtimestamp(actividad_fecha[actividad_id]).strftime("%Y-%m-%d")
        grupo_dia = actividad_grupo.get(actividad_id, "Sin clasificar")
        nombre = atleta_nombre.get(atleta_id, str(atleta_id))
        
        valor = metricas[(metricas["activity_id"] == actividad_id) & (metricas["athlete_id"] == atleta_id)]["parameter_value"]
        valor_metrica = float(valor.values[0]) if not valor.empty else 0.0
        
        datos.append({
            "jugador": nombre,
            "jugador_id": atleta_id,
            "fecha": fecha,
            "grupo_dia": grupo_dia,
            "actividad_id": actividad_id,
            "valor": valor_metrica
        })
    
    df = pd.DataFrame(datos)
    
    if df.empty:
        return {}
    
    # Crear gráfico con dos grupos de barras: Semana y Partido
    # Agrupar por jugador y grupo_dia, sumando valores
    df_grouped = df.groupby(["jugador", "grupo_dia", "fecha"])["valor"].sum().reset_index()
    
    # Separar datos de entrenamiento (semana) y partido (MD)
    df_semana = df_grouped[~df_grouped["grupo_dia"].isin(["MD", "Sin clasificar"])]
    df_partido = df_grouped[df_grouped["grupo_dia"] == "MD"]
    df_sin_clasificar = df_grouped[df_grouped["grupo_dia"] == "Sin clasificar"]
    
    # Crear mapeo de jugador a posición
    jugador_posicion = dict(zip(atletas_df["full_name"], atletas_df["position_name"]))
    
    # Orden de posiciones deseado
    orden_posiciones = [
        "Goal Keeper",
        "Lateral",
        "Central",
        "Mediocentro",
        "Interior",
        "Extremo",
        "Delantero"
    ]
    
    # Crear diccionario de prioridad de posiciones
    prioridad_posicion = {pos: idx for idx, pos in enumerate(orden_posiciones)}
    
    # Obtener jugadores únicos y ordenarlos por posición
    jugadores_unicos = df_grouped["jugador"].unique()
    
    def get_orden_jugador(jugador):
        """Retorna tupla (prioridad_posicion, carga_total) para ordenar"""
        posicion = jugador_posicion.get(jugador, "Sin posición")
        prioridad = prioridad_posicion.get(posicion, 999)  # 999 para posiciones no definidas
        
        # Calcular carga total de semana para ordenar dentro de la misma posición
        carga = df_semana[df_semana["jugador"] == jugador]["valor"].sum()
        
        return (prioridad, -carga)  # Negativo para ordenar descendente por carga
    
    jugadores_ordenados = sorted(jugadores_unicos, key=get_orden_jugador)
    
    # Orden de días de entrenamiento: MD+X (ascendente), luego MD-X (descendente desde mayor)
    # Orden: MD+1, MD+2, MD+3, MD-6, MD-5, MD-4, MD-3, MD-2, MD-1
    orden_dias_semana = ["MD+1", "MD+2", "MD+3", "MD-6", "MD-5", "MD-4", "MD-3", "MD-2", "MD-1"]
    
    # Paleta de colores profesional y moderna - AMPLIADA
    colores_dias = {
        "MD-6": "#2C3E50",  # Azul oscuro
        "MD-5": "#34495E",  # Azul grisáceo
        "MD-4": "#4A90E2",  # Azul cielo
        "MD-3": "#50C878",  # Verde esmeralda
        "MD-2": "#FFB84D",  # Naranja suave
        "MD-1": "#FF6B6B",  # Rojo coral
        "MD": "#9B59B6",    # Morado partido
        "MD+1": "#45B7D1",  # Turquesa
        "MD+2": "#5D6D7E",  # Gris azulado
        "MD+3": "#7F8C8D",  # Gris medio
        "Sin clasificar": "#BDC3C7"  # Gris claro
    }
    
    # Mapeo de nombres de posiciones a abreviaturas
    abrev_posiciones = {
        "Goal Keeper": "POR",
        "Lateral": "LAT",
        "Central": "CEN",
        "Mediocentro": "MCD",
        "Interior": "INT",
        "Extremo": "EXT",
        "Delantero": "DEL"
    }
    
    # Crear figura
    fig = go.Figure()
    
    # Obtener días únicos de semana y ordenarlos (TODOS los días que tengan datos)
    dias_semana_unicos = df_semana["grupo_dia"].unique()
    dias_semana_ordenados = [dia for dia in orden_dias_semana if dia in dias_semana_unicos]
    
    # Añadir días extra que no estén en el orden predefinido
    dias_extra = [dia for dia in dias_semana_unicos if dia not in orden_dias_semana]
    dias_semana_ordenados.extend(sorted(dias_extra))
    
    # GRUPO 1: Barras apiladas de SEMANA (entrenamientos)
    for dia in dias_semana_ordenados:
        df_dia = df_semana[df_semana["grupo_dia"] == dia]
        
        valores = []
        hover_data = []
        for jugador in jugadores_ordenados:
            df_jugador_dia = df_dia[df_dia["jugador"] == jugador]
            if not df_jugador_dia.empty:
                valor = df_jugador_dia["valor"].sum()
                fecha = df_jugador_dia["fecha"].iloc[0]
                posicion = jugador_posicion.get(jugador, "Sin posición")
                valores.append(valor)
                hover_data.append(f"{posicion}|{fecha}")
            else:
                valores.append(0)
                hover_data.append("||")
        
        # Determinar si el día debe estar oculto por defecto
        # Solo días MD-X (MD-6, MD-5, MD-4, MD-3, MD-2, MD-1) y MD+X están visibles por defecto
        es_dia_md = bool(re.match(r'^MD[-+]\d+$', dia))
        visible_por_defecto = True if es_dia_md else 'legendonly'
        
        fig.add_trace(go.Bar(
            name=dia,
            x=jugadores_ordenados,
            y=valores,
            marker=dict(
                color=colores_dias.get(dia, "#95a5a6"),
                line=dict(color='rgba(255,255,255,0.8)', width=1)
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<i>%{customdata[0]}</i><br>"
                f"<b>{dia}</b><br>"
                f"{metrica_label}: <b>%{{y:.1f}}</b><br>"
                "Fecha: %{customdata[1]}"
                "<extra></extra>"
            ),
            customdata=[[h.split('|')[0], h.split('|')[1]] for h in hover_data],
            offsetgroup=0,
            width=0.4,
            visible=visible_por_defecto  # Ocultar por defecto si no es MD-X o MD+X
        ))
    
    # GRUPO 2: Barra separada de PARTIDO (MD)
    if not df_partido.empty:
        valores_partido = []
        hover_partido = []
        for jugador in jugadores_ordenados:
            df_jugador_partido = df_partido[df_partido["jugador"] == jugador]
            if not df_jugador_partido.empty:
                valor = df_jugador_partido["valor"].sum()
                fecha = df_jugador_partido["fecha"].iloc[0]
                posicion = jugador_posicion.get(jugador, "Sin posición")
                
                # Calcular carga de semana para comparación
                carga_semana = df_semana[df_semana["jugador"] == jugador]["valor"].sum()
                porcentaje = (valor / carga_semana * 100) if carga_semana > 0 else 0
                
                valores_partido.append(valor)
                hover_partido.append(f"{posicion}|{fecha}|{carga_semana:.1f}|{porcentaje:.1f}")
            else:
                valores_partido.append(0)
                hover_partido.append("|||0|0")
        
        fig.add_trace(go.Bar(
            name="MD (Partido)",
            x=jugadores_ordenados,
            y=valores_partido,
            marker=dict(
                color=colores_dias["MD"],
                line=dict(color='rgba(255,255,255,0.8)', width=1),
                pattern=dict(shape="/", size=6, solidity=0.4)
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "<i>%{customdata[0]}</i><br>"
                "<b>PARTIDO</b><br>"
                f"{metrica_label}: <b>%{{y:.1f}}</b><br>"
                "Carga Semana: %{customdata[2]}<br>"
                "% vs Semana: <b>%{customdata[3]}%</b><br>"
                "Fecha: %{customdata[1]}"
                "<extra></extra>"
            ),
            customdata=[[h.split('|')[0], h.split('|')[1], h.split('|')[2], h.split('|')[3]] for h in hover_partido],
            offsetgroup=1,
            width=0.4
        ))
    
    # GRUPO 3: Sin clasificar (desactivado por defecto)
    if not df_sin_clasificar.empty:
        valores_sc = []
        fechas_sc = []
        for jugador in jugadores_ordenados:
            df_jugador_sc = df_sin_clasificar[df_sin_clasificar["jugador"] == jugador]
            if not df_jugador_sc.empty:
                valores_sc.append(df_jugador_sc["valor"].sum())
                fechas_sc.append(df_jugador_sc["fecha"].iloc[0])
            else:
                valores_sc.append(0)
                fechas_sc.append("")
        
        fig.add_trace(go.Bar(
            name="Sin clasificar",
            x=jugadores_ordenados,
            y=valores_sc,
            marker_color=colores_dias["Sin clasificar"],
            hovertemplate=f"<b>%{{x}}</b><br>Sin clasificar<br>{metrica_label}: %{{y:.1f}}<br>Fecha: %{{customdata}}<extra></extra>",
            customdata=fechas_sc,
            visible='legendonly',  # Desactivado por defecto
            offsetgroup=0  # Se apila con semana si se activa
        ))
    
    # Añadir líneas verticales y anotaciones discretas para separar posiciones
    posicion_anterior = None
    posiciones_indices = {}
    
    for idx, jugador in enumerate(jugadores_ordenados):
        posicion_actual = jugador_posicion.get(jugador, "Sin posición")
        
        if posicion_actual not in posiciones_indices:
            posiciones_indices[posicion_actual] = []
        posiciones_indices[posicion_actual].append(idx)
        
        # Línea separadora más sutil
        if posicion_anterior is not None and posicion_actual != posicion_anterior and idx > 0:
            fig.add_vline(
                x=idx - 0.5,
                line_width=1,
                line_dash="dot",
                line_color="rgba(150, 150, 150, 0.3)"
            )
        
        posicion_anterior = posicion_actual
    
    # Anotaciones discretas de posición (solo nombre, arriba dentro del área)
    for posicion, indices in posiciones_indices.items():
        if len(indices) > 0:
            centro = (min(indices) + max(indices)) / 2
            
            # Añadir anotación discreta arriba
            fig.add_annotation(
                x=centro,
                y=1.02,
                yref="paper",
                text=f"<i>{posicion}</i>",
                showarrow=False,
                font=dict(size=9, color="#aaaaaa", family="Montserrat"),
                xanchor='center'
            )
    
    # Configurar layout limpio y profesional
    fecha_inicio = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    fecha_fin = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    
    fig.update_layout(
        barmode='stack',
        title=None,  # Sin título para más espacio
        xaxis=dict(
            title=None,
            categoryorder='array',
            categoryarray=jugadores_ordenados,
            showgrid=False,
            tickfont=dict(size=10, family="Montserrat"),
            tickangle=-45,  # Rotados para evitar solapamiento
            tickmode='linear',
            automargin=True
        ),
        yaxis=dict(
            title=dict(
                text=f"{metrica_label}",
                font=dict(size=13, color="#1e3d59", family="Montserrat")
            ),
            showgrid=True,
            gridcolor='rgba(200, 200, 200, 0.15)',
            gridwidth=1,
            zeroline=True,
            zerolinecolor='rgba(100, 100, 100, 0.3)',
            zerolinewidth=1,
            tickfont=dict(size=11, family="Montserrat"),
            rangemode='tozero'
        ),
        height=550,
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#e0e0e0",
            borderwidth=1,
            font=dict(size=11, family="Montserrat"),
            itemsizing='constant',
            tracegroupgap=15,
            itemwidth=30
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=60, b=150, l=80, r=40),
        font=dict(family="Montserrat"),
        bargap=0.2,
        bargroupgap=0.1
    )
    
    return fig

