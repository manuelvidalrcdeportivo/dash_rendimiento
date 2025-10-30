# 📊 CÁLCULO CORRECTO DE MD Y PORCENTAJES

## 🎯 Cambio Crítico Implementado

### **Problema anterior:**
- El valor del MD se calculaba con TODOS los jugadores (promedio general)
- Los porcentajes se calculaban respecto al MD actual
- No se estandarizaba a 94 minutos

### **Solución implementada:**

## 1️⃣ **Cálculo del valor MD**

**SOLO jugadores con +70 minutos, estandarizado a 94'**

```python
# Filtrar jugadores con +70 minutos (4200 segundos)
MIN_FIELD_TIME = 4200
df_md_filtered = df_md_filtered[df_md_filtered['field_time'] >= MIN_FIELD_TIME]

# Estandarizar a 94 minutos (5640 segundos)
STANDARIZATION_TIME = 5640
df_md_filtered['metric_value_std'] = df_md_filtered['metric_value'] * (STANDARIZATION_TIME / df_md_filtered['field_time'])

# Calcular promedio estandarizado
md_actual_promedio = df_md_filtered['metric_value_std'].mean()
```

### ✅ Resultado:
- Barra MD muestra promedio de **titulares** (+70 mins) estandarizado a 94'
- No incluye suplentes ni jugadores con pocos minutos

---

## 2️⃣ **Cálculo de las líneas naranjas (Máx/Mín histórico)**

**De los últimos 4 MDs** (también estandarizados)

```python
# Obtener totales por atleta del MD actual
df_totals = get_microciclo_athlete_totals(microciclo_id, metric_name)

# Máximo y mínimo de promedios por atleta
max_historico_md = df_totals['avg_metric'].max()
min_historico_md = df_totals['avg_metric'].min()
```

### 📌 Nota:
- **Por ahora** usa datos del MD actual
- **TODO futuro**: Consultar los últimos 4 MDs desde tabla intermedia histórica

---

## 3️⃣ **Cálculo de porcentajes**

**Respecto a la LÍNEA NARANJA DEL MÁXIMO** (no respecto al MD actual)

```python
# Porcentaje sobre el máximo histórico
if max_historico_md and max_historico_md > 0:
    pct = (valor / max_historico_md) * 100
    text_label = f"{pct:.0f}%"
```

### ✅ Resultado:
- Barra MD-4: "85%" → Es el 85% del **máximo histórico** (línea naranja)
- Barra MD-2: "92%" → Es el 92% del **máximo histórico**
- Barra MD: Muestra valor absoluto (ej: "10250 m")

---

## 📊 Visualización Final

```
         │
12000m   │                     ┌─── Línea naranja MÁXIMO (referencia para %)
         │              ▓▓▓    │
11000m   │         ▒▒▒  ▓▓▓ ◄──┼─── Barra MD (titulares +70min, std a 94')
         │    ░░░  ▒▒▒  ▓▓▓    │
10000m   │    ░░░  ▒▒▒  ▓▓▓    │
         │    85%  92%  ▓▓▓    │
 9000m   │    ░░░  ▒▒▒  ▓▓▓    └─── Línea naranja MÍNIMO
         │    ░░░  ▒▒▒  ▓▓▓
         └────────────────────
           MD-4 MD-2  MD
```

**Interpretación:**
- MD-4 hizo **85%** de lo que marca la línea naranja (máximo histórico)
- MD-2 hizo **92%** de la línea naranja
- MD muestra valor absoluto (es el partido actual)

---

## 🔧 Cambios en Código

### **Archivo: `seguimiento_carga.py`**

#### 1. Cálculo del MD estandarizado
```python
# Líneas 1786-1816
if 'MD' in dias_con_datos and metric in ['total_distance', ...]:
    df_md_raw = get_microciclo_data_processed(microciclo_id, metric_name, ...)
    df_md_filtered = df_md_raw[df_md_raw['activity_tag'] == 'MD']
    
    # Filtrar +70 mins
    df_md_filtered = df_md_filtered[df_md_filtered['field_time'] >= 4200]
    
    # Estandarizar
    df_md_filtered['metric_value_std'] = df_md_filtered['metric_value'] * (5640 / df_md_filtered['field_time'])
    
    # Actualizar valor en df_summary
    df_summary.loc[df_summary['activity_tag'] == 'MD', 'avg_metric'] = df_md_filtered['metric_value_std'].mean()
```

