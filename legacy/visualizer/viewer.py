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
        self.animation_timer = None
        
        # Configuración de visualización
        self.show_trails = False
        self.trail_length = 50
        self.particle_trails = {}
        
        # Cargar datos
        self.load_snapshots()
        
        if not self.snapshots:
            print("No se encontraron datos para visualizar")
            return
        
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
        plt.ioff()  # Desactivar modo interactivo para evitar problemas
        self.fig = plt.figure(figsize=(12, 10))
        
        # Eje principal 3D
        self.ax = self.fig.add_subplot(111, projection='3d')
        
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
        
        # Calcular límites globales
        self.calculate_plot_limits()
        
    def calculate_plot_limits(self):
        """Calcula los límites del gráfico basado en todos los datos"""
        if not self.snapshots:
            return
            
        # Encontrar límites globales
        all_positions = []
        for snapshot in self.snapshots:
            for particle in snapshot['particles']:
                all_positions.append(particle['pos'])
        
        all_positions = np.array(all_positions)
        
        # Añadir margen
        margin = 0.1
        self.xlim = self._calculate_axis_limits(all_positions[:, 0], margin)
        self.ylim = self._calculate_axis_limits(all_positions[:, 1], margin)
        self.zlim = self._calculate_axis_limits(all_positions[:, 2], margin)
        
        # Aplicar límites
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_zlim(self.zlim)
    
    def _calculate_axis_limits(self, data, margin):
        """Calcula límites para un eje con margen"""
        min_val = np.min(data)
        max_val = np.max(data)
        range_val = max_val - min_val
        margin_val = range_val * margin
        return (min_val - margin_val, max_val + margin_val)
        
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
            self.scatter = None
        
        for line in self.trail_lines:
            try:
                line.remove()
            except:
                pass
        self.trail_lines = []
        
        # Determinar colores
        unique_masses = np.unique(masses)
        if len(unique_masses) > 1:
            # Colorear por masa
            colors = masses
            cmap = 'viridis'
        else:
            # Color uniforme
            colors = 'blue'
            cmap = None
        
        # Escalar tamaños
        sizes = np.clip(masses * 1000, 10, 100)
        
        # Dibujar partículas
        self.scatter = self.ax.scatter(positions[:, 0], positions[:, 1], positions[:, 2],
                                     c=colors, s=sizes, alpha=0.8, cmap=cmap)
        
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
        
        # Restaurar límites (importante para evitar problemas)
        self.ax.set_xlim(self.xlim)
        self.ax.set_ylim(self.ylim)
        self.ax.set_zlim(self.zlim)
        
        # Actualizar canvas
        self.fig.canvas.draw_idle()
    
    def toggle_play(self, event):
        """Inicia/pausa la animación"""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.start_animation()
        else:
            self.stop_animation()
    
    def start_animation(self):
        """Inicia la animación usando matplotlib timer"""
        if self.animation_timer is None:
            self.animation_timer = self.fig.canvas.new_timer(interval=self.frame_rate)
            self.animation_timer.add_callback(self.animate_step)
        self.animation_timer.start()
    
    def stop_animation(self):
        """Detiene la animación"""
        if self.animation_timer is not None:
            self.animation_timer.stop()
    
    def animate_step(self):
        """Un paso de la animación"""
        if not self.is_playing:
            return
            
        if self.current_frame < len(self.snapshots) - 1:
            self.current_frame += 1
        else:
            self.current_frame = 0  # Loop
            
        self.slider.set_val(self.current_frame)
        self.plot_frame()
    
    def reset_view(self, event):
        """Reinicia la vista"""
        self.current_frame = 0
        self.is_playing = False
        self.stop_animation()
        self.slider.set_val(0)
        self.plot_frame()
    
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
                for particle_id in self.particle_trails:
                    self.particle_trails[particle_id] = []
            self.plot_frame()
        
        elif label == 'Color by Mass':
            self.plot_frame()
    
    def update_speed(self, val):
        """Actualiza la velocidad de animación"""
        self.frame_rate = int(self.speed_slider.val)
        if self.animation_timer is not None:
            self.animation_timer.interval = self.frame_rate
    
    def show(self):
        """Muestra el visualizador"""
        if not self.snapshots:
            print("No hay datos para visualizar")
            return
            
        # Plotear primer frame
        self.plot_frame()
        
        print("\nControles:")
        print("- Play/Pause: Inicia o pausa la animación")
        print("- Reset: Vuelve al primer frame")
        print("- Save Frame: Guarda el frame actual como imagen")
        print("- Slider: Navega entre frames")
        print("- Show Trails: Muestra las trayectorias de las partículas")
        print("- Speed: Ajusta la velocidad de animación")
        print("\nPuedes rotar la vista con el mouse")
        
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