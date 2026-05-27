from typing import Dict, List

from femora.core.element_base import Element


class GhostNodeElement(Element):
    """Virtual element that owns mesh nodes without creating OpenSees elements.

    GhostNodeElement keeps nodes in the Femora mesh and Tcl export pipeline
    without emitting a structural ``element`` command. It is commonly used for
    center-of-mass nodes, control or reference nodes, and mass application
    points that should not participate in element stiffness.

    Note:
        - Each instance receives a unique sentinel ``ndf`` value so mesh merging
          does not combine ghost nodes with structural nodes or with one
          another. At export, the sentinel is mapped back to the real DOF count
          through ``resolve_ndf``.
        - ``to_tcl`` returns a Tcl comment rather than an OpenSees element
          command; the owning nodes are still written by the export loop.

    Example:
        ```python
        from femora.core.model import Model

        model = Model()
        ghost = model.element.special.ghost_node(ndof=6)
        print(ghost.real_ndof)
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["__init__", "resolve_ndf", "is_ghost_ndf", "real_ndof"],
    }

    _SENTINEL_START = 1000
    _sentinel_counter = _SENTINEL_START
    _ndf_map: Dict[int, int] = {}

    def __init__(self, ndof: int = 3, **kwargs):
        """Create a GhostNodeElement with merge-protected sentinel DOF metadata.

        Args:
            ndof: Real number of DOFs per node written during Tcl export. Must
                be 3 or 6.
            **kwargs: Additional keyword arguments forwarded to the base
                element constructor.

        Raises:
            ValueError: If ``ndof`` is not 3 or 6.
        """
        if ndof not in (3, 6):
            raise ValueError(
                f"GhostNodeElement requires 3 or 6 DOFs, but got {ndof}"
            )

        self._real_ndof = ndof
        sentinel_ndof = GhostNodeElement._next_sentinel(ndof)
        super().__init__("GhostNode", sentinel_ndof, **kwargs)

    @classmethod
    def _next_sentinel(cls, real_ndof: int) -> int:
        """Reserve and return the next unique sentinel ``ndf`` value.

        Args:
            real_ndof: Real DOF count (3 or 6) mapped back during export.

        Returns:
            A unique sentinel ``ndf`` integer greater than or equal to 1000.
        """
        sentinel = cls._sentinel_counter
        cls._sentinel_counter += 1
        cls._ndf_map[sentinel] = real_ndof
        return sentinel

    @classmethod
    def resolve_ndf(cls, ndf_value: int) -> int:
        """Map a mesh ``ndf`` value to the real DOF count for Tcl export.

        If ``ndf_value`` is a ghost sentinel, it is resolved through the
        internal map. Otherwise the input is returned unchanged.

        Args:
            ndf_value: Raw ``ndf`` value from mesh ``point_data["ndf"]``.

        Returns:
            The real DOF count to write into the Tcl ``node`` command.
        """
        return cls._ndf_map.get(int(ndf_value), int(ndf_value))

    @classmethod
    def is_ghost_ndf(cls, ndf_value: int) -> bool:
        """Check whether an ``ndf`` value is a ghost-node sentinel.

        Args:
            ndf_value: The ``ndf`` value to inspect.

        Returns:
            ``True`` if the value is a ghost-node sentinel.
        """
        return int(ndf_value) >= cls._SENTINEL_START

    @property
    def real_ndof(self) -> int:
        """Return the real DOF count written to the Tcl ``node`` command."""
        return self._real_ndof

    def to_tcl(self, tag: int, nodes: List[int]) -> str:
        """Return a Tcl comment instead of an OpenSees element command.

        The owning node(s) are still written by the export loop; only the
        ``element`` line is replaced with a comment.

        Args:
            tag: Element tag assigned by the manager.
            nodes: Node tags owned by this ghost element.

        Returns:
            str: Tcl comment describing the ghost element.
        """
        return (
            f"# GhostNode Element number {tag} nodes({', '.join(str(n) for n in nodes)}) "
            f"with {self.real_ndof} DOFs - no structural element generated"
        )
