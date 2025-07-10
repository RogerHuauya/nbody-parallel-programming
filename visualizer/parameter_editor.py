#!/usr/bin/env python3
"""
Editor de parámetros para simulador N-cuerpos
Permite modificar parámetros de simulación y generar nuevas condiciones iniciales
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider, TextBox
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import json

class ParameterEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Editor de Parámetros N-Cuerpos")
        self.master.geometry("600x500")
        
        # Parámetros por defecto
        self.parameters = {
            'n_particles': 1000,
            'n_processes': 1,
            'timestep': 0.01,
            'total_time': 10.0,
            'softening': 0.0,
            'output_frequency': 10,
            'integration_order': 4,
            'random_seed': 12345,
            'plummer_scale': 1.0,
            'virial_ratio': 0.5
        }
        
        # Variables de la interfaz
        self.param_vars = {}
        
        # Configurar interfaz
        self.setup_interface()
        
        # Cargar parámetros si existe archivo
        self.load_parameters()
        
    def setup_interface(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        title_label = ttk.Label(main_frame, text="Editor de Parámetros N-Cuerpos", 
                              font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Crear campos de parámetros
        self.create_parameter_fields(main_frame)
        
        # Botones
        self.create_buttons(main_frame)
        
        # Área de estado
        self.status_text = tk.Text(main_frame, height=8, width=70)
        self.status_text.grid(row=len(self.parameters)+3, column=0, columnspan=2, 
                             pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Scrollbar para el área de estado
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.status_text.yview)
        scrollbar.grid(row=len(self.parameters)+3, column=2, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # Configurar redimensionamiento
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def create_parameter_fields(self, parent):
        """Crea los campos de entrada para los parámetros"""
        row = 1
        
        # Parámetros básicos
        ttk.Label(parent, text="Parámetros Básicos", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        row += 1
        
        basic_params = [
            ('n_particles', 'Número de partículas:', int),
            ('n_processes', 'Número de procesos MPI:', int),
            ('integration_order', 'Orden de integración (4,6,8):', int),
            ('timestep', 'Paso temporal:', float),
            ('total_time', 'Tiempo total:', float),
            ('output_frequency', 'Frecuencia de salida:', int)
        ]
        
        for param, label, param_type in basic_params:
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            
            if param_type == int:
                var = tk.IntVar(value=self.parameters[param])
            else:
                var = tk.DoubleVar(value=self.parameters[param])
            
            entry = ttk.Entry(parent, textvariable=var, width=15)
            entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
            
            self.param_vars[param] = var
            row += 1
        
        # Parámetros avanzados
        ttk.Label(parent, text="Parámetros Avanzados", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, columnspan=2, pady=(20, 10), sticky=tk.W)
        row += 1
        
        advanced_params = [
            ('softening', 'Parámetro de suavizado:', float),
            ('random_seed', 'Semilla aleatoria:', int),
            ('plummer_scale', 'Escala de Plummer:', float),
            ('virial_ratio', 'Ratio virial:', float)
        ]
        
        for param, label, param_type in advanced_params:
            ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            
            if param_type == int:
                var = tk.IntVar(value=self.parameters[param])
            else:
                var = tk.DoubleVar(value=self.parameters[param])
            
            entry = ttk.Entry(parent, textvariable=var, width=15)
            entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
            
            self.param_vars[param] = var
            row += 1
        
        self.button_row = row + 1
        
    def create_buttons(self, parent):
        """Crea los botones de acción"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=self.button_row, column=0, columnspan=2, pady=(20, 10))
        
        # Botón para generar condiciones iniciales
        ttk.Button(button_frame, text="Generar Condiciones Iniciales", 
                  command=self.generate_initial_conditions).grid(row=0, column=0, padx=5)
        
        # Botón para ejecutar simulación
        ttk.Button(button_frame, text="Ejecutar Simulación", 
                  command=self.run_simulation).grid(row=0, column=1, padx=5)
        
        # Botón para guardar parámetros
        ttk.Button(button_frame, text="Guardar Parámetros", 
                  command=self.save_parameters).grid(row=0, column=2, padx=5)
        
        # Botón para cargar parámetros
        ttk.Button(button_frame, text="Cargar Parámetros", 
                  command=self.load_parameters_dialog).grid(row=0, column=3, padx=5)
        
        # Botón para lanzar visualizador
        ttk.Button(button_frame, text="Abrir Visualizador", 
                  command=self.launch_visualizer).grid(row=1, column=0, padx=5, pady=5)
        
        # Botón para análisis de error
        ttk.Button(button_frame, text="Análisis de Error", 
                  command=self.analyze_error).grid(row=1, column=1, padx=5, pady=5)
        
        # Botón para benchmark
        ttk.Button(button_frame, text="Ejecutar Benchmark", 
                  command=self.run_benchmark).grid(row=1, column=2, padx=5, pady=5)
        
    def update_parameters(self):
        """Actualiza los parámetros con los valores de la interfaz"""
        for param, var in self.param_vars.items():
            self.parameters[param] = var.get()
    
    def log_message(self, message):
        """Añade un mensaje al área de estado"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.master.update()
    
    def generate_initial_conditions(self):
        """Genera condiciones iniciales usando gen-plum"""
        self.update_parameters()
        
        self.log_message("Generando condiciones iniciales...")
        
        try:
            # Cambiar al directorio src
            os.chdir("src")
            
            # Compilar gen-plum si no existe
            if not os.path.exists("gen-plum"):
                self.log_message("Compilando gen-plum...")
                result = subprocess.run(["make", "gen-plum"], capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_message(f"Error compilando gen-plum: {result.stderr}")
                    return
            
            # Ejecutar gen-plum
            n_particles = self.parameters['n_particles']
            n_processes = self.parameters['n_processes']
            
            cmd = ["./gen-plum", str(n_particles), str(n_processes)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message(f"Condiciones iniciales generadas para {n_particles} partículas")
                self.log_message(f"Archivo generado: data.inp")
            else:
                self.log_message(f"Error generando condiciones iniciales: {result.stderr}")
                
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            os.chdir("..")
    
    def run_simulation(self):
        """Ejecuta la simulación"""
        self.update_parameters()
        
        self.log_message("Ejecutando simulación...")
        
        try:
            os.chdir("src")
            
            # Compilar el ejecutable apropiado
            order = self.parameters['integration_order']
            exe_name = f"cpu-{order}th"
            
            if not os.path.exists(exe_name):
                self.log_message(f"Compilando {exe_name}...")
                result = subprocess.run(["make", exe_name], capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_message(f"Error compilando: {result.stderr}")
                    return
            
            # Verificar que existan condiciones iniciales
            if not os.path.exists("data.inp"):
                self.log_message("No se encontraron condiciones iniciales. Generando...")
                self.generate_initial_conditions()
            
            # Ejecutar simulación
            n_processes = self.parameters['n_processes']
            cmd = ["mpirun", "-np", str(n_processes), f"./{exe_name}"]
            
            self.log_message(f"Ejecutando: {' '.join(cmd)}")
            
            # Ejecutar en background para no bloquear la interfaz
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            # Mostrar progreso
            self.log_message("Simulación en progreso...")
            
            # Esperar un poco y mostrar resultado
            self.master.after(1000, lambda: self.check_simulation_progress(process))
            
        except Exception as e:
            self.log_message(f"Error ejecutando simulación: {str(e)}")
        finally:
            os.chdir("..")
    
    def check_simulation_progress(self, process):
        """Verifica el progreso de la simulación"""
        if process.poll() is None:
            # Aún ejecutándose
            self.log_message("Simulación aún ejecutándose...")
            self.master.after(2000, lambda: self.check_simulation_progress(process))
        else:
            # Terminada
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                self.log_message("Simulación completada exitosamente")
                self.log_message("Archivos de salida generados")
            else:
                self.log_message(f"Error en simulación: {stderr}")
    
    def save_parameters(self):
        """Guarda los parámetros en un archivo JSON"""
        self.update_parameters()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.parameters, f, indent=2)
                self.log_message(f"Parámetros guardados en: {filename}")
            except Exception as e:
                self.log_message(f"Error guardando parámetros: {str(e)}")
    
    def load_parameters_dialog(self):
        """Carga parámetros desde un archivo JSON"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    loaded_params = json.load(f)
                
                # Actualizar parámetros
                for param, value in loaded_params.items():
                    if param in self.param_vars:
                        self.param_vars[param].set(value)
                
                self.log_message(f"Parámetros cargados desde: {filename}")
                
            except Exception as e:
                self.log_message(f"Error cargando parámetros: {str(e)}")
    
    def load_parameters(self):
        """Carga parámetros por defecto si existe el archivo"""
        default_file = "config/default_parameters.json"
        if os.path.exists(default_file):
            try:
                with open(default_file, 'r') as f:
                    loaded_params = json.load(f)
                
                self.parameters.update(loaded_params)
                self.log_message("Parámetros por defecto cargados")
                
            except Exception as e:
                self.log_message(f"Error cargando parámetros por defecto: {str(e)}")
    
    def launch_visualizer(self):
        """Lanza el visualizador"""
        try:
            subprocess.Popen(["python3", "visualizer/viewer.py"])
            self.log_message("Visualizador lanzado")
        except Exception as e:
            self.log_message(f"Error lanzando visualizador: {str(e)}")
    
    def analyze_error(self):
        """Ejecuta análisis de error"""
        try:
            subprocess.Popen(["python3", "scripts/analyze_error.py", "src", "results/error"])
            self.log_message("Análisis de error lanzado")
        except Exception as e:
            self.log_message(f"Error lanzando análisis: {str(e)}")
    
    def run_benchmark(self):
        """Ejecuta benchmark"""
        try:
            subprocess.Popen(["bash", "scripts/benchmark.sh"])
            self.log_message("Benchmark lanzado")
        except Exception as e:
            self.log_message(f"Error lanzando benchmark: {str(e)}")

def main():
    """Función principal"""
    root = tk.Tk()
    app = ParameterEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main() 