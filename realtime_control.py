#!/usr/bin/env python3
"""
Script de control para el sistema de visualización N-Body en tiempo real
"""

import subprocess
import sys
import os
import time
import psutil
import signal
import threading

# Importar el visualizador nativamente
try:
    from realtime_visualizer import RealtimeNBodyVisualizer, plot_final_comparison
    VISUALIZER_AVAILABLE = True
except ImportError as e:
    print(f"Advertencia: No se pudo importar el visualizador: {e}")
    VISUALIZER_AVAILABLE = False

class RealtimeController:
    def __init__(self):
        self.simulation_process = None
        self.visualizer = None
        self.visualizer_thread = None
        
    def check_dependencies(self):
        """Verificar que todas las dependencias estén instaladas"""
        print("Verificando dependencias...")
        
        # Verificar ejecutables
        required_files = ['cpu-4th', 'gen-plum', 'realtime_simulation.sh']
        missing = []
        
        for file in required_files:
            if not os.path.exists(file):
                missing.append(file)
        
        # Verificar visualizador (opcional)
        if not os.path.exists('realtime_visualizer.py'):
            print("Advertencia: realtime_visualizer.py no encontrado - la visualización no estará disponible")
        
        if missing:
            print(f"Error: Archivos faltantes: {missing}")
            return False
        
        # Verificar MPI
        try:
            subprocess.run(['mpirun', '--version'], capture_output=True, check=True)
        except:
            print("Error: MPI no está instalado. Ejecuta: sudo apt install mpich")
            return False
        
        print("✓ Todas las dependencias verificadas")
        return True
    
    def start_simulation(self, processors=2):
        """Iniciar las simulaciones en paralelo"""
        print(f"\nIniciando simulaciones con {processors} procesadores...")
        
        # Verificar que el archivo existe
        script_path = './realtime_simulation.sh'
        if not os.path.exists(script_path):
            print(f"ERROR: No se encuentra el archivo: {script_path}")
            print(f"Directorio actual: {os.getcwd()}")
            print(f"Archivos en el directorio:")
            for file in os.listdir('.'):
                print(f"  - {file}")
            return None
        
        # Hacer ejecutable el script
        try:
            os.chmod(script_path, 0o755)
            print(f"✓ Script {script_path} hecho ejecutable")
        except Exception as e:
            print(f"Error al hacer ejecutable {script_path}: {e}")
        
        # Mostrar información del comando que se va a ejecutar
        cmd = [script_path, str(processors)]
        print(f"Ejecutando comando: {' '.join(cmd)}")
        print(f"Ruta absoluta del script: {os.path.abspath(script_path)}")
        
        # Verificar permisos del archivo
        try:
            stat_info = os.stat(script_path)
            print(f"Permisos del archivo: {oct(stat_info.st_mode)[-3:]}")
            print(f"Es ejecutable: {os.access(script_path, os.X_OK)}")
        except Exception as e:
            print(f"Error al verificar permisos: {e}")
        
        # Verificar si bash está disponible
        try:
            bash_check = subprocess.run(['which', 'bash'], capture_output=True, text=True)
            print(f"Bash encontrado en: {bash_check.stdout.strip()}")
        except Exception as e:
            print(f"Error al buscar bash: {e}")

        try:
            print(f"Intentando ejecutar: {' '.join(cmd)}")
            self.simulation_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"✓ Subproceso iniciado exitosamente (PID: {self.simulation_process.pid})")
        except FileNotFoundError as e:
            print(f"ERROR: Archivo no encontrado - {e}")
            print("Intentando con ruta absoluta...")
            try:
                abs_cmd = [os.path.abspath(script_path), str(processors)]
                print(f"Comando con ruta absoluta: {' '.join(abs_cmd)}")
                self.simulation_process = subprocess.Popen(
                    abs_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                print(f"✓ Subproceso iniciado con ruta absoluta (PID: {self.simulation_process.pid})")
            except Exception as e2:
                print(f"ERROR con ruta absoluta: {e2}")
                return None
        except Exception as e:
            print(f"ERROR al iniciar subproceso: {e}")
            print(f"Tipo de error: {type(e).__name__}")
            return None
        
        print(f"Simulación iniciada (PID: {self.simulation_process.pid})")
        
        # Esperar un poco para que se creen los directorios
        time.sleep(2)
        
        return self.simulation_process
    
    def start_visualizer(self):
        """Iniciar el visualizador en tiempo real"""
        if not VISUALIZER_AVAILABLE:
            print("Error: No se puede importar el visualizador")
            return None
            
        print("\nIniciando visualizador 3D en tiempo real...")
        
        # Crear instancia del visualizador
        self.visualizer = RealtimeNBodyVisualizer()
        
        # Ejecutar en un thread separado para no bloquear el proceso principal
        def run_visualizer():
            try:
                self.visualizer.start()
            except Exception as e:
                print(f"Error en visualizador: {e}")
        
        self.visualizer_thread = threading.Thread(target=run_visualizer, daemon=True)
        self.visualizer_thread.start()
        
        print("✓ Visualizador iniciado en thread separado")
        return self.visualizer
    
    def monitor_processes(self):
        """Monitorear el estado de los procesos"""
        print("\nMonitoreando procesos...")
        print("Presiona Ctrl+C para detener todo\n")
        
        try:
            while True:
                # Verificar estado de simulación
                if self.simulation_process:
                    sim_status = self.simulation_process.poll()
                    if sim_status is not None:
                        print(f"\nSimulación completada con código: {sim_status}")
                        # Leer salida
                        stdout, stderr = self.simulation_process.communicate()
                        if stdout:
                            print("Salida de simulación:")
                            print(stdout)
                        if stderr:
                            print("Errores de simulación:")
                            print(stderr)
                        self.simulation_process = None
                
                # Verificar estado de visualizador
                viz_running = (self.visualizer_thread and self.visualizer_thread.is_alive())
                
                # Si ambos terminaron, salir
                if self.simulation_process is None and not viz_running:
                    break
                
                # Mostrar uso de recursos
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    print(f"\rCPU: {cpu_percent:5.1f}% | RAM: {memory.percent:5.1f}% | " +
                          f"Sim: {'Running' if self.simulation_process else 'Done'} | " +
                          f"Viz: {'Running' if viz_running else 'Done'}    ", 
                          end='', flush=True)
                except:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n\nDeteniendo procesos...")
            self.stop_all()
    
    def stop_all(self):
        """Detener todos los procesos"""
        if self.simulation_process:
            print("Deteniendo simulación...")
            self.simulation_process.terminate()
            try:
                self.simulation_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.simulation_process.kill()
        
        if self.visualizer:
            print("Deteniendo visualizador...")
            self.visualizer.running = False
            if self.visualizer_thread and self.visualizer_thread.is_alive():
                self.visualizer_thread.join(timeout=2)
    
    def show_final_results(self):
        """Mostrar resultados finales"""
        print("\n=== RESULTADOS FINALES ===")
        
        # Contar snapshots generados
        base_dir = 'realtime_simulations'
        sizes = [1, 2, 4, 8]
        
        for N in sizes:
            snapshot_dir = f"{base_dir}/N_{N}KB/snapshots"
            if os.path.exists(snapshot_dir):
                count = len([f for f in os.listdir(snapshot_dir) if f.startswith('snapshot_')])
                print(f"N={N*1024}: {count} snapshots generados")
        
        # Preguntar si mostrar comparación final
        response = input("\n¿Mostrar comparación final? (s/n): ")
        if response.lower() == 's' and VISUALIZER_AVAILABLE:
            try:
                plot_final_comparison()
            except Exception as e:
                print(f"Error al mostrar comparación final: {e}")
        elif response.lower() == 's':
            print("No se puede mostrar comparación final: visualizador no disponible")
    
    def run(self):
        """Ejecutar el sistema completo"""
        print("=== SISTEMA DE VISUALIZACIÓN N-BODY EN TIEMPO REAL ===\n")
        
        if not self.check_dependencies():
            return
        
        # Preguntar configuración
        try:
            processors = int(input("Número de procesadores a usar (default=2): ") or "2")
        except:
            processors = 2
        
        # Iniciar simulación
        self.start_simulation(processors)
        
        # Esperar un poco
        time.sleep(3)
        
        # Iniciar visualizador
        self.start_visualizer()
        
        # Monitorear
        self.monitor_processes()
        
        # Mostrar resultados
        self.show_final_results()
        
        print("\n¡Sistema finalizado!")

def main():
    controller = RealtimeController()
    
    # Configurar manejo de señales
    def signal_handler(sig, frame):
        print("\n\nInterrupción recibida...")
        controller.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Ejecutar
    controller.run()

if __name__ == "__main__":
    main() 