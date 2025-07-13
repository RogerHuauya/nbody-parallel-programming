#!/bin/bash

# Script para ejecutar simulaciones N-Body en paralelo con snapshots frecuentes
# para visualización en tiempo real

# Configuración
PROCESSORS=${1:-2}  # Número de procesadores (por defecto 2)
REALTIME_DIR="realtime_simulations"
SIZES=(1 2 4 8)  # N valores: 1024, 2048, 4096, 8192 partículas

echo "=== SIMULACIÓN N-BODY EN TIEMPO REAL ==="
echo "Procesadores: $PROCESSORS"
echo "Directorio: $REALTIME_DIR"

# Limpiar y crear estructura de directorios
rm -rf $REALTIME_DIR
mkdir -p $REALTIME_DIR

# Función para ejecutar simulación con snapshots frecuentes
run_simulation() {
    local N=$1
    local PROC=$2
    local DIR="$REALTIME_DIR/N_${N}KB"
    
    echo "[N=$((N*1024))] Iniciando simulación con $PROC procesadores..."
    
    # Crear directorio
    mkdir -p "$DIR/snapshots"
    
    # Generar datos iniciales
    ./gen-plum $N 1
    mv data.inp "$DIR/"
    
    # Crear archivo de configuración para snapshots muy frecuentes
    # eps, t_end, dt_disk, dt_contr, eta, eta_BH, input_file
    cat > "$DIR/phi-GPU4.cfg" << EOF
0.01 10.0 0.01 0.01 0.02 0.02 data.inp
EOF
    
    # Cambiar al directorio y ejecutar
    cd "$DIR"
    
    # Crear archivo de estado
    echo "RUNNING" > status.txt
    echo "0" > current_step.txt
    
    # Ejecutar simulación y guardar snapshots
    (
        # Loop para capturar snapshots durante la ejecución
        step=0
        while true; do
            if [ -f "data.con" ]; then
                # Copiar snapshot con timestamp
                cp data.con "snapshots/snapshot_$(printf "%04d" $step).dat"
                echo $step > current_step.txt
                ((step++))
                
                # Pequeña pausa para no saturar el sistema
                sleep 0.1
            fi
            
            # Verificar si la simulación terminó
            if [ -f "simulation_complete.flag" ]; then
                break
            fi
        done
    ) &
    MONITOR_PID=$!
    
    # Ejecutar la simulación
    echo "[N=$((N*1024))] Ejecutando simulación..."
    mpirun -np $PROC ../../cpu-4th > output.log 2>&1
    
    # Marcar como completada
    touch simulation_complete.flag
    echo "COMPLETED" > status.txt
    
    # Esperar al monitor
    wait $MONITOR_PID
    
    # Copiar archivo final
    if [ -f "data.con" ]; then
        cp data.con "snapshots/snapshot_final.dat"
    fi
    
    cd ../..
    
    echo "[N=$((N*1024))] Simulación completada. Snapshots en $DIR/snapshots/"
}

# Ejecutar todas las simulaciones en paralelo
echo ""
echo "Iniciando simulaciones en paralelo..."
echo "=================================="

# Array para almacenar PIDs
pids=()

# Lanzar simulaciones en background
for N in "${SIZES[@]}"; do
    run_simulation $N $PROCESSORS &
    pids+=($!)
    
    # Pequeña pausa para evitar conflictos de archivos
    sleep 1
done

# Crear archivo de información
cat > "$REALTIME_DIR/info.json" << EOF
{
    "processors": $PROCESSORS,
    "sizes": [1024, 2048, 4096, 8192],
    "directories": ["N_1KB", "N_2KB", "N_4KB", "N_8KB"],
    "status": "running",
    "start_time": "$(date -Iseconds)"
}
EOF

echo ""
echo "Todas las simulaciones iniciadas."
echo "PIDs: ${pids[@]}"
echo ""
echo "Para visualizar en tiempo real, ejecuta en otra terminal:"
echo "  python realtime_visualizer.py"
echo ""
echo "Esperando a que terminen las simulaciones..."

# Esperar a que terminen todas
for pid in "${pids[@]}"; do
    wait $pid
done

# Actualizar estado
sed -i 's/"status": "running"/"status": "completed"/' "$REALTIME_DIR/info.json"

echo ""
echo "¡Todas las simulaciones completadas!"
echo "Resultados en: $REALTIME_DIR/"

# Generar resumen
echo ""
echo "=== RESUMEN ==="
for N in "${SIZES[@]}"; do
    DIR="$REALTIME_DIR/N_${N}KB"
    if [ -d "$DIR/snapshots" ]; then
        count=$(ls -1 "$DIR/snapshots"/snapshot_*.dat 2>/dev/null | wc -l)
        echo "N=$((N*1024)): $count snapshots generados"
    fi
done 