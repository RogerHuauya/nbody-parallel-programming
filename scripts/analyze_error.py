#!/usr/bin/env python3
"""
Análisis de precisión para simulador N-cuerpos
Tarea c: Análisis de error y conservación de energía
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import glob

def read_snapshot(filename):
    """Lee un snapshot del simulador N-cuerpos"""
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
            pos = [float(parts[2]), float(parts[3]), float(parts[4])]
            vel = [float(parts[5]), float(parts[6]), float(parts[7])]
            
            particles.append({
                'id': particle_id,
                'mass': mass,
                'pos': np.array(pos),
                'vel': np.array(vel)
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

def calculate_energy(particles):
    """Calcula la energía total del sistema"""
    n = len(particles)
    
    # Energía cinética
    kinetic_energy = 0.0
    for p in particles:
        v_squared = np.sum(p['vel']**2)
        kinetic_energy += 0.5 * p['mass'] * v_squared
    
    # Energía potencial
    potential_energy = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            r_vec = particles[i]['pos'] - particles[j]['pos']
            r = np.linalg.norm(r_vec)
            if r > 0:  # Evitar división por cero
                potential_energy -= particles[i]['mass'] * particles[j]['mass'] / r
    
    return kinetic_energy, potential_energy, kinetic_energy + potential_energy

def calculate_momentum(particles):
    """Calcula el momento lineal total del sistema"""
    total_momentum = np.zeros(3)
    total_mass = 0.0
    
    for p in particles:
        total_momentum += p['mass'] * p['vel']
        total_mass += p['mass']
    
    return total_momentum, total_mass

def calculate_angular_momentum(particles):
    """Calcula el momento angular total del sistema"""
    total_angular_momentum = np.zeros(3)
    
    for p in particles:
        r_cross_v = np.cross(p['pos'], p['vel'])
        total_angular_momentum += p['mass'] * r_cross_v
    
    return total_angular_momentum

def analyze_conservation(data_dir, output_dir):
    """Analiza la conservación de energía y momento"""
    
    # Buscar archivos de snapshot
    snapshot_files = sorted(glob.glob(os.path.join(data_dir, "*.dat")))
    
    if not snapshot_files:
        print(f"No se encontraron archivos .dat en {data_dir}")
        return
    
    print(f"Analizando {len(snapshot_files)} snapshots...")
    
    # Arrays para almacenar resultados
    times = []
    kinetic_energies = []
    potential_energies = []
    total_energies = []
    momenta = []
    angular_momenta = []
    
    # Procesar cada snapshot
    for filename in snapshot_files:
        snapshot = read_snapshot(filename)
        if snapshot is None:
            continue
        
        # Calcular cantidades conservadas
        ke, pe, te = calculate_energy(snapshot['particles'])
        momentum, total_mass = calculate_momentum(snapshot['particles'])
        angular_momentum = calculate_angular_momentum(snapshot['particles'])
        
        times.append(snapshot['time'])
        kinetic_energies.append(ke)
        potential_energies.append(pe)
        total_energies.append(te)
        momenta.append(np.linalg.norm(momentum))
        angular_momenta.append(np.linalg.norm(angular_momentum))
    
    if not times:
        print("No se pudieron procesar los snapshots")
        return
    
    # Convertir a arrays numpy
    times = np.array(times)
    kinetic_energies = np.array(kinetic_energies)
    potential_energies = np.array(potential_energies)
    total_energies = np.array(total_energies)
    momenta = np.array(momenta)
    angular_momenta = np.array(angular_momenta)
    
    # Calcular errores relativos
    E0 = total_energies[0]
    p0 = momenta[0]
    L0 = angular_momenta[0]
    
    energy_error = np.abs((total_energies - E0) / E0) if E0 != 0 else np.zeros_like(total_energies)
    momentum_error = np.abs((momenta - p0) / p0) if p0 != 0 else np.zeros_like(momenta)
    angular_momentum_error = np.abs((angular_momenta - L0) / L0) if L0 != 0 else np.zeros_like(angular_momenta)
    
    # Generar reporte
    print("\n=== ANÁLISIS DE CONSERVACIÓN ===")
    print(f"Tiempo de simulación: {times[0]:.3f} - {times[-1]:.3f}")
    print(f"Energía inicial: {E0:.6e}")
    print(f"Energía final: {total_energies[-1]:.6e}")
    print(f"Error relativo de energía: {energy_error[-1]:.6e}")
    print(f"Error máximo de energía: {np.max(energy_error):.6e}")
    print(f"Error RMS de energía: {np.sqrt(np.mean(energy_error**2)):.6e}")
    
    print(f"\nMomento inicial: {p0:.6e}")
    print(f"Momento final: {momenta[-1]:.6e}")
    print(f"Error máximo de momento: {np.max(momentum_error):.6e}")
    
    print(f"\nMomento angular inicial: {L0:.6e}")
    print(f"Momento angular final: {angular_momenta[-1]:.6e}")
    print(f"Error máximo de momento angular: {np.max(angular_momentum_error):.6e}")
    
    # Generar gráficos
    generate_conservation_plots(times, kinetic_energies, potential_energies, total_energies,
                              momenta, angular_momenta, energy_error, momentum_error,
                              angular_momentum_error, output_dir)
    
    # Guardar datos para análisis posterior
    results_df = pd.DataFrame({
        'time': times,
        'kinetic_energy': kinetic_energies,
        'potential_energy': potential_energies,
        'total_energy': total_energies,
        'momentum': momenta,
        'angular_momentum': angular_momenta,
        'energy_error': energy_error,
        'momentum_error': momentum_error,
        'angular_momentum_error': angular_momentum_error
    })
    
    results_df.to_csv(os.path.join(output_dir, 'conservation_analysis.csv'), index=False)
    
    return results_df

def generate_conservation_plots(times, ke, pe, te, momentum, angular_momentum,
                               energy_error, momentum_error, angular_momentum_error, output_dir):
    """Genera gráficos de análisis de conservación"""
    
    plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
    
    # Gráfico 1: Evolución de energías
    plt.figure(figsize=(12, 8))
    plt.subplot(2, 2, 1)
    plt.plot(times, ke, 'b-', label='Energía cinética', linewidth=2)
    plt.plot(times, pe, 'r-', label='Energía potencial', linewidth=2)
    plt.plot(times, te, 'g-', label='Energía total', linewidth=2)
    plt.xlabel('Tiempo')
    plt.ylabel('Energía')
    plt.title('Evolución de las Energías')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Gráfico 2: Error de energía
    plt.subplot(2, 2, 2)
    plt.semilogy(times, energy_error, 'g-', linewidth=2)
    plt.xlabel('Tiempo')
    plt.ylabel('Error relativo de energía')
    plt.title('Error de Conservación de Energía')
    plt.grid(True, alpha=0.3)
    
    # Gráfico 3: Error de momento
    plt.subplot(2, 2, 3)
    plt.semilogy(times, momentum_error, 'b-', linewidth=2)
    plt.xlabel('Tiempo')
    plt.ylabel('Error relativo de momento')
    plt.title('Error de Conservación de Momento')
    plt.grid(True, alpha=0.3)
    
    # Gráfico 4: Error de momento angular
    plt.subplot(2, 2, 4)
    plt.semilogy(times, angular_momentum_error, 'r-', linewidth=2)
    plt.xlabel('Tiempo')
    plt.ylabel('Error relativo de momento angular')
    plt.title('Error de Conservación de Momento Angular')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'conservation_analysis.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfico adicional: Comparación de errores
    plt.figure(figsize=(10, 6))
    plt.semilogy(times, energy_error, 'g-', label='Error de energía', linewidth=2)
    plt.semilogy(times, momentum_error, 'b-', label='Error de momento', linewidth=2)
    plt.semilogy(times, angular_momentum_error, 'r-', label='Error de momento angular', linewidth=2)
    plt.xlabel('Tiempo')
    plt.ylabel('Error relativo')
    plt.title('Comparación de Errores de Conservación')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'error_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\nGráficos de conservación generados en: {output_dir}")
    print("- conservation_analysis.png")
    print("- error_comparison.png")

def compare_integration_orders(orders_data, output_dir):
    """Compara diferentes órdenes de integración"""
    
    plt.figure(figsize=(15, 10))
    
    for i, (order, data) in enumerate(orders_data.items()):
        plt.subplot(2, 3, i+1)
        plt.semilogy(data['time'], data['energy_error'], linewidth=2, label=f'Orden {order}')
        plt.xlabel('Tiempo')
        plt.ylabel('Error relativo de energía')
        plt.title(f'Integrador de Orden {order}')
        plt.grid(True, alpha=0.3)
    
    # Comparación directa
    plt.subplot(2, 3, len(orders_data)+1)
    for order, data in orders_data.items():
        plt.semilogy(data['time'], data['energy_error'], linewidth=2, label=f'Orden {order}')
    plt.xlabel('Tiempo')
    plt.ylabel('Error relativo de energía')
    plt.title('Comparación de Órdenes')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'integration_order_comparison.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Comparación de órdenes guardada en: {output_dir}/integration_order_comparison.png")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 analyze_error.py <directorio_datos> [directorio_salida]")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    os.makedirs(output_dir, exist_ok=True)
    
    analyze_conservation(data_dir, output_dir) 