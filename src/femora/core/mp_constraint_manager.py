from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from femora.components.Assemble.Assembler import Assembler
from femora.core.constraint_base import MPConstraint
from femora.core.tagging import CompactRetagPolicy
from pykdtree.kdtree import KDTree
import numpy as np


class MPConstraintManager:
    """Local manager for multi-point constraint lifecycle and tag assignment."""

    def __init__(self, owner):
        from femora.core.constraint_manager import ConstraintManager as ConstraintManagerClass

        if not isinstance(owner, ConstraintManagerClass):
            raise TypeError("owner must be a ConstraintManager instance")
        if getattr(owner, "mp", None) is not None:
            raise ValueError("constraint manager already owns MP constraints")

        self._owner = owner
        self._mesh_maker = owner._mesh_maker
        self._constraints: Dict[int, MPConstraint] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[MPConstraint]()

    def __len__(self) -> int:
        return len(self._constraints)

    def __iter__(self):
        return iter(self._constraints.values())

    def add(self, constraint: MPConstraint) -> MPConstraint:
        if not isinstance(constraint, MPConstraint):
            raise TypeError("constraint must be an MPConstraint instance")
        if constraint._owner is None:
            constraint._owner = self
        elif constraint._owner is not self:
            raise ValueError("constraint already belongs to another manager")
        try:
            constraint.tag = self._tagging.assign_tag(self._constraints, constraint, self._start_tag)
        except ValueError as exc:
            raise ValueError(f"Constraint tag {constraint.tag} already exists") from exc
        self._constraints[constraint.tag] = constraint
        return constraint

    def equal_dof(self, master_node: int, slave_nodes: List[int], dofs: List[int]):
        from femora.components.constraint.mp_constraints import EqualDOF

        return self.add(EqualDOF(master_node, slave_nodes, dofs))

    def rigid_link(self, type_str: str, master_node: int, slave_nodes: List[int]):
        from femora.components.constraint.mp_constraints import RigidLink

        return self.add(RigidLink(type_str, master_node, slave_nodes))

    def rigid_diaphragm(self, direction: int, master_node: int, slave_nodes: List[int]):
        from femora.components.constraint.mp_constraints import RigidDiaphragm

        return self.add(RigidDiaphragm(direction, master_node, slave_nodes))

    def laminar_boundary(self, dofs: List[int], bounds: Tuple[float, float], direction: int = 3, tol: float = 1e-2) -> None:
        assembler = Assembler()
        if assembler.AssembeledMesh is None:
            raise ValueError("AssembeledMesh is not created yet")

        mesh = assembler.AssembeledMesh.copy()
        surface = mesh.extract_surface()
        xmin, xmax, ymin, ymax, zmin, zmax = surface.bounds
        eps = tol
        if direction == 3:
            xmin += eps
            xmax -= eps
            ymin += eps
            ymax -= eps
            zmin -= eps
            zmax += eps
        elif direction == 2:
            xmin += eps
            xmax -= eps
            ymin -= eps
            ymax += eps
            zmin += eps
            zmax -= eps
        elif direction == 1:
            xmin -= eps
            xmax += eps
            ymin += eps
            ymax -= eps
            zmin += eps
            zmax -= eps
        else:
            raise ValueError("Direction must be 1, 2, or 3")

        ind = surface.find_cells_within_bounds((xmin, xmax, ymin, ymax, zmin, zmax))
        surface = surface.extract_cells(ind, invert=True)
        points = surface.points
        tolerance = tol

        kdtree = KDTree(mesh.points)
        distances, indices = kdtree.query(points, k=1)
        nodeTags = indices + self._mesh_maker.get_start_node_tag()

        z = points[:, direction - 1]

        boundmin = bounds[0]
        boundmax = bounds[1]
        mask = (z >= boundmin - tolerance) & (z <= boundmax + tolerance)
        z = z[mask]
        nodeTags = nodeTags[mask]
        points = points[mask]

        z_rounded = np.round(z / tolerance) * tolerance
        unique_z, group_ids = np.unique(z_rounded, return_inverse=True)

        Taggroups = [nodeTags[group_ids == i] for i in range(len(unique_z))]

        for group in Taggroups:
            if len(group) > 1:
                for slave in group[1:]:
                    self.equal_dof(master_node=group[0], slave_nodes=[slave], dofs=dofs)

    def equal_dof_between_meshparts(self, meshpart_master: str, meshpart_slave: str, dofs: List[int], tol: float = 1e-5) -> None:
        from femora.components.Mesh.meshPartBase import MeshPart

        assembler = Assembler()
        if assembler.AssembeledMesh is None:
            raise ValueError("AssembeledMesh is not created yet")

        master_part = MeshPart.get_mesh_parts().get(meshpart_master)
        slave_part = MeshPart.get_mesh_parts().get(meshpart_slave)
        if master_part is None:
            raise ValueError(f"MeshPart '{meshpart_master}' not found")
        if slave_part is None:
            raise ValueError(f"MeshPart '{meshpart_slave}' not found")

        ndf_master = master_part.element._ndof
        ndf_slave = slave_part.element._ndof
        max_common = min(ndf_master, ndf_slave)
        if any((d < 1 or d > max_common) for d in dofs):
            raise ValueError(f"Requested DOFs {dofs} invalid for master ndf={ndf_master} and slave ndf={ndf_slave}")

        assembled = assembler.get_mesh()
        points = assembled.points
        master_idx = assembled.extract_values(values=master_part.tag, scalars="MeshPartTag_celldata", preference="cell")
        slave_idx = assembled.extract_values(values=slave_part.tag, scalars="MeshPartTag_celldata", preference="cell")
        master_idx = master_idx.point_data["vtkOriginalPointIds"]
        slave_idx = slave_idx.point_data["vtkOriginalPointIds"]

        if len(master_idx) != master_part.mesh.n_points:
            print(
                f"Warning: Number of points in master mesh part '{meshpart_master}' "
                f"({master_part.number_of_points}) does not match points found in assembled mesh ({len(master_idx)})."
            )
        if len(slave_idx) != slave_part.mesh.n_points:
            print(
                f"Warning: Number of points in slave mesh part '{meshpart_slave}' "
                f"({slave_part.number_of_points}) does not match points found in assembled mesh ({len(slave_idx)})."
            )

        if master_idx.size == 0:
            raise ValueError(f"No points found for master mesh part '{meshpart_master}' in assembled mesh")
        if slave_idx.size == 0:
            raise ValueError(f"No points found for slave mesh part '{meshpart_slave}' in assembled mesh")

        master_pts = points[master_idx]
        slave_pts = points[slave_idx]

        tree = KDTree(slave_pts)
        distances, nearest = tree.query(master_pts, k=1)

        start_node_tag = self._mesh_maker.get_start_node_tag()

        for i, (dist, j) in enumerate(zip(distances, nearest)):
            if dist <= tol:
                master_point_idx = int(master_idx[i])
                slave_point_idx = int(slave_idx[j])
                master_node_tag = master_point_idx + start_node_tag
                slave_node_tag = slave_point_idx + start_node_tag
                self.equal_dof(master_node=master_node_tag, slave_nodes=[slave_node_tag], dofs=dofs)

    def get(self, tag: int) -> Optional[MPConstraint]:
        return self._constraints.get(int(tag))

    def get_constraint(self, tag: int) -> Optional[MPConstraint]:
        return self.get(tag)

    def get_all(self) -> Dict[int, MPConstraint]:
        return dict(self._constraints)

    def remove(self, tag: int) -> None:
        constraint = self._constraints.pop(int(tag), None)
        if constraint is not None:
            constraint.tag = None
            constraint._owner = None
            self._reassign_tags()

    def remove_constraint(self, tag: int) -> None:
        self.remove(tag)

    def to_tcl(self) -> str:
        tcl_str = ""
        for constraint in self._constraints.values():
            tcl_str += constraint.to_tcl()
        return tcl_str

    def clear(self) -> None:
        for constraint in list(self._constraints.values()):
            constraint.tag = None
            constraint._owner = None
        self._constraints.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._constraints, self._start_tag)


__all__ = ["MPConstraintManager"]
