---
title: Process and Analysis
icon: material/cog-play-outline
---

# Process and Analysis

The physical layout of your model is completely decoupled from the numerical algorithms used to solve the finite element equations. Femora manages solver settings and execution sequences using Analysis and Process.

---

## Mental Model

* **Analysis**: The mathematical parameters and algorithms configured to solve the system of equations. This includes defining constraint handlers, numbering schemes, linear equation solvers, convergence test criteria, nonlinear solution algorithms, and time integrators.
* **Process**: An ordered list of steps (recorders, loads, analysis steps) that defines the execution sequence.

Decoupling modeling from execution means you can define your structure once and run different types of analyses on it. For example, you can add a step to run a static gravity analysis, followed by an eigenvalue analysis to find the natural periods of the system, followed by a transient dynamic analysis to simulate an earthquake.

---

## Where It Fits

Process and Analysis represent the final steps of your simulation script. Once the model is assembled, you define analysis components, register them as steps in the process manager, and compile them into a unified solver script:

```text
Run Assembly
  └─ Define static or transient Analysis components
       └─ Add Analysis steps to ProcessManager (model.process.add_step)
            └─ Export Process sequence to TCL (model.export_to_tcl)
```

---

## Minimal Example

Configuring a static gravity analysis followed by a transient dynamic analysis, and adding them to the process:

```python
from femora.core.model import Model

model = Model()

# (Configure and compile assembly here...)

# 1. Define a static analysis step for gravity loading
gravity_analysis = model.analysis.static(
    name="gravity_step",
    load_steps=10
)

# 2. Define a transient dynamic analysis step for earthquake loading
transient_analysis = model.analysis.transient(
    name="seismic_step",
    dt=0.01,
    num_steps=1000,
    algorithm="KrylovNewton"
)

# 3. Add the analysis components to the process sequence
model.process.add_step(gravity_analysis, description="Run gravity analysis")
model.process.add_step(transient_analysis, description="Run dynamic earthquake analysis")
```

For available solution algorithms and parameters, refer to the [Analysis Manager API Reference](../reference/core/analysis_manager.md) and [Process Manager API Reference](../reference/core/process_manager.md).

---

## What Femora Stores

The `ProcessManager` tracks:
- **`steps`**: An ordered list of dictionaries containing references to constraints, patterns, recorders, and analysis steps.
- **`current_step`**: The active step counter during evaluation.

When exporting, Femora iterates through this process list in order, converting each step to its respective solver instructions (e.g. OpenSees TCL commands) and writing them to the output file.

---

## Common Mistakes

???+ warning "Running Analysis Before Assembly"
    You cannot define process steps or configure analysis integrators before calling `model.assembler.assemble()`. The model must be compiled so that solver tags, node coordinates, and element configurations are initialized.

---

## Related Concepts

* [Assembly](assembly.md): Compile the model before configuring solvers.
* [Loads, Time Series, and Patterns](loads-time-series-and-patterns.md): Understand the loads applied during analysis steps.
* [Partitioning and Parallel Execution](partitioning-and-parallel-execution.md): See how to split solver execution across CPU cores.
