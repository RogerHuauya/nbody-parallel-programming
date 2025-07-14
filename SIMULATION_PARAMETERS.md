# N-Body Simulation Parameters Guide

## Configuration File Format

The simulation reads parameters from `phi-GPU4.cfg` (or `phi-GPU6.cfg`, `phi-GPU8.cfg` depending on the integrator order). The file format is:

```
eps t_end dt_disk dt_contr eta eta_BH input_file
```

## Parameter Descriptions

### 1. **eps** (Softening Parameter)
- **Type**: double
- **Typical value**: 0.01
- **Purpose**: Prevents singularities when particles get too close
- **How it's used**: 
  ```c++
  eps2 = eps * eps;  // Used in force calculations
  ```
- **Effect**: Larger values = smoother interactions, smaller values = more accurate but potentially unstable

### 2. **t_end** (End Time)
- **Type**: double
- **Typical value**: 1.0 - 10.0
- **Purpose**: Total simulation time in N-body units
- **How it's used**:
  ```c++
  while(time_cur < t_end) {
      // Main simulation loop
  }
  ```
- **Effect**: Controls how long the simulation runs

### 3. **dt_disk** (Disk Output Interval)
- **Type**: double
- **Typical value**: 0.01 - 0.1
- **Purpose**: Time interval between snapshot outputs
- **How it's used**:
  ```c++
  if(time_cur >= dt_disk * diskstep) {
      outputsnap();  // Save snapshot
      diskstep++;
  }
  ```
- **Effect**: Smaller values = more frequent snapshots = smoother animation but larger disk usage

### 4. **dt_contr** (Control Output Interval)
- **Type**: double
- **Typical value**: 0.05 - 0.1
- **Purpose**: Time interval for energy/momentum conservation checks
- **How it's used**:
  ```c++
  if(time_cur >= dt_contr * contrstep) {
      energy(myRank);  // Check conservation
      contrstep++;
  }
  ```
- **Effect**: Controls frequency of diagnostic outputs

### 5. **eta** (Time Step Parameter)
- **Type**: double
- **Typical value**: 0.02
- **Purpose**: Controls accuracy of time step calculation
- **How it's used**:
  ```c++
  dt = eta * sqrt(eps2 / acceleration);  // Simplified
  ```
- **Effect**: Smaller values = smaller time steps = more accurate but slower

### 6. **eta_BH** (Binary/Black Hole Time Step Parameter)
- **Type**: double
- **Typical value**: 0.02
- **Purpose**: Special time step parameter for close encounters or binary systems
- **How it's used**: Applied when particles are very close to ensure accuracy
- **Effect**: Prevents integration errors in tight binaries

### 7. **input_file** (Input Data File)
- **Type**: string
- **Typical value**: "data.inp"
- **Purpose**: Specifies the file containing initial conditions
- **Format**:
  ```
  diskstep N_particles time_current
  id1 mass1 x1 y1 z1 vx1 vy1 vz1
  id2 mass2 x2 y2 z2 vx2 vy2 vz2
  ...
  ```

## Example Configuration

### For Quick Test (N=1024, fast):
```
0.01 1.0 0.01 0.05 0.02 0.02 data.inp
```
- Runs for 1 time unit
- Saves snapshots every 0.01 time units (100 snapshots)
- Good for testing

### For Production Run (N=4096, accurate):
```
0.001 10.0 0.05 0.1 0.01 0.01 data.inp
```
- Runs for 10 time units
- More accurate (smaller eps and eta)
- Saves snapshots every 0.05 time units (200 snapshots)

### For Real-time Visualization (variable by processors):
```bash
# In realtime_simulation.sh
if [ $PROC -eq 1 ]; then
    T_END=5.0      # Longer simulation for P=1
    DT_DISK=0.05   # Less frequent snapshots
elif [ $PROC -eq 8 ]; then
    T_END=1.0      # Shorter simulation for P=8 
    DT_DISK=0.01   # More frequent snapshots
fi
```

## Time Units in N-Body Simulations

In N-body units:
- G (gravitational constant) = 1
- M (total mass) = 1
- R (characteristic radius) = 1

This means:
- 1 time unit ≈ crossing time of the system
- For a galaxy: 1 time unit ≈ 100 million years
- For a star cluster: 1 time unit ≈ 1 million years

## Tips for Parameter Selection

1. **For visualization**: Use larger `dt_disk` (0.05-0.1) to avoid too many files
2. **For accuracy studies**: Use smaller `eps` and `eta` values
3. **For performance tests**: Keep parameters constant, vary only processors
4. **For stability**: If simulation crashes, increase `eps` or decrease `eta`

## Reading Parameters in Code

The C++ code reads the configuration file like this:

```c++
// Open appropriate config file based on integrator order
std::ifstream ifs("phi-GPU4.cfg");

// Read all parameters in order
ifs >> eps >> t_end >> dt_disk >> dt_contr >> eta >> eta_BH >> inp_fname;

// Then open and read the input data file
std::ifstream inp(inp_fname);
inp >> diskstep >> nbody >> time_cur;

// Read particle data
for(int i=0; i<nbody; i++){
    inp >> p.id >> p.mass >> p.pos >> p.vel;
}
```

This configuration system allows flexible control over simulation accuracy, duration, and output frequency. 