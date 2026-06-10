# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from femora.core.damping_base import Damping
from femora.core.region_base import RegionBase


class GlobalRegion(RegionBase):
    """A special region representing the entire structural model.

    GlobalRegion represents the entire finite element model as a single region.
    It is pre-instantiated by the region manager and assigned a reserved tag of `0`.
    It is typically used to apply global Rayleigh or modal damping.

    Tcl form:
        None (renders as an empty string since it is the global default).

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Retrieve the pre-defined global region
        glob_reg = model.region.global_region
        print(glob_reg.tag)  # 0
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(self, damping: Damping = None):
        """Initialize the global region.

        Args:
            damping: Optional Damping component to assign globally.
        """
        super().__init__(user_name="GlobalRegion", damping=damping)
        self.elements = None
        self.element_range = None
        self.nodes = None
        self.node_range = None

    def to_tcl(self) -> str:
        """Render this global region as an OpenSees Tcl command.

        Returns:
            An empty string as the global region represents the default scope.
        """
        return ""

    @staticmethod
    def get_type() -> str:
        """Get the type name of the region.

        Returns:
            The string "GlobalRegion".
        """
        return "GlobalRegion"


class ElementRegion(RegionBase):
    """A region defined by a set of elements or a range of element tags.

    ElementRegion groups a collection of elements (specified as an explicit list
    or tag range) into a named structural region. This is useful for assigning
    element-specific damping models (such as Rayleigh damping) in OpenSees.

    Tcl form:
        ``region <tag> -ele <eleTags...>`` or ``region <tag> -eleRange <start> <end>``

    Note:
        - Only one of `elements` or `element_range` can be provided.
        - Renders with `-eleOnly` or `-eleRangeOnly` if `element_only` is set to `True`.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create an element-based region for elements 1 to 10
        reg = model.region.element(
            user_name="story_one_elements",
            element_range=[1, 10],
        )
        print(reg.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(self, damping: Damping = None, **kwargs):
        """Create an element-based region.

        Args:
            damping: Optional Damping component to assign to the elements in this region.
            **kwargs: Key-value arguments including:
                user_name: Unique name of the region.
                elements: Optional list or array of explicit element tags.
                element_range: Optional list/tuple of two integers `[start, end]`.
                element_only: Optional boolean. If True, includes only the elements.

        Raises:
            ValueError: If both `elements` and `element_range` are specified, or if
                the input formats are invalid.
        """
        user_name = kwargs.pop("user_name", kwargs.pop("name", None))
        super().__init__(user_name=user_name, damping=damping)
        self.elements = []
        self.element_range = []
        self.element_only = False

        if kwargs:
            if "elements" in kwargs and "element_range" in kwargs:
                raise ValueError("Both elements and element_range cannot be provided at the same time")

            elements = kwargs.get("elements", [])
            element_range = kwargs.get("element_range", [])
            element_only = kwargs.get("element_only", False)

            if elements and not isinstance(elements, (list, np.ndarray)):
                raise ValueError("elements should be a list of integers")

            if element_range:
                if not isinstance(element_range, (list, np.ndarray)) or len(element_range) != 2:
                    raise ValueError("element_range should be a list of 2 integers")

            self.elements = list(elements) if elements is not None else []
            self.element_range = list(element_range) if element_range is not None else []
            self.element_only = bool(element_only)

    def to_tcl(self) -> str:
        """Render this element region as OpenSees Tcl commands.

        Returns:
            The Tcl command string.

        Raises:
            ValueError: If the region is not currently managed.
        """
        if self.tag is None:
            raise ValueError(f"Region '{self.user_name}' must be managed before rendering TCL")
            
        cmd = f"eval \"region {self.tag}"
        if len(self.element_range) > 0:
            cmd += " -eleRange {} {}".format(*self.element_range)
            if self.element_only:
                cmd += "Only"
        elif len(self.elements) > 0:
            cmd += " -ele" + ("Only" if self.element_only else "")
            cmd += " " + " ".join(str(e) for e in self.elements)

        if self.damping:
            if self.damping.get_type() in ["Rayleigh", "Frequency Rayleigh"]:
                cmd += f" -rayleigh {self.damping.alphaM} {self.damping.betaK} {self.damping.betaKInit} {self.damping.betaKComm}"
            else:
                cmd += f" -damp {self.damping.tag}"
        cmd += "\""
        return cmd
    
    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\tNum of Elements: {len(self.elements)}"
        res += f"\n\tElement Range: {self.element_range}"
        res += f"\n\tElement Only: {self.element_only}"
        return res

    @staticmethod
    def get_type() -> str:
        """Get the region type name.

        Returns:
            The string "ElementRegion".
        """
        return "ElementRegion"


class NodeRegion(RegionBase):
    """A region defined by a set of nodes or a range of node tags.

    NodeRegion groups a collection of nodes (specified as a list or a tag range)
    into a named structural region. This allows targeted assignments such as node-based
    recorders or specialized damping properties in OpenSees.

    Tcl form:
        ``region <tag> -node <nodeTags...>`` or ``region <tag> -nodeRange <start> <end>``

    Note:
        - Only one of `nodes` or `node_range` can be provided.
        - Renders with `-nodeOnly` or `-nodeRangeOnly` if `node_only` is set to `True`.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        # Create a node-based region for node tags 1, 2, and 3
        reg = model.region.node(
            user_name="foundation_nodes",
            nodes=[1, 2, 3],
        )
        print(reg.tag)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "get_type"],
    }

    def __init__(self, damping: Damping = None, **kwargs):
        """Create a node-based region.

        Args:
            damping: Optional Damping component to assign.
            **kwargs: Key-value arguments including:
                user_name: Unique name of the region.
                nodes: Optional list or array of explicit node tags.
                node_range: Optional list/tuple of two integers `[start, end]`.
                node_only: Optional boolean. If True, includes only the nodes.

        Raises:
            ValueError: If both `nodes` and `node_range` are specified, or if
                the input formats are invalid.
        """
        user_name = kwargs.pop("user_name", kwargs.pop("name", None))
        super().__init__(user_name=user_name, damping=damping)
        self.nodes = []
        self.node_range = []
        self.node_only = False
        
        if kwargs:
            if "nodes" in kwargs and "node_range" in kwargs:
                raise ValueError("Both nodes and node_range cannot be provided at the same time")

            nodes = kwargs.get("nodes", [])
            node_range = kwargs.get("node_range", [])
            node_only = kwargs.get("node_only", False)

            if nodes and not isinstance(nodes, (list, np.ndarray)):
                raise ValueError("nodes should be a list of integers")

            if node_range:
                if not isinstance(node_range, (list, np.ndarray)) or len(node_range) != 2:
                    raise ValueError("node_range should be a list of 2 integers")

            self.nodes = list(nodes) if nodes is not None else []
            self.node_range = list(node_range) if node_range is not None else []
            self.node_only = bool(node_only)

    def to_tcl(self) -> str:
        """Render this node region as OpenSees Tcl commands.

        Returns:
            The Tcl command string.

        Raises:
            ValueError: If the region is not currently managed.
        """
        if self.tag is None:
            raise ValueError(f"Region '{self.user_name}' must be managed before rendering TCL")
            
        cmd = f"region {self.tag}"
        if len(self.node_range) > 0:
            cmd += " -node" + ("Only" if self.node_only else "") + "Range"
            cmd += " {} {}".format(*self.node_range)
        elif len(self.nodes) > 0:
            cmd += " -node" + ("Only" if self.node_only else "")
            cmd += " " + " ".join(str(n) for n in self.nodes)

        if self.damping:
            if self.damping.get_type() in ["Rayleigh", "Frequency Rayleigh"]:
                cmd += f" -rayleigh {self.damping.alphaM} {self.damping.betaK} {self.damping.betaKInit} {self.damping.betaKComm}"
            else:
                cmd += f" -damp {self.damping.tag}"
        return cmd
    
    def __str__(self) -> str:
        res = super().__str__()
        res += f"\n\tNum of Nodes: {len(self.nodes)}"
        res += f"\n\tNode Range: {self.node_range}"
        return res

    @staticmethod
    def get_type() -> str:
        """Get the region type name.

        Returns:
            The string "NodeRegion".
        """
        return "NodeRegion"


from femora.core.region_manager import RegionManager

def initialize_region_base():
    """No-op for compatibility."""
    pass
