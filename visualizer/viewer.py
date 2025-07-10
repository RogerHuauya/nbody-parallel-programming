#!/usr/bin/env python3
"""
Visualizador 3D para simulador N-cuerpos
Tarea d: Visualizador interactivo
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider, CheckButtons
import os
import glob
import sys

class NBodyVisualizer:
    def __init__(self, data_dir="results/snapshots"):
        self.data_dir = data_dir
        self.snapshots = []
        self.current_frame = 0
        self.is_playing = False
        self.frame_rate = 50  # ms
        
        # Configuración de visualización
        self.show_trails = False
        self.trail_length = 50
        self.particle_trails = {}
        
        # Cargar datos
        self.load_snapshots()
        
        # Configurar interfaz
        self.setup_plot()
        self.setup_controls()
        
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
        
        # Inicializar trails
        if self.snapshots:
            for particle in self.snapshots[0]['particles']:
                self.particle_trails[particle['id']] = []
    
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
            for i in range(3, 3 + n_particles):
                parts = lines[i].strip().split()
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
        self.fig = plt.figure(figsize=(12, 10))
        
        # Eje principal 3D
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Configurar límites iniciales
        if self.snapshots:
            self.update_plot_limits()
        
        # Configurar apariencia
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Simulación N-Cuerpos')
        
        # Elementos de visualización
        self.scatter = None
        self.trail_lines = []
        self.time_text = self.ax.text2D(0.02, 0.98, '', transform=self.ax.transAxes)
        
        # Ajustar layout para controles
        plt.subplots_adjust(bottom=0.2)
        
    def setup_controls(self):
        """Configura los controles interactivos"""
        # Botones
        ax_play = plt.axes([0.1, 0.05, 0.1, 0.04])
        self.btn_play = Button(ax_play, 'Play/Pause')
        self.btn_play.on_clicked(self.toggle_play)
        
        ax_reset = plt.axes([0.25, 0.05, 0.1, 0.04])
        self.btn_reset = Button(ax_reset, 'Reset')
        self.btn_reset.on_clicked(self.reset_view)
        
        ax_save = plt.axes([0.4, 0.05, 0.1, 0.04])
        self.btn_save = Button(ax_save, 'Save Frame')
        self.btn_save.on_clicked(self.save_frame)
        
        # Slider para navegación
        ax_slider = plt.axes([0.1, 0.1, 0.5, 0.03])
        self.slider = Slider(ax_slider, 'Frame', 0, 
                           max(1, len(self.snapshots)-1), valinit=0, valfmt='%d')
        self.slider.on_changed(self.update_frame)
        
        # Checkbox para opciones
        ax_check = plt.axes([0.7, 0.05, 0.15, 0.1])
        self.check = CheckButtons(ax_check, ['Show Trails', 'Color by Mass'])
        self.check.on_clicked(self.toggle_options)
        
        # Slider para velocidad
        ax_speed = plt.axes([0.1, 0.15, 0.2, 0.03])
        self.speed_slider = Slider(ax_speed, 'Speed', 10, 200, valinit=50, valfmt='%d ms')
        self.speed_slider.on_changed(self.update_speed)
        
    def update_plot_limits(self):
        """Actualiza los límites del gráfico basado en los datos"""
        if not self.snapshots:
            return
            
        # Calcular límites globales
        all_positions = []
        for snapshot in self.snapshots:
            for particle in snapshot['particles']:
                all_positions.append(particle['pos'])
        
        all_positions = np.array(all_positions)
        
        # Añadir margen
        margin = 0.1
        ranges = np.ptp(all_positions, axis=0)
        centers = np.mean(all_positions, axis=0)
        
        for i, (center, range_val) in enumerate(zip(centers, ranges)):
            margin_val = range_val * margin
            if i == 0:  # X
                self.ax.set_xlim(center - range_val/2 - margin_val, 
                               center + range_val/2 + margin_val)
            elif i == 1:  # Y
                self.ax.set_ylim(center - range_val/2 - margin_val, 
                               center + range_val/2 + margin_val)
            else:  # Z
                self.ax.set_zlim(center - range_val/2 - margin_val, 
                               center + range_val/2 + margin_val)
    
    def update_frame(self, val):
        """Actualiza el frame actual"""
        self.current_frame = int(self.slider.val)
        self.plot_frame()
    
    def plot_frame(self):
        """Dibuja el frame actual"""
        if not self.snapshots or self.current_frame >= len(self.snapshots):
            return
            
        snapshot = self.snapshots[self.current_frame]
        
        # Extraer posiciones y masas
        positions = []
        masses = []
        
        for particle in snapshot['particles']:
            positions.append(particle['pos'])
            masses.append(particle['mass'])
            
            # Actualizar trails
            if self.show_trails:
                trail = self.particle_trails.get(particle['id'], [])
                trail.append(particle['pos'].copy())
                
                # Limitar longitud del trail
                if len(trail) > self.trail_length:
                    trail.pop(0)
                    
                self.particle_trails[particle['id']] = trail
        
        positions = np.array(positions)
        masses = np.array(masses)
        
        # Limpiar gráfico anterior
        if self.scatter:
            self.scatter.remove()
        
        for line in self.trail_lines:
            line.remove()
        self.trail_lines = []
        
        # Dibujar partículas
        colors = masses if len(set(masses)) > 1 else 'blue'
        sizes = np.clip(masses * 1000, 10, 100)  # Escalar tamaño
        
        self.scatter = self.ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                                     c=colors, s=sizes, alpha=0.8, cmap='viridis')
        
        # Dibujar trails
        if self.show_trails:
            for particle_id, trail in self.particle_trails.items():
                if len(trail) > 1:
                    trail_array = np.array(trail)
                    line = self.ax.plot(trail_array[:, 0], trail_array[:, 1], trail_array[:, 2],
                                      alpha=0.3, linewidth=1)[0]
                    self.trail_lines.append(line)
        
        # Actualizar información
        self.time_text.set_text(f'Time: {snapshot["time"]:.3f}\nStep: {snapshot["step"]}\n'
                              f'Particles: {snapshot["n_particles"]}')
        
        # Actualizar slider
        self.slider.set_val(self.current_frame)
        
        self.fig.canvas.draw()
    
    def toggle_play(self, event):
        """Inicia/pausa la animación"""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.animate()
    
    def animate(self):
        """Función de animación"""
        if not self.is_playing:
            return
            
        if self.current_frame < len(self.snapshots) - 1:
            self.current_frame += 1
        else:
            self.current_frame = 0  # Loop
            
        self.plot_frame()
        
        # Programar siguiente frame
        self.fig.canvas.draw_idle()
        self.fig.canvas.get_tk_widget().after(int(self.frame_rate), self.animate)
    
    def reset_view(self, event):
        """Reinicia la vista"""
        self.current_frame = 0
        self.is_playing = False
        self.plot_frame()
        self.update_plot_limits()
    
    def save_frame(self, event):
        """Guarda el frame actual"""
        if not self.snapshots:
            return
            
        filename = f"frame_{self.current_frame:04d}.png"
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Frame guardado como {filename}")
    
    def toggle_options(self, label):
        """Activa/desactiva opciones"""
        if label == 'Show Trails':
            self.show_trails = not self.show_trails
            if not self.show_trails:
                # Limpiar trails
                for line in self.trail_lines:
                    line.remove()
                self.trail_lines = []
                self.fig.canvas.draw()
        
        elif label == 'Color by Mass':
            self.plot_frame()
    
    def update_speed(self, val):
        """Actualiza la velocidad de animación"""
        self.frame_rate = int(self.speed_slider.val)
    
    def show(self):
        """Muestra el visualizador"""
        if not self.snapshots:
            print("No hay datos para visualizar")
            return
            
        # Plotear primer frame
        self.plot_frame()
        
        # Mostrar la figura
        plt.show()

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = "results/snapshots"
    
    print(f"Iniciando visualizador N-cuerpos...")
    print(f"Directorio de datos: {data_dir}")
    
    visualizer = NBodyVisualizer(data_dir)
    visualizer.show()

if __name__ == "__main__":
    main() 