## 🔰 0. Plain-English Quick Start

*Think of an **Interface** as the zipper that joins two pieces of fabric (your mesh parts).*

1. **Why do I need it?**  
   When two regions of your model touch, you often need special elements, nodes or just "rules" that say *how* they stick, slide or transfer load.  That bundle of elements or rules is an **Interface**.

2. **What does Femora do for me?**  
   • It remembers every interface you create.  
   • It _automatically_ rebuilds or relocates that interface when you regroup the mesh for parallel computing.  
   • It writes the right TCL commands at export time.

3. **Smallest possible example:**
   ```python
   import femora as fm
   from my_laminar import LaminarBoundary  # example class shown later

   #     name        master-side nodes   slave-side nodes
   LaminarBoundary("ZeroSlip",     [1,2,3],           [101,102,103])

   fm.assembler.Assemble()  # interface hooks in automatically
   fm.export_to_tcl("model.tcl")
   ```
   You never call a special "apply" method—the event system does that for you.

4. **Mental model of the event system**  
   • **Assembler shouts**: "I'm done!" → interfaces create their stuff.  
   • **Assembler shouts**: "Cores have changed!" → interfaces move/duplicate.  
   • **MeshMaker shouts**: "I'm exporting!" → interfaces print TCL.

5. **Where to look if something breaks?**  
   *event_bus.py* lists the events; put a `print()` in your handler to see if it fires.

> *Skip the rest until you need deeper details—everything below is for power users.*

---

# Femora Interface System

> **Introduced:** Femora vX.X (experimental)
>
> **Location:** `src/femora/components/Interface/`

This document explains **why** the new *Interface* layer exists, **how** it is wired into the Femora pipeline, and **how you can implement your own interfaces** (from a one-line equal-DOF constraint up to a full cohesive-zone element generator).

---

## 1  What *is* an Interface?

An **Interface** is the logical “glue” between two (or more) parts of a Femora model.  Depending on the engineering problem it might:

* generate its *own* nodes or elements (e.g. zero-thickness cohesive elements);
* create (mp or sp) **constraints** that tie existing nodes together (e.g. equal-DOF layers);
* simply keep track of which cells must migrate from one core/partition to another after a mesh is decomposed.

The key requirement is **resilience to domain decomposition changes**: after you call

```python
fm.assembler.Assemble()
```
…or later repartition the mesh, the interface must still be valid.

---

## 2  Building Blocks

```
Interface/
├── event_bus.py          # tiny pub/sub hub
├── interface_base.py     # common parent class
├── mixins.py             # capability mix-ins
└── interface_manager.py  # singleton helper
```

### 2.1  EventBus & `FemoraEvent`
* A **3-line pub/sub** utility (no third-party deps).
* Emits four standard events:
  1. `PRE_ASSEMBLE`     (reserved)  
  2. `POST_ASSEMBLE`  → assembled mesh exists  
  3. `RESOLVE_CORE_CONFLICTS` → `Core` array final  
  4. `PRE_EXPORT`      → MeshMaker is about to write TCL.
* Components emit – interfaces subscribe.

### 2.2  `InterfaceBase`
* Registers itself in a global dict (`InterfaceBase.all()`).
* Auto-subscribes to the three life-cycle events (2–4).
* Default handlers are NO-OP; mix-ins or subclasses override them.

### 2.3  Capability Mix-ins (`mixins.py`)
| Mixin                       | Purpose                                    |
|-----------------------------|--------------------------------------------|
| `GeneratesMeshMixin`        | Interface owns a *mesh* (cells).           |
| `GeneratesNodesMixin`       | Interface only adds nodes.                 |
| `GeneratesConstraintsMixin` | Interface creates mp/sp constraints.       |
| `HandlesDecompositionMixin` | Needs to migrate/duplicate things on core changes. |

Combine only what you need:

