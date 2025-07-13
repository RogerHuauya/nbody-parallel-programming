#!/usr/bin/env python3
"""
Análisis de rendimiento para simulador N-cuerpos
Tarea b: Mediciones de rendimiento
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def parse_time_string(time_str):
    """Convierte string de tiempo (formato mm:ss.sss) a segundos"""
    if pd.isna(time_str) or time_str == "":
        return 0.0
    
    try:
        # Formato mm:ss.sss
        if ':' in str(time_str):
            parts = str(time_str).split(':')
            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
        
        # Formato ss.sss
        return float(time_str)
    except:
        return 0.0

def analyze_timing_data(csv_file):
    """Analiza los datos de timing y genera gráficos"""
    
    # Leer datos
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {csv_file}")
        return
    
    # Convertir tiempos a segundos
    df['Real_Time_Sec'] = df['Real_Time'].apply(parse_time_string)
    df['User_Time_Sec'] = df['User_Time'].apply(parse_time_string)
    df['Sys_Time_Sec'] = df['Sys_Time'].apply(parse_time_string)
    
    # Calcular eficiencia paralela
    df['Efficiency'] = 0.0
    
    for n_particles in df['N_Particles'].unique():
        for order in df['Order'].unique():
            # Encontrar tiempo secuencial (P=1)
            sequential_time = df[(df['N_Particles'] == n_particles) & 
                               (df['Order'] == order) & 
                               (df['N_Processes'] == 1)]['Real_Time_Sec']
            
            if len(sequential_time) > 0:
                t_seq = sequential_time.iloc[0]
                if t_seq > 0:
                    # Calcular eficiencia para todos los procesos
                    mask = (df['N_Particles'] == n_particles) & (df['Order'] == order)
                    df.loc[mask, 'Efficiency'] = t_seq / (df.loc[mask, 'Real_Time_Sec'] * df.loc[mask, 'N_Processes'])
    
    # Calcular speedup
    df['Speedup'] = 0.0
    
    for n_particles in df['N_Particles'].unique():
        for order in df['Order'].unique():
            # Encontrar tiempo secuencial (P=1)
            sequential_time = df[(df['N_Particles'] == n_particles) & 
                               (df['Order'] == order) & 
                               (df['N_Processes'] == 1)]['Real_Time_Sec']
            
            if len(sequential_time) > 0:
                t_seq = sequential_time.iloc[0]
                if t_seq > 0:
                    # Calcular speedup
                    mask = (df['N_Particles'] == n_particles) & (df['Order'] == order)
                    df.loc[mask, 'Speedup'] = t_seq / df.loc[mask, 'Real_Time_Sec']
    
    # Generar reportes
    print("\n=== ANÁLISIS DE RENDIMIENTO ===")
    print(f"Total de experimentos: {len(df)}")
    print(f"Rango de partículas: {df['N_Particles'].min()} - {df['N_Particles'].max()}")
    print(f"Rango de procesos: {df['N_Processes'].min()} - {df['N_Processes'].max()}")
    
    # Reporte por orden de integración
    print("\n--- Tiempos promedio por orden de integración ---")
    for order in sorted(df['Order'].unique()):
        order_data = df[df['Order'] == order]
        avg_time = order_data['Real_Time_Sec'].mean()
        print(f"Orden {order}: {avg_time:.3f} segundos promedio")
    
    # Reporte de escalabilidad
    print("\n--- Análisis de escalabilidad ---")
    for n_particles in sorted(df['N_Particles'].unique()):
        print(f"\nN = {n_particles} partículas:")
        particle_data = df[df['N_Particles'] == n_particles]
        
        for order in sorted(particle_data['Order'].unique()):
            order_data = particle_data[particle_data['Order'] == order]
            if len(order_data) > 1:
                max_speedup = order_data['Speedup'].max()
                max_efficiency = order_data['Efficiency'].max()
                print(f"  Orden {order}: Speedup máximo = {max_speedup:.2f}, Eficiencia máxima = {max_efficiency:.2f}")
    
    # Generar gráficos
    results_dir = os.path.dirname(csv_file)
    generate_plots(df, results_dir)
    
    return df

def generate_plots(df, results_dir):
    """Genera gráficos de análisis"""
    
    plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
    
    # Gráfico 1: Tiempo vs Número de procesos
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    for i, n_particles in enumerate(sorted(df['N_Particles'].unique())):
        ax = axes[i//2, i%2]
        particle_data = df[df['N_Particles'] == n_particles]
        
        for order in sorted(particle_data['Order'].unique()):
            order_data = particle_data[particle_data['Order'] == order]
            ax.plot(order_data['N_Processes'], order_data['Real_Time_Sec'], 
                   'o-', label=f'Orden {order}', linewidth=2, markersize=6)
        
        ax.set_title(f'Tiempo de ejecución (N={n_particles})')
        ax.set_xlabel('Número de procesos')
        ax.set_ylabel('Tiempo (segundos)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/timing_vs_processes.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 2: Speedup
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    for i, n_particles in enumerate(sorted(df['N_Particles'].unique())):
        ax = axes[i//2, i%2]
        particle_data = df[df['N_Particles'] == n_particles]
        
        for order in sorted(particle_data['Order'].unique()):
            order_data = particle_data[particle_data['Order'] == order]
            ax.plot(order_data['N_Processes'], order_data['Speedup'], 
                   'o-', label=f'Orden {order}', linewidth=2, markersize=6)
        
        # Línea de speedup ideal
        max_proc = particle_data['N_Processes'].max()
        ax.plot([1, max_proc], [1, max_proc], 'k--', alpha=0.5, label='Speedup ideal')
        
        ax.set_title(f'Speedup (N={n_particles})')
        ax.set_xlabel('Número de procesos')
        ax.set_ylabel('Speedup')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/speedup_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 3: Eficiencia
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    for i, n_particles in enumerate(sorted(df['N_Particles'].unique())):
        ax = axes[i//2, i%2]
        particle_data = df[df['N_Particles'] == n_particles]
        
        for order in sorted(particle_data['Order'].unique()):
            order_data = particle_data[particle_data['Order'] == order]
            ax.plot(order_data['N_Processes'], order_data['Efficiency'], 
                   'o-', label=f'Orden {order}', linewidth=2, markersize=6)
        
        # Línea de eficiencia ideal
        ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='Eficiencia ideal')
        
        ax.set_title(f'Eficiencia (N={n_particles})')
        ax.set_xlabel('Número de procesos')
        ax.set_ylabel('Eficiencia')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/efficiency_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico 4: Escalabilidad fuerte
    plt.figure(figsize=(12, 8))
    
    for order in sorted(df['Order'].unique()):
        order_data = df[df['Order'] == order]
        
        # Agrupar por número de procesos y calcular promedio
        avg_data = order_data.groupby('N_Processes').agg({
            'Real_Time_Sec': 'mean',
            'Speedup': 'mean',
            'Efficiency': 'mean'
        }).reset_index()
        
        plt.plot(avg_data['N_Processes'], avg_data['Speedup'], 
                'o-', label=f'Orden {order}', linewidth=2, markersize=6)
    
    # Línea de speedup ideal
    max_proc = df['N_Processes'].max()
    plt.plot([1, max_proc], [1, max_proc], 'k--', alpha=0.5, label='Speedup ideal')
    
    plt.title('Escalabilidad Fuerte - Speedup Promedio')
    plt.xlabel('Número de procesos')
    plt.ylabel('Speedup')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{results_dir}/strong_scaling.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nGráficos generados en: {results_dir}")
    print("- timing_vs_processes.png")
    print("- speedup_analysis.png")
    print("- efficiency_analysis.png")
    print("- strong_scaling.png")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 analyze_timing.py <archivo_csv>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    analyze_timing_data(csv_file) 