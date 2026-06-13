# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

from abc import ABC
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional

from femora.core.event_bus import FemoraEvent

if TYPE_CHECKING:
    from femora.core.model import Model


class _BoundaryNamespace:
    """Boundary-specialized interface registration namespace."""

    def __init__(self, manager: "InterfaceManager"):
        self._manager = manager

    def absorber(
        self,
        *,
        num_layers: Optional[int] = None,
        num_partitions: Optional[int] = None,
        partition_algo: Optional[str] = None,
        geometry: Optional[str] = None,
        boundary_type: Optional[str] = None,
        rayleigh_damping: Optional[float] = None,
        match_damping: Optional[bool] = None,
        progress_callback=None,
        **kwargs,
    ) -> None:
        """Register a rectangular absorbing boundary to apply after assembly."""
        from femora.components.interface.boundary_absorber import _normalize_absorber_kwargs

        config = _normalize_absorber_kwargs(
            num_layers=num_layers,
            num_partitions=num_partitions,
            partition_algo=partition_algo,
            geometry=geometry,
            boundary_type=boundary_type,
            rayleigh_damping=rayleigh_damping,
            match_damping=match_damping,
            progress_callback=progress_callback,
            **kwargs,
        )
        self._manager._register_boundary_absorber(config)


class InterfaceBase(ABC):
    """Common logic for all interface objects on one Model model."""

    def __init__(self, name: str, owners: List[str]) -> None:
        self.name = name
        self.owners = owners
        self._owner: Optional["InterfaceManager"] = None

    def _bind_manager(self, manager: "InterfaceManager") -> None:
        if self._owner is not None and self._owner is not manager:
            raise ValueError("interface already belongs to another manager")
        self._owner = manager
        self._subscribe_events()

    def _model_events(self):
        return self._owner._mesh_maker.events

    def _subscribe_events(self) -> None:
        pass

    def _unsubscribe_events(self) -> None:
        pass


