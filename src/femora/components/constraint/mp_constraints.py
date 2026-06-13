# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import List

from femora.core.constraint_base import MPConstraint


class EqualDOF(MPConstraint):
    """Multi-point equal degree of freedom constraint.

    EqualDOF constrains specified degrees of freedom (DOFs) of multiple slave
    nodes to be identical to the corresponding DOFs of a master node. It is
    commonly used to model rigid connections, symmetry boundaries, or sliding joints.

    Tcl form:
        ``equalDOF <masterNode> <slaveNode> <dof1> <dof2> ...``

    Note:
        - The DOFs list contains 1-indexed integers representing the active degrees
          of freedom to constrain.
        - A single EqualDOF object can define equal kinematic conditions between a single
          master node and multiple slave nodes.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Constrain DOF 1 (horizontal displacement) of node 2 to node 1
        constraint = model.constraint.mp.equal_dof(
            master_node=1,
            slave_nodes=[2],
            dofs=[1],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, master_node: int, slave_nodes: List[int], dofs: List[int]):
        """Create an equal DOF constraint.

        Args:
            master_node: Tag of the retained (master) node.
            slave_nodes: List of constrained (slave) node tags.
            dofs: List of 1-indexed degrees of freedom to constrain.
        """
        super().__init__(master_node, slave_nodes)
        self.dofs = dofs

    def to_tcl(self) -> str:
        """Render this multi-point constraint as OpenSees Tcl commands.

        Returns:
            The OpenSees equalDOF command string.
        """
        tcl_str = ""
        for slave in self.slave_nodes:
            dofs_str = " ".join(str(dof) for dof in self.dofs)
            tcl_str += f"equalDOF {self.master_node} {slave} {dofs_str}"
        return tcl_str


class RigidLink(MPConstraint):
    """Multi-point rigid link kinematic constraint.

    RigidLink defines a kinematic constraint representing a rigid link between
    a master node and multiple slave nodes. It supports two kinematic behaviors:
    axial rigidity only ('bar') or axial and bending rigidity ('beam').

    Tcl form:
        ``rigidLink <type> <masterNode> <slaveNode>``

    Note:
        - The rigid link type must be either `'bar'` or `'beam'`.
        - Using the `'beam'` link type requires that the participating master
          and slave nodes have rotational degrees of freedom.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Constrain node 2 to master node 1 with a rigid beam link
        constraint = model.constraint.mp.rigid_link(
            type_str="beam",
            master_node=1,
            slave_nodes=[2],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, type_str: str, master_node: int, slave_nodes: List[int]):
        """Create a rigid link kinematic constraint.

        Args:
            type_str: Kinematic link type. Must be either `'bar'` or `'beam'`.
            master_node: Tag of the retained (master) node.
            slave_nodes: List of constrained (slave) node tags.

        Raises:
            ValueError: If `type_str` is not `'bar'` or `'beam'`.
        """
        super().__init__(master_node, slave_nodes)
        if type_str not in ['bar', 'beam']:
            raise ValueError("RigidLink type must be 'bar' or 'beam'")
        self.type = type_str

    def to_tcl(self) -> str:
        """Render this multi-point constraint as OpenSees Tcl commands.

        Returns:
            The OpenSees rigidLink command string.
        """
        tcl_str = ""
        for slave in self.slave_nodes:
            tcl_str += f"rigidLink {self.type} {self.master_node} {slave}"
        return tcl_str


class RigidDiaphragm(MPConstraint):
    """Multi-point rigid diaphragm kinematic constraint.

    RigidDiaphragm defines a kinematic constraint representing a rigid floor
    diaphragm in 3D structures. It constrains the in-plane movement of multiple
    slave nodes to match the rigid body movement of a master node.

    Tcl form:
        ``rigidDiaphragm <direction> <masterNode> <slaveNode1> <slaveNode2> ...``

    Note:
        - The direction argument specifies the perpendicular axis normal to the
          diaphragm plane (e.g., 3 for the XY plane normal in 3D space).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Constrain nodes 2 and 3 to master node 1 on the XY plane (direction 3 normal)
        constraint = model.constraint.mp.rigid_diaphragm(
            direction=3,
            master_node=1,
            slave_nodes=[2, 3],
        )
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(self, direction: int, master_node: int, slave_nodes: List[int]):
        """Create a rigid diaphragm kinematic constraint.

        Args:
            direction: 1-indexed perpendicular axis normal to the diaphragm plane.
            master_node: Tag of the retained (master) node.
            slave_nodes: List of constrained (slave) node tags.
        """
        super().__init__(master_node, slave_nodes)
        self.direction = direction

    def to_tcl(self) -> str:
        """Render this multi-point constraint as OpenSees Tcl commands.

        Returns:
            The OpenSees rigidDiaphragm command string.
        """
        slaves_str = " ".join(str(node) for node in self.slave_nodes)
        return f"rigidDiaphragm {self.direction} {self.master_node} {slaves_str}"


__all__ = ["MPConstraint", "EqualDOF", "RigidLink", "RigidDiaphragm"]