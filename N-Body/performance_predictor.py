#!/usr/bin/env python3
"""
Predictor de Rendimiento para N-Body Paralelo
Implementa las fórmulas matemáticas del análisis teórico
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class NBodyPerformancePredictor:
    def __init__(self):
        # Parámetros del sistema (ajustados experimentalmente)
        self.alpha = 1e-8      # Tiempo por interacción (segundos)
        self.beta = 1e-9       # Tiempo actualización por partícula
        self.tau = 1e-5        # Latencia MPI
        self.mu = 1e-9         # Tiempo transferencia por byte
        self.delta = 1e-6      # Overhead sincronización
        self.gamma = 0.01      # Tiempo inicialización
        
        # Parámetros de visualización
        self.lambda_frame = 0.001   # Tiempo base por frame
        self.omega = 1e-6           # Tiempo por partícula por frame
        self.xi = 0.01              # Overhead threading
        
    def t_sequential(self, N, n_steps):
        """Tiempo de ejecución secuencial"""
        return self.alpha * N**2 * n_steps + self.beta * N * n_steps + self.gamma
    
    def t_parallel(self, N, p, n_steps):
        """Tiempo de ejecución paralelo"""
        t_comp = (self.alpha * N**2 * n_steps) / p
        t_comm = n_steps * (self.tau * np.log2(p) + self.mu * N * 8 * 8 * np.log2(p))
        t_sync = self.delta * n_steps * np.log2(p)
        return t_comp + t_comm + t_sync
    
    def speedup_strong(self, N, p, n_steps):
        """Speedup para strong scaling"""
        return self.t_sequential(N, n_steps) / self.t_parallel(N, p, n_steps)
    
    def efficiency_strong(self, N, p, n_steps):
        """Eficiencia para strong scaling"""
        return self.speedup_strong(N, p, n_steps) / p
    
    def speedup_weak(self, n_per_proc, p, n_steps):
        """Speedup para weak scaling"""
        N_total = n_per_proc * p
        t_seq = self.t_sequential(N_total, n_steps)
        t_par = self.t_parallel(N_total, p, n_steps)
        return t_seq / t_par
    
    def efficiency_weak(self, n_per_proc, p, n_steps):
        """Eficiencia para weak scaling"""
        # En weak scaling ideal, el tiempo debería mantenerse constante
        t_1 = self.t_parallel(n_per_proc, 1, n_steps)
        t_p = self.t_parallel(n_per_proc * p, p, n_steps)
        return t_1 / t_p
    
    def gflops(self, N, p, n_steps):
        """Rendimiento en GFlops"""
        flops_per_step = 20 * N**2 + 6 * N
        total_flops = flops_per_step * n_steps
        time = self.t_parallel(N, p, n_steps)
        return (total_flops / time) / 1e9
    
    def optimal_processors(self, N):
        """Número óptimo de procesadores para un tamaño N"""
        # Aproximación: p_opt ≈ sqrt(N / log(N))
        return int(np.sqrt(N / np.log(N)))
    
    def visualization_time(self, N, n_frames, n_cores):
        """Tiempo de visualización paralela"""
        t_sequential = n_frames * (self.lambda_frame + N * self.omega)
        t_parallel = t_sequential / n_cores + self.xi * n_cores
        return t_parallel
    
    def predict_total_time(self, N, p, n_steps, n_frames, n_cores):
        """Tiempo total del pipeline completo"""
        t_sim = self.t_parallel(N, p, n_steps)
        t_viz = self.visualization_time(N, n_frames, n_cores)
        t_io = 0.1 * t_sim  # Aproximación: I/O es 10% del tiempo de simulación
        return t_sim + t_viz + t_io

def generate_predictions():
    """Generar predicciones y gráficas"""
    predictor = NBodyPerformancePredictor()
    
    # Configuración
    n_steps = 1000
    n_frames = 100
    n_cores = 8
    
    # Rango de valores
    N_values = [1024, 2048, 4096, 8192, 16384]
    p_values = [1, 2, 4, 8, 16]
    
    # Crear figura con subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Predicciones de Rendimiento N-Body', fontsize=16)
    
    # 1. Strong Scaling
    for N in [4096, 8192]:
        speedups = [predictor.speedup_strong(N, p, n_steps) for p in p_values]
        efficiencies = [predictor.efficiency_strong(N, p, n_steps) for p in p_values]
        
        ax1.plot(p_values, speedups, 'o-', label=f'N={N}')
        ax2.plot(p_values, efficiencies, 's-', label=f'N={N}')
    
    ax1.plot(p_values, p_values, 'k--', label='Ideal')
    ax1.set_xlabel('Procesadores')
    ax1.set_ylabel('Speedup')
    ax1.set_title('Strong Scaling - Speedup')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.axhline(y=1.0, color='k', linestyle='--', label='Ideal')
    ax2.set_xlabel('Procesadores')
    ax2.set_ylabel('Eficiencia')
    ax2.set_title('Strong Scaling - Eficiencia')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1.1)
    
    # 3. GFlops vs N
    for p in [1, 4, 8]:
        gflops = [predictor.gflops(N, p, n_steps) for N in N_values]
        ax3.plot(N_values, gflops, '^-', label=f'p={p}')
    
    ax3.set_xlabel('Número de Partículas')
    ax3.set_ylabel('GFlops')
    ax3.set_title('Rendimiento vs Tamaño del Problema')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale('log')
    
    # 4. Procesadores Óptimos
    optimal_p = [predictor.optimal_processors(N) for N in N_values]
    ax4.plot(N_values, optimal_p, 'ro-', markersize=8)
    ax4.set_xlabel('Número de Partículas')
    ax4.set_ylabel('Procesadores Óptimos')
    ax4.set_title('Número Óptimo de Procesadores')
    ax4.grid(True, alpha=0.3)
    ax4.set_xscale('log')
    
    plt.tight_layout()
    plt.savefig('performance_predictions.png', dpi=300)
    plt.show()
    
    # Tabla de predicciones
    print("\n=== TABLA DE PREDICCIONES ===")
    print("N\t\tp_opt\tT_seq(s)\tT_par(s)\tSpeedup\tGFlops")
    print("-" * 70)
    
    for N in N_values:
        p_opt = predictor.optimal_processors(N)
        t_seq = predictor.t_sequential(N, n_steps)
        t_par = predictor.t_parallel(N, p_opt, n_steps)
        speedup = t_seq / t_par
        gflops = predictor.gflops(N, p_opt, n_steps)
        
        print(f"{N}\t\t{p_opt}\t{t_seq:.2f}\t{t_par:.2f}\t{speedup:.2f}\t{gflops:.2f}")
    
    # Comparación con datos experimentales
    print("\n=== VALIDACIÓN CON DATOS EXPERIMENTALES ===")
    print("(Comparar con resultados reales de scaling_results.csv)")
    
    # Predicción para configuración experimental típica
    N_exp = 4096
    p_exp = 4
    n_steps_exp = 16589  # Valor observado en los logs
    
    t_pred = predictor.t_parallel(N_exp, p_exp, n_steps_exp)
    speedup_pred = predictor.speedup_strong(N_exp, p_exp, n_steps_exp)
    eff_pred = predictor.efficiency_strong(N_exp, p_exp, n_steps_exp)
    
    print(f"\nPredicción para N={N_exp}, p={p_exp}, steps={n_steps_exp}:")
    print(f"Tiempo predicho: {t_pred:.2f} segundos")
    print(f"Speedup predicho: {speedup_pred:.2f}")
    print(f"Eficiencia predicha: {eff_pred:.2%}")

if __name__ == "__main__":
    generate_predictions() 