class InterfaceManager:
    """Model-owned factory and lifecycle for interface objects on one Model."""

    def __init__(self, mesh_maker: "Model") -> None:
        from femora.core.model import Model as ModelClass

        self._interfaces: Dict[str, InterfaceBase] = {}
        self._embeddedinfo_list: list = []
        self._beam_solid_count = 0
        self._beam_solid_conflict_subscribed = False
        if not isinstance(mesh_maker, ModelClass):
            raise TypeError("mesh_maker must be a Model instance")
        existing = getattr(mesh_maker, "interface", None)
        if isinstance(existing, InterfaceManager) and existing is not self:
            raise ValueError("mesh_maker already owns an interface manager")
        self._mesh_maker = mesh_maker
        mesh_maker.interface = self
        self.boundary = _BoundaryNamespace(self)
        self._boundary_absorbers: list[dict] = []
        self._boundary_post_assemble_subscribed = False

    def _register_boundary_absorber(self, config: dict) -> None:
        self._boundary_absorbers.append(config)
        self._ensure_boundary_absorber_subscribed()

    def _ensure_boundary_absorber_subscribed(self) -> None:
        if self._boundary_post_assemble_subscribed:
            return
        self._mesh_maker.events.subscribe(
            FemoraEvent.POST_ASSEMBLE,
            self._apply_boundary_absorbers,
        )
        self._boundary_post_assemble_subscribed = True

    def _release_boundary_absorber_subscription(self) -> None:
        if not self._boundary_post_assemble_subscribed:
            return
        self._mesh_maker.events.unsubscribe(
            FemoraEvent.POST_ASSEMBLE,
            self._apply_boundary_absorbers,
        )
        self._boundary_post_assemble_subscribed = False

    def _apply_boundary_absorbers(self, assembled_mesh=None, **kwargs) -> None:
        if not self._boundary_absorbers:
            return
        from femora.components.interface.boundary_absorber import apply_rectangular_absorbing_layer

        pending = list(self._boundary_absorbers)
        self._boundary_absorbers.clear()
        for config in pending:
            apply_rectangular_absorbing_layer(self._mesh_maker, config)

    def add(self, interface: InterfaceBase) -> InterfaceBase:
        if not isinstance(interface, InterfaceBase):
            raise TypeError("interface must be an InterfaceBase instance")
        if interface.name in self._interfaces and self._interfaces[interface.name] is not interface:
            raise ValueError(f"Interface with name '{interface.name}' already exists")
        interface._bind_manager(self)
        self._interfaces[interface.name] = interface
        from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface

        if isinstance(interface, EmbeddedBeamSolidInterface):
            self._register_beam_solid_interface()
        return interface

    def beam_solid_interface(self, **kwargs) -> InterfaceBase:
        from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface

        kwargs["meshpart"] = self._mesh_maker.meshpart
        return self.add(EmbeddedBeamSolidInterface(**kwargs))

    def node_interface(self, **kwargs) -> InterfaceBase:
        from femora.components.interface.embedded_node_interface import EmbeddedNodeInterface

        kwargs["meshpart"] = self._mesh_maker.meshpart
        return self.add(EmbeddedNodeInterface(**kwargs))

    def get(self, name: str) -> Optional[InterfaceBase]:
        return self._interfaces.get(name)

    def get_all(self) -> Dict[str, InterfaceBase]:
        return dict(self._interfaces)

    def require(self, name: str) -> InterfaceBase:
        interface = self._interfaces.get(name)
        if interface is None:
            raise ValueError(f"Interface '{name}' is not registered in InterfaceManager")
        return interface

    def require_registered(self, interface: InterfaceBase) -> InterfaceBase:
        if interface._owner is None:
            raise ValueError(
                f"Interface '{interface.name}' is not managed by InterfaceManager; "
                "create it with model.interface.beam_solid_interface(...) "
                "or model.interface.node_interface(...)"
            )
        if interface._owner is not self:
            raise ValueError(
                f"Interface '{interface.name}' belongs to a different model's InterfaceManager"
            )
        registered = self._interfaces.get(interface.name)
        if registered is not interface:
            raise ValueError(
                f"Interface '{interface.name}' is not registered in the current InterfaceManager"
            )
        return interface

    def _release_interface(self, interface: InterfaceBase) -> None:
        interface._unsubscribe_events()
        interface._owner = None
        from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface

        if isinstance(interface, EmbeddedBeamSolidInterface):
            interface._instance_embeddedinfo_list.clear()
            self._unregister_beam_solid_interface()

    def _register_beam_solid_interface(self) -> None:
        self._beam_solid_count += 1
        if self._beam_solid_count == 1:
            self._ensure_beam_solid_conflict_subscribed()

    def _unregister_beam_solid_interface(self) -> None:
        if self._beam_solid_count <= 0:
            return
        self._beam_solid_count -= 1
        if self._beam_solid_count == 0:
            self._release_beam_solid_conflict_subscription_if_idle()

    def _ensure_beam_solid_conflict_subscribed(self) -> None:
        if self._beam_solid_conflict_subscribed:
            return
        self._mesh_maker.events.subscribe(
            FemoraEvent.RESOLVE_CORE_CONFLICTS,
            self._resolve_beam_solid_conflicts,
        )
        self._beam_solid_conflict_subscribed = True

    def _release_beam_solid_conflict_subscription_if_idle(self) -> None:
        if self._beam_solid_count != 0:
            return
        if not self._beam_solid_conflict_subscribed:
            return
        self._mesh_maker.events.unsubscribe(
            FemoraEvent.RESOLVE_CORE_CONFLICTS,
            self._resolve_beam_solid_conflicts,
        )
        self._beam_solid_conflict_subscribed = False

    def _resolve_beam_solid_conflicts(self, assembled_mesh, **kwargs):
        """Resolve core conflicts across beam-solid EmbeddedInfo collected during assembly."""
        from femora.components.interface.embedded_beam_solid_interface import EmbeddedBeamSolidInterface
        from femora.components.interface.embedded_info import EmbeddedInfo

        if not any(
            isinstance(interface, EmbeddedBeamSolidInterface)
            for interface in self._interfaces.values()
        ):
            return

        embeddedinfo_list = self._embeddedinfo_list
        if not embeddedinfo_list:
            return  # nothing to do
        # print("resolving core conflicts")
        # ----------------------------------------------------------
        # 1. Deduplicate identical EmbeddedInfo objects
        # ----------------------------------------------------------
        unique_infos: list[EmbeddedInfo] = []
        for info in embeddedinfo_list:
            if all(info != u for u in unique_infos):
                unique_infos.append(info)

        infos = unique_infos
        n = len(infos)

        # ----------------------------------------------------------
        # 2–3. Build similarity graph & detect conflicts
        # ----------------------------------------------------------
        parent = list(range(n))  # union-find structure

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int):
            pi, pj = find(i), find(j)
            if pi != pj:
                parent[pj] = pi

        for i in range(n):
            for j in range(i + 1, n):
                relation = infos[i].compare(infos[j])
                if relation == "conflict":
                    raise ValueError(
                        f"EmbeddedInfo conflict detected between {infos[i]} and {infos[j]}"
                    )
                elif relation == "similar":
                    union(i, j)
                # "equal" already handled via deduplication

        # ----------------------------------------------------------
        # 4. Apply lowest core number per connected component
        # ----------------------------------------------------------
        groups = defaultdict(list)  # root index → list[info index]
        for idx in range(n):
            groups[find(idx)].append(idx)

        for idx_list in groups.values():
            min_core = min(infos[i].core_number for i in idx_list)
            for i in idx_list:
                info = infos[i]
                # Create a new EmbeddedInfo with updated core_number
                new_info = EmbeddedInfo(
                    beams=info.beams,
                    core_number=min_core,
                    beams_solids=info.beams_solids
                )
                infos[i] = new_info
                for idx, orig in enumerate(embeddedinfo_list):
                    if orig == info:
                        embeddedinfo_list[idx] = new_info
                for interface in self._interfaces.values():
                    if not isinstance(interface, EmbeddedBeamSolidInterface):
                        continue
                    inst_list = interface._instance_embeddedinfo_list
                    for idx2, orig2 in enumerate(inst_list):
                        if orig2 == info:
                            inst_list[idx2] = new_info
                for _beams, solids in new_info.beams_solids:
                    try:
                        assembled_mesh.cell_data["Core"][solids] = min_core
                    except Exception as exc:
                        print(
                            f"[EmbeddedBeamSolidInterface] Failed to set core for solids {solids}: {exc}"
                        )
                try:
                    assembled_mesh.cell_data["Core"][list(new_info.beams)] = min_core
                except Exception as exc:
                    print(f"[EmbeddedBeamSolidInterface] Failed to set core for beams {new_info.beams}: {exc}")

    def remove(self, name: str) -> None:
        interface = self._interfaces.pop(name, None)
        if interface is None:
            return
        self._release_interface(interface)

    def clear(self) -> None:
        for interface in list(self._interfaces.values()):
            self._release_interface(interface)
        self._interfaces.clear()
        self._embeddedinfo_list.clear()
        self._boundary_absorbers.clear()
        self._release_boundary_absorber_subscription()
