---
title: Assembly
icon: material/source-merge
---

# Assembly

Assembly is the compile phase of a Femora model. It compiles individual coordinate-isolated mesh parts and interfaces into a single global coordinate space and solver-ready topology.

---

## Mental Model

Before assembly, your model is a collection of independent geometric blocks. Think of them as physical blocks sitting on a table. Although they might touch, the computer does not know they are connected.

The **Assembler** is the compiler that:
1. Gathers all independent parts.
2. Combines their coordinate meshes into a single global grid: `model.assembled_mesh`.
3. Performs a spatial sweep, merging coincident points that lie within a specified distance (`tolerance=1e-5`) to establish continuous elements.
4. Triggers the event bus (`PRE_ASSEMBLE`, `POST_ASSEMBLE`) to allow sub-managers (such as interfaces, boundary absorbers, and later assembled-model behaviors) to update the unified grid.

---

## Where It Fits

Assembly acts as the boundary between the geometry definition phase and the execution configuration phase:

```text
Define Building Blocks & Mesh Parts
  └─ Declare Interfaces (pre-compile setup)
       └─ [Run Assembler: assemble()]  <-- Compile phase
            ├─ Merge coincident points
            ├─ Trigger POST_ASSEMBLE events
            └─ Build model.assembled_mesh
                 └─ Define Analysis Steps & Solve
```

---

## Minimal Example

Compiling a model using an assembly section and verifying the global grid:

```python
from femora.core.model import Model

model = Model()

# (Define materials, elements, soil_box part, and pile part here...)

# 1. Create an assembly section containing the parts to merge
model.assembler.create_section(
    meshparts=["soil_domain", "pile_domain"],
    merge_points=True,
    tolerance=1e-5
)

# 2. Compile the global grid
model.assembler.assemble()

# 3. Plot the final unified assembled mesh
model.assembler.plot(show_edges=True)
```

Refer to the [Assembler API Reference](../reference/core/assembler.md) for options.

---

## What Femora Stores

Upon compilation, the Assembler builds:
- **`model.assembled_mesh`**: A unified PyVista dataset containing all compiled coordinates, elements, cell data, and part tags.
- **Node and Element Map**: Mapping arrays translating local part coordinates to global solver tags.
- **`Core` cell data**: Array containing partition indices for parallel execution support.

---

## Common Mistakes

???+ warning "Forgetting to Run Assembly Before Exporting"
    If you attempt to write a TCL script (`model.export_to_tcl()`) or configure recorders without first executing `model.assembler.assemble()`, the operation will fail or export an empty model. Node coordinates and connectivity only exist after assembly compiles them.

???+ warning "Point Merging vs. Element Merging"
    Point merging combines overlapping node coordinates along contact faces to ensure structural continuity. However, **elements are never merged**. A hexahedral soil brick and a structural concrete brick remain distinct element formulations, even if they share nodes along their contact boundary.

---

## Related Concepts

* [Mesh Parts](mesh-parts.md): Define the source geometries compiled by the assembler.
* [Interfaces](constraints-and-interfaces.md): Learn how mesh-part relationships execute during assembly events.
* [Tags, Sources, Regions, and Groups](tags-sources-regions-and-groups.md): See how to organize the assembled grid.
