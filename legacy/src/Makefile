# Makefile para proyecto N-Cuerpos con MPI
# Basado en el Makefile original del profesor

# Configuración de CUDA (ajustar según tu sistema)
CUDA_PATH?=/usr/local/cuda
SDK_PATH?=/usr/local/cuda/samples/common/inc

# Detectar sistema operativo
UNAME_S := $(shell uname -s)

# Compilador y flags
NVCC=nvcc -arch=sm_30 -I. -Xcompiler "-Wall -O3"
CXXFLAGS = -O3 -Wall
CFLAGS = -O3 -Wall
MPICC = mpicxx

# Configuración específica del sistema
ifeq ($(UNAME_S),Darwin)
    # macOS - clang no soporta -fopenmp por defecto
    CXXFLAGS += 
    CFLAGS += 
else
    # Linux - gcc soporta -fopenmp
    CXXFLAGS += -fopenmp
    CFLAGS += -fopenmp
endif

# Targets principales
all: gen-plum cpu-4th cpu-6th cpu-8th

# Verificar si CUDA está disponible
cuda-check:
	@which nvcc >/dev/null 2>&1 && echo "CUDA disponible" || echo "CUDA no disponible, solo CPU"

# Generar condiciones iniciales
gen-plum: gen-plum.c
	gcc $(CFLAGS) -o $@ $< -lm

# Versiones CPU
cpu-4th: phi-GPU.cpp hermite4.h
	$(MPICC) $(CXXFLAGS) -DFOURTH -o $@ $<

cpu-6th: phi-GPU.cpp hermite6.h
	$(MPICC) $(CXXFLAGS) -DSIXTH -o $@ $<

cpu-8th: phi-GPU.cpp hermite8.h
	$(MPICC) $(CXXFLAGS) -DEIGHTH -o $@ $<

# Versiones GPU (solo si CUDA está disponible)
gpu-4th: phi-GPU.cpp hermite4-gpu.o
	$(MPICC) $(CXXFLAGS) -DFOURTH -DGPU -I$(CUDA_PATH)/include -L$(CUDA_PATH)/lib64 -lcudart -o $@ $^

gpu-6th: phi-GPU.cpp hermite6-gpu.o
	$(MPICC) $(CXXFLAGS) -DSIXTH -DGPU -I$(CUDA_PATH)/include -L$(CUDA_PATH)/lib64 -lcudart -o $@ $^

gpu-8th: phi-GPU.cpp hermite8-gpu.o
	$(MPICC) $(CXXFLAGS) -DEIGHTH -DGPU -I$(CUDA_PATH)/include -L$(CUDA_PATH)/lib64 -lcudart -o $@ $^

# Compilación de archivos CUDA
hermite4-gpu.o: hermite4-gpu.cu hermite4-gpu.h
	$(NVCC) -c $<

hermite6-gpu.o: hermite6-gpu.cu hermite6-gpu.h
	$(NVCC) -c $<

hermite8-gpu.o: hermite8-gpu.cu hermite8-gpu.h
	$(NVCC) -c $<

# Limpieza
clean:
	rm -f *.o gen-plum cpu-4th cpu-6th cpu-8th gpu-4th gpu-6th gpu-8th
	rm -f *.dat data.inp data.con

# Targets para generar datos de ejemplo
data-small: gen-plum
	./gen-plum 1000 1

data-medium: gen-plum
	./gen-plum 5000 1

data-large: gen-plum
	./gen-plum 10000 1

# Target para pruebas rápidas
test: gen-plum cpu-4th data-small
	mpirun -np 2 ./cpu-4th

# Información del sistema
info:
	@echo "Información del sistema:"
	@echo "Sistema: $(UNAME_S)"
	@echo "MPI: $(shell which mpicc 2>/dev/null || echo 'No encontrado')"
	@echo "CUDA: $(shell which nvcc 2>/dev/null || echo 'No encontrado')"
	@echo "Procesadores: $(shell nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'Desconocido')"

.PHONY: all clean test info cuda-check data-small data-medium data-large 