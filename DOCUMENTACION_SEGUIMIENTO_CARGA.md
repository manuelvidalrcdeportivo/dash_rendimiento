# DOCUMENTACIÓN: SEGUIMIENTO DE CARGA DE MICROCICLOS

## 📋 ÍNDICE
1. [Descripción General](#descripción-general)
2. [Estructura de Microciclos](#estructura-de-microciclos)
3. [Jugadores Incluidos](#jugadores-incluidos)
4. [Métricas Monitorizadas](#métricas-monitorizadas)
5. [Cálculos y Normalizaciones](#cálculos-y-normalizaciones)
6. [Tabla Evolutiva](#tabla-evolutiva)
7. [Compensatorio (MD+1/MD+2)](#compensatorio-md1md2)
8. [Umbrales y Colores](#umbrales-y-colores)
9. [Visualización de Microciclo](#visualización-de-microciclo)

---

## 📖 DESCRIPCIÓN GENERAL

El módulo de **Seguimiento de Carga** permite monitorizar la carga de entrenamiento del equipo a lo largo de la temporada, organizando las sesiones en **microciclos** (semanas de entrenamiento entre partidos).

**Objetivo principal:** Controlar que la carga de entrenamiento se mantenga dentro de rangos óptimos según el tipo de microciclo, evitando sobrecargas o subcargas.

---

## 🗓️ ESTRUCTURA DE MICROCICLOS

### Tipos de Microciclos

Un microciclo es el período entre dos partidos oficiales. Se clasifican según el número de días disponibles:

| Tipo | Días entre partidos | Descripción |
|------|---------------------|-------------|
| **Estándar** | 7-8 días | Semana completa de entrenamiento |
| **Extendido** | 9+ días | Más de una semana (parón, lesiones) |
| **Reducido** | 5-6 días | Semana corta |
| **Super-recortado** | 3-4 días | Muy pocos días de recuperación |
| **Especial** | Otros | Situaciones atípicas (sin umbrales) |

### Estructura de Días

Cada microciclo se organiza en días relativos al partido (MD = Match Day):

- **MD-4, MD-3, MD-2, MD-1**: Entrenamientos previos al partido
- **MD**: Día del partido
- **MD+1, MD+2**: Entrenamientos compensatorios post-partido

**Ejemplo de microciclo estándar (7 días):**
```
Lunes (MD+1) → Martes (MD-4) → Miércoles (MD-3) → Jueves (MD-2) → Viernes (MD-1) → Sábado (MD) → Domingo (descanso)
```

---

## 👥 JUGADORES INCLUIDOS

### Criterios de Inclusión

**En entrenamientos (MD-4 a MD-1 y MD+1/MD+2):**
- ✅ Jugadores de campo (NO porteros)
- ✅ Solo participación **Full** (completa)
- ❌ Excluidos: Participación **Part** (parcial) o **Rehab** (rehabilitación)

**En partidos (MD):**
- ✅ TODOS los jugadores que participaron (incluye porteros)
- ✅ Solo jugadores con **+70 minutos** para cálculos de máximos históricos
- ✅ Valores normalizados a 94 minutos (tiempo completo)

### Selección de Jugadores

El sistema usa **jugadores activos** que realmente participaron en entrenamientos durante la temporada actual (desde agosto), no todos los jugadores históricos de la base de datos.

**Ejemplo:**
- Total jugadores en BD: 60 (incluye históricos inactivos)
- Jugadores activos sin porteros: ~18-20
- **Se usan solo los 18-20 activos** para cálculos

---

## 📊 MÉTRICAS MONITORIZADAS

Se monitorizan **5 métricas principales** de carga física:

| Métrica | Descripción | Unidad | Tipo |
|---------|-------------|--------|------|
| **Distancia Total** | Distancia recorrida total | metros (m) | Suma |
| **Distancia +21 km/h** | Distancia a alta velocidad | metros (m) | Suma |
| **Distancia +24 km/h** | Distancia a muy alta velocidad | metros (m) | Suma |
| **Acel/Decel +3 m/s²** | Aceleraciones y deceleraciones intensas | conteo | Suma |
| **Ritmo Medio** | Velocidad media de desplazamiento | m/min | Media |

---

## 🔢 CÁLCULOS Y NORMALIZACIONES

### 1. Entrenamientos (MD-4 a MD-1)

**Cálculo:** Promedio simple de todos los jugadores seleccionados con participación Full.

```
Valor entrenamiento = Suma(valores_jugadores) / Número_jugadores
```

**Ejemplo MD-3:**
- 15 jugadores entrenan
- Distancia total: 180,000m acumulados
- **Valor MD-3 = 180,000 / 15 = 12,000m por jugador**

### 2. Partido (MD)

**Cálculo especial con normalización:**

1. **Filtrar:** Solo jugadores con +70 minutos (4200 segundos)
2. **Normalizar:** Estandarizar a 94 minutos (5640 segundos)
3. **Promediar:** Media de valores normalizados

```
Valor_normalizado = Valor_real × (5640 / Tiempo_jugado)
Valor_MD = Promedio(Valores_normalizados)
```

**Ejemplo MD:**
- Jugador A: 10,000m en 90 mins → 10,000 × (94/90) = 10,444m
- Jugador B: 9,500m en 85 mins → 9,500 × (94/85) = 10,506m
- Jugador C: 9,800m en 94 mins → 9,800 × (94/94) = 9,800m
- **Valor MD = (10,444 + 10,506 + 9,800) / 3 = 10,250m**

**Razón de la normalización:** Permite comparar jugadores que jugaron diferentes tiempos, llevándolos todos a un estándar de 94 minutos.

### 3. Máximos Históricos

Para calcular porcentajes y umbrales, se usa el **máximo** de los últimos 4 partidos:

```
Máximo_histórico = MAX(últimos_4_MDs_normalizados)
```

**Ejemplo:**
- MD actual: 10,489m
- MD-1 partido: 10,208m
- MD-2 partido: 8,778m
- MD-3 partido: 10,160m
- **Máximo histórico = 10,489m** (el mayor de los 4)

---

## 📈 TABLA EVOLUTIVA

### Descripción

Muestra la evolución de las 5 métricas a lo largo de todos los microciclos de la temporada, expresadas como **porcentaje acumulado** respecto a los umbrales del tipo de microciclo.

### Cálculo de Acumulados

Para cada microciclo, se suma la carga de todos los entrenamientos (MD-4 a MD-1):

```
Acumulado_métrica = Suma(MD-4, MD-3, MD-2, MD-1)
```

**Ejemplo Distancia Total (microciclo estándar):**
- MD-4: 12,000m
- MD-3: 10,500m
- MD-2: 8,000m
- MD-1: 5,500m
- **Acumulado = 36,000m**

### Cálculo de Porcentaje

Se compara el acumulado con los umbrales del tipo de microciclo:

```
Porcentaje = (Acumulado / Umbral_máximo) × 100
```

**Ejemplo (microciclo estándar - Distancia Total):**
- Acumulado: 36,000m
- Umbral máximo: 230% del máximo histórico
- Máximo histórico: 10,489m
- Umbral máximo absoluto: 10,489 × 2.30 = 24,125m
- **Porcentaje = (36,000 / 24,125) × 100 = 149%**

### Colores en la Tabla

| Color | Rango | Significado |
|-------|-------|-------------|
| 🟢 **Verde** | Entre mínimo y máximo | Carga óptima |
| 🔴 **Rojo claro** | Por debajo del mínimo | Subcarga |
| 🔴 **Rojo oscuro** | Por encima del máximo | Sobrecarga |
| ⚪ **Gris** | Sin datos o especial | No aplicable |

---

## 🏃 COMPENSATORIO (MD+1/MD+2)

### Descripción

El **compensatorio** es el entrenamiento de recuperación activa que se realiza 1 o 2 días después del partido. Solo hay **UN compensatorio por microciclo** (puede ser MD+1 o MD+2, pero no ambos).

### Detección

1. **Buscar MD+1:** Si existe y tiene jugadores Full, usar MD+1
2. **Si no hay MD+1:** Buscar MD+2 como alternativa
3. **Solo uno:** Nunca se cuentan ambos en el mismo microciclo

### Cálculo

```
Valor_compensatorio = Promedio(distancia_total_jugadores_Full)
Porcentaje = (Valor_compensatorio / Máximo_histórico_MD) × 100
```

**Importante:** 
- Se usan los **mismos jugadores** que en los entrenamientos (sin porteros, solo Full)
- Se compara con el **máximo histórico de MDs** (no con umbrales de entrenamientos)

**Ejemplo:**
- MD+1: 8 jugadores Full
- Distancia promedio: 4,003.6m
- Máximo histórico MD: 10,489.6m
- **Porcentaje = (4,003.6 / 10,489.6) × 100 = 38%**

### Umbrales Compensatorio

| Rango | Color | Significado |
|-------|-------|-------------|
| 55-70% | 🟢 Verde | Carga compensatoria óptima |
| <55% | 🔴 Rojo claro | Compensatorio insuficiente |
| >70% | 🔴 Rojo oscuro | Compensatorio excesivo |

**Nota:** Pueden existir variaciones mínimas (±1-2%) debido a redondeos o problemas de etiquetado de jugadores Part/Rehab en la base de datos.

---

## 🎯 UMBRALES Y COLORES

### Umbrales por Tipo de Microciclo

Los umbrales varían según el tipo de microciclo y se expresan como **porcentaje del máximo histórico**:

#### Microciclo ESTÁNDAR (7-8 días)

**Distancia Total:**
- MD-4: 65-85% (rango óptimo)
- MD-3: 50-70%
- MD-2: 35-55%
- MD-1: 20-40%

**Distancia +21 km/h:**
- MD-4: 60-80%
- MD-3: 45-65%
- MD-2: 30-50%
- MD-1: 15-35%

**Distancia +24 km/h:**
- MD-4: 55-75%
- MD-3: 40-60%
- MD-2: 25-45%
- MD-1: 10-30%

**Acel/Decel +3:**
- MD-4: 60-80%
- MD-3: 45-65%
- MD-2: 30-50%
- MD-1: 15-35%

**Ritmo Medio:**
- MD-4: 60-80%
- MD-3: 50-70%
- MD-2: 40-60%
- MD-1: 30-50%

#### Microciclo EXTENDIDO (9+ días)

Umbrales más altos (más días de entrenamiento):
- MD-4: 70-90%
- MD-3: 55-75%
- MD-2: 40-60%
- MD-1: 25-45%

#### Microciclo REDUCIDO (5-6 días)

Umbrales más bajos (menos días de recuperación):
- MD-4: 55-75%
- MD-3: 40-60%
- MD-2: 25-45%
- MD-1: 10-30%

#### Microciclo SUPER-RECORTADO (3-4 días)

Umbrales muy bajos (recuperación mínima):
- MD-3: 40-60%
- MD-2: 25-45%
- MD-1: 10-30%

### Lógica de Colores en Gráficos

**Entrenamientos normales (MD-4 a MD-1):**
- 🟩 Rectángulos verdes: Rango óptimo según tipo de microciclo
- 🟥 Líneas rojas: Límites mínimo y máximo

**Compensatorios (MD+1/MD+2):**
- 🟦 Rectángulos azul claro: Rango 55-70% del máximo histórico
- 🔵 Líneas azul acero: Límites compensatorio

**Partido (MD):**
- 🟧 Línea naranja: Máximo histórico (referencia 100%)
- Sin rectángulos (no tiene umbrales, es la referencia)

---

## 📊 VISUALIZACIÓN DE MICROCICLO

### Gráfico de Barras

Muestra la carga de cada día del microciclo para una métrica específica:

**Elementos visuales:**
1. **Barras verticales:** Valor de cada día
2. **Rectángulos de fondo:** Rangos óptimos
3. **Línea naranja:** Máximo histórico (100%)
4. **Texto en barras:**
   - MD: Valor absoluto + nombre del partido
   - Entrenamientos: Porcentaje sobre máximo histórico

**Ejemplo de lectura:**
```
MD-4: 75% (barra en zona verde) → Carga óptima
MD-3: 55% (barra en zona verde) → Carga óptima
MD-2: 40% (barra en zona verde) → Carga óptima
MD-1: 25% (barra en zona verde) → Carga óptima
MD: 10,489m (línea naranja) → Partido actual
MD+1: 38% (barra azul) → Compensatorio adecuado
```

### Hover (Información al pasar el ratón)

**Entrenamientos:**
- Día (MD-4, MD-3, etc.)
- Fecha de la sesión
- Valor absoluto de la métrica
- Porcentaje sobre máximo histórico
- Número de jugadores

**Partido (MD):**
- Nombre del partido
- Fecha
- Valor normalizado
- "Referencia 100%"
- Número de jugadores +70 mins

**Compensatorio:**
- Día (MD+1 o MD+2)
- Fecha
- Valor absoluto
- Porcentaje sobre máximo histórico
- Número de jugadores Full

---

## 🔍 CASOS ESPECIALES

### Sin Compensatorio

Si no hay MD+1 ni MD+2 con jugadores Full:
- Celda en gris en la tabla evolutiva
- No aparece en el gráfico de visualización

### Microciclos Especiales

Para situaciones atípicas (parón de selecciones, lesiones masivas):
- No se aplican umbrales
- Todo aparece en gris
- Solo se muestra información descriptiva

### Jugadores Part/Rehab

Los jugadores con participación parcial o en rehabilitación:
- ❌ NO se incluyen en entrenamientos normales (MD-4 a MD-1)
- ❌ NO se incluyen en compensatorios (MD+1/MD+2)
- ✅ SÍ se incluyen en partidos (MD) si jugaron +70 mins

**Razón:** Los entrenamientos Part/Rehab tienen cargas muy diferentes y distorsionarían los promedios del equipo.

---

## 📝 RESUMEN DE FLUJO DE CÁLCULO

### 1. Carga de Datos
```
1. Identificar microciclo (fecha inicio - fecha fin)
2. Cargar todas las sesiones del microciclo
3. Filtrar jugadores (sin porteros, solo Full para entrenamientos)
4. Cargar últimos 4 MDs históricos
```

### 2. Procesamiento por Día
```
Para cada día (MD-4, MD-3, MD-2, MD-1, MD, MD+1, MD+2):
  1. Agrupar jugadores por día
  2. Calcular promedio de cada métrica
  3. Si es MD: normalizar a 94 minutos
  4. Si es compensatorio: filtrar Part/Rehab
```

### 3. Cálculo de Máximos
```
1. Tomar últimos 4 MDs (normalizados a 94 mins)
2. Calcular MAX de cada métrica
3. Usar como referencia 100% (línea naranja)
```

### 4. Cálculo de Porcentajes
```
Para cada día de entrenamiento:
  Porcentaje = (Valor_día / Máximo_histórico) × 100
```

### 5. Asignación de Colores
```
1. Obtener umbrales según tipo de microciclo y día
2. Comparar valor con umbrales
3. Asignar color (verde/rojo claro/rojo oscuro/gris)
```

### 6. Tabla Evolutiva
```
Para cada microciclo de la temporada:
  1. Sumar carga de entrenamientos (MD-4 a MD-1)
  2. Calcular porcentaje sobre umbrales acumulados
  3. Calcular compensatorio (MD+1 o MD+2)
  4. Asignar colores según rangos
```

---

## 🎓 CONCEPTOS CLAVE

### Normalización a 94 minutos
Permite comparar jugadores que jugaron diferentes tiempos en un partido, estandarizando todos los valores como si hubieran jugado 94 minutos completos.

### Máximo Histórico
El valor más alto registrado en los últimos 4 partidos oficiales (con jugadores +70 mins). Sirve como referencia 100% para calcular porcentajes.

### Participación Full
Jugador que completó toda la sesión de entrenamiento sin limitaciones. Excluye Part (parcial) y Rehab (rehabilitación).

### Microciclo
Período de entrenamiento entre dos partidos consecutivos, organizado en días relativos al partido (MD-4, MD-3, etc.).

### Compensatorio
Entrenamiento de recuperación activa post-partido (MD+1 o MD+2), con carga controlada entre 55-70% del máximo histórico.

---

## 📞 NOTAS TÉCNICAS

### Precisión de Datos
- Los porcentajes se redondean al entero más cercano
- Pueden existir variaciones de ±1-2% debido a redondeos
- Problemas de etiquetado Part/Rehab pueden causar pequeñas discrepancias

### Rendimiento
- Sistema ultra-optimizado: solo 2 queries SQL por microciclo
- Procesamiento en memoria con pandas
- Tiempo de carga: 3-5 segundos por microciclo

### Actualización
- Los datos se actualizan automáticamente desde la base de datos
- Los máximos históricos se recalculan dinámicamente
- La tabla evolutiva se regenera al cargar la página

---

**Documento generado:** Noviembre 2024  
**Versión:** 1.0  
**RC Deportivo La Coruña - Departamento de Rendimiento**
