from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Iterator, List, Optional

from femora.core.damping_base import Damping
from femora.core.tagging import CompactRetagPolicy

if TYPE_CHECKING:
    from femora.components.MeshMaker import MeshMaker


class DampingManager:
    """Manager-owned lifecycle and tagging for damping objects."""

    def __init__(self, mesh_maker: MeshMaker):
        from femora.components.MeshMaker import MeshMaker as MeshMakerClass

        if not isinstance(mesh_maker, MeshMakerClass):
            raise TypeError("mesh_maker must be a MeshMaker instance")
        existing_manager = getattr(mesh_maker, "damping", None)
        if isinstance(existing_manager, DampingManager):
            raise ValueError("mesh_maker already owns a damping manager")

        self._mesh_maker = mesh_maker
        self._dampings: Dict[int, Damping] = {}
        self._names: Dict[str, Damping] = {}
        self._start_tag = 1
        self._tagging = CompactRetagPolicy[Damping]()

    def add(self, damping: Damping) -> Damping:
        if not isinstance(damping, Damping):
            raise TypeError("damping must be a Damping instance")
        if damping._owner is None:
            damping._owner = self
        elif damping._owner is not self:
            raise ValueError("damping already belongs to another manager")
        if damping.user_name == "UnnamedDamping":
            damping.user_name = self._generate_default_name(damping)
        existing_by_name = self._names.get(damping.user_name)
        if existing_by_name is not None and existing_by_name is not damping:
            raise ValueError(f"Damping name '{damping.user_name}' already exists in this manager")

        damping.tag = self._tagging.assign_tag(self._dampings, damping, self._start_tag)
        self._dampings[damping.tag] = damping
        self._names[damping.user_name] = damping
        return damping

    def rayleigh(self, **kwargs):
        from femora.components.damping.dampings import RayleighDamping
        return self.add(RayleighDamping(**kwargs))

    def modal(self, **kwargs):
        from femora.components.damping.dampings import ModalDamping
        return self.add(ModalDamping(**kwargs))

    def frequency_rayleigh(self, **kwargs):
        from femora.components.damping.dampings import FrequencyRayleighDamping
        return self.add(FrequencyRayleighDamping(**kwargs))

    def uniform(self, **kwargs):
        from femora.components.damping.dampings import UniformDamping
        return self.add(UniformDamping(**kwargs))

    def secant_stiffness_proportional(self, **kwargs):
        from femora.components.damping.dampings import SecantStiffnessProportional
        return self.add(SecantStiffnessProportional(**kwargs))

    frequencyRayleigh = frequency_rayleigh
    secantStiffnessProportional = secant_stiffness_proportional

    def get(self, tag: int) -> Optional[Damping]:
        return self._dampings.get(int(tag))

    def remove(self, tag: int) -> None:
        damping = self._dampings.pop(int(tag), None)
        if damping is not None:
            self._names.pop(damping.user_name, None)
            damping.tag = None
            damping._owner = None
            self._reassign_tags()

    def get_all(self) -> Dict[int, Damping]:
        return dict(self._dampings)

    def clear(self) -> None:
        for damping in list(self._dampings.values()):
            damping.tag = None
            damping._owner = None
        self._dampings.clear()
        self._names.clear()

    def set_tag_start(self, start_tag: int) -> None:
        self._start_tag = self._tagging.validate_start_tag(start_tag)
        self._reassign_tags()

    def _reassign_tags(self) -> None:
        self._tagging.reassign_tags(self._dampings, self._start_tag)
        self._names = {d.user_name: d for d in self._dampings.values()}

    def _generate_default_name(self, damping: Damping) -> str:
        base_name = damping.__class__.__name__
        if base_name not in self._names:
            return base_name

        index = 2
        while True:
            candidate = f"{base_name}_{index}"
            if candidate not in self._names:
                return candidate
            index += 1

    def get_available_types(self) -> List[str]:
        return [
            "rayleigh",
            "modal",
            "frequency rayleigh",
            "uniform",
            "secant stiffness proportional",
        ]

    def __len__(self) -> int:
        return len(self._dampings)

    def __iter__(self) -> Iterator[Damping]:
        return iter(self._dampings.values())
