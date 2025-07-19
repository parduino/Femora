class GeneratesMeshMixin:
    """Mixin for interfaces that must create their own mesh (cells)."""

    interface_mesh = None  # type: ignore

    def build_mesh(self, **kwargs):
        """Populate *interface_mesh*.  Must be overridden."""
        raise NotImplementedError

    def integrate_mesh(self, assembled_mesh, **kwargs):
        """Optional: merge or attach mesh to the main assembled mesh."""
        pass


class GeneratesNodesMixin:
    """Mixin for interfaces that only add nodes (no cells)."""

    new_nodes = []  # type: ignore

    def build_nodes(self, **kwargs):
        raise NotImplementedError

    def integrate_nodes(self, assembled_mesh, **kwargs):
        pass


class GeneratesConstraintsMixin:
    """Mixin for interfaces that create mp or sp constraints."""

    constraints = []  # type: ignore

    def build_constraints(self, **kwargs):
        raise NotImplementedError

    def register_constraints(self):
        """Push constraints to the global managers (mp/sp)."""
        pass


class HandlesDecompositionMixin:
    """Mixin that is notified when the mesh is repartitioned and may react."""

    def on_partition_update(self, assembled_mesh, **kwargs):
        """Update internal state after Core arrays change."""
        pass
    


