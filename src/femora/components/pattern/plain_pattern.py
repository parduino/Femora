from __future__ import annotations

from typing import List

from femora.core.load_base import Load
from femora.core.load_manager import LoadManager
from femora.core.pattern_base import Pattern
from femora.core.time_series_base import TimeSeries


class PlainPattern(Pattern):
    """OpenSees ``Plain`` load pattern with attached loads.

    A plain pattern references one managed ``TimeSeries`` and owns a collection
    of loads that render inside the pattern block. This pattern applies a static
    or dynamic set of loads proportional to a specified time series.

    Tcl form:
        ``pattern Plain <patternTag> <timeSeriesTag> [-fact factor] { ... }``

    Example:
        ```python
        import femora as fm

        model = fm.Model()

        # Create a time series
        ts = model.timeSeries.constant(factor=2.0)

        # Create a plain pattern
        pattern = model.pattern.plain(time_series=ts)
        print(pattern.tag)

        # Add a nodal load directly to the pattern using the proxy
        node_load = pattern.add_load.node(node_tag=1, dof=1, value=10.0)
        print(node_load.tag)

        # Add an element load
        ele_load = pattern.add_load.element(ele_tag=2, dof=2, value=5.0)
        print(ele_load.tag)
        ```
    """

    def __init__(self, time_series: TimeSeries, factor: float = 1.0):
        """Create a plain load pattern.

        Args:
            time_series: Managed ``TimeSeries`` referenced by this pattern.
            factor: Optional scale factor applied to contained loads.

        Raises:
            ValueError: If ``time_series`` is invalid or unmanaged.
        """
        super().__init__("Plain")
        if not isinstance(time_series, TimeSeries):
            raise ValueError("time_series must be a TimeSeries object")
        if time_series.tag is None:
            raise ValueError("time_series must be managed before it is used by a pattern")
        self.time_series = time_series
        self.factor = float(factor)
        self._loads: List[Load] = []

    def add_load_instance(self, load: Load) -> None:
        """Attach an existing load to this pattern.

        If the load is already attached, this method does nothing.

        Args:
            load: Load instance to emit inside the pattern block.

        Raises:
            ValueError: If ``load`` is not a ``Load`` instance.
        """
        if not isinstance(load, Load):
            raise ValueError("load must be an instance of Load")
        if load in self._loads:
            return
        load.pattern_tag = self.tag
        self._loads.append(load)

    def remove_load(self, load: Load) -> None:
        """Detach a load from this pattern if it is currently attached.

        Args:
            load: Load instance to remove.
        """
        if load in self._loads:
            self._loads.remove(load)
            load.pattern_tag = None

    def clear_loads(self) -> None:
        """Detach all loads from this pattern.

        All loads currently associated with this pattern will be removed,
        and their ``pattern_tag`` attribute will be reset.
        """
        for load in self._loads:
            load.pattern_tag = None
        self._loads.clear()

    def get_loads(self) -> List[Load]:
        """Return a copy of the loads attached to this pattern.

        Returns:
            A list of Load instances attached to this pattern.
        """
        return list(self._loads)

    def to_tcl(self) -> str:
        """Render this pattern and its attached loads as an OpenSees Tcl block.

        Returns:
            A string representing the OpenSees Tcl command block for this pattern
            and its loads.
        """
        fact = f" -fact {self.factor}" if self.factor != 1.0 else ""
        lines = [f"pattern Plain {self._require_tag()} {self.time_series.tag}{fact} {{"]
        for load in self._loads:
            lines.append(f"\t{load.to_tcl()}")
        lines.append("}")
        return "\n".join(lines)

    class _AddLoadProxy:
        """Factory proxy for creating and attaching loads to a ``PlainPattern``.

        This proxy provides convenient methods to create various types of loads
        (e.g., nodal, element, single-point) and automatically attaches them
        to the owning ``PlainPattern`` instance. This ensures that the loads
        are rendered within the pattern's Tcl block.

        Example:
            ```python
            import femora as fm

            model = fm.Model()
            ts = model.timeSeries.constant(factor=1.0)
            pattern = model.pattern.plain(time_series=ts)

            # Use the proxy to create and attach a nodal load
            nodal_load = pattern.add_load.node(node_tag=1, dof=1, value=50.0)

            # Use the proxy to create and attach an element load
            element_load = pattern.add_load.element(ele_tag=10, dof=2, value=100.0)
            ```
        """

        def __init__(self, pattern: "PlainPattern"):
            """Create a proxy for ``pattern``.

            Args:
                pattern: The ``PlainPattern`` instance to which loads will be attached.
            """
            self._pattern = pattern

        def _load_manager(self) -> LoadManager:
            pattern_owner = self._pattern._owner
            if pattern_owner is None:
                raise ValueError("Pattern must be managed before adding loads")
            return pattern_owner._mesh_maker.load

        def node(self, **kwargs) -> Load:
            """Create a nodal load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to ``LoadManager.node``.

            Returns:
                Created and attached load instance.
            """
            load = self._load_manager().node(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def element(self, **kwargs) -> Load:
            """Create an element load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to ``LoadManager.element``.

            Returns:
                Created and attached load instance.
            """
            load = self._load_manager().element(**kwargs)
            self._pattern.add_load_instance(load)
            return load

        def sp(self, **kwargs) -> Load:
            """Create a single-point load and attach it to the owning pattern.

            Args:
                **kwargs: Arguments forwarded to ``LoadManager.sp``.

            Returns:
                Created and attached load instance.
            """
            load = self._load_manager().sp(**kwargs)
            self._pattern.add_load_instance(load)
            return load

    @property
    def add_load(self) -> "PlainPattern._AddLoadProxy":
        """Return a proxy for creating loads directly on this pattern.

        This property provides a convenient factory interface to create and
        automatically associate various types of loads (e.g., node, element, sp)
        with this ``PlainPattern`` instance.

        Returns:
            An instance of ``_AddLoadProxy`` for creating and attaching loads.
        """
        return PlainPattern._AddLoadProxy(self)