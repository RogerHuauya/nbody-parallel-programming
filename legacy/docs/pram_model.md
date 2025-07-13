# Modelo PRAM para Simulador N-Cuerpos

## Tarea a: Modelo Teórico PRAM

### Resumen del Algoritmo

El simulador N-cuerpos resuelve el sistema de N partículas interactuando gravitacionalmente usando el integrador de Hermite. El algoritmo principal consiste en:

1. **Cálculo de fuerzas**: Para cada partícula, calcular la fuerza gravitacional ejercida por todas las demás partículas
2. **Integración temporal**: Actualizar posiciones y velocidades usando el método de Hermite
3. **Comunicación MPI**: Distribuir partículas entre procesos y sincronizar resultados

### Modelo PRAM

#### Definición del Modelo

**PRAM (Parallel Random Access Machine)** es un modelo teórico de computación paralela que considera:
- **N**: Número de partículas
- **P**: Número de procesadores
- **T**: Número de pasos temporales

#### Análisis de Complejidad

##### 1. Cálculo de Fuerzas (Parte más costosa)

**Secuencial**: O(N²) por paso temporal
- Para cada partícula i (N iteraciones)
- Calcular fuerza de cada partícula j ≠ i (N-1 iteraciones)
- Cada cálculo de fuerza es O(1)

**Paralelo con P procesadores**:
- Distribución: N/P partículas por procesador
- Cada procesador calcula fuerzas para sus N/P partículas
- Complejidad local: O(N²/P) por procesador
- **Tiempo paralelo**: O(N²/P)

##### 2. Comunicación MPI

**Broadcast de posiciones**:
- Cada procesador necesita conocer posiciones de todas las partículas
- Comunicación all-to-all o broadcast
- **Tiempo de comunicación**: O(N log P) usando algoritmos eficientes

**Reducción de fuerzas**:
- Combinar fuerzas calculadas por diferentes procesadores
- **Tiempo de reducción**: O(N log P)

##### 3. Integración Temporal

**Secuencial**: O(N) por paso temporal
- Para cada partícula: actualizar posición y velocidad

**Paralelo**:
- N/P partículas por procesador
- **Tiempo paralelo**: O(N/P)

#### Complejidad Total por Paso Temporal

**Secuencial**: T_seq = O(N²)

**Paralelo**: T_par = O(N²/P + N log P)

**Speedup Teórico**: S_p = T_seq / T_par = N² / (N²/P + N log P)

**Eficiencia**: E_p = S_p / P = N² / (N² + P·N log P)

#### Análisis de Escalabilidad

##### Escalabilidad Fuerte (N fijo, P variable)

Para N fijo y P creciente:
- **Speedup máximo**: Limitado por el término de comunicación N log P
- **Eficiencia**: Decrece como E_p ≈ N / (N + P log P)
- **Procesadores óptimos**: P_opt ≈ N / log N

##### Escalabilidad Débil (N/P fijo, N y P crecen proporcionalmente)

Para N/P = constante:
- **Tiempo paralelo**: O(N²/P) + O(N log P) = O(N²/P) + O((N/P)·P log P)
- **Escalabilidad**: Buena mientras N²/P >> N log P
- **Condición**: N/P >> log P

#### Limitaciones del Modelo

1. **Comunicación**: El modelo asume comunicación instantánea
2. **Balanceo de carga**: Asume distribución uniforme perfecta
3. **Memoria**: No considera limitaciones de memoria
4. **Latencia**: Ignora latencia de comunicación

#### Predicciones del Modelo

##### Para N = 1000, 5000, 10000 partículas:

**N = 1000**:
- P_opt ≈ 1000 / log(1000) ≈ 145 procesadores
- Speedup máximo ≈ 145 (ideal)
- Eficiencia > 50% para P < 70

**N = 5000**:
- P_opt ≈ 5000 / log(5000) ≈ 586 procesadores
- Speedup máximo ≈ 586 (ideal)
- Eficiencia > 50% para P < 300

**N = 10000**:
- P_opt ≈ 10000 / log(10000) ≈ 1085 procesadores
- Speedup máximo ≈ 1085 (ideal)
- Eficiencia > 50% para P < 540

### Implementación del Modelo

#### Pseudocódigo PRAM

```
ALGORITMO N-CUERPOS PRAM
Input: N partículas, P procesadores, T pasos temporales
Output: Evolución temporal del sistema

Para cada procesador p de 0 a P-1:
    // Inicialización
    particulas_locales = N/P
    inicio_local = p * (N/P)
    fin_local = (p+1) * (N/P)
    
    Para t = 0 a T-1:
        // Comunicación: Broadcast de posiciones
        MPI_Allgather(posiciones_locales, posiciones_globales)
        
        // Cálculo de fuerzas (O(N²/P))
        Para i = inicio_local a fin_local:
            fuerza[i] = 0
            Para j = 0 a N-1:
                Si i ≠ j:
                    fuerza[i] += calcular_fuerza(particula[i], particula[j])
        
        // Integración temporal local (O(N/P))
        Para i = inicio_local a fin_local:
            integrar_hermite(particula[i], fuerza[i], dt)
        
        // Sincronización opcional
        MPI_Barrier()
```

#### Optimizaciones Consideradas

1. **Comunicación Asíncrona**: Overlap comunicación-cómputo
2. **Distribución Adaptativa**: Balanceo dinámico de carga
3. **Métodos Aproximados**: Algoritmos O(N log N) como Barnes-Hut
4. **Jerarquía de Memoria**: Optimización de cache

### Validación Experimental

El modelo PRAM será validado comparando:
- Speedup teórico vs medido
- Eficiencia predicha vs observada
- Escalabilidad fuerte y débil

### Conclusiones del Modelo

1. **Limitación Principal**: Comunicación O(N log P)
2. **Regime Eficiente**: N²/P >> N log P
3. **Escalabilidad**: Buena para problemas grandes
4. **Aplicabilidad**: Sistemas con N > 1000 partículas

Este modelo PRAM proporciona una base teórica para entender y predecir el comportamiento paralelo del simulador N-cuerpos, siendo especialmente útil para guiar la optimización y el dimensionamiento de experimentos. 