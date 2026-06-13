# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from typing import Dict, List, Optional

from femora.core.element_base import Element


class ASDEmbeddedNodeElement3D(Element):
    """Embedded-node constraint element for 3D solid domains.

    This element constrains one embedded node to a domain defined by four
    retained nodes forming a tetrahedral interpolation patch. It is intended for
    3D embedded-node coupling and is typically used together with the
    EmbeddedNode interface workflow in Femora.

    Tcl form:
        ``element ASDEmbeddedNodeElement <eleTag> <Cnode> <Rnode1> <Rnode2> <Rnode3> <Rnode4> [-rot] [-p] [-K K] [-KP KP] [-contact Kn Kt mu [-orient ox oy oz] [-int_type int_type]]``

    Warning:
        This element is specialized for 3D embedded-node coupling and can be
        difficult to use correctly outside the intended interface workflow.

    Note:
        - Requires five nodes at export: one constrained node followed by four
          retained nodes.
        - When ``contact`` is enabled, normal and tangential penalty stiffness
          and friction parameters are exported with the element command.

    Attributes:
        rot: Whether rotational DOFs at the constrained node are constrained.
        p: Whether pressure DOFs are constrained.
        K: Optional penalty stiffness for displacement constraints.
        KP: Optional penalty stiffness for pressure constraints.
        contact: Whether frictional contact behavior is enabled.
        Kn: Normal contact penalty stiffness used when ``contact`` is enabled.
        Kt: Tangential contact penalty stiffness used when ``contact`` is enabled.
        mu: Friction coefficient used when ``contact`` is enabled.
        orient: Default contact orientation vector when ``orient_map`` is not
            used.
        orient_map: Per-node orientation vectors keyed by constrained node tag.
        int_type: Contact integration type (``0`` implicit, ``1`` IMPL-EX).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ele = model.element.special.asd_embedded_node(
            ndof=6,
            rot=True,
            contact=True,
            Kn=1.0e8,
            Kt=1.0e8,
            mu=0.5,
        )
        print(ele.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__"],
    }

    def __init__(
        self,
        ndof: int,
        rot: bool = False,
        p: bool = False,
        K: Optional[float] = None,
        KP: Optional[float] = None,
        contact: bool = False,
        Kn: float = 1.0e8,
        Kt: float = 1.0e8,
        mu: float = 0.5,
        orient: list = None,
        orient_map: dict = None,
        int_type: int = 1,
        **kwargs,
    ):
        """Create an ASDEmbeddedNodeElement3D with validated constraint options.

        Args:
            ndof: Number of DOFs per node. Must be 3, 4, or 6.
            rot: Whether to constrain rotational DOFs at the embedded node.
            p: Whether to constrain pressure DOFs.
            K: Optional user-defined penalty stiffness for displacement
                constraints.
            KP: Optional user-defined penalty stiffness for pressure
                constraints.
            contact: Whether to enable frictional contact behavior.
            Kn: Normal contact penalty stiffness when ``contact`` is enabled.
            Kt: Tangential contact penalty stiffness when ``contact`` is enabled.
            mu: Friction coefficient when ``contact`` is enabled.
            orient: Default orientation vector ``[ox, oy, oz]`` used when
                ``orient_map`` does not provide a node-specific vector.
            orient_map: Mapping from constrained node tag to orientation vector.
            int_type: Contact integration type (``0`` implicit, ``1`` IMPL-EX).
            **kwargs: Additional element parameters stored on the base element.

        Raises:
            ValueError: If ``ndof`` is unsupported or if orientation or contact
                parameters are invalid.
        """
        if ndof not in [3, 4, 6]:
            raise ValueError(f"ASDEmbeddedNodeElement3D requires 3, 4, or 6 DOFs, but got {ndof}")

        self.rot = bool(rot)
        self.p = bool(p)
        self.K = float(K) if K is not None else None
        self.KP = float(KP) if KP is not None else None
        self.contact = bool(contact)
        self.Kn = float(Kn)
        self.Kt = float(Kt)
        self.mu = float(mu)

        if orient is not None:
            if not isinstance(orient, (list, tuple)) or len(orient) != 3:
                raise ValueError("orient must be a list/tuple of 3 floats")
            self.orient = [float(x) for x in orient]
        else:
            self.orient = None

        if orient_map is not None:
            if not isinstance(orient_map, dict):
                raise ValueError("orient_map must be a dictionary")
            self.orient_map = {k: [float(x) for x in v] for k, v in orient_map.items()}
        else:
            self.orient_map = None

        self.int_type = int(int_type)
        if self.int_type not in [0, 1]:
            raise ValueError("int_type must be 0 or 1")

        super().__init__("ASDEmbeddedNodeElement", ndof, material=None, **kwargs)

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Render the element as an OpenSees Tcl command.

        Args:
            tag: Assigned element tag.
            nodes: Five node tags ``[Cnode, Rnode1, Rnode2, Rnode3, Rnode4]``.

        Returns:
            str: Tcl ``element ASDEmbeddedNodeElement`` command for this element.

        Raises:
            ValueError: If ``nodes`` does not contain exactly five node tags.
        """
        if len(nodes) != 5:
            raise ValueError("ASDEmbeddedNodeElement3D requires 5 nodes (1 constrained, 4 retained)")

        nodes_str = " ".join(str(node) for node in nodes)
        cmd = f"element ASDEmbeddedNodeElement {tag} {nodes_str}"

        if self.rot:
            cmd += " -rot"
        if self.p:
            cmd += " -p"
        if self.K is not None:
            cmd += f" -K {self.K}"
        if self.KP is not None:
            cmd += f" -KP {self.KP}"

        if self.contact:
            cmd += f" -contact {self.Kn} {self.Kt} {self.mu}"

            orient = None
            if self.orient_map and nodes[0] in self.orient_map:
                orient = self.orient_map[nodes[0]]
            elif self.orient:
                orient = self.orient

            if orient:
                cmd += f" -orient {orient[0]} {orient[1]} {orient[2]}"

            cmd += f" -int_type {self.int_type}"

        return cmd