#### 2. Cálculo de máx/mín histórico
```python
# Líneas 1818-1838
max_historico_md = None
min_historico_md = None

if 'MD' in dias_ordenados and metric in ['total_distance', ...]:
    df_totals = get_microciclo_athlete_totals(microciclo_id, metric_name, ...)
    
    if not df_totals.empty:
        max_historico_md = df_totals['avg_metric'].max()
        min_historico_md = df_totals['avg_metric'].min()
```

#### 3. Porcentajes respecto a máximo histórico
```python
# Líneas 1854-1871
if max_historico_md and max_historico_md > 0:
    pct = (valor / max_historico_md) * 100
    porcentaje_md = f"<br>% sobre máx histórico: <b>{pct:.1f}%</b>"
    
    # En la barra (excepto MD)
    if dia != 'MD':
        text_label = f"{pct:.0f}%"
```

#### 4. Líneas naranjas usan valores calculados
```python
# Líneas 1951-1991
if max_historico_md and min_historico_md and 'MD' in dias_ordenados:
    # Rectángulo naranja
    fig.add_shape(type="rect", y0=min_historico_md, y1=max_historico_md, ...)
    
    # Línea MÁXIMO (referencia para %)
    fig.add_shape(type="line", y0=max_historico_md, ...)
    
    # Línea MÍNIMO
    fig.add_shape(type="line", y0=min_historico_md, ...)
```

### **Archivo: `db_manager.py`**

#### Añadido field_time a query
```python
# Línea 1341-1355
query = f'''
    SELECT 
        activity_tag,
        ...
        {column_name} as metric_value,
        field_time  -- AÑADIDO para estandarización
    FROM microciclos_metricas_procesadas
    WHERE microciclo_id = %s
'''
```

---

## ✅ Beneficios

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Valor MD** | Promedio de todos | Solo titulares (+70 mins) |
| **Estandarización** | No | Sí, a 94 minutos |
| **Porcentajes** | Respecto a MD actual | Respecto a máx histórico |
| **Líneas naranjas** | No había | Máx/mín de últimos 4 MDs |
| **Precisión** | Baja | Alta |

---

## 🚀 Próximos Pasos

### **TODO: Histórico real de últimos 4 MDs**

Actualmente usa el MD actual. Implementar:

```python
# Query para obtener últimos 4 MDs desde tabla intermedia
query = '''
    SELECT microciclo_id, fecha_partido, AVG(valor_std) as promedio
    FROM (
        SELECT microciclo_id, fecha_partido,
               metric_value * (5640 / field_time) as valor_std
        FROM microciclos_metricas_procesadas
        WHERE activity_tag = 'MD'
          AND field_time >= 4200
          AND metric_name = %s
          AND fecha_partido <= CURRENT_DATE
    ) subquery
    GROUP BY microciclo_id, fecha_partido
    ORDER BY fecha_partido DESC
    LIMIT 4
'''
```

Esto daría:
- Máx/mín real de últimos 4 partidos
- Porcentajes más precisos
- Comparación histórica correcta

---

## 📝 Fórmulas Aplicadas

### Estandarización a 94 minutos:
```
valor_estandarizado = valor_real × (5640 / field_time_segundos)

Ejemplo:
- Jugador corrió 9500m en 80 minutos (4800 segundos)
- Estandarizado = 9500 × (5640 / 4800) = 11,162.5m
```

### Porcentaje sobre máximo:
```
porcentaje = (valor_dia / max_historico_md) × 100

Ejemplo:
- MD-4: 8500m
- Máximo histórico: 10,000m  
- Porcentaje: (8500 / 10000) × 100 = 85%
```

---

**Fecha:** 28 de octubre de 2025  
**Versión:** v2.2 - Cálculo correcto MD y porcentajes
