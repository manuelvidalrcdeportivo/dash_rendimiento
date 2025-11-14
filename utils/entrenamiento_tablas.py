"""
Utilidades para generación de tablas evolutivas de microciclos.
Código extraído de seguimiento_carga.py manteniendo la lógica exacta.
"""

from dash import html
import dash_bootstrap_components as dbc


def generar_tabla_evolutiva(datos_evolutivos):
    """
    Genera el componente visual de la tabla evolutiva de microciclos.
    
    Args:
        datos_evolutivos: Dict con 'microciclos' y 'acumulados' de cargar_tabla_evolutiva_microciclos()
    
    Returns:
        Componente Dash con la tabla
    """
    if not datos_evolutivos or not datos_evolutivos.get('microciclos'):
        return html.Div("No hay datos disponibles para la tabla evolutiva", 
                       className="text-muted text-center p-4")
    
    microciclos = datos_evolutivos['microciclos']
    acumulados = datos_evolutivos['acumulados']
    jugadores_ids = datos_evolutivos.get('jugadores_ids', None)  # IDs de jugadores usados
    
    # Métricas a mostrar
    metricas = [
        {'id': 'total_distance', 'label': 'Distancia Total (%)'},
        {'id': 'distancia_21_kmh', 'label': 'Dist. +21 km/h (%)'},
        {'id': 'distancia_24_kmh', 'label': 'Dist. +24 km/h (%)'},
        {'id': 'acc_dec_total', 'label': 'Acel/Decel +3 (%)'},
        {'id': 'ritmo_medio', 'label': 'Ritmo Medio (%)'}
    ]
    
    # Calcular valores de compensatorio (MD+1/MD+2) para cada microciclo
    # IMPORTANTE: Usar los mismos jugadores_ids que el resto de la tabla
    from pages.seguimiento_carga_ultra_optimizado import obtener_compensatorios_tabla
    compensatorios = obtener_compensatorios_tabla(microciclos, jugadores_ids=jugadores_ids)
    
    # Mapeo de colores
    color_map = {
        'verde': '#d4edda',  # Verde claro
        'naranja': '#fff3cd',  # Naranja tenue (zona de tolerancia ±5%)
        'rojo_claro': '#f8d7da',  # Rojo claro
        'rojo_oscuro': '#e74c3c',  # Rojo oscuro
        'gris': '#e9ecef'  # Gris
    }
    
    color_text_map = {
        'verde': '#155724',
        'naranja': '#856404',  # Texto naranja oscuro
        'rojo_claro': '#721c24',
        'rojo_oscuro': '#ffffff',
        'gris': '#6c757d'
    }
    
    # Crear encabezados de columnas (microciclos completos)
    headers = [
        html.Th("", style={
            'backgroundColor': '#1e3d59',
            'color': 'white',
            'padding': '12px 8px',
            'fontSize': '13px',
            'fontWeight': '600',
            'textAlign': 'left',
            'borderRight': '1px solid #dee2e6',
            'position': 'sticky',
            'left': 0,
            'zIndex': 10
        })
    ]
    
    # Calcular % de semanas en verde por métrica
    porcentajes_verde = {}
    for metrica in metricas:
        metrica_id = metrica['id']
        total_microciclos = len(microciclos)
        verdes = sum(1 for mc in microciclos if acumulados[metrica_id].get(mc['id'], {}).get('color') == 'verde')
        porcentaje = (verdes / total_microciclos * 100) if total_microciclos > 0 else 0
        porcentajes_verde[metrica_id] = {
            'verdes': verdes,
            'total': total_microciclos,
            'porcentaje': porcentaje
        }
    
    for mc in microciclos:
        # Mostrar jornada en primera línea y label simplificado en segunda
        headers.append(
            html.Th(
                html.Div([
                    html.Div(mc['jornada'], style={
                        'fontWeight': '700', 
                        'fontSize': '15px',
                        'marginBottom': '3px'
                    }),
                    html.Div(mc['label'], style={
                        'fontSize': '8px', 
                        'fontWeight': '300',
                        'lineHeight': '1.1',
                        'whiteSpace': 'normal',
                        'wordBreak': 'break-word',
                        'maxHeight': '30px',
                        'overflow': 'hidden'
                    })
                ]), 
                style={
                    'backgroundColor': '#1e3d59',
                    'color': 'white',
                    'padding': '8px 4px',
                    'fontSize': '11px',
                    'textAlign': 'center',
                    'borderRight': '1px solid #dee2e6',
                    'minWidth': '100px',
                    'maxWidth': '120px',
                    'cursor': 'pointer',
                    'verticalAlign': 'middle'
                }, 
                id={'type': 'tabla-evolutiva-header', 'microciclo_id': mc['id']},
                n_clicks=0,  # Necesario para que sea clickeable
                title=mc['label']  # Tooltip con el nombre
            )
        )
    
    # Añadir columna % Cumplimiento al final (NO sticky, después de la última semana)
    headers.append(
        html.Th("% Cumplimiento", style={
            'backgroundColor': '#1e3d59',
            'color': 'white',
            'padding': '8px 4px',
            'fontSize': '12px',
            'fontWeight': '700',
            'textAlign': 'center',
            'borderRight': '1px solid #dee2e6',
            'minWidth': '110px'
        })
    )
    
    # Crear fila de Tipo de Microciclo
    tipo_cells = [
        html.Td("Tipo Microciclo", style={
            'backgroundColor': '#f8f9fa',
            'padding': '10px 8px',
            'fontSize': '12px',
            'fontWeight': '600',
            'color': '#1e3d59',
            'borderRight': '1px solid #dee2e6',
            'position': 'sticky',
            'left': 0,
            'zIndex': 5
        })
    ]
    
    tipo_label_map = {
        'estandar': 'Estándar',
        'extendido': 'Extendido',
        'reducido': 'Recortado',
        'superrecortado': 'Super Recortado',
        'especial': 'Especial'
    }
    
    for mc in microciclos:
        tipo = mc['tipo_microciclo']
        tipo_cells.append(
            html.Td(tipo_label_map.get(tipo, 'N/A'), style={
                'padding': '6px 4px',
                'fontSize': '10px',
                'textAlign': 'center',
                'backgroundColor': '#f1f3f5',
                'color': '#495057',
                'fontWeight': '600',
                'borderRight': '1px solid #dee2e6',
                'lineHeight': '1.2'
            }, id={'type': 'tabla-evolutiva-tipo', 'microciclo_id': mc['id']})
        )
    
    # Celda vacía en fila de tipo para columna % Cumplimiento
    tipo_cells.append(
        html.Td("—", style={
            'padding': '6px 4px',
            'fontSize': '10px',
            'textAlign': 'center',
            'backgroundColor': '#1e3d59',
            'color': 'white',
            'fontWeight': '600',
            'borderRight': '1px solid #dee2e6'
        })
    )
    
    # Crear filas de métricas
    filas_metricas = []
    
    for metrica in metricas:
        metrica_id = metrica['id']
        metrica_label = metrica['label']
        
        cells = [
            html.Td(metrica_label, style={
                'backgroundColor': '#f8f9fa',
                'padding': '10px 8px',
                'fontSize': '12px',
                'fontWeight': '600',
                'color': '#1e3d59',
                'borderRight': '1px solid #dee2e6',
                'position': 'sticky',
                'left': 0,
                'zIndex': 5
            })
        ]
        
        for mc in microciclos:
            mc_id = mc['id']
            datos_celda = acumulados[metrica_id].get(mc_id, {})
            
            acumulado_val = datos_celda.get('acumulado')
            color = datos_celda.get('color', 'gris')
            
            # Generar texto de la celda
            if acumulado_val is not None:
                texto = f"{acumulado_val:.0f}%"
            else:
                texto = "—"
            
            # Obtener colores de los mapas
            bg_color = color_map.get(color, '#e9ecef')
            text_color = color_text_map.get(color, '#6c757d')
            
            cells.append(
                html.Td(texto, style={
                    'padding': '8px 6px',
                    'fontSize': '13px',
                    'fontWeight': '600',
                    'textAlign': 'center',
                    'backgroundColor': bg_color,
                    'color': text_color,
                    'borderRight': '1px solid #dee2e6',
                    'cursor': 'pointer' if acumulado_val is not None else 'default'
                }, 
                id={'type': 'tabla-evolutiva-celda', 'microciclo_id': mc_id, 'metrica_id': metrica_id},
                n_clicks=0  # Necesario para que sea clickeable
                )
            )
        
        # Añadir celda con % Cumplimiento al final de la fila (color del encabezado)
        pct_info = porcentajes_verde[metrica_id]
        cells.append(
            html.Td(f"{pct_info['porcentaje']:.0f}%", style={
                'padding': '8px 6px',
                'fontSize': '13px',
                'fontWeight': '700',
                'textAlign': 'center',
                'backgroundColor': '#1e3d59',
                'color': 'white',
                'borderRight': '1px solid #dee2e6'
            }, title=f"{pct_info['verdes']} de {pct_info['total']} semanas en verde")
        )
        
        filas_metricas.append(html.Tr(cells))
    
    # Crear fila de Compensatorio (MD+1 o MD+2)
    comp_cells = [
        html.Td("Compensatorio MD+1/+2 (%)", style={
            'backgroundColor': '#f8f9fa',
            'padding': '10px 8px',
            'fontSize': '12px',
            'fontWeight': '600',
            'color': '#1e3d59',
            'borderRight': '1px solid #dee2e6',
            'position': 'sticky',
            'left': 0,
            'zIndex': 5
        })
    ]
    
    # Calcular % de compensatorios en verde
    total_compensatorios = len([c for c in compensatorios.values() if c['valor'] is not None])
    verdes_compensatorios = sum(1 for c in compensatorios.values() if c['color'] == 'verde')
    pct_comp_verde = (verdes_compensatorios / total_compensatorios * 100) if total_compensatorios > 0 else 0
    
    for mc in microciclos:
        mc_id = mc['id']
        comp_data = compensatorios.get(mc_id, {})
        
        porcentaje_val = comp_data.get('porcentaje')
        color_comp = comp_data.get('color', 'gris')
        
        if porcentaje_val is not None:
            texto = f"{porcentaje_val:.0f}%"
        else:
            texto = "—"
        
        # Obtener colores
        bg_color = color_map.get(color_comp, '#e9ecef')
        text_color = color_text_map.get(color_comp, '#6c757d')
        
        comp_cells.append(
            html.Td(texto, style={
                'padding': '8px 6px',
                'fontSize': '13px',
                'fontWeight': '600',
                'textAlign': 'center',
                'backgroundColor': bg_color,
                'color': text_color,
                'borderRight': '1px solid #dee2e6'
            })
        )
    
    # Añadir celda de % Cumplimiento para compensatorio
    comp_cells.append(
        html.Td(f"{pct_comp_verde:.0f}%", style={
            'padding': '8px 6px',
            'fontSize': '13px',
            'fontWeight': '700',
            'textAlign': 'center',
            'backgroundColor': '#1e3d59',
            'color': 'white',
            'borderRight': '1px solid #dee2e6'
        }, title=f"{verdes_compensatorios} de {total_compensatorios} compensatorios en rango 55-70%")
    )
    
    filas_metricas.append(html.Tr(comp_cells))
    
    # Crear tabla completa
    tabla = html.Div([
        html.H5("Evolución de Carga por Microciclo", style={
            'color': '#1e3d59',
            'fontWeight': '600',
            'fontSize': '18px',
            'marginBottom': '15px'
        }),
        html.Div(
            html.Table([
                html.Thead(html.Tr(headers)),
                html.Tbody([
                    html.Tr(tipo_cells),
                    *filas_metricas
                ])
            ], style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'border': '1px solid #dee2e6',
                'fontSize': '12px'
            }),
            id='tabla-evolutiva-scroll-container',
            style={
                'overflowX': 'auto',
                'maxWidth': '100%',
                'marginBottom': '10px'
            }
        ),
        # Script para hacer scroll a la derecha automáticamente
        html.Script('''
            setTimeout(function() {
                var container = document.getElementById('tabla-evolutiva-scroll-container');
                if (container) {
                    container.scrollLeft = container.scrollWidth;
                }
            }, 100);
        '''),
        html.Div([
            html.Div([
                html.Span("Leyenda: ", style={'fontWeight': '600', 'marginRight': '15px'}),
                html.Span("●", style={'color': color_map['verde'], 'fontSize': '20px', 'marginRight': '5px'}),
                html.Span("Dentro del rango", style={'marginRight': '15px', 'fontSize': '11px'}),
                html.Span("●", style={'color': color_map['naranja'], 'fontSize': '20px', 'marginRight': '5px'}),
                html.Span("Zona tolerancia (±5%)", style={'marginRight': '15px', 'fontSize': '11px'}),
                html.Span("●", style={'color': color_map['rojo_claro'], 'fontSize': '20px', 'marginRight': '5px'}),
                html.Span("Por debajo del mínimo", style={'marginRight': '15px', 'fontSize': '11px'}),
                html.Span("●", style={'color': color_map['rojo_oscuro'], 'fontSize': '20px', 'marginRight': '5px'}),
                html.Span("Por encima del máximo", style={'marginRight': '15px', 'fontSize': '11px'}),
                html.Span("●", style={'color': color_map['gris'], 'fontSize': '20px', 'marginRight': '5px'}),
                html.Span("Sin datos/Especial", style={'fontSize': '11px'})
            ], style={'marginBottom': '5px'}),
            html.Div([
                html.Span("⚠️ ", style={'marginRight': '5px'}),
                html.Span("Compensatorio (MD+1 o MD+2): pueden existir errores  por etiquetado Part/Rehab", 
                         style={'fontSize': '10px', 'fontStyle': 'italic', 'color': '#856404'})
            ])
        ], style={'marginTop': '10px', 'color': '#6c757d', 'fontSize': '12px'})
    ], style={
        'marginBottom': '25px'
    })
    
    return tabla
