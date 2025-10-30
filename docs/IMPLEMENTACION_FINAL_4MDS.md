# ✅ IMPLEMENTACIÓN FINAL - Últimos 4 MDs

## 🎯 Objetivo Conseguido

Cálculo correcto del valor MD y porcentajes basados en los **últimos 4 partidos** (MD actual + 3 anteriores).

---

## 📋 Proceso Implementado

### **Paso 1: Cargar un microciclo**
Usuario selecciona un microciclo del dropdown → Se obtiene su `microciclo_id` y `fecha_partido`.

### **Paso 2: Leer MD actual + 3 anteriores**
Nueva función: `get_ultimos_4_mds_promedios(metric_name, fecha_partido_actual)`

**Query SQL ejecutada:**
```sql
SELECT 
    fecha_partido,
    microciclo_id,
    microciclo_nombre,
    AVG(metric_column * (5640.0 / field_time)) as promedio_estandarizado
FROM microciclos_metricas_procesadas
WHERE activity_tag = 'MD'
  AND field_time >= 4200              -- ✅ Solo jugadores +70 minutos
  AND metric_column IS NOT NULL
  AND fecha_partido <= fecha_actual   -- ✅ Hacia atrás desde partido actual
  AND (participation_type IS NULL OR participation_type NOT IN ('Part', 'Rehab'))
  AND athlete_position != 'Goal Keeper'
GROUP BY fecha_partido, microciclo_id, microciclo_nombre
ORDER BY fecha_partido DESC
LIMIT 4                               -- ✅ Últimos 4 partidos
```

### **Paso 3: Calcular MAX y MIN**
De los 4 promedios obtenidos:
```python
max_historico_md = df_ultimos_4_mds['promedio_estandarizado'].max()
min_historico_md = df_ultimos_4_mds['promedio_estandarizado'].min()
```

### **Paso 4: Calcular porcentajes**
Todos los porcentajes se calculan respecto al **MAX de esos 4 partidos**:
```python
if max_historico_md and max_historico_md > 0:
    pct = (valor_dia / max_historico_md) * 100
```

---

## 🔧 Código Implementado

### **1. Nueva función en `db_manager.py`**

```python
def get_ultimos_4_mds_promedios(metric_name, fecha_partido_actual, 
                                 exclude_part_rehab=True, exclude_goalkeepers=True):
    """
    Obtiene los promedios de los últimos 4 MDs (incluyendo el actual).
    CRÍTICO: Filtra jugadores +70 mins y estandariza a 94'.
    
    Returns:
        DataFrame con: fecha_partido, microciclo_id, promedio_estandarizado
    """
```

**Características clave:**
- ✅ Filtro `field_time >= 4200` (70 minutos)
- ✅ Estandarización `metric * (5640.0 / field_time)` (a 94 minutos)
- ✅ Agregación `AVG()` por partido
- ✅ Solo actividades `MD`
- ✅ Excluye Part/Rehab y porteros
- ✅ Retorna hasta 4 partidos históricos

---

### **2. Uso en `seguimiento_carga.py`**

#### **Import añadido:**
```python
from utils.db_manager import (
    ...
    get_ultimos_4_mds_promedios  # NUEVO
)
```

#### **Cálculo en `generar_grafico_desde_tabla_intermedia()`:**

