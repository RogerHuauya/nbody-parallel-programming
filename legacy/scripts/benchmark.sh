#!/bin/bash

# Script de benchmarking para simulador N-cuerpos
# Tarea b: Mediciones de rendimiento

# Configuración
PROJECT_DIR=$(dirname "$(dirname "$(readlink -f "$0")")")
SRC_DIR="$PROJECT_DIR/src"
RESULTS_DIR="$PROJECT_DIR/results/timing"

# Crear directorio de resultados si no existe
mkdir -p "$RESULTS_DIR"

# Configuración de experimentos
N_PARTICLES=(1000 2000 5000 10000)        # Números de partículas
N_PROCESSES=(1 2 4 8 16)                  # Números de procesos MPI
INTEGRATION_ORDERS=(4 6 8)                # Órdenes de integración
TIMESTEPS=100                             # Número de pasos temporales para benchmark

# Archivo de log principal
LOG_FILE="$RESULTS_DIR/benchmark_$(date +%Y%m%d_%H%M%S).log"

echo "=== BENCHMARK N-CUERPOS ===" | tee "$LOG_FILE"
echo "Fecha: $(date)" | tee -a "$LOG_FILE"
echo "Sistema: $(uname -a)" | tee -a "$LOG_FILE"
echo "MPI: $(which mpirun)" | tee -a "$LOG_FILE"
echo "Procesadores disponibles: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null)" | tee -a "$LOG_FILE"
echo "==============================" | tee -a "$LOG_FILE"

# Función para ejecutar benchmark
run_benchmark() {
    local n_particles=$1
    local n_processes=$2
    local order=$3
    local exe_name="cpu-${order}th"
    
    echo "Ejecutando: N=$n_particles, P=$n_processes, Orden=$order" | tee -a "$LOG_FILE"
    
    # Generar condiciones iniciales
    cd "$SRC_DIR"
    ./gen-plum $n_particles 1 > /dev/null 2>&1
    
    # Nombre del archivo de resultados
    RESULT_FILE="$RESULTS_DIR/N${n_particles}_P${n_processes}_O${order}.txt"
    
    # Ejecutar simulación con medición de tiempo
    echo "Ejecutando simulación..." | tee -a "$LOG_FILE"
    
    # Usar time para medir tiempo total
    (time mpirun -np $n_processes ./$exe_name) > "$RESULT_FILE" 2>&1
    
    # Extraer tiempos del resultado
    if [ -f "$RESULT_FILE" ]; then
        REAL_TIME=$(grep "real" "$RESULT_FILE" | awk '{print $2}')
        USER_TIME=$(grep "user" "$RESULT_FILE" | awk '{print $2}')
        SYS_TIME=$(grep "sys" "$RESULT_FILE" | awk '{print $2}')
        
        echo "  Tiempo real: $REAL_TIME" | tee -a "$LOG_FILE"
        echo "  Tiempo usuario: $USER_TIME" | tee -a "$LOG_FILE"
        echo "  Tiempo sistema: $SYS_TIME" | tee -a "$LOG_FILE"
        
        # Añadir línea de resumen al archivo CSV
        echo "$n_particles,$n_processes,$order,$REAL_TIME,$USER_TIME,$SYS_TIME" >> "$RESULTS_DIR/summary.csv"
    else
        echo "  ERROR: No se pudo generar archivo de resultados" | tee -a "$LOG_FILE"
    fi
    
    echo "---" | tee -a "$LOG_FILE"
}

# Compilar todos los ejecutables necesarios
echo "Compilando ejecutables..." | tee -a "$LOG_FILE"
cd "$SRC_DIR"
make clean > /dev/null 2>&1
make gen-plum cpu-4th cpu-6th cpu-8th | tee -a "$LOG_FILE"

# Verificar que se compilaron correctamente
for order in "${INTEGRATION_ORDERS[@]}"; do
    if [ ! -f "cpu-${order}th" ]; then
        echo "ERROR: No se pudo compilar cpu-${order}th" | tee -a "$LOG_FILE"
        exit 1
    fi
done

# Crear archivo CSV con headers
echo "N_Particles,N_Processes,Order,Real_Time,User_Time,Sys_Time" > "$RESULTS_DIR/summary.csv"

# Ejecutar benchmarks
echo "Iniciando benchmarks..." | tee -a "$LOG_FILE"

for n_particles in "${N_PARTICLES[@]}"; do
    for n_processes in "${N_PROCESSES[@]}"; do
        for order in "${INTEGRATION_ORDERS[@]}"; do
            run_benchmark $n_particles $n_processes $order
        done
    done
done

echo "Benchmarks completados!" | tee -a "$LOG_FILE"
echo "Resultados guardados en: $RESULTS_DIR" | tee -a "$LOG_FILE"

# Generar reporte básico
echo "Generando reporte..." | tee -a "$LOG_FILE"
python3 "$PROJECT_DIR/scripts/analyze_timing.py" "$RESULTS_DIR/summary.csv" | tee -a "$LOG_FILE"

echo "=== BENCHMARK COMPLETADO ===" | tee -a "$LOG_FILE" 