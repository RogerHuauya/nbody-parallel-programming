#!/bin/bash

# Script de inicio para el proyecto N-Cuerpos
# Proporciona un menú interactivo para ejecutar diferentes componentes

PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
cd "$PROJECT_ROOT"

show_menu() {
    echo "========================================"
    echo "    PROYECTO N-CUERPOS CON MPI"
    echo "========================================"
    echo "1. Compilar código fuente"
    echo "2. Generar condiciones iniciales"
    echo "3. Ejecutar simulación rápida"
    echo "4. Ejecutar benchmark"
    echo "5. Análisis de error"
    echo "6. Abrir visualizador"
    echo "7. Abrir editor de parámetros"
    echo "8. Información del sistema"
    echo "9. Limpiar archivos temporales"
    echo "0. Salir"
    echo "========================================"
    echo -n "Seleccione una opción: "
}

compile_code() {
    echo "Compilando código fuente..."
    cd src
    make clean
    make all
    cd ..
    echo "Compilación completada."
}

generate_initial_conditions() {
    echo "Generando condiciones iniciales..."
    cd src
    if [ ! -f "gen-plum" ]; then
        echo "Compilando gen-plum..."
        make gen-plum
    fi
    
    echo -n "Número de partículas [1000]: "
    read n_particles
    n_particles=${n_particles:-1000}
    
    echo -n "Número de procesos [1]: "
    read n_processes
    n_processes=${n_processes:-1}
    
    ./gen-plum $n_particles $n_processes
    cd ..
    echo "Condiciones iniciales generadas."
}

run_quick_simulation() {
    echo "Ejecutando simulación rápida..."
    cd src
    
    # Verificar que existan condiciones iniciales
    if [ ! -f "data.inp" ]; then
        echo "No se encontraron condiciones iniciales. Generando..."
        generate_initial_conditions
    fi
    
    # Compilar si es necesario
    if [ ! -f "cpu-4th" ]; then
        echo "Compilando cpu-4th..."
        make cpu-4th
    fi
    
    echo -n "Número de procesos MPI [2]: "
    read n_procs
    n_procs=${n_procs:-2}
    
    echo "Ejecutando simulación con $n_procs procesos..."
    mpirun -np $n_procs ./cpu-4th
    
    cd ..
    echo "Simulación completada."
}

run_benchmark() {
    echo "Ejecutando benchmark..."
    if [ ! -f "scripts/benchmark.sh" ]; then
        echo "Error: Script de benchmark no encontrado."
        return 1
    fi
    
    echo "Esto puede tomar varios minutos..."
    bash scripts/benchmark.sh
    echo "Benchmark completado."
}

analyze_error() {
    echo "Ejecutando análisis de error..."
    if [ ! -f "scripts/analyze_error.py" ]; then
        echo "Error: Script de análisis no encontrado."
        return 1
    fi
    
    echo "Analizando archivos en src/..."
    python3 scripts/analyze_error.py src results/error
    echo "Análisis completado."
}

open_visualizer() {
    echo "Abriendo visualizador..."
    if [ ! -f "visualizer/viewer.py" ]; then
        echo "Error: Visualizador no encontrado."
        return 1
    fi
    
    python3 visualizer/viewer.py &
    echo "Visualizador lanzado en background."
}

open_parameter_editor() {
    echo "Abriendo editor de parámetros..."
    if [ ! -f "visualizer/parameter_editor.py" ]; then
        echo "Error: Editor de parámetros no encontrado."
        return 1
    fi
    
    python3 visualizer/parameter_editor.py &
    echo "Editor de parámetros lanzado en background."
}

show_system_info() {
    echo "========================================"
    echo "    INFORMACIÓN DEL SISTEMA"
    echo "========================================"
    echo "Sistema operativo: $(uname -s)"
    echo "Arquitectura: $(uname -m)"
    echo "Procesadores: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'Desconocido')"
    echo "Memoria: $(free -h 2>/dev/null | grep '^Mem:' | awk '{print $2}' || echo 'Desconocido')"
    echo "MPI: $(which mpirun 2>/dev/null || echo 'No encontrado')"
    echo "CUDA: $(which nvcc 2>/dev/null || echo 'No encontrado')"
    echo "Python: $(python3 --version 2>/dev/null || echo 'No encontrado')"
    echo "========================================"
}

clean_temp_files() {
    echo "Limpiando archivos temporales..."
    
    # Limpiar archivos compilados
    cd src
    make clean 2>/dev/null
    rm -f data.inp data.con *.dat
    cd ..
    
    # Limpiar resultados temporales
    rm -f results/timing/*.txt
    rm -f results/error/*.png
    rm -f results/snapshots/*.dat
    rm -f *.png
    
    echo "Archivos temporales eliminados."
}

# Verificar dependencias
check_dependencies() {
    echo "Verificando dependencias..."
    
    # Verificar MPI
    if ! command -v mpirun &> /dev/null; then
        echo "Advertencia: MPI no encontrado. Algunas funciones pueden no funcionar."
    fi
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python3 no encontrado. Necesario para visualización y análisis."
        return 1
    fi
    
    # Verificar módulos de Python
    python3 -c "import numpy, matplotlib" 2>/dev/null || {
        echo "Advertencia: Faltan módulos de Python (numpy, matplotlib)."
        echo "Instale con: pip3 install numpy matplotlib pandas"
    }
    
    echo "Verificación completada."
}

# Función principal
main() {
    check_dependencies
    
    while true; do
        echo ""
        show_menu
        read option
        
        case $option in
            1) compile_code ;;
            2) generate_initial_conditions ;;
            3) run_quick_simulation ;;
            4) run_benchmark ;;
            5) analyze_error ;;
            6) open_visualizer ;;
            7) open_parameter_editor ;;
            8) show_system_info ;;
            9) clean_temp_files ;;
            0) echo "¡Hasta luego!"; exit 0 ;;
            *) echo "Opción inválida. Intente nuevamente." ;;
        esac
        
        echo ""
        echo "Presione Enter para continuar..."
        read
    done
}

# Ejecutar función principal
main 