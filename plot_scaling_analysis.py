#!/usr/bin/env python3
"""
Script para visualizar los resultados de Strong Scaling y Weak Scaling
del algoritmo N-Body paralelo
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime

# Configuración de estilo para las gráficas
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 8

def load_data():
    """Cargar los datos desde los archivos CSV"""
    try:
        # Cargar datos generales
        df_all = pd.read_csv('performance_data/scaling_results.csv')
        
        # Separar por tipo de scaling
        df_strong = df_all[df_all['scaling_type'] == 'strong']
        df_weak = df_all[df_all['scaling_type'] == 'weak']
        df_baseline = df_all[df_all['scaling_type'] == 'baseline']
        
        return df_all, df_strong, df_weak, df_baseline
    except FileNotFoundError as e:
        print(f"Error: No se encontraron los archivos CSV. Asegúrate de ejecutar primero generate_datasets.sh")
        print(f"Detalles: {e}")
        return None, None, None, None

def plot_strong_scaling(df_strong):
    """Graficar los resultados de Strong Scaling"""
    if df_strong.empty:
        print("No hay datos de strong scaling para graficar")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análisis de Strong Scaling - N-Body Simulation', fontsize=16, fontweight='bold')
    
    # Obtener datos base (1 procesador)
    base_time = df_strong[df_strong['processors'] == 1]['time_seconds'].values[0]
    base_gflops = df_strong[df_strong['processors'] == 1]['gflops'].values[0]
    
    # 1. Tiempo de ejecución vs Procesadores
    ax1.plot(df_strong['processors'], df_strong['time_seconds'], 'bo-', label='Tiempo real')
    ax1.plot(df_strong['processors'], base_time/df_strong['processors'], 'r--', label='Tiempo ideal')
    ax1.set_xlabel('Número de Procesadores')
    ax1.set_ylabel('Tiempo de Ejecución (s)')
    ax1.set_title('Tiempo de Ejecución vs Procesadores')
    ax1.legend()
    ax1.grid(True)
    ax1.set_xticks(df_strong['processors'])
    
    # 2. Speedup
    speedup = base_time / df_strong['time_seconds']
    ideal_speedup = df_strong['processors']
    
    ax2.plot(df_strong['processors'], speedup, 'go-', label='Speedup real')
    ax2.plot(df_strong['processors'], ideal_speedup, 'r--', label='Speedup ideal')
    ax2.set_xlabel('Número de Procesadores')
    ax2.set_ylabel('Speedup')
    ax2.set_title('Speedup vs Procesadores')
    ax2.legend()
    ax2.grid(True)
    ax2.set_xticks(df_strong['processors'])
    
    # 3. Eficiencia
    efficiency = speedup / df_strong['processors'] * 100
    
    ax3.plot(df_strong['processors'], efficiency, 'mo-', label='Eficiencia')
    ax3.axhline(y=100, color='r', linestyle='--', label='Eficiencia ideal (100%)')
    ax3.set_xlabel('Número de Procesadores')
    ax3.set_ylabel('Eficiencia (%)')
    ax3.set_title('Eficiencia vs Procesadores')
    ax3.legend()
    ax3.grid(True)
    ax3.set_ylim(0, 110)
    ax3.set_xticks(df_strong['processors'])
    
    # 4. GFlops
    ax4.plot(df_strong['processors'], df_strong['gflops'], 'co-', label='GFlops reales')
    ax4.set_xlabel('Número de Procesadores')
    ax4.set_ylabel('GFlops')
    ax4.set_title('Rendimiento (GFlops) vs Procesadores')
    ax4.legend()
    ax4.grid(True)
    ax4.set_xticks(df_strong['processors'])
    
    plt.tight_layout()
    plt.savefig('performance_data/strong_scaling_analysis.png', dpi=300)
    
    # Imprimir tabla de resultados
    print("\n=== RESULTADOS DE STRONG SCALING ===")
    print(f"N fijo = {df_strong['N_particles'].iloc[0]} partículas")
    print("\nProcesadores | Tiempo (s) | Speedup | Eficiencia (%) | GFlops")
    print("-" * 65)
    for i, row in df_strong.iterrows():
        proc = row['processors']
        time = row['time_seconds']
        sp = base_time / time
        eff = (sp / proc) * 100
        gf = row['gflops']
        print(f"{proc:^12} | {time:^10.2f} | {sp:^7.2f} | {eff:^14.1f} | {gf:^7.2f}")

def plot_weak_scaling(df_weak):
    """Graficar los resultados de Weak Scaling"""
    if df_weak.empty:
        print("No hay datos de weak scaling para graficar")
        return
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Análisis de Weak Scaling - N-Body Simulation\n(Nota: N-Body tiene complejidad O(N²), por lo que el weak scaling no es ideal)', fontsize=14, fontweight='bold')
    
    # Crear una copia para evitar SettingWithCopyWarning
    df_weak = df_weak.copy()
    
    # Calcular tiempo por partícula
    df_weak['time_per_particle'] = df_weak['time_seconds'] / df_weak['N_particles']
    base_time_per_particle = df_weak[df_weak['processors'] == 1]['time_per_particle'].values[0]
    
    # 1. Tiempo total vs Procesadores
    ax1.plot(df_weak['processors'], df_weak['time_seconds'], 'bo-', label='Tiempo real', markersize=10)
    ax1.axhline(y=df_weak['time_seconds'].iloc[0], color='r', linestyle='--', label='Tiempo ideal constante')
    
    # Agregar curva teórica O(N²)
    base_time = df_weak['time_seconds'].iloc[0]
    theoretical_times = base_time * df_weak['processors'].values  # Como N crece linealmente pero el trabajo crece cuadráticamente
    ax1.plot(df_weak['processors'], theoretical_times, 'g:', label='Teórico O(N²)', linewidth=2)
    
    # Agregar valores de N en cada punto
    for i, row in df_weak.iterrows():
        ax1.annotate(f'N={row["N_particles"]}', 
                    (row['processors'], row['time_seconds']),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    ax1.set_xlabel('Número de Procesadores')
    ax1.set_ylabel('Tiempo de Ejecución (s)')
    ax1.set_title('Tiempo de Ejecución vs Procesadores (N proporcional)')
    ax1.legend()
    ax1.grid(True)
    ax1.set_xticks(df_weak['processors'])
    
    # 2. Tiempo por partícula
    ax2.plot(df_weak['processors'], df_weak['time_per_particle'] * 1000, 'go-', label='Tiempo/partícula', markersize=10)
    
    # Agregar valores de N en cada punto
    for i, row in df_weak.iterrows():
        ax2.annotate(f'N={row["N_particles"]}', 
                    (row['processors'], row['time_per_particle'] * 1000),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    ax2.set_xlabel('Número de Procesadores')
    ax2.set_ylabel('Tiempo por Partícula (ms)')
    ax2.set_title('Tiempo por Partícula vs Procesadores')
    ax2.legend()
    ax2.grid(True)
    ax2.set_xticks(df_weak['processors'])
    
    # 3. Eficiencia de Weak Scaling
    weak_efficiency = (df_weak['time_seconds'].iloc[0] / df_weak['time_seconds']) * 100
    
    ax3.plot(df_weak['processors'], weak_efficiency, 'mo-', label='Eficiencia', markersize=10)
    ax3.axhline(y=100, color='r', linestyle='--', label='Eficiencia ideal (100%)')
    
    # Agregar valores de N y eficiencia en cada punto
    for idx, (i, row) in enumerate(df_weak.iterrows()):
        eff = weak_efficiency.iloc[idx]
        ax3.annotate(f'N={row["N_particles"]}\n{eff:.1f}%', 
                    (row['processors'], eff),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
    
    ax3.set_xlabel('Número de Procesadores')
    ax3.set_ylabel('Eficiencia de Weak Scaling (%)')
    ax3.set_title('Eficiencia de Weak Scaling')
    ax3.legend()
    ax3.grid(True)
    ax3.set_ylim(0, 120)
    ax3.set_xticks(df_weak['processors'])
    
    # 4. Partículas vs Procesadores
    ax4.plot(df_weak['processors'], df_weak['N_particles'], 'co-', label='Partículas', markersize=10)
    
    # Agregar valores exactos en cada punto
    for i, row in df_weak.iterrows():
        ax4.annotate(f'{row["N_particles"]}', 
                    (row['processors'], row['N_particles']),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    # Agregar línea de tendencia ideal (partículas = 1024 * procesadores)
    ideal_particles = df_weak['processors'] * 1024
    ax4.plot(df_weak['processors'], ideal_particles, 'r--', label='Ideal (1024*p)', alpha=0.7)
    
    ax4.set_xlabel('Número de Procesadores')
    ax4.set_ylabel('Número de Partículas')
    ax4.set_title('Tamaño del Problema vs Procesadores')
    ax4.legend()
    ax4.grid(True)
    ax4.set_xticks(df_weak['processors'])
    
    plt.tight_layout()
    plt.savefig('performance_data/weak_scaling_analysis.png', dpi=300)
    
    # Imprimir tabla de resultados
    print("\n=== RESULTADOS DE WEAK SCALING ===")
    print("Partículas por procesador = 1024")
    print("\nProcesadores | Partículas | Tiempo (s) | Tiempo/Part (ms) | Eficiencia (%)")
    print("-" * 75)
    for i, row in df_weak.iterrows():
        proc = row['processors']
        parts = row['N_particles']
        time = row['time_seconds']
        tpp = (time / parts) * 1000
        eff = (df_weak['time_seconds'].iloc[0] / time) * 100
        print(f"{proc:^12} | {parts:^10} | {time:^10.2f} | {tpp:^16.3f} | {eff:^14.1f}")

def plot_combined_analysis(df_all):
    """Crear una gráfica combinada con todos los resultados"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Separar datos
    df_strong = df_all[df_all['scaling_type'] == 'strong']
    df_weak = df_all[df_all['scaling_type'] == 'weak']
    
    if not df_strong.empty:
        # Calcular speedup para strong scaling
        base_time_strong = df_strong[df_strong['processors'] == 1]['time_seconds'].values[0]
        speedup_strong = base_time_strong / df_strong['time_seconds']
        ax.plot(df_strong['processors'], speedup_strong, 'bo-', 
                label='Strong Scaling', markersize=10, linewidth=2)
    
    if not df_weak.empty:
        # Calcular eficiencia para weak scaling
        base_time_weak = df_weak[df_weak['processors'] == 1]['time_seconds'].values[0]
        efficiency_weak = (base_time_weak / df_weak['time_seconds']) * df_weak['processors'].max()
        ax.plot(df_weak['processors'], efficiency_weak, 'ro-', 
                label='Weak Scaling (normalizado)', markersize=10, linewidth=2)
    
    # Línea ideal
    processors = sorted(df_all['processors'].unique())
    ax.plot(processors, processors, 'g--', label='Escalamiento Ideal', linewidth=2)
    
    ax.set_xlabel('Número de Procesadores', fontsize=14)
    ax.set_ylabel('Speedup / Eficiencia Normalizada', fontsize=14)
    ax.set_title('Comparación de Strong y Weak Scaling', fontsize=16, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(processors)
    
    plt.tight_layout()
    plt.savefig('performance_data/combined_scaling_analysis.png', dpi=300)

def plot_baseline_performance(df_baseline):
    """Graficar el rendimiento base para diferentes tamaños de N"""
    if df_baseline.empty:
        print("No hay datos baseline para graficar")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Rendimiento Base - Diferentes Tamaños de Problema', fontsize=16, fontweight='bold')
    
    # 1. Tiempo vs N
    ax1.plot(df_baseline['N_particles'], df_baseline['time_seconds'], 'bo-', markersize=8)
    ax1.set_xlabel('Número de Partículas')
    ax1.set_ylabel('Tiempo de Ejecución (s)')
    ax1.set_title('Tiempo vs Tamaño del Problema')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    
    # 2. Complejidad O(N²)
    N = df_baseline['N_particles'].values
    theoretical_time = df_baseline['time_seconds'].iloc[0] * (N / N[0])**2
    
    ax2.plot(N, df_baseline['time_seconds'], 'bo-', label='Tiempo real', markersize=8)
    ax2.plot(N, theoretical_time, 'r--', label='O(N²) teórico', linewidth=2)
    ax2.set_xlabel('Número de Partículas')
    ax2.set_ylabel('Tiempo de Ejecución (s)')
    ax2.set_title('Verificación de Complejidad O(N²)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig('performance_data/baseline_performance.png', dpi=300)


def main():
    """Función principal"""
    print("=== ANÁLISIS DE ESCALABILIDAD N-BODY ===\n")
    
    # Verificar que existe el directorio
    if not os.path.exists('performance_data'):
        print("Error: No existe el directorio performance_data/")
        print("Ejecuta primero: ./generate_datasets.sh")
        return
    
    # Cargar datos
    df_all, df_strong, df_weak, df_baseline = load_data()
    
    if df_all is None:
        return
    
    print(f"Datos cargados: {len(df_all)} registros totales")
    print(f"- Strong scaling: {len(df_strong)} registros")
    print(f"- Weak scaling: {len(df_weak)} registros")
    print(f"- Baseline: {len(df_baseline)} registros")
    
    # Generar gráficas
    if not df_strong.empty:
        print("\nGenerando gráficas de Strong Scaling...")
        plot_strong_scaling(df_strong)
    
    if not df_weak.empty:
        print("\nGenerando gráficas de Weak Scaling...")
        plot_weak_scaling(df_weak)
    
    if not df_all.empty:
        print("\nGenerando análisis combinado...")
        plot_combined_analysis(df_all)
    
    if not df_baseline.empty:
        print("\nGenerando análisis de rendimiento base...")
        plot_baseline_performance(df_baseline)
  
    print("\n¡Análisis completado! Revisa los archivos en performance_data/")

if __name__ == "__main__":
    main() 