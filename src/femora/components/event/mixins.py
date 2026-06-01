"""Lifecycle mixins for advanced event-driven components.

These mixins are primarily used by advanced interface-like components that
react to model lifecycle stages such as post-assembly augmentation or
partition-aware updates. They are not ordinary end-user modeling classes.

Each mixin documents one kind of work a component may perform:

- generate auxiliary mesh
- generate standalone nodes
- generate constraints after geometry is known
- react to partition/core ownership updates

Read these pages as extension roles rather than standalone features. The
mixins explain what an advanced component is responsible for when it hooks into
Femora's event system.
"""

class GeneratesMeshMixin:
    """Role mixin for components that generate auxiliary mesh cells.

    Use this mixin when a component needs to create its own mesh representation
    after the ordinary model geometry already exists. This is common for
    advanced interfaces that derive extra elements from the assembled mesh
    rather than from a simple pre-assembly meshpart.

    In practice, components using this mixin usually:

    1. subscribe to a lifecycle event such as `POST_ASSEMBLE`
    2. inspect the assembled mesh or nearby geometry
    3. build an internal interface mesh
    4. merge or attach that mesh into the model-owned assembled mesh

    The two hook methods separate those responsibilities:

    - `build_mesh()` creates the component's internal mesh description
    - `integrate_mesh()` inserts that mesh into the assembled model

    Example:
        ```python
        class MyInterface(GeneratesMeshMixin):
            def build_mesh(self, assembled_mesh, **kwargs):
                self.interface_mesh = assembled_mesh.extract_surface()

            def integrate_mesh(self, assembled_mesh, **kwargs):
                assembled_mesh.merge(self.interface_mesh, inplace=True)
        ```

    Tip:
        Use this mixin when the component is responsible for *cells* or an
        actual interface mesh. If the component only creates standalone points,
        [`GeneratesNodesMixin`][femora.components.event.mixins.GeneratesNodesMixin]
        is the better fit.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["build_mesh", "integrate_mesh"],
    }

    interface_mesh = None  # type: ignore

    def build_mesh(self, **kwargs) -> None:
        """Construct the component-owned auxiliary mesh.

        Subclasses implement this hook to derive the interface mesh they need
        from runtime context such as the assembled mesh, nearby cells, or
        component-specific geometry.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the build context.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def integrate_mesh(self, assembled_mesh, **kwargs) -> None:
        """Integrate the generated mesh into the model-owned assembled mesh.

        This hook runs after `build_mesh()` has created the component's
        auxiliary mesh. Subclasses use it to merge, attach, or otherwise
        register that geometry with the global assembled mesh.

        Args:
            assembled_mesh: The global assembled mesh object to which the interface
                mesh cells will be attached.
            **kwargs: Arbitrary keyword arguments passed from the integration context.
        """
        pass


class GeneratesNodesMixin:
    """Role mixin for components that generate standalone nodes.

    Use this mixin when a component needs to add points or nodes to the model
    but does not generate a full cell-based mesh. This is useful for advanced
    interfaces that create helper nodes first and later connect them through
    constraints or special elements.

    Under the hood, the workflow is usually:

    1. derive node locations from existing geometry or assembled state
    2. store the new nodes in component-owned data
    3. register or merge those nodes into the assembled model

    Example:
        ```python
        class ProbeNodes(GeneratesNodesMixin):
            def build_nodes(self, assembled_mesh, **kwargs):
                self.new_nodes = assembled_mesh.points[:4]

            def integrate_nodes(self, assembled_mesh, **kwargs):
                # Register those points with the owning model or mesh container.
                ...
        ```
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["build_nodes", "integrate_nodes"],
    }

    new_nodes = []  # type: ignore

    def build_nodes(self, **kwargs) -> None:
        """Construct the component-owned node set.

        Subclasses implement this hook when node positions can only be known at
        runtime, for example after assembly or after inspecting other geometry.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the build context.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def integrate_nodes(self, assembled_mesh, **kwargs) -> None:
        """Register or merge the generated nodes into the assembled model.

        Args:
            assembled_mesh: The global assembled mesh object to which the new
                nodes will be registered.
            **kwargs: Arbitrary keyword arguments passed from the integration context.
        """
        pass


class GeneratesConstraintsMixin:
    """Role mixin for components that build runtime constraints.

    Use this mixin when a component must create multi-point or single-point
    constraints only after it has discovered geometry relationships at runtime.
    This is common for embedded or coupling interfaces where the paired nodes
    are not fully known until the assembled mesh has been inspected.

    The two hook methods deliberately separate:

    - `build_constraints()`: decide *what constraints should exist*
    - `register_constraints()`: push those constraints into the owning model

    Example:
        ```python
        class CouplingInterface(GeneratesConstraintsMixin):
            def build_constraints(self, assembled_mesh, **kwargs):
                self.constraints = [("equal_dof", 10, 25, [1, 2, 3])]

            def register_constraints(self):
                for _, master, slave, dofs in self.constraints:
                    self._owner._mesh_maker.constraint.mp.equal_dof(master, [slave], dofs)
        ```

    Note:
        This mixin is about lifecycle-dependent constraint creation. If a
        constraint can be created directly up front, it usually does not need
        to be routed through the event system.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["build_constraints", "register_constraints"],
    }

    constraints = []  # type: ignore

    def build_constraints(self, **kwargs) -> None:
        """Construct the component-owned constraint description.

        Subclasses implement this hook after geometry pairing, node lookup, or
        post-assembly inspection has revealed what constraints are required.

        Args:
            **kwargs: Arbitrary keyword arguments passed from the build context.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def register_constraints(self) -> None:
        """Register the generated constraints with the owning model.

        Subclasses typically use model-owned constraint managers here rather
        than mutating the assembled mesh directly.
        """
        pass


class HandlesDecompositionMixin:
    """Role mixin for components that react to decomposition or core updates.

    Use this mixin when a component depends on partition/core ownership data
    and must update itself after the assembled mesh has been repartitioned or
    after core-conflict resolution has changed that ownership information.

    This is a narrower and more advanced role than ordinary assembly hooks. It
    matters when a component caches partition-sensitive state or needs to keep
    parallel/decomposition metadata aligned with the latest assembled mesh.

    Example:
        ```python
        class PartitionAwareInterface(HandlesDecompositionMixin):
            def on_partition_update(self, assembled_mesh, **kwargs):
                self.cached_core_ids = assembled_mesh.cell_data["Core"]
        ```

    Tip:
        Use this mixin only when the component genuinely depends on
        partition-aware state. Many advanced interfaces need `POST_ASSEMBLE`
        hooks but do not need decomposition updates.
    """

    __doc_controls__ = {
        "show_docstring_attributes": True,
        "members": ["on_partition_update"],
    }

    def on_partition_update(self, assembled_mesh, **kwargs) -> None:
        """Refresh component state after partition/core ownership changes.

        Subclasses implement this hook when the component stores data that must
        stay aligned with the current decomposition of the assembled mesh.

        Args:
            assembled_mesh: The global assembled mesh containing the updated core
                and partition information.
            **kwargs: Arbitrary keyword arguments passed from the update context.
        """
        pass
