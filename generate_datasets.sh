#!/bin/bash

# Script para generar datasets con diferentes tamaños N (potencias de 2)
# y ejecutar simulaciones almacenando estados para animación
# Captura datos de rendimiento para strong scaling y weak scaling

echo "Generando datasets para diferentes tamaños N..."

# Verificar que los ejecutables existan
if [ ! -f "bin/gen-plum" ]; then
    echo "Error: bin/gen-plum no encontrado. Ejecutando 'make gen-plum'..."
    make gen-plum
fi

if [ ! -f "bin/cpu-4th" ]; then
    echo "Error: bin/cpu-4th no encontrado. Ejecutando 'make cpu-4th'..."
    make cpu-4th
fi

# Crear directorio para resultados
mkdir -p datasets
mkdir -p snapshots
mkdir -p performance_data

# Crear archivo CSV para los resultados
echo "N_particles,processors,time_seconds,gflops,scaling_type" > performance_data/scaling_results.csv

# Diferentes tamaños N (potencias de 2)
sizes=(1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192)
processors=(1 2 4 8)  # Diferentes números de procesadores para scaling

echo "=== GENERANDO DATOS PARA STRONG SCALING ==="
# Strong scaling: tamaño fijo, variar procesadores
FIXED_N=4  # 4096 partículas fijas
echo "Usando N fijo = $((FIXED_N*1024)) partículas"

for proc in "${processors[@]}"; do
    echo "Strong scaling: N=$((FIXED_N*1024)), procesadores=$proc"
    
    # Generar datos iniciales
    ./bin/gen-plum $FIXED_N 1
    
    # Crear directorio
    mkdir -p "datasets/strong_N${FIXED_N}_P${proc}"
    cp data.inp "datasets/strong_N${FIXED_N}_P${proc}/"
    
    # Crear configuración
    cat > "datasets/strong_N${FIXED_N}_P${proc}/phi-GPU4.cfg" << EOF
0.01 0.5 0.1 0.1 0.02 0.02 data.inp
EOF
    
    cd "datasets/strong_N${FIXED_N}_P${proc}"
    
    # Ejecutar con medición de tiempo
    echo "Ejecutando con $proc procesadores..."
    start_time=$(date +%s.%N)
    
    mpirun -np $proc ../../bin/cpu-4th > output.log 2>&1
    
    end_time=$(date +%s.%N)
    execution_time=$(echo "$end_time - $start_time" | bc)
    
    # Extraer GFlops de la salida
    gflops=$(grep "Real Speed" output.log | awk '{print $4}' || echo "0")
    
    # Guardar en CSV
    echo "$((FIXED_N*1024)),$proc,$execution_time,$gflops,strong" >> ../../performance_data/scaling_results.csv
    
    echo "Tiempo: ${execution_time}s, GFlops: $gflops"
    
    cd ../..
done

echo "=== GENERANDO DATOS PARA WEAK SCALING ==="
# Weak scaling: aumentar N proporcionalmente con procesadores

base_particles_per_proc=1024  # 1024 partículas por procesador

for proc in "${processors[@]}"; do
    N_scaled=$((proc * base_particles_per_proc / 1024))  # Convertir a unidades de KB
    if [ $N_scaled -eq 0 ]; then
        N_scaled=1
    fi
    
    echo "Weak scaling: N=$((N_scaled*1024)), procesadores=$proc ($(($N_scaled*1024/proc)) partículas/proc)"
    
    # Generar datos iniciales
    ./bin/gen-plum $N_scaled 1
    
    # Crear directorio
    mkdir -p "datasets/weak_N${N_scaled}_P${proc}"
    cp data.inp "datasets/weak_N${N_scaled}_P${proc}/"
    
    # Crear configuración
    cat > "datasets/weak_N${N_scaled}_P${proc}/phi-GPU4.cfg" << EOF
0.01 0.5 0.1 0.1 0.02 0.02 data.inp
EOF
    
    cd "datasets/weak_N${N_scaled}_P${proc}"
    
    # Ejecutar con medición de tiempo
    start_time=$(date +%s.%N)
    
    mpirun -np $proc ../../bin/cpu-4th > output.log 2>&1
    
    end_time=$(date +%s.%N)
    execution_time=$(echo "$end_time - $start_time" | bc)
    
    # Extraer GFlops
    gflops=$(grep "Real Speed" output.log | awk '{print $4}' || echo "0")
    
    # Calcular tiempo por partícula
    time_per_particle=$(echo "scale=6; $execution_time / $((N_scaled*1024))" | bc)
    
    # Guardar en CSV
    echo "$((N_scaled*1024)),$proc,$execution_time,$gflops,weak" >> ../../performance_data/scaling_results.csv
    
    echo "Tiempo: ${execution_time}s, Tiempo/partícula: ${time_per_particle}s"
    
    cd ../..
done

echo "=== GENERANDO DATOS PARA DIFERENTES TAMAÑOS N ==="
# Datos originales para visualización
for N in "${sizes[@]}"; do
    echo "Generando dataset para N = $((N*1024)) partículas..."
    
    # Generar datos iniciales
    ./bin/gen-plum $N 1
    
    # Crear directorio para este tamaño
    mkdir -p "datasets/N_${N}KB"
    mkdir -p "snapshots/N_${N}KB"
    
    # Copiar datos iniciales
    cp data.inp "datasets/N_${N}KB/"
    
    # Crear archivo de configuración para capturar más snapshots
    cat > "datasets/N_${N}KB/phi-GPU4.cfg" << EOF
0.01 1.0 0.05 0.05 0.02 0.02 data.inp
EOF
    
    # Ejecutar simulación
    echo "Ejecutando simulación para N = $((N*1024))..."
    cd "datasets/N_${N}KB"
    
    # Ejecutar y capturar snapshots
    start_time=$(date +%s.%N)
    mpirun -np 1 ../../bin/cpu-4th > output.log 2>&1
    end_time=$(date +%s.%N)
    execution_time=$(echo "$end_time - $start_time" | bc)
    
    # Extraer GFlops
    gflops=$(grep "Real Speed" output.log | awk '{print $4}' || echo "0")
    
    # Guardar en CSV general
    echo "$((N*1024)),1,$execution_time,$gflops,baseline" >> ../../performance_data/scaling_results.csv
    
    # Guardar archivos de salida
    if [ -f "data.con" ]; then
        cp data.con "../../snapshots/N_${N}KB/"
    fi
    
    cd ../..
    
    echo "Completado para N = $((N*1024)) - Tiempo: ${execution_time}s"
done

echo "Generación de datasets completa!"
echo "Datasets disponibles en: datasets/"
echo "Snapshots disponibles en: snapshots/"
echo "Datos de rendimiento en: performance_data/"

# Mostrar resumen de archivos generados
echo ""
echo "=== ARCHIVO CSV GENERADO ==="
echo "1. scaling_results.csv - Todos los resultados de scaling"

ls -la performance_data/ 