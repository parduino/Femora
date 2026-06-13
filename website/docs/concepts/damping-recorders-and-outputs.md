---
title: Damping, Recorders, and Outputs
icon: material/database-export-outline
---

# Damping, Recorders, and Outputs

Running a simulation is only useful if you can model physical energy dissipation (Damping), instrument the model to record responses (Recorders), and write files for visualization (Outputs).

---

## Mental Model

* **Damping**: Dissipation mechanisms (such as mass- and stiffness-proportional Rayleigh damping) applied to structural or soil elements to represent energy loss during dynamic simulations.
* **Recorders**: Virtual sensors placed at nodes or elements. Instead of saving data for the entire model, you specify what to record (e.g. displacement, velocity, acceleration) and where to record it.
* **Outputs**: The final artifacts produced by Femora, including solver input files (TCL), post-processing databases, and 3D visualization grids (VTK, JSON).

Think of recorders as cameras placed around a crash-test site. You do not need a camera on every single part of the vehicle; you place them at key interest points to capture data efficiently.

---

## Where It Fits

Damping, recorders, and outputs are configured after assembly. Damping properties are assigned to regions, recorders are added as process steps, and outputs are written at the end:

```text
Run Assembly
   ├─ Apply Damping to physical regions (e.g. model.damping.rayleigh)
   ├─ Define Recorders on node/element groups
   ├─ Add Recorders to Process steps (model.process.add_step)
   └─ Export Outputs (export_to_tcl, export_to_vtk)
```

---

## Minimal Example

Applying Rayleigh damping, creating a node recorder for a group, and exporting the model:

```python
from femora.core.model import Model

model = Model()

# (Configure and compile assembly here...)

# 1. Apply Rayleigh damping to a physical region
model.damping.rayleigh(
    name="soil_viscous_damping",
    alpha=0.20,
    beta=0.003,
    region=model.region.get("soil_domain")
)

# 2. Record displacements for ground surface nodes
surf_disp_rec = model.recorder.node(
    name="surf_disp_rec",
    response="disp",
    dof=[1, 2, 3],
    group=model.group.get("ground_surface")
)

# 3. Add the recorder to the process steps
model.process.add_step(surf_disp_rec, description="Record surface motion")

# 4. Export the assembled model to VTK for PyVista/ParaView
model.export_to_vtk("mesh_geometry.vtk")
```

For recorder and damping configurations, refer to the [Recorder Manager API Reference](../reference/core/recorder_manager.md) and [Damping Manager API Reference](../reference/core/damping_manager.md).

---

## What Femora Stores

For damping, recorders, and outputs, Femora tracks:
- **Damping**: Viscous coefficients, target element lists, and associated frequency-damping bounds.
- **Recorders**: Target node/element groups, output file names, time step frequencies (`dt`), and requested response fields.
- **Outputs**: Path references and output file writers.

---

## Common Mistakes

???+ warning "Recording Too Many Nodes in 3D Models"
    In large-scale 3D models with hundreds of thousands of nodes, creating a recorder for all nodes will create massive files on disk, causing severe I/O bottlenecks and drastically slowing down solver execution. Always restrict recorders to targeted, named node or element [Groups](tags-sources-regions-and-groups.md).

---

## Related Concepts

* [Tags, Sources, Regions, and Groups](tags-sources-regions-and-groups.md): Learn how regions and groups partition the mesh.
* [Process and Analysis](process-and-analysis.md): Understand where recorders are active during the solver run.
