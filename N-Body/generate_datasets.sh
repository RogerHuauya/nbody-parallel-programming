#!/bin/bash

# Script para generar datasets con diferentes tamaños N (potencias de 2)
# y ejecutar simulaciones almacenando estados para animación

echo "Generando datasets para diferentes tamaños N..."

# Crear directorio para resultados
mkdir -p datasets
mkdir -p snapshots

# Diferentes tamaños N (potencias de 2)
sizes=(1 2 4 8 16)  # Equivale a 1024, 2048, 4096, 8192, 16384 partículas

for N in "${sizes[@]}"; do
    echo "Generando dataset para N = $((N*1024)) partículas..."
    
    # Generar datos iniciales
    ./gen-plum $N 1
    
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
    mpirun -np 1 ../../cpu-4th
    
    # Guardar archivos de salida
    if [ -f "data.con" ]; then
        cp data.con "../../snapshots/N_${N}KB/"
    fi
    
    cd ../..
    
    echo "Completado para N = $((N*1024))"
done

echo "Generación de datasets completa!"
echo "Datasets disponibles en: datasets/"
echo "Snapshots disponibles en: snapshots/" 