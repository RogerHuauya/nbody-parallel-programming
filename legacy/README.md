# Proyecto N-Cuerpos con MPI

## Descripción
Este proyecto implementa un simulador de N-cuerpos gravitacional en 3D usando MPI para paralelización. Incluye análisis de rendimiento, precisión y un visualizador interactivo.

## Estructura del Proyecto

```
proyecto-nbody/
├── src/                    # Código fuente modificado
├── visualizer/            # Visualizador interactivo
├── scripts/               # Scripts de benchmarking y análisis
├── results/               # Resultados de experimentos
│   ├── timing/           # Mediciones de rendimiento
│   ├── error/            # Análisis de precisión
│   └── snapshots/        # Instantáneas para visualización
├── docs/                  # Documentación
└── N-Body 2/             # Código original del profesor (no modificar)
```

## Tareas del Proyecto

### a) Modelo PRAM
- Análisis teórico del algoritmo de N-cuerpos
- Modelo de complejidad y paralelización

### b) Mediciones de Rendimiento
- Benchmarking con diferentes números de procesos
- Análisis de escalabilidad
- Comparación cómputo vs comunicación

### c) Análisis de Precisión
- Verificación de conservación de energía
- Comparación de diferentes órdenes de integración
- Análisis de error numérico

### d) Visualizador Interactivo
- Visualización 3D de partículas
- Controles de simulación
- Editor de parámetros

## Dependencias
- MPI (mpich o openmpi)
- CUDA (opcional, para GPU)
- Python 3.x (para visualización)
- numpy, matplotlib (para análisis)

## Uso

### Generación de Condiciones Iniciales
```bash
cd src
make gen-plum
./gen-plum <N> <NP>
```

### Ejecución de Simulación
```bash
make cpu-4th
mpirun -np <P> ./cpu-4th
```

### Benchmarking
```bash
cd scripts
./benchmark.sh
```

### Visualización
```bash
cd visualizer
python viewer.py
```

## Autor
[Tu nombre]
Proyecto de Programación Paralela - N-Cuerpos con MPI 