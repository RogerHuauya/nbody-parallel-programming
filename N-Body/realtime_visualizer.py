#!/usr/bin/env python3
"""
Visualizador 3D en tiempo real para simulaciones N-Body
Monitorea archivos de snapshots y actualiza la visualización continuamente
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import os
import glob
import time
import json
from datetime import datetime
import threading
import queue
from collections import deque

# Configuración
plt.style.use('dark_background')
plt.rcParams['figure.figsize'] = (15, 10)

class RealtimeNBodyVisualizer:
    def __init__(self, base_dir='realtime_simulations', update_interval=100):
        self.base_dir = base_dir
        self.update_interval = update_interval  # ms
        self.simulations = {}
        self.data_queue = queue.Queue()
        self.running = True
        self.current_view = 0  # Qué simulación mostrar (0-3 para N=1,2,4,8)
        
        # Configuración de visualización
        self.fig = plt.figure(figsize=(15, 10))
        self.fig.suptitle('N-Body Realtime Visualization', fontsize=16, color='white')
        
        # Crear subplots 2x2 para las 4 simulaciones
        self.axes = []
        for i in range(4):
            ax = self.fig.add_subplot(2, 2, i+1, projection='3d')
            ax.set_facecolor('black')
            ax.grid(True, alpha=0.2)
            self.axes.append(ax)
        
        # Inicializar datos de simulación
        self.sizes = [1, 2, 4, 8]
        for i, N in enumerate(self.sizes):
            self.simulations[N] = {
                'dir': f"{base_dir}/N_{N}KB",
                'particles': None,
                'scatter': None,
                'current_snapshot': -1,
                'snapshots': deque(maxlen=10),  # Mantener últimos 10 snapshots
                'status': 'waiting',
                'ax': self.axes[i]
            }
        
        # Configurar controles
        self.setup_controls()
        
    def setup_controls(self):
        """Configurar controles interactivos"""
        # Botones para cambiar vista
        from matplotlib.widgets import Button, Slider
        
        # Slider para velocidad de reproducción
        ax_speed = plt.axes([0.15, 0.02, 0.3, 0.03])
        self.speed_slider = Slider(ax_speed, 'Speed', 0.1, 5.0, valinit=1.0)
        
        # Información de estado
        self.status_text = self.fig.text(0.02, 0.98, '', fontsize=10, 
                                        verticalalignment='top', color='green')
        
    def monitor_files(self):
        """Thread para monitorear archivos nuevos"""
        while self.running:
            for N, sim in self.simulations.items():
                snapshot_dir = f"{sim['dir']}/snapshots"
                
                if os.path.exists(snapshot_dir):
                    # Buscar nuevos snapshots
                    snapshots = sorted(glob.glob(f"{snapshot_dir}/snapshot_*.dat"))
                    
                    if snapshots and len(snapshots) > sim['current_snapshot'] + 1:
                        # Cargar el siguiente snapshot
                        next_idx = sim['current_snapshot'] + 1
                        if next_idx < len(snapshots):
                            try:
                                data = self.load_snapshot(snapshots[next_idx])
                                if data is not None:
                                    self.data_queue.put((N, data, next_idx))
                                    sim['status'] = 'running'
                            except Exception as e:
                                print(f"Error loading snapshot for N={N}: {e}")
                
                # Verificar estado
                status_file = f"{sim['dir']}/status.txt"
                if os.path.exists(status_file):
                    with open(status_file, 'r') as f:
                        sim['status'] = f.read().strip()
            
            time.sleep(0.05)  # Chequear cada 50ms
    
    def load_snapshot(self, filename):
        """Cargar datos de un snapshot"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 4:
                return None
            
            # Parsear encabezado
            n_particles = int(lines[1].strip())
            
            # Cargar posiciones
            positions = []
            masses = []
            
            for i in range(3, min(3 + n_particles, len(lines))):
                parts = lines[i].split()
                if len(parts) >= 8:
                    masses.append(float(parts[1]))
                    positions.append([float(parts[2]), float(parts[3]), float(parts[4])])
            
            if positions:
                return {
                    'positions': np.array(positions),
                    'masses': np.array(masses),
                    'n_particles': len(positions)
                }
        except Exception as e:
            print(f"Error parsing snapshot {filename}: {e}")
            return None
    
    def update_visualization(self, frame):
        """Actualizar la visualización"""
        # Procesar datos de la cola
        updated = False
        while not self.data_queue.empty():
            try:
                N, data, snapshot_idx = self.data_queue.get_nowait()
                sim = self.simulations[N]
                sim['particles'] = data
                sim['current_snapshot'] = snapshot_idx
                sim['snapshots'].append(data)
                updated = True
            except queue.Empty:
                break
        
        # Actualizar cada subplot
        for i, N in enumerate(self.sizes):
            sim = self.simulations[N]
            ax = sim['ax']
            
            if sim['particles'] is not None:
                data = sim['particles']
                positions = data['positions']
                masses = data['masses']
                
                # Limpiar y redibujar
                ax.clear()
                
                # Configurar límites
                max_range = np.max(np.abs(positions)) * 1.1
                ax.set_xlim(-max_range, max_range)
                ax.set_ylim(-max_range, max_range)
                ax.set_zlim(-max_range/2, max_range/2)
                
                # Dibujar partículas
                scatter = ax.scatter(positions[:, 0], 
                                   positions[:, 1], 
                                   positions[:, 2],
                                   c=masses, 
                                   cmap='plasma',
                                   s=20*masses/masses.max() + 5,
                                   alpha=0.8,
                                   edgecolors='white',
                                   linewidth=0.5)
                
                # Dibujar trayectorias (últimos puntos)
                if len(sim['snapshots']) > 1:
                    # Seleccionar algunas partículas para trayectorias
                    n_tracks = min(5, data['n_particles'])
                    track_ids = np.linspace(0, data['n_particles']-1, n_tracks, dtype=int)
                    
                    for tid in track_ids:
                        trajectory = []
                        for snap in list(sim['snapshots'])[-5:]:  # Últimos 5 snapshots
                            if tid < len(snap['positions']):
                                trajectory.append(snap['positions'][tid])
                        
                        if len(trajectory) > 1:
                            trajectory = np.array(trajectory)
                            ax.plot(trajectory[:, 0], 
                                   trajectory[:, 1], 
                                   trajectory[:, 2],
                                   'w-', alpha=0.3, linewidth=1)
                
                # Configurar etiquetas
                ax.set_xlabel('X', fontsize=8)
                ax.set_ylabel('Y', fontsize=8)
                ax.set_zlabel('Z', fontsize=8)
                ax.set_title(f'N = {N*1024} particles\nSnapshot: {sim["current_snapshot"]}\nStatus: {sim["status"]}', 
                           fontsize=10)
                
                # Ajustar vista
                ax.view_init(elev=20, azim=frame * self.speed_slider.val)
            else:
                ax.set_title(f'N = {N*1024} particles\nWaiting for data...', fontsize=10)
                ax.set_xlim(-1, 1)
                ax.set_ylim(-1, 1)
                ax.set_zlim(-1, 1)
        
        # Actualizar información de estado
        status_info = f"Realtime N-Body Visualization | Time: {datetime.now().strftime('%H:%M:%S')}\n"
        for N in self.sizes:
            sim = self.simulations[N]
            status_info += f"N={N*1024}: Snapshot {sim['current_snapshot']} | "
        self.status_text.set_text(status_info)
        
        return self.axes
    
    def start(self):
        """Iniciar visualización en tiempo real"""
        print("=== VISUALIZADOR N-BODY EN TIEMPO REAL ===")
        print(f"Monitoreando: {self.base_dir}")
        print("Controles:")
        print("  - Slider: Ajustar velocidad de rotación")
        print("  - Cerrar ventana: Detener visualización")
        print("")
        
        # Iniciar thread de monitoreo
        monitor_thread = threading.Thread(target=self.monitor_files, daemon=True)
        monitor_thread.start()
        
        # Crear animación
        self.anim = FuncAnimation(self.fig, self.update_visualization, 
                                 interval=self.update_interval, 
                                 blit=False, cache_frame_data=False)
        
        # Configurar cierre limpio
        def on_close(event):
            self.running = False
            print("\nDeteniendo visualización...")
        
        self.fig.canvas.mpl_connect('close_event', on_close)
        
        # Mostrar
        plt.tight_layout()
        plt.show()
        
        # Limpieza
        self.running = False
        monitor_thread.join(timeout=1)
        print("Visualización detenida.")

