CUDA_PATH=/usr/local/cuda
SDK_PATH=/usr/local/cuda/samples/common/inc
NVCC=nvcc -arch=sm_86 -I. -Xcompiler "-Wall -O3"

###CUDA_PATH=/export/opt/cuda
###SDK_PATH=/export/opt/cuda/NVIDIA_CUDA_SDK

###CUDA_PATH=/usr/local/cuda
###SDK_PATH=/usr/local/NVIDIA_CUDA_SDK

CXXFLAGS = -O3 -Wall 
###-fopenmp

# Create bin directory
BIN_DIR = bin

all: $(BIN_DIR) gpu-4th gpu-6th gpu-8th cpu-4th gen-plum

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

asm: gpu-4th.s gpu-6th.s gpu-8th.s

cubin: hermite4-gpu.cubin hermite6-gpu.cubin hermite8-gpu.cubin

cpu: cpu-4th cpu-6th cpu-8th

clean:
	rm -f *.o *.s *.cubin .*.swp
	rm -rf $(BIN_DIR)

# Data generation executable
gen-plum: gen-plum.c
	gcc -O3 -Wall -o $(BIN_DIR)/gen-plum $< -lm

# GPU executables
gpu-8th: phi-GPU.cpp hermite8-gpu.o
	mpicxx $(CXXFLAGS) -DEIGHTH -DGPU -I$(CUDA_PATH)/include -L$(CUDA_PATH)/lib64 -lcudart -o $(BIN_DIR)/$@ $^

gpu-6th: phi-GPU.cpp hermite6-gpu.o
	mpicxx $(CXXFLAGS) -DSIXTH -DGPU -I$(CUDA_PATH)/include -L$(CUDA_PATH)/lib64 -lcudart -o $(BIN_DIR)/$@ $^

gpu-4th: phi-GPU.cpp hermite4-gpu.o
	mpicxx $(CXXFLAGS) -DFOURTH -DGPU -I$(CUDA_PATH)/include -L$(CUDA_PATH)/lib64 -L/usr/lib/x86_64-linux-gnu -lcudart -lcuda -o $(BIN_DIR)/$@ $^

# Assembly files
gpu-8th.s: phi-GPU.cpp
	mpicxx $(CXXFLAGS) -DEIGHTH -DGPU -I$(CUDA_PATH)/include  -S -o $@ $<

gpu-6th.s: phi-GPU.cpp
	mpicxx $(CXXFLAGS) -DSIXTH -DGPU -I$(CUDA_PATH)/include  -S -o $@ $<

gpu-4th.s: phi-GPU.cpp
	mpicxx $(CXXFLAGS) -DFOURTH -DGPU -I$(CUDA_PATH)/include  -S -o $@ $<

# CUDA object files
hermite8-gpu.o: hermite8-gpu.cu hermite8-gpu.h
	$(NVCC) -c $<

hermite6-gpu.o: hermite6-gpu.cu hermite6-gpu.h
	$(NVCC) -c $<

hermite4-gpu.o: hermite4-gpu.cu hermite4-gpu.h
	$(NVCC) -c $<

# CUDA cubin files
hermite8-gpu.cubin: hermite8-gpu.cu
	nvcc -I $(SDK_PATH)/common/inc -Xcompiler "-O3" -cubin $<

hermite6-gpu.cubin: hermite6-gpu.cu
	nvcc -I $(SDK_PATH)/common/inc -Xcompiler "-O3" -cubin $<

hermite4-gpu.cubin: hermite4-gpu.cu
	nvcc -I $(SDK_PATH)/common/inc -Xcompiler "-O3" -cubin $<

# CPU executables
cpu-8th: phi-GPU.cpp hermite8.h
	mpicxx $(CXXFLAGS) -DEIGHTH  -o $(BIN_DIR)/$@ $<

cpu-6th: phi-GPU.cpp hermite6.h
	mpicxx $(CXXFLAGS) -DSIXTH  -o $(BIN_DIR)/$@ $<

cpu-4th: phi-GPU.cpp hermite4.h
	mpicxx $(CXXFLAGS) -DFOURTH -o $(BIN_DIR)/$@ $<

# Install target to make executables available in PATH
install: all
	@echo "Executables built in $(BIN_DIR)/"
	@echo "Add $(BIN_DIR) to your PATH or use ./$(BIN_DIR)/executable_name"

.PHONY: all clean install cpu asm cubin $(BIN_DIR)

