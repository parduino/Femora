"""Interface package for Femora.

This package contains runtime contact and boundary interface component classes that 
couple model parts, nodes, or elements together (such as embedded beam-solid or 
embedded node constraints) and apply absorbing boundaries.

Normal runtime usage should go through `Model` manager entry points under the
`model.interface` namespace:
- `model.interface.beam_solid_interface(...)` for embedded beam-solid interfaces
- `model.interface.node_interface(...)` for embedded node-to-domain constraint interfaces
- `model.interface.boundary.absorber(...)` for applying rectangular boundary absorbers
"""