def plot_final_comparison():
    """Generar comparación final de todas las simulaciones"""
    base_dir = 'realtime_simulations'
    sizes = [1, 2, 4, 8]
    
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('Final State Comparison - N-Body Simulations', fontsize=16)
    
    for i, N in enumerate(sizes):
        ax = fig.add_subplot(2, 2, i+1, projection='3d')
        
        # Buscar snapshot final
        final_snapshot = f"{base_dir}/N_{N}KB/snapshots/snapshot_final.dat"
        if not os.path.exists(final_snapshot):
            snapshots = sorted(glob.glob(f"{base_dir}/N_{N}KB/snapshots/snapshot_*.dat"))
            if snapshots:
                final_snapshot = snapshots[-1]
        
        if os.path.exists(final_snapshot):
            # Cargar datos
            visualizer = RealtimeNBodyVisualizer()
            data = visualizer.load_snapshot(final_snapshot)
            
            if data:
                positions = data['positions']
                masses = data['masses']
                
                # Configurar límites
                max_range = np.max(np.abs(positions)) * 1.1
                ax.set_xlim(-max_range, max_range)
                ax.set_ylim(-max_range, max_range)
                ax.set_zlim(-max_range/2, max_range/2)
                
                # Dibujar
                scatter = ax.scatter(positions[:, 0], 
                                   positions[:, 1], 
                                   positions[:, 2],
                                   c=masses, 
                                   cmap='viridis',
                                   s=30*masses/masses.max() + 10,
                                   alpha=0.8)
                
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_title(f'N = {N*1024} particles - Final State')
                ax.view_init(elev=30, azim=45)
        else:
            ax.set_title(f'N = {N*1024} particles - No data')
    
    plt.tight_layout()
    plt.savefig(f'{base_dir}/final_comparison.png', dpi=300)
    plt.show()

def main():
    """Función principal"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--final':
        # Mostrar comparación final
        plot_final_comparison()
    else:
        # Iniciar visualización en tiempo real
        visualizer = RealtimeNBodyVisualizer()
        visualizer.start()

if __name__ == "__main__":
    main() 