```python
# 1. Obtener fecha del partido actual
fecha_partido_query = f'''
    SELECT MAX(fecha_partido) as fecha_partido
    FROM microciclos_metricas_procesadas
    WHERE microciclo_id = '{microciclo_id}'
'''
df_fecha = pd.read_sql(fecha_partido_query, engine)
fecha_partido_actual = df_fecha['fecha_partido'].iloc[0]

# 2. Obtener últimos 4 MDs
df_ultimos_4_mds = get_ultimos_4_mds_promedios(
    metric_name=metric,
    fecha_partido_actual=fecha_partido_actual,
    exclude_part_rehab=excluir_part_rehab,
    exclude_goalkeepers=True
)

# 3. Calcular MAX y MIN
if not df_ultimos_4_mds.empty:
    max_historico_md = df_ultimos_4_mds['promedio_estandarizado'].max()
    min_historico_md = df_ultimos_4_mds['promedio_estandarizado'].min()
    
    print(f"✅ Últimos 4 MDs calculados: MAX={max_historico_md:.1f}, MIN={min_historico_md:.1f}")
    print(f"   Partidos: {', '.join(df_ultimos_4_mds['microciclo_nombre'].tolist())}")
```

#### **Uso en barras:**
```python
# Porcentaje en hover
if max_historico_md and max_historico_md > 0:
    pct = (valor / max_historico_md) * 100
    porcentaje_md = f"<br>% sobre máx histórico: <b>{pct:.1f}%</b>"

# Porcentaje en texto de barra (excepto MD)
if max_historico_md and max_historico_md > 0 and dia != 'MD':
    pct = (valor / max_historico_md) * 100
    text_label = f"{pct:.0f}%"
```

#### **Líneas naranjas:**
```python
if max_historico_md and min_historico_md and 'MD' in dias_ordenados:
    idx_md = dias_ordenados.index('MD')
    
    # Rectángulo naranja
    fig.add_shape(
        type="rect",
        x0=idx_md-0.35, x1=idx_md+0.35,
        y0=min_historico_md, y1=max_historico_md,
        fillcolor="rgba(255, 200, 100, 0.25)",
        ...
    )
    
    # Línea MÁXIMO (referencia para %)
    fig.add_shape(
        type="line",
        y0=max_historico_md, y1=max_historico_md,
        line=dict(color="rgba(255, 100, 0, 0.9)", width=3),
    )
    
    # Línea MÍNIMO
    fig.add_shape(
        type="line",
        y0=min_historico_md, y1=min_historico_md,
        line=dict(color="rgba(255, 100, 0, 0.9)", width=3),
    )
```

---

## 📊 Ejemplo de Funcionamiento

### **Escenario:**
- Usuario carga: **Microciclo vs Oviedo (10-11-2024)**
- Métrica: **Distancia Total**

### **Proceso:**

**1. Query a BD obtiene últimos 4 MDs:**
```
MD 1: vs Oviedo (10-11-2024)    → 10,250m (promedio de jugadores +70mins estandarizado)
MD 2: vs Burgos (03-11-2024)    → 10,800m
MD 3: vs Racing (27-10-2024)    → 10,150m
MD 4: vs Eldense (20-10-2024)   → 10,500m
```

**2. Cálculo de MAX y MIN:**
```
MAX = 10,800m (vs Burgos)
MIN = 10,150m (vs Racing)
```

**3. Barra del MD actual:**
```
Valor mostrado: 10,250m (titulares del partido vs Oviedo)
```

**4. Porcentajes en otras barras:**
```
MD-4: 8,500m → (8500 / 10800) × 100 = 79% (respecto a MAX de Burgos)
MD-2: 9,200m → (9200 / 10800) × 100 = 85%
MD-1: 7,800m → (7800 / 10800) × 100 = 72%
```

**5. Líneas naranjas en barra MD:**
```
Línea superior: 10,800m (MAX)
Línea inferior: 10,150m (MIN)
Rectángulo naranja relleno entre ambas
```

---

## ✅ Validación del Cálculo

### **Checklist de requisitos cumplidos:**

- [x] **Cargar microciclo** → Se obtiene `microciclo_id` y `fecha_partido`
- [x] **Leer MD + 3 anteriores** → Query SQL con `LIMIT 4` ordenado por fecha DESC
- [x] **Filtrar jugadores +70 mins** → `field_time >= 4200` en WHERE
- [x] **Estandarizar a 94 mins** → `metric * (5640.0 / field_time)` en SELECT
- [x] **Calcular MAX y MIN** → `.max()` y `.min()` de los 4 promedios
- [x] **Barra MD muestra valor actual** → Promedio estandarizado del MD actual
- [x] **Porcentajes respecto a MAX** → `(valor / max_historico_md) * 100`
- [x] **Líneas naranjas en MD** → Shapes en índice de MD con max/min

