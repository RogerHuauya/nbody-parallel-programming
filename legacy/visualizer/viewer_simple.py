#!/usr/bin/env python3
"""
Visualizador 3D simplificado para simulador N-cuerpos
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import os
import glob
import sys

class SimpleNBodyVisualizer:
    def __init__(self, data_dir="results/snapshots"):
        self.data_dir = data_dir
        self.snapshots = []
        self.current_frame = 0
        
        # Cargar datos
        self.load_snapshots()
        
        if not self.snapshots:
            print("No se encontraron snapshots para visualizar")
            return
            
        # Configurar plot
        self.setup_plot()
        
    def load_snapshots(self):
        """Carga los snapshots de la simulación"""
        snapshot_files = sorted(glob.glob(os.path.join(self.data_dir, "*.dat")))
        
        if not snapshot_files:
            print(f"No se encontraron snapshots en {self.data_dir}")
            return
            
        print(f"Cargando {len(snapshot_files)} snapshots...")
        
        for filename in snapshot_files:
            snapshot = self.read_snapshot(filename)
            if snapshot:
                self.snapshots.append(snapshot)
                
        print(f"Cargados {len(self.snapshots)} snapshots")
    
    def read_snapshot(self, filename):
        """Lee un snapshot del simulador"""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            # Parsear header
            step = int(lines[0].strip())
            n_particles = int(lines[1].strip())
            time = float(lines[2].strip())
            
            # Parsear partículas
            particles = []
            for i in range(3, min(3 + n_particles, len(lines))):
                parts = lines[i].strip().split()
                if len(parts) >= 8:
                    particle_id = int(parts[0])
                    mass = float(parts[1])
                    pos = np.array([float(parts[2]), float(parts[3]), float(parts[4])])
                    vel = np.array([float(parts[5]), float(parts[6]), float(parts[7])])
                    
                    particles.append({
                        'id': particle_id,
                        'mass': mass,
                        'pos': pos,
                        'vel': vel
                    })
            
            return {
                'step': step,
                'n_particles': n_particles,
                'time': time,
                'particles': particles
            }
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
            return None
    
    def setup_plot(self):
        """Configura la figura y los ejes 3D"""
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Configurar apariencia
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Simulación N-Cuerpos')
        
        # Crear animación
        self.ani = animation.FuncAnimation(
            self.fig, 
            self.update_plot, 
            frames=len(self.snapshots),
            interval=100,  # milisegundos entre frames
            repeat=True
        )
        
    def update_plot(self, frame):
        """Actualiza el plot para cada frame"""
        self.ax.clear()
        
        # Configurar títulos de nuevo
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        
        snapshot = self.snapshots[frame]
        
        # Extraer posiciones
        positions = np.array([p['pos'] for p in snapshot['particles']])
        
        # Título con información del frame
        self.ax.set_title(f'N-Cuerpos - Tiempo: {snapshot["time"]:.3f} - Frame: {frame+1}/{len(self.snapshots)}')
        
        # Dibujar partículas
        self.ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2], 
                       c='blue', marker='o', s=20, alpha=0.6)
        
        # Ajustar límites
        if frame == 0:
            # Calcular límites globales en el primer frame
            all_positions = []
            for snap in self.snapshots:
                for p in snap['particles']:
                    all_positions.append(p['pos'])
            all_positions = np.array(all_positions)
            
            # Encontrar rangos
            margin = 0.1
            for i, axis in enumerate(['x', 'y', 'z']):
                min_val = np.min(all_positions[:, i])
                max_val = np.max(all_positions[:, i])
                range_val = max_val - min_val
                margin_val = range_val * margin
                
                if i == 0:
                    self.xlim = (min_val - margin_val, max_val + margin_val)
                    self.ax.set_xlim(self.xlim)
                elif i == 1:
                    self.ylim = (min_val - margin_val, max_val + margin_val)
                    self.ax.set_ylim(self.ylim)
                else:
                    self.zlim = (min_val - margin_val, max_val + margin_val)
                    self.ax.set_zlim(self.zlim)
        else:
            # Usar límites calculados
            self.ax.set_xlim(self.xlim)
            self.ax.set_ylim(self.ylim)
            self.ax.set_zlim(self.zlim)
        
        return self.ax.collections
    
    def show(self):
        """Muestra el visualizador"""
        if not self.snapshots:
            print("No hay datos para visualizar")
            return
            
        print("\nControles:")
        print("- Cierra la ventana para terminar")
        print("- La animación se repite automáticamente")
        print(f"- Mostrando {len(self.snapshots)} frames")
        
        plt.show()

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "results/snapshots"
    
    print(f"Iniciando visualizador N-cuerpos simplificado...")
    print(f"Directorio de datos: {data_dir}")
    
    visualizer = SimpleNBodyVisualizer(data_dir)
    visualizer.show()

if __name__ == "__main__":
    main() 