```python
class CohesiveInterface(InterfaceBase,
                         GeneratesMeshMixin,
                         GeneratesConstraintsMixin,
                         HandlesDecompositionMixin):
    ...
```

### 2.4  `InterfaceManager`
* Thin singleton exposed as `fm.interface` (similar to `fm.meshPart`, `fm.element`, …).
* Utility factory / registry wrapper.

---

## 3  Life-cycle Diagram

```text
User creates Interface → (idle)
           │
           ▼
Assembler POST_ASSEMBLE  ─► Interface.build_*()  (creates nodes / mesh / constraints)
           │
           ▼
Assembler RESOLVE_CORE_CONFLICTS ─► Interface.on_partition_update()  (move / duplicate across cores)
           │
           ▼
MeshMaker PRE_EXPORT     ─► Interface writes TCL (nodes, elements, equalDOF, …)
```

Interfaces therefore “wake up” automatically at each critical stage – you never call them manually.

---

## 4  Writing Your First Interface

Below is a **minimal** node-only interface that constrains two mesh parts so that opposite nodes share X- and Y-translations (classic 2-D *laminar* boundary):

```python
# my_laminar.py
from femora.components.Interface.interface_base import InterfaceBase
from femora.components.Interface.mixins import GeneratesConstraintsMixin
from femora.components.Constraint.mpConstraint import mpConstraintManager

class LaminarBoundary(InterfaceBase, GeneratesConstraintsMixin):
    def __init__(self, name: str, master_nodes: list[int], slave_nodes: list[int]):
        super().__init__(name=name, owners=["global"])
        self.master_nodes = master_nodes
        self.slave_nodes  = slave_nodes
        self.constraints = []  # will be filled in build_constraints

    # ------------ mandatory overrides ---------------------------------
    def build_constraints(self, **kw):
        mp = mpConstraintManager()
        for m, s in zip(self.master_nodes, self.slave_nodes):
            self.constraints.append(
                mp.create_equal_dof(master_node=m,
                                     slave_nodes=[s],
                                     dofs=[1, 2])
            )

    def register_constraints(self):
        # Already registered inside mpConstraintManager; nothing to do
        pass
```

Usage:

```python
import femora as fm
from my_laminar import LaminarBoundary

LaminarBoundary("XFace", master_nodes=left_ids, slave_nodes=right_ids)
```

That’s all—no further calls necessary.  When you assemble ➜ partition ➜ export, the equal-DOF commands are written into the correct cores automatically.

---

## 5  Accessing Interfaces

```python
>>> import femora as fm
>>> fm.interface.all().keys()
dict_keys(['XFace', 'MyCohesiveZone'])
>>> ifc = fm.interface.get('XFace')
```

---

## 6  Integration Points in Core Code

| Component | Change | Purpose |
|-----------|--------|---------|
| `Assembler.Assemble()` | Emits `POST_ASSEMBLE`, `RESOLVE_CORE_CONFLICTS` | Triggers interface build / core sync |
| `MeshMaker.export_to_tcl()` | Emits `PRE_EXPORT` | Gives interfaces a chance to write TCL |
| `MeshMaker` | Exposes `self.interface` | Convenience access for users and GUI |

No other parts of Femora were modified.

---

## 7  Advanced Tips

* **Decomposition safe IDs** – store `vtkGlobalCellIds` / point indices, not sequential tags.
* **Performance** – reuse `pykdtree` (already a dependency) for nearest-point queries.
* **GUI** – you can plug dialogs under `Interface/gui/` and call `InterfaceManager.create_interface()` directly.
* **Custom events** – add your own `FemoraEvent.XYZ` and emit from anywhere; interfaces may subscribe.

---

## 8  Future Extensions

* Support for automatic Metis/Scotch partition awareness once those algorithms land in `Assembler`.
* Library of pre-made interface types (cohesive, contact-spring, periodic).
* Optional JSON/YAML serialization for interface definitions.

---

Happy interfacing!  For questions or contributions open an issue or contact the Femora maintainers. 