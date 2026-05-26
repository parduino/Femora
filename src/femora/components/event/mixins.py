"""Lifecycle and mesh-generation mixins for model interfaces.

These mixin classes define interface behaviors and hooks during the Model assembly 
and simulation lifecycle.
"""

class GeneratesMeshMixin:
    """Mixin for interfaces that must generate their own mesh cells.

    Classes inheriting from this mixin are expected to construct and integrate 
    custom mesh elements (cells) into the global model during the assembly phase.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [],
    }

    interface_mesh = None  # type: ignore

    def build_mesh(self, **kwargs) -> None:
        """Populate the internal interface mesh.

        This method must be overridden by subclasses to generate the mesh cells
        associated with the interface.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the build context.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def integrate_mesh(self, assembled_mesh, **kwargs) -> None:
        """Merge or attach the custom interface mesh to the global assembled mesh.

        Args:
            assembled_mesh: The global assembled mesh object to which the interface
                mesh cells will be attached.
            **kwargs: Arbitrary keyword arguments passed from the integration context.
        """
        pass


class GeneratesNodesMixin:
    """Mixin for interfaces that generate custom nodes without cell connectivity.

    Classes inheriting from this mixin generate independent nodes to be registered
    with the global model.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [],
    }

    new_nodes = []  # type: ignore

    def build_nodes(self, **kwargs) -> None:
        """Populate the custom nodes for the interface.

        This method must be overridden by subclasses to define the new nodes.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the build context.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def integrate_nodes(self, assembled_mesh, **kwargs) -> None:
        """Merge or attach the custom interface nodes to the global assembled mesh.

        Args:
            assembled_mesh: The global assembled mesh object to which the new
                nodes will be registered.
            **kwargs: Arbitrary keyword arguments passed from the integration context.
        """
        pass


class GeneratesConstraintsMixin:
    """Mixin for interfaces that create multi-point or single-point constraints.

    Classes inheriting from this mixin generate constraints to couple nodes or degrees
    of freedom in the system.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [],
    }

    constraints = []  # type: ignore

    def build_constraints(self, **kwargs) -> None:
        """Construct the multi-point or single-point constraints.

        This method must be overridden by subclasses to generate the constraints.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the build context.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def register_constraints(self) -> None:
        """Register the constructed constraints with the global constraint managers."""
        pass


class HandlesDecompositionMixin:
    """Mixin notified when the model mesh partition/decomposition changes.

    Classes inheriting from this mixin react to repartitioning updates (e.g. core
    boundary changes in parallel computations) by updating their internal state.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": [],
    }

    def on_partition_update(self, assembled_mesh, **kwargs) -> None:
        """Update internal state after Core partition arrays change.

        Args:
            assembled_mesh: The global assembled mesh containing the updated core
                and partition information.
            **kwargs: Arbitrary keyword arguments passed from the update context.
        """
        pass
