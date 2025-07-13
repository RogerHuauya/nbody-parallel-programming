# Sistema de Visualización N-Body en Tiempo Real

Este sistema permite ejecutar múltiples simulaciones N-Body en paralelo y visualizarlas en tiempo real mientras se ejecutan.

## Componentes

1. **`realtime_simulation.sh`** - Script bash que ejecuta las simulaciones en paralelo
2. **`realtime_visualizer.py`** - Visualizador 3D que actualiza en tiempo real
3. **`realtime_control.py`** - Script de control integrado (recomendado)

## Instalación Rápida

```bash
# Instalar dependencias Python adicionales
pip install psutil matplotlib numpy pandas

# Hacer ejecutables los scripts
chmod +x realtime_simulation.sh
chmod +x realtime_control.py
chmod +x realtime_visualizer.py
```

## Uso

### Opción 1: Sistema Integrado (Recomendado)

```bash
python realtime_control.py
```

Esto:
- Verifica todas las dependencias
- Inicia las simulaciones en paralelo
- Abre automáticamente el visualizador 3D
- Monitorea el uso de recursos
- Permite ver comparación final

### Opción 2: Ejecución Manual

En una terminal:
```bash
# Ejecutar simulaciones (con 2 procesadores)
./realtime_simulation.sh 2
```

En otra terminal:
```bash
# Iniciar visualizador
python realtime_visualizer.py
```

Para ver comparación final:
```bash
python realtime_visualizer.py --final
```

## Estructura de Directorios

```
realtime_simulations/
├── N_1KB/               # N=1024 partículas
│   ├── data.inp         # Condiciones iniciales
│   ├── phi-GPU4.cfg     # Configuración
│   ├── output.log       # Log de simulación
│   ├── status.txt       # Estado (RUNNING/COMPLETED)
│   ├── current_step.txt # Snapshot actual
│   └── snapshots/       # Directorio de snapshots
│       ├── snapshot_0000.dat
│       ├── snapshot_0001.dat
│       └── ...
├── N_2KB/               # N=2048 partículas
├── N_4KB/               # N=4096 partículas
├── N_8KB/               # N=8192 partículas
└── info.json            # Información general
```

## Características del Visualizador

- **Vista 2x2**: Muestra las 4 simulaciones simultáneamente
- **Actualización en tiempo real**: Se actualiza conforme se generan snapshots
- **Trayectorias**: Muestra las últimas 5 posiciones de partículas seleccionadas
- **Control de velocidad**: Slider para ajustar velocidad de rotación
- **Información de estado**: Muestra snapshot actual y estado de cada simulación

## Parámetros de Simulación

Configurables en `realtime_simulation.sh`:
- `PROCESSORS`: Número de procesadores MPI (default: 2)
- `SIZES`: Tamaños N a simular (default: 1, 2, 4, 8)
- `dt_disk`: Frecuencia de snapshots (default: 0.01)
- `t_end`: Tiempo final de simulación (default: 10.0)

## Optimización

Para mejor rendimiento:
1. Usa menos procesadores si el sistema está sobrecargado
2. Aumenta `dt_disk` para menos snapshots (menos I/O)
3. Reduce `t_end` para simulaciones más cortas

## Solución de Problemas

1. **"No se encuentran snapshots"**
   - Espera a que las simulaciones generen datos
   - Verifica que `realtime_simulations/` existe

2. **Visualizador muy lento**
   - Reduce el número de partículas mostradas
   - Aumenta el intervalo de actualización

3. **Error de MPI**
   - Verifica: `which mpirun`
   - Instala: `sudo apt install mpich`

## Ejemplo de Uso Completo

```bash
# 1. Limpiar ejecuciones anteriores (opcional)
rm -rf realtime_simulations/

# 2. Ejecutar sistema completo
python realtime_control.py

# 3. Ingresa número de procesadores (ej: 4)
# 4. Observa la visualización en tiempo real
# 5. Al finalizar, opcionalmente ve la comparación final
```

## Interpretación de Resultados

- **Colores**: Representan la masa de las partículas
- **Tamaño**: Proporcional a la masa
- **Trayectorias blancas**: Muestran el movimiento reciente
- **Rotación automática**: Para mejor visualización 3D

¡Disfruta viendo la evolución de los sistemas gravitacionales en tiempo real! 