---

## 🎨 Resultado Visual

```
         │
12000m   │                     
         │              ▓▓▓    ─── Línea naranja MAX (10,800m) ← REFERENCIA PARA %
11000m   │         ▒▒▒  ▓▓▓    
         │    ░░░  ▒▒▒  ▓▓▓    ─── Barra MD actual (10,250m)
10000m   │    ░░░  ▒▒▒  ▓▓▓    ─── Línea naranja MIN (10,150m)
         │    79%  85%  ▓▓▓
 9000m   │    ░░░  ▒▒▒  ▓▓▓
         │    ░░░  ▒▒▒  ▓▓▓
         └────────────────────
           MD-4 MD-2  MD
```

**Interpretación:**
- MD-4 hizo **79%** del máximo histórico (10,800m vs Burgos)
- MD-2 hizo **85%** del máximo histórico
- MD muestra **10,250m** (valor del partido actual)
- Líneas naranjas marcan rango de últimos 4 partidos

---

## 🚀 Logs de Debugging

Cuando funciona correctamente, se verán estos logs:

```
✅ Últimos 4 MDs calculados: MAX=10800.5, MIN=10150.3
   Partidos: vs Burgos, vs Oviedo, vs Eldense, vs Racing
```

Si hay error:
```
⚠️ Error calculando últimos 4 MDs históricos: [detalle del error]
[stacktrace completo]
```

---

## 📝 Archivos Modificados

### **1. `utils/db_manager.py`**
- ✅ Añadida función `get_ultimos_4_mds_promedios()` (líneas 1499-1567)

### **2. `pages/seguimiento_carga.py`**
- ✅ Añadido import de `get_ultimos_4_mds_promedios` (línea 28)
- ✅ Modificada lógica de cálculo de max/min histórico (líneas 1819-1856)
- ✅ Los porcentajes ya usan `max_historico_md` (líneas 1870-1888)
- ✅ Las líneas naranjas ya usan `max_historico_md` y `min_historico_md` (líneas 1968-1991)

---

## ⚠️ Requisitos para Funcionar

### **Datos necesarios en `microciclos_metricas_procesadas`:**

1. **Columna `fecha_partido`** debe existir y tener fechas válidas
2. **Columna `field_time`** debe tener valores en segundos
3. **Al menos 4 MDs históricos** en la BD (si hay menos, usa los disponibles)
4. **Métricas no NULL** para los jugadores +70 mins

### **Si falta algo:**
- El sistema intenta calcular con los MDs disponibles
- Si no hay MDs históricos, las líneas naranjas no aparecen
- Los porcentajes no se calculan (solo valores absolutos)
- Se muestran logs de advertencia para debugging

---

## 🎉 Estado Final

**✅ IMPLEMENTACIÓN COMPLETA Y CORRECTA**

| Aspecto | Estado |
|---------|--------|
| Query últimos 4 MDs | ✅ Implementada |
| Filtro +70 minutos | ✅ En query SQL |
| Estandarización a 94' | ✅ En query SQL |
| Cálculo MAX/MIN | ✅ De los 4 promedios |
| Porcentajes correctos | ✅ Respecto a MAX |
| Líneas naranjas | ✅ Con MAX y MIN |
| Valor barra MD | ✅ Del partido actual |
| Logs informativos | ✅ Para debugging |

---

**Fecha:** 28 de octubre de 2025  
**Versión:** v2.3 - Implementación final últimos 4 MDs  
**Estado:** ✅ **LISTO PARA TESTING CON DATOS REALES**
