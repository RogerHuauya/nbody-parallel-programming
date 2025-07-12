import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import glob
import time
from joblib import Parallel, delayed

# --- Parámetros de Configuración ---
NUM_PARTICULAS_A_MOSTRAR = 2048  # Muestra solo una fracción para que sea más rápido
ARCHIVOS_DAT = sorted(glob.glob('*.dat')) # Encuentra todos los archivos .dat
NUM_PROCESOS_PARALELOS = 4 # Número de núcleos de CPU a usar
# ----------------------------------

print(f"Se encontraron {len(ARCHIVOS_DAT)} archivos de snapshots.")

# Función para leer un solo archivo .dat
def leer_snapshot(filename):
    """Lee las posiciones de las partículas de un archivo de snapshot."""
    try:
        # Saltar las 3 primeras líneas de cabecera
        # Leer las columnas 3, 4 y 5 (pos_x, pos_y, pos_z)
        data = np.loadtxt(filename, skiprows=3, usecols=(2, 3, 4))
        if data.shape[0] > NUM_PARTICULAS_A_MOSTRAR:
            return data[:NUM_PARTICULAS_A_MOSTRAR, :]
        return data
    except Exception as e:
        print(f"Error leyendo {filename}: {e}")
        return None

# Función que genera un frame (una imagen) de la animación
def generar_frame(i, datos, scatter):
    """Actualiza los datos del gráfico para el frame i."""
    puntos = datos[i]
    if puntos is not None:
        # Actualiza las posiciones de los puntos en el gráfico 3D
        scatter._offsets3d = (puntos[:, 0], puntos[:, 1], puntos[:, 2])
        ax.set_title(f'Evolución del Cúmulo - Tiempo {i+1:03d}')
    return scatter,

# --- Ejecución y Medición de Tiempos ---

print("Leyendo datos de simulación en paralelo...")
start_time = time.time()

# Usar Joblib para leer los archivos en paralelo
datos_snapshots = Parallel(n_jobs=NUM_PROCESOS_PARALELOS)(delayed(leer_snapshot)(f) for f in ARCHIVOS_DAT)

end_time = time.time()
print(f"Lectura de datos completada en {end_time - start_time:.2f} segundos usando {NUM_PROCESOS_PARALELOS} procesos.")

# --- Creación de la Animación ---

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(projection='3d')

# Configuración inicial del gráfico con el primer snapshot
puntos_iniciales = datos_snapshots[0]
scatter = ax.scatter(puntos_iniciales[:, 0], puntos_iniciales[:, 1], puntos_iniciales[:, 2], s=1, c='cyan', marker='o')

# Configuración de los ejes
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_facecolor('black')
ax.grid(False)

# Crear la animación
print("Creando animación...")
ani = animation.FuncAnimation(fig, generar_frame, frames=len(datos_snapshots), fargs=(datos_snapshots, scatter), blit=False, interval=50)

# Guardar la animación como un video MP4
start_time_anim = time.time()
ani.save('nbody_simulation.mp4', writer='ffmpeg', fps=15, dpi=150)
end_time_anim = time.time()

print(f"\n¡Animación guardada como 'nbody_simulation.mp4'!")
print(f"Tiempo total para generar el video: {end_time_anim - start_time_anim:.2f} segundos.")