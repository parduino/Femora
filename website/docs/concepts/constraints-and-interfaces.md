---
title: Constraints and Interfaces
icon: material/vector-link
---

# Constraints and Interfaces

Boundary conditions and spatial connections between independent mesh parts are defined using Constraints and Interfaces.

---

## Mental Model

* **Constraints**: Mathematical rules applied directly to degrees of freedom (DOFs) at specific node coordinates.
  * **Single-Point Constraints (SP)**: Enforce fixities or boundary walls (e.g., locking the base nodes to prevent motion).
  * **Multi-Point Constraints (MP)**: Link the DOFs of different nodes together (e.g. enforcing that boundary nodes move in unison).
* **Interfaces**: High-level modeling constructs used to connect separate [Mesh Parts](mesh-parts.md) that do not share nodes initially (e.g., embedding a pile column inside a solid soil domain).

Instead of forcing you to build a single conformal mesh where all parts share matching nodes along boundaries, Femora allows you to mesh parts independently and declare logical interfaces to link them. The interface handles resolving these connections during compilation.

---

## Where It Fits

Constraints and Interfaces are declared **before** assembly. They register to listen for compiler events, executing their search and intersection operations only when the final model is compiled:

```text
Instantiate Mesh Parts
   └─ Declare Interfaces (e.g. beam_solid_interface)
        └─ Compile via Assembly Section
             └─ [Assembly Event: POST_ASSEMBLE]
                  └─ Interfaces search coordinates, find overlapping cells, 
                     and generate mathematical constraints on the assembled mesh
```

---

## Minimal Example

Fixing base boundary DOFs and embedding a beam pile part into a solid soil volume:

```python
from femora.core.model import Model

model = Model()

# 1. Define single-point (SP) fixity constraints on boundary faces
# Fixes all three translation DOFs at the minimum Z boundary coordinate
model.constraint.sp.fix_macro_z_min(dofs=[1, 1, 1], tol=1e-3)

# 2. Define an interface to connect a line part with solid volume parts
# Note: This is declared before assembly, and evaluates once assembly runs
pile_contact = model.interface.beam_solid_interface(
    name="pile_soil_interface",
    beam_part="pile",
    solid_parts=["soil_box"],
    radius=0.5,
)
```

For more options, refer to the [SpConstraintManager API Reference](../reference/core/sp_constraint_manager.md) and [InterfaceManager API Reference](../reference/core/interface_base.md).

---

## What Femora Stores

For constraints and interfaces, Femora tracks:
- **SP/MP Constraints**: Coordinate bounds, target degrees of freedom, tolerance thresholds, and target values.
- **Interfaces**: Target beam parts, solid parts, cross-sectional geometry properties (e.g. shape, radius), and numerical penalty parameters.
- **Event Listeners**: Internal subscriptions to compiler stages like `POST_ASSEMBLE` and `RESOLVE_CORE_CONFLICTS`.

---

## Common Mistakes

???+ warning "Interfaces do not physically merge nodes"
    Do not use interfaces when you want two touching grids to behave as a single continuous volume. If parts are meant to be physically continuous, the assembler's node-merging step will combine their overlapping points automatically. Use interfaces only to resolve contact surfaces, apply slip conditions, or embed line elements inside solid volumes.

---

## Related Concepts

* [Mesh Parts](mesh-parts.md): Define the parts connected by interfaces.
* [Assembly](assembly.md): Explore the compile phase where interface searches are executed.
