---
title: Partitioning and Parallel Execution
icon: material/cpu-64-bit
---

# Partitioning and Parallel Execution

Large-scale finite element simulations with hundreds of thousands of elements can be solved concurrently by dividing the mesh into balanced subdomains.

---

## Mental Model

* **Mesh Partitioning**: The process of dividing a global finite element mesh into smaller, balanced sub-grids (subdomains) that can be solved concurrently.
* **Parallel Execution**: Running the simulation across multiple CPU cores or processes using parallel-solver binaries (such as `OpenSeesSP` or `OpenSeesMP`).

Think of mesh partitioning as dividing a large construction project among several distinct labor crews. To finish the project efficiently, you must split the work so that:
1. Every crew has roughly the same amount of work (load balancing).
2. The communication between crews is kept to a minimum (minimizing boundary node sharing).

Femora automates this by executing spatial partitioning algorithms (like `kd-tree`, `morton`, or `geometric` partitioning) during the assembly phase.

---

## Where It Fits

Partitioning is configured during the assembly definition phase, ensuring the global mesh is split before exporting the solver commands or configuring parallel steps:

```text
Define Mesh Parts
  └─ Define Assembly Section with num_partitions and partitioner
       └─ [Run Assembler: assemble()]  <-- Mesh is divided, Core IDs assigned
            └─ Export to parallel-compatible solver scripts
```

---

## Minimal Example

Configuring an assembly section to partition the model into 4 subdomains using a kd-tree algorithm:

```python
from femora.core.model import Model

model = Model()

# (Define materials, elements, soil_box part, etc...)

# Partitioning is configured at the Assembly Section level
model.assembler.create_section(
    meshparts=["soil_domain"],
    num_partitions=4,
    partitioner="kd-tree"
)

# Compile and partition the global mesh
model.assembler.assemble()

# Plot the mesh and color it by Core ID to verify partition domains
model.assembler.plot(scalars="Core", show_edges=True)
```

Refer to the [Assembler API Reference](../reference/core/assembler.md) for options.

---

## What Femora Stores

For partitioning, Femora tracks:
- **`num_partitions`**: The requested number of parallel subdomains.
- **`partitioner`**: The algorithm used to divide the nodes and elements (e.g. `kd-tree`, `morton`, `geometric`).
- **`Core` cell data**: Array containing partition indices for parallel execution support.

---

## Common Mistakes

???+ warning "Attempting to Partition Individual Mesh Parts"
    A common mistake is trying to partition an individual `MeshPart` instance. Mesh parts are coordinate-isolated. Partitioning must occur at the **Assembly Section** level, where the global topology and connectivity are known.

???+ warning "Parallel Solver Compatibility"
    Running partitioned models requires a parallel-capable solver binary (such as `OpenSeesSP` or `OpenSeesMP`). If you attempt to execute a partitioned model on a standard single-process `OpenSees` binary, the partitioning metadata will be ignored or cause execution errors.

---

## Related Concepts

* [Assembly](assembly.md): Learn how the compile phase assigns partition Core IDs.
* [Process and Analysis](process-and-analysis.md): Understand solver execution.
