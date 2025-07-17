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
import json

class RealtimeController:
    def __init__(self):
        self.simulation_process = None
        self.visualizer_process = None

    def clean_simulation(self):
        """Limpiar la simulación"""
        print("Limpiando simulación...")
        subprocess.run(['rm', '-rf', 'realtime_simulations'])

    def compile_code(self):
        """Compilar el código"""
        print("Compilando código...")
        subprocess.run(['make', 'clean'], check=True)
        subprocess.run(['make', 'cpu-4th'], check=True)
        subprocess.run(['make', 'gen-plum'], check=True)
        
    def check_dependencies(self):
        """Verificar que todas las dependencias estén instaladas"""
        print("Verificando dependencias...")
        
        # Verificar ejecutables
        required_files = ['bin/cpu-4th', 'bin/gen-plum', 'realtime_simulation.sh', 'realtime_visualizer.py']
        missing = []
        
        for file in required_files:
            if not os.path.exists(file):
                missing.append(file)
        
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
    
    def start_simulation(self, n_size=4):
        """Iniciar las simulaciones con diferentes procesadores"""
        print(f"\nIniciando simulaciones con N = {n_size*1024} partículas...")
        print("Procesadores a probar: 1, 2, 4, 8")
        
        # Hacer ejecutable el script
        os.chmod('realtime_simulation.sh', 0o755)
        
        # Iniciar simulación en background
        self.simulation_process = subprocess.Popen(
            ['./realtime_simulation.sh', str(n_size)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Simulación iniciada (PID: {self.simulation_process.pid})")
        
        # Esperar un poco para que se creen los directorios
        time.sleep(2)
        
        return self.simulation_process
    
    def start_visualizer(self):
        """Iniciar el visualizador en tiempo real"""
        print("\nIniciando visualizador 3D en tiempo real...")
        
        self.visualizer_process = subprocess.Popen(
            [sys.executable, 'realtime_visualizer.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"Visualizador iniciado (PID: {self.visualizer_process.pid})")
        return self.visualizer_process
    
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
                if self.visualizer_process:
                    viz_status = self.visualizer_process.poll()
                    if viz_status is not None:
                        print(f"\nVisualizador cerrado con código: {viz_status}")
                        self.visualizer_process = None
                
                # Si ambos terminaron, salir
                if self.simulation_process is None and self.visualizer_process is None:
                    break
                
                # Mostrar uso de recursos
                try:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    print(f"\rCPU: {cpu_percent:5.1f}% | RAM: {memory.percent:5.1f}% | " +
                          f"Sim: {'Running' if self.simulation_process else 'Done'} | " +
                          f"Viz: {'Running' if self.visualizer_process else 'Done'}    ", 
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
        
        if self.visualizer_process:
            print("Deteniendo visualizador...")
            self.visualizer_process.terminate()
            try:
                self.visualizer_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.visualizer_process.kill()
    
    def show_final_results(self):
        """Mostrar resultados finales"""
        print("\n=== RESULTADOS FINALES ===")
        
        # Contar snapshots generados
        base_dir = 'realtime_simulations'
        processors = [1, 2, 4, 8]
        
        # Obtener N del archivo info
        try:
            with open(f"{base_dir}/info.json", 'r') as f:
                info = json.load(f)
                n_particles = info['n_particles']
                n_size = n_particles // 1024
        except:
            n_size = 4
            n_particles = 4096
        
        print(f"N = {n_particles} partículas (constante)")
        print("\nResultados por procesador:")
        
        for P in processors:
            sim_dir = f"{base_dir}/P{P}_N{n_size}KB"
            if os.path.exists(sim_dir):
                data_con_file = f"{sim_dir}/data.con"
                if os.path.exists(data_con_file):
                    print(f"P={P}: data.con generado")
                else:
                    print(f"P={P}: sin data.con")
                
                # Buscar GFlops en output.log
                output_file = f"{base_dir}/P{P}_N{n_size}KB/output.log"
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        content = f.read()
                        if 'Real Speed' in content:
                            for line in content.split('\n'):
                                if 'Real Speed' in line:
                                    gflops = line.split()[3]
                                    print(f"      GFlops: {gflops}")
                                    break
        
        # Preguntar si mostrar comparación final
        response = input("\n¿Mostrar comparación final? (s/n): ")
        if response.lower() == 's':
            subprocess.run([sys.executable, 'realtime_visualizer.py', '--final'])
    
    def run(self):
        """Ejecutar el sistema completo"""
        print("=== SISTEMA DE VISUALIZACIÓN N-BODY EN TIEMPO REAL ===\n")

        self.compile_code()
        
        self.clean_simulation()
        
        if not self.check_dependencies():
            return
        
        # Preguntar configuración
        try:
            n_kb = int(input("Tamaño N en KB (1=1024, 2=2048, 4=4096, 8=8192) [default=4]: ") or "4")
            if n_kb not in [1, 2, 4, 8]:
                n_kb = 4
        except:
            n_kb = 4
        
        # Iniciar simulación
        self.start_simulation(n_kb)
        
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