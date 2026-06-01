"""---
icon: material/link-variant
---

Constraint component package for Femora.

This package contains runtime constraint component classes that define boundary
conditions and kinematic constraints in OpenSees.

Normal runtime usage should go through `Model` manager entry points under the
`model.constraint` namespace:
- Single-point constraints (SPC) via `model.constraint.sp`
- Multi-point constraints (MPC) via `model.constraint.mp`

Direct imports from this package are mainly useful for typed references, tests,
and low-level constraint development.
"""
