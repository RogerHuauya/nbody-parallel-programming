#!/bin/bash

# Script para ejecutar simulaciones N-Body con diferentes procesadores
# para demostrar speedup en visualización en tiempo real

# Configuración
N_SIZE=${1:-4}  # Tamaño N en KB (por defecto 4 = 4096 partículas)
REALTIME_DIR="realtime_simulations"
PROCESSORS=(1 2 4 8)  # Diferentes números de procesadores para mostrar speedup

echo "=== SIMULACIÓN N-BODY EN TIEMPO REAL ==="
echo "N = $((N_SIZE*1024)) partículas (constante)"
echo "Procesadores a probar: ${PROCESSORS[@]}"
echo "Directorio: $REALTIME_DIR"

# Verificar que los ejecutables existan
if [ ! -f "bin/gen-plum" ]; then
    echo "Error: bin/gen-plum no encontrado. Ejecutando 'make gen-plum'..."
    make gen-plum
fi

if [ ! -f "bin/cpu-4th" ]; then
    echo "Error: bin/cpu-4th no encontrado. Ejecutando 'make cpu-4th'..."
    make cpu-4th
fi

# Limpiar y crear estructura de directorios
rm -rf $REALTIME_DIR
mkdir -p $REALTIME_DIR

# Generar datos iniciales una sola vez para todas las simulaciones
echo "Generando datos iniciales..."
./bin/gen-plum $N_SIZE 1
mv data.inp "$REALTIME_DIR/"

# Función para ejecutar simulación con snapshots frecuentes
run_simulation() {
    local PROC=$1
    local N=$N_SIZE
    local DIR="$REALTIME_DIR/P${PROC}_N${N}KB"
    
    echo "[P=$PROC] Iniciando simulación con N=$((N*1024)) partículas..."
    
    # Crear directorio
    mkdir -p "$DIR"
    
    # Usar el mismo archivo de datos iniciales para todas las simulaciones
    cp "$REALTIME_DIR/data.inp" "$DIR/"
    
    # Crear archivo de configuración para snapshots muy frecuentes
    # eps, t_end, dt_disk, dt_contr, eta, eta_BH, input_file
    cat > "$DIR/phi-GPU4.cfg" << EOF
0.1 100.0 0.01 0.01 0.02 0.02 data.inp
EOF
    
    # Cambiar al directorio y ejecutar
    cd "$DIR"
    
    # Crear archivo de estado
    echo "RUNNING" > status.txt
    
    # Ejecutar la simulación
    echo "[N=$((N*1024))] Ejecutando simulación..."
    mpirun -np $PROC ../../bin/cpu-4th > output.log 2>&1
    
    # Marcar como completada
    echo "COMPLETED" > status.txt
    
    cd ../..
    
    echo "[P=$PROC] Simulación completada. Archivos .dat en $DIR/"
}

# Ejecutar todas las simulaciones en paralelo
echo ""
echo "Iniciando simulaciones con diferentes procesadores..."
echo "=================================================="

# Array para almacenar PIDs
pids=()

# Lanzar simulaciones en background
for PROC in "${PROCESSORS[@]}"; do
    run_simulation $PROC &
    pids+=($!)
    
    # Pequeña pausa para evitar conflictos de archivos
    sleep 1
done

# Crear archivo de información
cat > "$REALTIME_DIR/info.json" << EOF
{
    "n_particles": $((N_SIZE*1024)),
    "processors": [1, 2, 4, 8],
    "directories": ["P1_N${N_SIZE}KB", "P2_N${N_SIZE}KB", "P4_N${N_SIZE}KB", "P8_N${N_SIZE}KB"],
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
echo "N = $((N_SIZE*1024)) partículas (constante)"
for PROC in "${PROCESSORS[@]}"; do
    DIR="$REALTIME_DIR/P${PROC}_N${N_SIZE}KB"
    if [ -d "$DIR" ]; then
        if [ -f "$DIR/data.con" ]; then
            echo "P=$PROC procesadores: data.con generado"
        else
            echo "P=$PROC procesadores: sin data.con"
        fi
    fi
done 