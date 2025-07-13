# Análisis de Procesos de Visualización y Generación de Gráficas

## 1. Procesos Involucrados en la Generación de Gráficas

### 1.1 Pipeline de Visualización

El proceso completo desde la simulación hasta las gráficas finales involucra:

```
Simulación → Snapshots → Carga de Datos → Procesamiento → Renderizado → Gráfica Final
```

### 1.2 Desglose de Tiempos por Proceso

#### a) Escritura de Snapshots (Durante Simulación)
```
T_snapshot = n_snapshots · [t_gather + t_format + t_write]
```

Donde:
- `t_gather = τ_mpi · log(p) + μ_mpi · N · 8 · sizeof(double)` (recolección MPI)
- `t_format = κ · N` (formateo de datos)
- `t_write = N · bytes_per_particle / disk_bandwidth`

#### b) Lectura y Parsing de Datos
```
T_read = n_files · [t_open + t_parse + t_store]
```

Donde:
- `t_open = disk_latency ≈ 10ms`
- `t_parse = ρ · file_size` (ρ = velocidad de parsing)
- `t_store = N · sizeof(particle) / memory_bandwidth`

#### c) Procesamiento de Datos para Visualización
```
T_process = N · n_frames · [t_transform + t_project + t_color]
```

#### d) Renderizado 3D
```
T_render = n_frames · [t_clear + N · t_draw_particle + t_composite]
```

## 2. Paralelización de la Visualización

### 2.1 Estrategias de Paralelización

#### Estrategia 1: Paralelización por Frames (Implementada)
```python
# Pseudocódigo
frames = Parallel(n_jobs=n_cores)(
    delayed(generate_frame)(t) for t in time_steps
)
```

**Tiempo paralelo:**
```
T_frames_parallel = T_frames_sequential / n_cores + overhead_threading
```

#### Estrategia 2: Paralelización por Partículas
```
T_particles_parallel = N · n_frames / n_cores + sync_overhead · n_frames
```

### 2.2 Análisis de Speedup en Visualización

**Speedup de generación de frames:**
```
S_viz_frames = n_cores / [1 + (thread_overhead · n_cores) / (frame_time · n_frames)]
```

**Eficiencia de visualización:**
```
E_viz = 1 / [1 + thread_overhead / (frame_time · n_frames / n_cores)]
```

## 3. Análisis de la Generación de Gráficas de Scaling

### 3.1 Proceso de Análisis de Strong Scaling

Para generar las gráficas de strong scaling:

1. **Recolección de datos:**
   ```
   T_collect = n_runs · T_simulation(N, p)
   ```

2. **Cálculo de métricas:**
   ```
   for p in processors:
       speedup[p] = T_seq / T_par[p]
       efficiency[p] = speedup[p] / p
   ```

3. **Generación de gráficas:**
   ```
   T_plot = 4 · (t_setup + n_points · t_draw + t_save)
   ```

### 3.2 Proceso de Análisis de Weak Scaling

1. **Configuración de experimentos:**
   ```
   for p in processors:
       N[p] = base_particles_per_proc · p
   ```

2. **Normalización de tiempos:**
   ```
   normalized_time[p] = T_par[p] / T_par[1]
   weak_efficiency[p] = T_par[1] / T_par[p]
   ```

## 4. Complejidad Computacional de la Visualización

### 4.1 Visualización Estándar

```
O_viz = O(N · n_frames) + O(n_frames · log(n_frames))
```

### 4.2 Visualización en Tiempo Real

```
O_realtime = O(N) por actualización + O(buffer_size) para trayectorias
```

### 4.3 Comparación de Métodos

| Método | Complejidad Temporal | Complejidad Espacial | Paralelizable |
|--------|---------------------|---------------------|---------------|
| Estándar | O(N · n_frames) | O(N · n_frames) | Sí (frames) |
| Tiempo Real | O(N) por frame | O(N · buffer) | Limitado |
| Trayectorias | O(N · n_frames²) | O(N · n_frames) | Sí (partículas) |

## 5. Optimizaciones Implementadas

### 5.1 Reducción de Datos

Para grandes N, se implementa:

```python
# Muestreo de partículas para trayectorias
n_display = min(N, max_particles_display)
sample_indices = np.linspace(0, N-1, n_display, dtype=int)
```

### 5.2 Buffer Circular para Tiempo Real

```python
snapshots = deque(maxlen=buffer_size)  # O(1) inserción/eliminación
```

### 5.3 Vectorización con NumPy

```python
# Transformación vectorizada
positions_transformed = positions @ rotation_matrix + translation
```

## 6. Análisis de Rendimiento del Pipeline Completo

### 6.1 Tiempo Total del Pipeline

```
T_pipeline = T_sim + T_snapshot + T_read + T_process + T_render + T_save
```

### 6.2 Identificación de Cuellos de Botella

Para N = 8192:
- **Simulación:** 60-70% del tiempo total
- **I/O (snapshots):** 15-20%
- **Visualización:** 10-15%
- **Post-procesamiento:** 5%

### 6.3 Speedup Global del Sistema

```
S_global = T_sequential_total / T_parallel_total
        = (T_sim_seq + T_viz_seq) / (T_sim_par + T_viz_par)
```

## 7. Modelo Predictivo de Rendimiento

### 7.1 Predicción de Tiempo de Visualización

```python
def predict_viz_time(N, n_frames, n_cores):
    t_base = 0.001  # segundos por frame base
    t_per_particle = 1e-6  # segundos por partícula
    t_overhead = 0.01 * n_cores  # overhead de threading
    
    t_sequential = n_frames * (t_base + N * t_per_particle)
    t_parallel = t_sequential / n_cores + t_overhead
    
    return t_parallel
```

### 7.2 Recomendaciones Basadas en N

```python
def recommend_settings(N):
    if N < 1000:
        return {"fps": 60, "frames": 200, "cores": 4}
    elif N < 10000:
        return {"fps": 30, "frames": 100, "cores": 8}
    else:
        return {"fps": 15, "frames": 50, "cores": "all"}
```

## 8. Conclusiones sobre Procesos Gráficos

1. **Paralelización por frames** es más eficiente que por partículas para N < 100,000
2. **El I/O de snapshots** puede ser un cuello de botella significativo
3. **La visualización en tiempo real** requiere balance entre frecuencia de actualización y calidad
4. **El buffer circular** optimiza el uso de memoria en visualización en tiempo real

---

*Este análisis complementa el análisis matemático principal, enfocándose específicamente en los procesos de visualización y generación de gráficas.* 