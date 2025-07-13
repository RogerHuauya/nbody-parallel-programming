# N-Body Parallel Simulation Project

This project implements a parallel N-Body simulation using MPI and provides comprehensive tools for performance analysis, 3D visualization, and real-time monitoring.

## Project Structure

```
N-Body/
├── cpu-4th                    # CPU version of N-Body simulator
├── gpu-4th                    # GPU version (CUDA)
├── gen-plum                   # Initial conditions generator
├── generate_datasets.sh       # Script to generate data and run scaling tests
├── plot_scaling_analysis.py   # Generate scaling performance plots
├── visualize_nbody_3d.py      # 3D visualization with parallel rendering
├── realtime_simulation.sh     # Execute parallel simulations with real-time snapshots
├── realtime_visualizer.py     # Real-time 3D visualization system
├── realtime_control.py        # Integrated control system for real-time execution
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── REALTIME_README.md        # Documentation for real-time system
├── ANALISIS_MATEMATICO.md    # Mathematical analysis of parallel algorithm
├── ANALISIS_PROCESOS_GRAFICOS.md # Analysis of visualization processes
├── RESUMEN_ANALISIS.md       # Executive summary of mathematical analysis
└── performance_predictor.py   # Performance prediction tool
```

## Installation

### 1. System Requirements

```bash
# Install MPI
sudo apt install mpich

# Install build tools
sudo apt install build-essential

# Install ffmpeg for video generation
sudo apt install ffmpeg

# Install Python dependencies
pip install -r requirements.txt
```

### 2. CUDA (Optional - for GPU version)
If you have an NVIDIA GPU and want to use the GPU version:
- Install CUDA Toolkit 12.4+
- Update paths in Makefile if needed

## Quick Start

### 1. Real-Time Visualization System (NEW!)

The easiest way to see the N-Body simulation in action:

```bash
# Run the integrated control system
python realtime_control.py
```

This will:
- Execute 4 simulations in parallel (N=1024, 2048, 4096, 8192)
- Display real-time 3D visualization with live updates
- Monitor system resources (CPU/RAM usage)
- Generate over 1000 snapshots per simulation
- Allow interactive exploration of results

For more details, see [REALTIME_README.md](REALTIME_README.md)

### 2. Performance Analysis

#### Generate Datasets and Run Scaling Analysis

```bash
# Make scripts executable
chmod +x generate_datasets.sh

# Run the complete scaling analysis
./generate_datasets.sh
```

This will:
- Generate datasets for different N values (1024, 2048, 4096, 8192 particles)
- Run strong scaling tests (fixed N=4096, vary processors: 1, 2, 4)
- Run weak scaling tests (N proportional to processors)
- Save performance data in CSV files

#### Generate Performance Plots

```bash
python plot_scaling_analysis.py
```

This creates:
- `strong_scaling_analysis.png/pdf` - Complete strong scaling analysis
- `weak_scaling_analysis.png/pdf` - Complete weak scaling analysis
- `combined_scaling_analysis.png` - Comparison of both
- `baseline_performance.png` - Performance for different N values

### 3. Standard 3D Visualizations

```bash
python visualize_nbody_3d.py
```

Options:
1. Visualize a specific simulation
2. Run visualization benchmark
3. Create all available visualizations

## Quick Example

Want to see N-Body simulation in action? Just run:

```bash
# See real-time visualization of 4 simulations
python realtime_control.py
```

That's it! The system will:
1. Ask for number of processors (press Enter for default=2)
2. Start 4 simulations in parallel
3. Open a real-time 3D visualization
4. Show system resource usage
5. Generate final comparison when done

## Understanding N

The parameter N controls the number of particles:
- N=1 → 1024 particles (1KB)
- N=2 → 2048 particles (2KB)
- N=4 → 4096 particles (4KB)
- N=8 → 8192 particles (8KB)
- N=16 → 16384 particles (16KB)

## Performance Analysis

### Strong Scaling
- Fixed problem size (N=4096 particles)
- Vary number of processors (1, 2, 4)
- Measures speedup and efficiency

### Weak Scaling
- Problem size scales with processors
- 1024 particles per processor
- Measures scalability

## Output Files

