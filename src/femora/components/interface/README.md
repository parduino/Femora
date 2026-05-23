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

fm.assembler.assemble()  # interface hooks in automatically
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
> **Location:** `src/femora/core/interface_base.py` (base/manager) and `src/femora/components/interface/` (implementations)

This document explains **why** the new *Interface* layer exists, **how** it is wired into the Femora pipeline, and **how you can implement your own interfaces** (from a one-line equal-DOF constraint up to a full cohesive-zone element generator).

---

## 1  What *is* an Interface?

An **Interface** is the logical “glue” between two (or more) parts of a Femora model.  Depending on the engineering problem it might:

* generate its *own* nodes or elements (e.g. zero-thickness cohesive elements);
* create (mp or sp) **constraints** that tie existing nodes together (e.g. equal-DOF layers);
* simply keep track of which cells must migrate from one core/partition to another after a mesh is decomposed.

The key requirement is **resilience to domain decomposition changes**: after you call

```python
fm.assembler.assemble()
```
…or later repartition the mesh, the interface must still be valid.

---

## 2  Building Blocks

```
interface runtime layout
├── src/femora/core/interface_base.py          # InterfaceBase + InterfaceManager
├── src/femora/components/interface/           # concrete interface implementations
│   ├── embedded_beam_solid_interface.py
│   ├── embedded_node_interface.py
│   └── embedded_info.py
└── src/femora/components/event/event_bus.py     # model-owned event bus (via mesh_maker.events)
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
* Manager-owned: created through `mesh_maker.interface` and bound to one model.
* Subscribes only to the events each concrete class needs (via `_subscribe_events()`).
* Conflict resolution for beam-solid interfaces is handled by `InterfaceManager`, not per-instance hooks.

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
* Model-owned registry exposed as `mesh_maker.interface`.
* Factory helpers: `beam_solid_interface(...)`, `node_interface(...)`.
* Registry access: `get(name)`, `get_all()`.

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
from femora.core.interface_base import InterfaceBase
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

fm = fm.MeshMaker()
fm.interface.add(LaminarBoundary("XFace", master_nodes=left_ids, slave_nodes=right_ids))
```

That’s all—no further calls necessary.  When you assemble ➜ partition ➜ export, the equal-DOF commands are written into the correct cores automatically.

---

## 5  Accessing Interfaces

```python
>>> manager = fm.interface
>>> manager.get_all().keys()
dict_keys(['pile_ifc', 'node_ifc'])
>>> ifc = manager.get('pile_ifc')
```

---

## 6  Integration Points in Core Code

| Component | Change | Purpose |
|-----------|--------|---------|
| `Assembler.assemble()` | Emits `POST_ASSEMBLE`, `RESOLVE_CORE_CONFLICTS` | Triggers interface build / core sync |
| `MeshMaker.export_to_tcl()` | Emits `PRE_EXPORT` | Gives interfaces a chance to write TCL |
| `MeshMaker` | Exposes `self.interface` | Convenience access for users and GUI |

No other parts of Femora were modified.

---

## 7  Advanced Tips

* **Decomposition safe IDs** – store `vtkGlobalCellIds` / point indices, not sequential tags.
* **Performance** – reuse `pykdtree` (already a dependency) for nearest-point queries.
* **GUI** – interface dialogs live under `src/femora/gui/components/interface/` and use the same manager-owned API (`beam_solid_interface`, `node_interface`, `get_all()`).
* **Custom events** – add your own `FemoraEvent.XYZ` and emit from anywhere; interfaces may subscribe.

---

## 8  Future Extensions

* Support for automatic Metis/Scotch partition awareness once those algorithms land in `Assembler`.
* Library of pre-made interface types (cohesive, contact-spring, periodic).
* Optional JSON/YAML serialization for interface definitions.

---

Happy interfacing!  For questions or contributions open an issue or contact the Femora maintainers. 
