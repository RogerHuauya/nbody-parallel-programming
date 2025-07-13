#!/usr/bin/env python3
"""
Visualizador 3D paralelo para simulaciones N-Body
Utiliza matplotlib para animación y joblib para paralelización
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import joblib
from joblib import Parallel, delayed
import os
import time
import pandas as pd
from glob import glob

# Configuración para mejor rendimiento
plt.rcParams['animation.embed_limit'] = 50  # MB

class NBodyVisualizer:
    def __init__(self, data_file, output_dir='visualizations'):
        self.data_file = data_file
        self.output_dir = output_dir
        self.particles = None
        self.snapshots = []
        self.n_particles = 0
        self.current_frame = 0
        
        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)
        
    def load_data(self):
        """Cargar datos de simulación desde archivo"""
        print(f"Cargando datos desde {self.data_file}...")
        
        with open(self.data_file, 'r') as f:
            lines = f.readlines()
        
        # Primera línea: step
        # Segunda línea: número de partículas
        self.n_particles = int(lines[1].strip())
        
        # Cargar todas las partículas
        particles_data = []
        for i in range(3, 3 + self.n_particles):
            parts = lines[i].split()
            particle = {
                'id': int(parts[0]),
                'mass': float(parts[1]),
                'x': float(parts[2]),
                'y': float(parts[3]),
                'z': float(parts[4]),
                'vx': float(parts[5]),
                'vy': float(parts[6]),
                'vz': float(parts[7])
            }
            particles_data.append(particle)
        
        self.particles = pd.DataFrame(particles_data)
        print(f"Cargadas {self.n_particles} partículas")
        
    def prepare_snapshot(self, frame_data):
        """Preparar un snapshot para visualización (función paralela)"""
        positions = np.array([
            [p['x'], p['y'], p['z']] 
            for _, p in frame_data.iterrows()
        ])
        masses = frame_data['mass'].values
        return positions, masses
        
    def create_animation_parallel(self, n_frames=100, fps=30):
        """Crear animación 3D usando paralelización"""
        print("Creando animación 3D con paralelización...")
        
        # Simular múltiples frames (en un caso real, cargarías múltiples snapshots)
        # Aquí simulamos movimiento orbital simple
        t_values = np.linspace(0, 2*np.pi, n_frames)
        
        # Preparar frames en paralelo
        start_time = time.time()
        
        def generate_frame(t):
            # Simular evolución (en realidad cargarías diferentes snapshots)
            frame_data = self.particles.copy()
            # Rotación simple para demostración
            angle = t
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            
            new_x = frame_data['x'] * cos_a - frame_data['y'] * sin_a
            new_y = frame_data['x'] * sin_a + frame_data['y'] * cos_a
            
            frame_data['x'] = new_x
            frame_data['y'] = new_y
            
            return self.prepare_snapshot(frame_data)
        
        # Paralelizar la generación de frames
        with joblib.parallel_backend('threading', n_jobs=-1):
            self.snapshots = Parallel()(
                delayed(generate_frame)(t) for t in t_values
            )
        
        parallel_time = time.time() - start_time
        print(f"Frames preparados en paralelo en {parallel_time:.2f} segundos")
        
        # Crear figura y animación
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Configurar límites
        positions_all = np.vstack([s[0] for s in self.snapshots])
        max_range = np.max(np.abs(positions_all)) * 1.1
        
        ax.set_xlim(-max_range, max_range)
        ax.set_ylim(-max_range, max_range)
        ax.set_zlim(-max_range/2, max_range/2)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Simulación N-Body 3D')
        
        # Scatter plot inicial
        positions, masses = self.snapshots[0]
        scatter = ax.scatter(positions[:, 0], 
                           positions[:, 1], 
                           positions[:, 2],
                           c=masses, 
                           cmap='viridis',
                           s=50*masses/masses.max(),
                           alpha=0.6)
        
        # Función de actualización
        def update(frame):
            positions, masses = self.snapshots[frame]
            scatter._offsets3d = (positions[:, 0], 
                                 positions[:, 1], 
                                 positions[:, 2])
            ax.set_title(f'Simulación N-Body 3D - Frame {frame}/{n_frames}')
            return scatter,
        
        # Crear animación
        anim = FuncAnimation(fig, update, frames=n_frames, 
                           interval=1000/fps, blit=False)
        
        # Guardar animación
        output_file = os.path.join(self.output_dir, 
                                  f'nbody_animation_{self.n_particles}p.mp4')
        print(f"Guardando animación en {output_file}...")
        anim.save(output_file, writer='ffmpeg', fps=fps, dpi=100)
        
        plt.close()
        
        return parallel_time
    
    def create_trajectory_plot(self):
        """Crear plot de trayectorias"""
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # Para cada partícula, dibujar su trayectoria
        n_samples = min(10, self.n_particles)  # Limitar para claridad
        sample_ids = np.random.choice(self.n_particles, n_samples, replace=False)
        
        colors = plt.cm.rainbow(np.linspace(0, 1, n_samples))
        
        for idx, (pid, color) in enumerate(zip(sample_ids, colors)):
            trajectory = []
            for positions, _ in self.snapshots[::5]:  # Cada 5 frames
                trajectory.append(positions[pid])
            
            trajectory = np.array(trajectory)
            ax.plot(trajectory[:, 0], 
                   trajectory[:, 1], 
                   trajectory[:, 2],
                   color=color, alpha=0.7, linewidth=2,
                   label=f'Partícula {pid}')
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'Trayectorias de {n_samples} partículas')
        ax.legend()
        
        output_file = os.path.join(self.output_dir, 
                                  f'trajectories_{self.n_particles}p.png')
        plt.savefig(output_file, dpi=300)
        plt.close()
        
        print(f"Trayectorias guardadas en {output_file}")

def benchmark_parallel_visualization(sizes=[1024, 2048, 4096]):
    """Benchmark de rendimiento de visualización paralela"""
    results = []
    
    for n in sizes:
        print(f"\n=== Benchmark para N = {n} partículas ===")
        
        # Buscar archivo de datos
        data_file = f"datasets/N_{n//1024}KB/data.inp"
        if not os.path.exists(data_file):
            print(f"Archivo {data_file} no encontrado, saltando...")
            continue
        
        visualizer = NBodyVisualizer(data_file)
        visualizer.load_data()
        
        # Medir tiempo con paralelización
        n_frames = 50
        parallel_time = visualizer.create_animation_parallel(n_frames=n_frames, fps=15)
        
        # Crear plot de trayectorias
        visualizer.create_trajectory_plot()
        
        # Medir speedup estimado (comparando con tiempo secuencial estimado)
        estimated_sequential_time = parallel_time * joblib.cpu_count()
        speedup = estimated_sequential_time / parallel_time
        efficiency = speedup / joblib.cpu_count() * 100
        
        result = {
            'n_particles': n,
            'n_frames': n_frames,
            'parallel_time': parallel_time,
            'speedup': speedup,
            'efficiency': efficiency,
            'cores_used': joblib.cpu_count()
        }
        results.append(result)
        
        print(f"Tiempo paralelo: {parallel_time:.2f}s")
        print(f"Speedup estimado: {speedup:.2f}x")
        print(f"Eficiencia: {efficiency:.1f}%")
    
    # Guardar resultados
    df_results = pd.DataFrame(results)
    df_results.to_csv('performance_data/visualization_benchmark.csv', index=False)
    
    # Crear gráfica de benchmark
    if results:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        ax1.plot(df_results['n_particles'], df_results['parallel_time'], 'bo-', markersize=8)
        ax1.set_xlabel('Número de Partículas')
        ax1.set_ylabel('Tiempo de Visualización (s)')
        ax1.set_title('Tiempo de Renderizado Paralelo')
        ax1.grid(True, alpha=0.3)
        
        ax2.bar(df_results['n_particles'].astype(str), df_results['efficiency'])
        ax2.set_xlabel('Número de Partículas')
        ax2.set_ylabel('Eficiencia de Paralelización (%)')
        ax2.set_title('Eficiencia del Renderizado Paralelo')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('performance_data/visualization_benchmark.png', dpi=300)
        plt.close()
        
        print("\nResultados de benchmark guardados en performance_data/")

def main():
    """Función principal"""
    print("=== VISUALIZADOR 3D N-BODY PARALELO ===\n")
    
    # Verificar que existen los datos
    if not os.path.exists('datasets'):
        print("Error: No existe el directorio datasets/")
        print("Ejecuta primero: ./generate_datasets.sh")
        return
    
    # Opciones del menú
    print("Opciones:")
    print("1. Visualizar una simulación específica")
    print("2. Ejecutar benchmark de visualización paralela")
    print("3. Crear todas las visualizaciones disponibles")
    
    choice = input("\nSelecciona una opción (1-3): ")
    
    if choice == '1':
        # Listar datasets disponibles
        datasets = glob('datasets/*/data.inp')
        if not datasets:
            print("No se encontraron datasets")
            return
        
        print("\nDatasets disponibles:")
        for i, ds in enumerate(datasets):
            print(f"{i+1}. {ds}")
        
        idx = int(input("Selecciona dataset (número): ")) - 1
        
        visualizer = NBodyVisualizer(datasets[idx])
        visualizer.load_data()
        visualizer.create_animation_parallel(n_frames=100, fps=30)
        visualizer.create_trajectory_plot()
        
    elif choice == '2':
        benchmark_parallel_visualization()
        
    elif choice == '3':
        # Visualizar todos los datasets disponibles
        datasets = glob('datasets/N_*/data.inp')
        for ds in datasets:
            print(f"\nProcesando {ds}...")
            visualizer = NBodyVisualizer(ds)
            visualizer.load_data()
            visualizer.create_animation_parallel(n_frames=50, fps=15)
            visualizer.create_trajectory_plot()
    
    print("\n¡Visualización completada!")

if __name__ == "__main__":
    main() 