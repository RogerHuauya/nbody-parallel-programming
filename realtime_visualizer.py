#!/usr/bin/env python3
"""
Enhanced 3D N-Body Visualization with Beautiful Graphics
Real-time monitoring with advanced visual effects
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as mpatches
from matplotlib import cm
import os
import glob
import time
import json
from datetime import datetime
import threading
import queue
from collections import deque
import matplotlib.gridspec as gridspec

# Advanced style configuration
plt.style.use('dark_background')
plt.rcParams['figure.figsize'] = (20, 12)
plt.rcParams['figure.facecolor'] = '#0a0a0a'
plt.rcParams['axes.facecolor'] = '#0a0a0a'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.labelcolor'] = '#cccccc'
plt.rcParams['xtick.color'] = '#666666'
plt.rcParams['ytick.color'] = '#666666'
plt.rcParams['grid.color'] = '#222222'
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10

class RealtimeNBodyVisualizer:
    def __init__(self, base_dir='realtime_simulations', update_interval=50):
        self.base_dir = base_dir
        self.update_interval = update_interval  # ms
        self.simulations = {}
        self.data_queue = queue.Queue()
        self.running = True
        self.current_view = 0
        self.rotation_speed = 0.5
        self.show_trails = True
        self.trail_length = 10
        self.particle_size_scale = 1.0
        
        # Create figure with GridSpec for better layout
        self.fig = plt.figure(figsize=(16, 12))
        self.fig.patch.set_facecolor('#0a0a0a')

        # 3 rows, 2 columns → first row for controls, next two rows for 2×2 grid
        gs = gridspec.GridSpec(4, 2, figure=self.fig,
                               height_ratios=[0.06, 1, 1, 0.06],
                               width_ratios=[1, 1],
                               hspace=0.15, wspace=0.12)

        # Title spans entire top
        self.fig.text(0.5, 0.98, 'N-Body Parallel Computing Visualization',
                      fontsize=22, fontweight='bold', ha='center',
                      color='#ffffff', family='monospace')

        # Create 2x2 subplots for simulations
        self.axes = []
        for i in range(4):
            row = 1 + i // 2  # Rows 1 and 2 in GridSpec
            col = i % 2
            ax = self.fig.add_subplot(gs[row, col], projection='3d')
            ax.set_facecolor('#000000')
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False
            ax.xaxis.pane.set_edgecolor('#1a1a1a')
            ax.yaxis.pane.set_edgecolor('#1a1a1a')
            ax.zaxis.pane.set_edgecolor('#1a1a1a')
            ax.grid(True, alpha=0.1, linestyle='--')
            ax.xaxis._axinfo['grid']['linewidth'] = 0.3
            ax.yaxis._axinfo['grid']['linewidth'] = 0.3
            ax.zaxis._axinfo['grid']['linewidth'] = 0.3
            self.axes.append(ax)

        # Status bar along bottom row (row 3 spanning two columns)
        self.status_text = self.fig.text(0.5, 0.015, '', fontsize=11,
                                         ha='center', color='#aaaaaa',
                                         family='monospace')
        
        # Initialize simulations
        self.processors = [1, 2, 4, 8]
        self.n_size = self.get_n_size()
        
        # Color schemes for each processor count
        self.color_schemes = {
            1: {'cmap': 'hot', 'base': '#ff6b6b', 'glow': '#ff0000'},
            2: {'cmap': 'cool', 'base': '#4ecdc4', 'glow': '#00ffff'},
            4: {'cmap': 'spring', 'base': '#95e1d3', 'glow': '#00ff00'},
            8: {'cmap': 'plasma', 'base': '#c56cf0', 'glow': '#ff00ff'}
        }
        
        for i, P in enumerate(self.processors):
            # Attempt to read t_end from cfg
            cfg_path = f"{self.base_dir}/P{P}_N{self.n_size}KB/phi-GPU4.cfg"
            t_end_val = 100.0
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r') as cf:
                        tokens = cf.read().strip().split()
                        if len(tokens) >= 2:
                            t_end_val = float(tokens[1])
                except:
                    pass

            self.simulations[P] = {
                'dir': f"{self.base_dir}/P{P}_N{self.n_size}KB",
                'processors': P,
                'particles': None,
                'scatter': None,
                'current_snapshot': -1,
                'snapshots': deque(maxlen=self.trail_length),
                'status': 'waiting',
                'ax': self.axes[i],
                'start_time': None,
                'processing_times': [],
                'rotation_angle': 0,
                'velocities': None,
                'energies': None,
                't_end': t_end_val,
                'current_time': 0.0,
                'last_mtime': 0
            }
        
        # Setup controls
        self.setup_controls()
        
    def get_n_size(self):
        """Obtener el tamaño N del archivo de información"""
        try:
            with open(f"{self.base_dir}/info.json", 'r') as f:
                info = json.load(f)
                return info['n_particles'] // 1024
        except:
            return 1  # Default 1KB
    
    def setup_controls(self):
        """Configurar controles interactivos"""
        # Rotation speed control
        ax_rotation = plt.axes([0.08, 0.92, 0.25, 0.025])
        ax_rotation.set_facecolor('#1a1a1a')
        from matplotlib.widgets import Slider
        self.rotation_slider = Slider(ax_rotation, 'Rotation', 0, 2, 
                                      valinit=self.rotation_speed, 
                                      color='#4ecdc4')
        self.rotation_slider.on_changed(self.update_rotation_speed)
        
        # Particle size control
        ax_size = plt.axes([0.38, 0.92, 0.25, 0.025])
        ax_size.set_facecolor('#1a1a1a')
        self.size_slider = Slider(ax_size, 'Particle Size', 0.1, 3, 
                                  valinit=self.particle_size_scale,
                                  color='#95e1d3')
        self.size_slider.on_changed(self.update_particle_size)
        
        # Trail toggle button
        ax_trail = plt.axes([0.72, 0.92, 0.12, 0.025])
        from matplotlib.widgets import Button
        self.trail_button = Button(ax_trail, 'Toggle Trails', 
                                  color='#3a3a3a', hovercolor='#5a5a5a')
        self.trail_button.on_clicked(self.toggle_trails)
    
    def update_rotation_speed(self, val):
        self.rotation_speed = val
    
    def update_particle_size(self, val):
        self.particle_size_scale = val
    
    def toggle_trails(self, event):
        self.show_trails = not self.show_trails
        
    def monitor_files(self):
        """Thread para monitorear data.con directamente"""
        while self.running:
            for P, sim in self.simulations.items():
                sim_dir = sim['dir']
                data_con_file = f"{sim_dir}/data.con"
                
                if os.path.exists(data_con_file):
                    try:
                        # Check if data.con has been updated
                        current_mtime = os.path.getmtime(data_con_file)
                        
                        # Only process if file has been modified since last read
                        if current_mtime > sim.get('last_mtime', 0):
                            # Check if file is stable (not being written)
                            initial_size = os.path.getsize(data_con_file)
                            time.sleep(0.01)  # Small delay to ensure write is complete
                            final_size = os.path.getsize(data_con_file)
                            
                            if initial_size == final_size and final_size > 0:
                                start_load = time.time()
                                data = self.load_snapshot(data_con_file)
                                load_time = time.time() - start_load
                                
                                if data is not None:
                                    # Calculate velocities for visualization
                                    if sim['particles'] is not None:
                                        old_pos = sim['particles']['positions']
                                        new_pos = data['positions']
                                        
                                        # Only calculate velocities if particle counts match
                                        if old_pos.shape[0] == new_pos.shape[0]:
                                            data['velocities'] = np.linalg.norm(new_pos - old_pos, axis=1)
                                        else:
                                            # Particle count mismatch - use zeros for now
                                            data['velocities'] = np.zeros(data['n_particles'])
                                    else:
                                        data['velocities'] = np.zeros(data['n_particles'])
                                    
                                    # Update last modification time
                                    sim['last_mtime'] = current_mtime
                                    sim['current_snapshot'] += 1
                                    
                                    self.data_queue.put((P, data, sim['current_snapshot'], load_time))
                                    sim['status'] = 'running'
                                    if sim['start_time'] is None:
                                        sim['start_time'] = time.time()
                    except Exception as e:
                        print(f"Error loading data.con for P={P}: {e}")
                
                # Verificar estado
                status_file = f"{sim['dir']}/status.txt"
                if os.path.exists(status_file):
                    with open(status_file, 'r') as f:
                        sim['status'] = f.read().strip()
            
            time.sleep(0.05)  # Check every 50ms
    
    def load_snapshot(self, filename):
        """Cargar datos de un snapshot con verificación de escritura completa"""
        try:
            # Check if file is still being written by checking size stability
            initial_size = os.path.getsize(filename)
            time.sleep(0.01)  # Small delay
            final_size = os.path.getsize(filename)
            
            # If file size is still changing, skip this read
            if initial_size != final_size or final_size == 0:
                return None
            
            # Try to open with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with open(filename, 'r') as f:
                        lines = f.readlines()
                    break
                except (IOError, OSError):
                    if attempt < max_retries - 1:
                        time.sleep(0.01)
                        continue
                    else:
                        return None
            
            if len(lines) < 4:
                return None
            
            # Parse header
            try:
                n_particles = int(lines[1].strip())
                sim_time = float(lines[2].strip())
            except (ValueError, IndexError):
                return None
            
            # Verify we have enough lines for all particles
            expected_lines = 3 + n_particles
            if len(lines) < expected_lines:
                return None
            
            # Load positions
            positions = []
            masses = []
            
            for i in range(3, 3 + n_particles):
                if i >= len(lines):
                    break
                parts = lines[i].split()
                if len(parts) >= 8:
                    try:
                        masses.append(float(parts[1]))
                        positions.append([float(parts[2]), float(parts[3]), float(parts[4])])
                    except (ValueError, IndexError):
                        continue
            
            # Only return if we got all expected particles
            if len(positions) == n_particles and positions:
                return {
                    'positions': np.array(positions),
                    'masses': np.array(masses),
                    'n_particles': len(positions),
                    'time': sim_time
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error parsing snapshot {filename}: {e}")
            return None
    
    def update_visualization(self, frame):
        """Update visualization with enhanced graphics"""
        # Process queue data
        updated = False
        while not self.data_queue.empty():
            try:
                P, data, snapshot_idx, load_time = self.data_queue.get_nowait()
                sim = self.simulations[P]
                sim['particles'] = data
                sim['current_snapshot'] = snapshot_idx
                sim['snapshots'].append(data)
                sim['processing_times'].append(load_time)
                sim['velocities'] = data.get('velocities', np.zeros(data['n_particles']))
                sim['current_time'] = data.get('time', sim['current_time'])
                updated = True
            except queue.Empty:
                break
        
        # Update each subplot
        for i, P in enumerate(self.processors):
            sim = self.simulations[P]
            ax = sim['ax']
            
            # Update rotation
            sim['rotation_angle'] += self.rotation_speed
            
            if sim['particles'] is not None:
                data = sim['particles']
                positions = data['positions']
                masses = data['masses']
                velocities = sim['velocities']
                
                # Clear and redraw
                ax.clear()
                
                # Configure limits
                max_range = np.max(np.abs(positions)) * 1.2
                ax.set_xlim(-max_range, max_range)
                ax.set_ylim(-max_range, max_range)
                ax.set_zlim(-max_range/2, max_range/2)
                
                # Calculate particle properties for visualization
                # Normalize masses for size
                mass_norm = (masses - masses.min()) / (masses.max() - masses.min() + 1e-10)
                sizes = (50 + 200 * mass_norm) * self.particle_size_scale
                
                # Color based on velocity magnitude
                vel_norm = velocities / (velocities.max() + 1e-10)
                
                # Get color scheme
                scheme = self.color_schemes[P]
                
                # Main particle scatter with glow effect
                # Inner bright core
                scatter = ax.scatter(positions[:, 0], 
                                   positions[:, 1], 
                                   positions[:, 2],
                                   c=vel_norm, 
                                   cmap=scheme['cmap'],
                                   s=sizes * 0.5,
                                   alpha=1.0,
                                   edgecolors='none',
                                   vmin=0, vmax=1)
                
                # Outer glow
                ax.scatter(positions[:, 0], 
                          positions[:, 1], 
                          positions[:, 2],
                          c=vel_norm, 
                          cmap=scheme['cmap'],
                          s=sizes * 2,
                          alpha=0.2,
                          edgecolors='none',
                          vmin=0, vmax=1)
                
                # Draw enhanced trails
                if self.show_trails and len(sim['snapshots']) > 1:
                    # Select particles for trails (more for visual effect)
                    n_tracks = min(10, data['n_particles'])
                    track_ids = np.linspace(0, data['n_particles']-1, n_tracks, dtype=int)
                    
                    for tid in track_ids:
                        trajectory = []
                        for snap in list(sim['snapshots']):
                            if tid < len(snap['positions']):
                                trajectory.append(snap['positions'][tid])
                        
                        if len(trajectory) > 1:
                            trajectory = np.array(trajectory)
                            # Gradient trail with fading
                            for j in range(len(trajectory)-1):
                                alpha = (j+1) / len(trajectory) * 0.5
                                ax.plot(trajectory[j:j+2, 0], 
                                       trajectory[j:j+2, 1], 
                                       trajectory[j:j+2, 2],
                                       color=scheme['base'], 
                                       alpha=alpha, 
                                       linewidth=1.5)
                
                # Draw progress bar of simulation time using 2D inset axis (avoids 3D projection issues)
                progress = min(max(sim['current_time'] / sim['t_end'], 0.0), 1.0)
                if 'progress_ax' not in sim or sim['progress_ax'] is None:
                    # Create once
                    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
                    sim['progress_ax'] = inset_axes(ax, width="90%", height="6%", 
                                                    loc='lower left', borderpad=2)
                    sim['progress_ax'].set_facecolor('none')
                    sim['progress_ax'].set_xticks([])
                    sim['progress_ax'].set_yticks([])
                    sim['progress_ax'].set_xlim(0, 1)
                    sim['progress_ax'].set_ylim(0, 1)
                p_ax = sim['progress_ax']
                p_ax.clear()
                p_ax.barh(0.5, 1.0, height=1.0, color='#333333', alpha=0.6)
                p_ax.barh(0.5, progress, height=1.0, color=scheme['base'], alpha=0.9)
                p_ax.set_xticks([])
                p_ax.set_yticks([])
                p_ax.text(0.5, 0.5, f"t = {sim['current_time']:.1f}/{sim['t_end']}",
                           ha='center', va='center', fontsize=7, color='#dddddd')
                
                # Style the axes
                ax.set_xlabel('X', fontsize=9, color='#888888')
                ax.set_ylabel('Y', fontsize=9, color='#888888')
                ax.set_zlabel('Z', fontsize=9, color='#888888')
                ax.tick_params(colors='#666666', labelsize=8)
                
                # Performance metrics
                if sim['processing_times']:
                    avg_time = np.mean(sim['processing_times'][-10:])
                    fps = 1.0 / avg_time if avg_time > 0 else 0
                    speedup = self.simulations[1]['processing_times'][-1] / avg_time if P > 1 and self.simulations[1]['processing_times'] else P
                else:
                    fps = 0
                    speedup = 1
                
                # Enhanced title with metrics
                title = f'P = {P} {"processor" if P == 1 else "processors"}\n'
                title += f'Snapshot: {sim["current_snapshot"]:04d} | '
                title += f'FPS: {fps:.1f} | '
                title += f'Speedup: {speedup:.1f}x'
                
                ax.text2D(0.5, 0.95, title, transform=ax.transAxes,
                         fontsize=11, ha='center', va='top',
                         color=scheme['base'], weight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', 
                                  facecolor='#1a1a1a', 
                                  edgecolor=scheme['base'],
                                  alpha=0.8))
                
                # Set viewing angle with rotation
                ax.view_init(elev=20, azim=sim['rotation_angle'])
                
                # Remove axis lines for cleaner look
                ax.xaxis.line.set_visible(False)
                ax.yaxis.line.set_visible(False)
                ax.zaxis.line.set_visible(False)
            else:
                # Waiting state
                ax.text2D(0.5, 0.5, f'Waiting for data...\nP = {P}', 
                         transform=ax.transAxes,
                         fontsize=14, ha='center', va='center',
                         color='#666666', style='italic')
                ax.set_xlim(-1, 1)
                ax.set_ylim(-1, 1)
                ax.set_zlim(-1, 1)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_zticks([])
        
        # Update status bar
        status = f"Time: {datetime.now().strftime('%H:%M:%S')} | "
        status += f"Particles: {self.n_size*1024} | "
        status += "Status: "
        for P in self.processors:
            sim = self.simulations[P]
            status += f"P{P}:{sim['status'][:3].upper()} "
        
        self.status_text.set_text(status)
        
        return self.axes
    
    def run(self):
        """Execute the visualization system"""
        print("=== Enhanced N-Body Real-time Visualization ===")
        print(f"Monitoring: {self.base_dir}")
        print(f"Particles: {self.n_size*1024}")
        print("Starting monitoring thread...")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_files)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Create animation
        self.anim = FuncAnimation(self.fig, self.update_visualization,
                                 interval=self.update_interval,
                                 blit=False, cache_frame_data=False)
        
        plt.show()
        
        # Cleanup
        self.running = False
        monitor_thread.join(timeout=1)

def main():
    # Create and run visualizer
    visualizer = RealtimeNBodyVisualizer()
    visualizer.run()

if __name__ == "__main__":
    main() 