### Real-Time System Output
- `realtime_simulations/N_*KB/snapshots/` - Thousands of simulation snapshots
- `realtime_simulations/N_*KB/output.log` - Simulation logs
- `realtime_simulations/N_*KB/status.txt` - Current simulation status
- `realtime_simulations/final_comparison.png` - Final state comparison
- `realtime_simulations/info.json` - System configuration

### Performance Data
- `performance_data/scaling_results.csv` - All performance measurements
- `performance_data/strong_scaling.csv` - Strong scaling specific data
- `performance_data/weak_scaling.csv` - Weak scaling specific data
- `performance_data/visualization_benchmark.csv` - Rendering performance
- `performance_data/strong_scaling_analysis.png` - Strong scaling plots
- `performance_data/weak_scaling_analysis.png` - Weak scaling plots
- `performance_data/combined_scaling_analysis.png` - Combined analysis
- `performance_data/baseline_performance.png` - Baseline performance

### Visualizations
- `visualizations/nbody_animation_*p.mp4` - 3D animations
- `visualizations/trajectories_*p.png` - Particle trajectories
- `performance_data/visualization_benchmark.png` - Rendering performance

## Running Individual Components

### Generate Initial Conditions
```bash
./gen-plum N NP
# Example: ./gen-plum 4 1  # 4096 particles
```

### Run Simulation
```bash
mpirun -np <processors> ./cpu-4th
```

### Configuration File
Create `phi-GPU4.cfg`:
```
eps t_end dt_disk dt_contr eta eta_BH input_file
```
Example:
```
0.01 1.0 0.1 0.1 0.02 0.02 data.inp
```

## Troubleshooting

1. **MPI errors**: Ensure MPI is properly installed
   ```bash
   which mpirun
   mpirun --version
   ```

2. **Missing data files**: Run `generate_datasets.sh` first

3. **Python import errors**: Install requirements
   ```bash
   pip install -r requirements.txt
   ```

4. **Video generation fails**: Install ffmpeg
   ```bash
   sudo apt install ffmpeg
   ```

## Algorithm Details

The N-Body simulation uses:
- Hermite 4th order integration scheme
- O(N²) direct particle-particle interactions
- MPI for distributed computing
- Optional GPU acceleration with CUDA

### Mathematical Analysis

For detailed mathematical analysis of the parallel algorithm, including:
- Sequential vs Parallel time complexity
- Speedup and Efficiency formulas
- Strong and Weak scaling models
- Performance predictions

See: [ANALISIS_MATEMATICO.md](ANALISIS_MATEMATICO.md)

For analysis of visualization processes:
- Pipeline breakdown and timing
- Parallelization strategies
- Complexity analysis
- Performance optimization

See: [ANALISIS_PROCESOS_GRAFICOS.md](ANALISIS_PROCESOS_GRAFICOS.md)

### Performance Prediction

The project includes a performance prediction tool based on the mathematical model:

```bash
python performance_predictor.py
```

This generates:
- Strong scaling predictions
- Efficiency analysis
- Optimal processor recommendations
- GFlops performance estimates

For a quick summary, see: [RESUMEN_ANALISIS.md](RESUMEN_ANALISIS.md)

## Features Summary

This project provides:

### 🚀 Core Simulation
- **Hermite 4th order** integration scheme
- **MPI parallelization** for distributed computing
- **GPU acceleration** with CUDA (optional)
- **Plummer model** initial conditions

### 📊 Performance Analysis
- **Strong scaling** analysis (fixed problem size)
- **Weak scaling** analysis (proportional problem size)
- **Automated benchmarking** with CSV output
- **Publication-ready plots** with detailed metrics

### 🎨 Visualization
- **Real-time 3D visualization** during simulation
- **Parallel rendering** with joblib
- **Interactive controls** for rotation and speed
- **Trajectory tracking** for selected particles
- **Multi-simulation display** (2x2 grid view)

### 🔧 Advanced Features
- **Automatic snapshot generation** (1000+ per simulation)
- **Resource monitoring** (CPU/RAM usage)
- **Integrated control system** with error handling
- **Configurable parameters** for all components

## Recent Updates

- ✅ Added real-time visualization system
- ✅ Implemented parallel simulation execution
- ✅ Created integrated control interface
- ✅ Added resource monitoring
- ✅ Improved documentation

## Citation

If you use this code for research, please cite the original N-Body algorithm papers and acknowledge the parallel implementation. 