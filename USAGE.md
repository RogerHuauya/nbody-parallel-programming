# Guía de Uso - Proyecto N-Cuerpos con MPI

## Inicio Rápido

### 1. Instalación de Dependencias

```bash
# Instalar dependencias de Python
pip3 install -r requirements.txt

# Verificar MPI (debe estar instalado en el sistema)
which mpirun
```

### 2. Ejecución del Proyecto

Ejecutar el script de inicio interactivo:

```bash
./run_project.sh
```

Este script proporciona un menú con todas las opciones disponibles.

## Uso Manual

### Compilación

```bash
cd src
make all      # Compila todas las versiones
make cpu-4th  # Solo integrador de 4º orden
make gen-plum # Solo generador de condiciones iniciales
```

### Generación de Condiciones Iniciales

```bash
cd src
./gen-plum <N_partículas> <N_procesos>
# Ejemplo: ./gen-plum 1000 1
```

### Ejecución de Simulación

```bash
cd src
mpirun -np <N_procesos> ./cpu-4th
# Ejemplo: mpirun -np 4 ./cpu-4th
```

### Benchmarking

```bash
# Ejecutar benchmark completo
bash scripts/benchmark.sh

# Analizar resultados
python3 scripts/analyze_timing.py results/timing/summary.csv
```

### Análisis de Error

```bash
# Analizar conservación de energía
python3 scripts/analyze_error.py src results/error
```

### Visualización

```bash
# Visualizador 3D interactivo
python3 visualizer/viewer.py

# Editor de parámetros
python3 visualizer/parameter_editor.py
```

## Estructura de Archivos

```
nbody-parallel-programming/
├── src/                    # Código fuente
│   ├── gen-plum.c         # Generador de condiciones iniciales
│   ├── phi-GPU.cpp        # Simulador principal
│   ├── hermite*.h         # Integradores Hermite
│   └── Makefile           # Sistema de compilación
├── visualizer/             # Herramientas de visualización
│   ├── viewer.py          # Visualizador 3D
│   └── parameter_editor.py # Editor de parámetros
├── scripts/               # Scripts de análisis
│   ├── benchmark.sh       # Benchmark automatizado
│   ├── analyze_timing.py  # Análisis de rendimiento
│   └── analyze_error.py   # Análisis de precisión
├── results/               # Resultados de experimentos
│   ├── timing/           # Mediciones de rendimiento
│   ├── error/            # Análisis de precisión
│   └── snapshots/        # Datos de simulación
├── docs/                  # Documentación
│   └── pram_model.md     # Modelo teórico PRAM
├── config/               # Configuración
│   └── default_parameters.json
└── N-Body 2/             # Código original del profesor
```

## Flujo de Trabajo Recomendado

### 1. Compilación Inicial
```bash
./run_project.sh
# Seleccionar opción 1: Compilar código fuente
```

### 2. Prueba Rápida
```bash
./run_project.sh
# Seleccionar opción 3: Ejecutar simulación rápida
```

### 3. Análisis de Rendimiento
```bash
./run_project.sh
# Seleccionar opción 4: Ejecutar benchmark
```

### 4. Visualización
```bash
./run_project.sh
# Seleccionar opción 6: Abrir visualizador
```

### 5. Análisis de Precisión
```bash
./run_project.sh
# Seleccionar opción 5: Análisis de error
```

## Tareas del Proyecto

### Tarea a: Modelo PRAM
- Archivo: `docs/pram_model.md`
- Contiene análisis teórico completo
- Predicciones de escalabilidad

### Tarea b: Mediciones de Rendimiento
- Script: `scripts/benchmark.sh`
- Análisis: `scripts/analyze_timing.py`
- Resultados: `results/timing/`

### Tarea c: Análisis de Precisión
- Script: `scripts/analyze_error.py`
- Análisis de conservación de energía
- Comparación de órdenes de integración

### Tarea d: Visualizador Interactivo
- Visualizador: `visualizer/viewer.py`
- Editor: `visualizer/parameter_editor.py`
- Características:
  - Visualización 3D
  - Controles interactivos
  - Trails de partículas
  - Análisis en tiempo real

## Solución de Problemas

### Error: MPI no encontrado
```bash
# Ubuntu/Debian
sudo apt-get install openmpi-bin openmpi-dev

# macOS
brew install openmpi

# CentOS/RHEL
sudo yum install openmpi openmpi-devel
```

### Error: Módulos de Python faltantes
```bash
pip3 install numpy matplotlib pandas scipy
```

### Error: Compilación fallida
```bash
# Verificar compilador
gcc --version
mpicxx --version

# Limpiar y recompilar
cd src
make clean
make all
```

### Error: No se pueden ejecutar simulaciones
```bash
# Verificar permisos
chmod +x src/gen-plum src/cpu-4th

# Verificar MPI
mpirun --version
```

## Consejos de Optimización

1. **Para sistemas grandes**: Usar N > 5000 partículas
2. **Para benchmarks**: Ejecutar con diferentes números de procesos
3. **Para análisis**: Guardar snapshots frecuentes
4. **Para visualización**: Usar resolución temporal adecuada

## Resultados Esperados

- **Speedup**: Hasta 8x con 16 procesos (dependiendo del sistema)
- **Eficiencia**: > 50% hasta 8 procesos
- **Precisión**: Error de energía < 10^-6 con integrador de 8º orden
- **Escalabilidad**: Buena hasta P ≈ N/100

## Contacto y Soporte

Para problemas específicos:
1. Revisar logs en `results/timing/`
2. Verificar dependencias con opción 8 del menú
3. Consultar documentación en `docs/` 