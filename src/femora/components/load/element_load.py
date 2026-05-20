from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from femora.core.load_base import Load


def _require_numeric(name: str, value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc


class ElementLoad(Load):
    """Element load for the OpenSees ``eleLoad`` command."""

    def __init__(
        self,
        *,
        kind: str,
        params: Dict[str, float],
        ele_tags: Optional[List[int]] = None,
        ele_range: Optional[Tuple[int, int]] = None,
        element_mask: Optional[object] = None,
        pid: Optional[int] = None,
    ) -> None:
        super().__init__()

        kind = str(kind).strip()
        if kind not in ("beamUniform", "beamPoint"):
            raise ValueError("kind must be 'beamUniform' or 'beamPoint'")

        if element_mask is not None:
            from femora.components.mask.mask_base import ElementMask

            if not isinstance(element_mask, ElementMask):
                raise ValueError("element_mask must be an ElementMask")

        if element_mask is None:
            if (ele_tags is None and ele_range is None) or (
                ele_tags is not None and ele_range is not None
            ):
                raise ValueError("Provide either ele_tags or ele_range or element_mask")

        if ele_tags is not None:
            if not isinstance(ele_tags, (list, tuple)) or len(ele_tags) == 0:
                raise ValueError("ele_tags must be a non-empty list/tuple of ints")
            try:
                ele_tags = [int(e) for e in ele_tags]
            except (TypeError, ValueError) as exc:
                raise ValueError("ele_tags must be integers") from exc
            if any(e < 1 for e in ele_tags):
                raise ValueError("ele_tags must be positive integers")

        if ele_range is not None:
            if not (isinstance(ele_range, (list, tuple)) and len(ele_range) == 2):
                raise ValueError("ele_range must be a tuple/list of (start, end)")
            try:
                start, end = int(ele_range[0]), int(ele_range[1])
            except (TypeError, ValueError) as exc:
                raise ValueError("ele_range bounds must be integers") from exc
            if start < 1 or end < 1 or end < start:
                raise ValueError("ele_range must be positive and end >= start")
            ele_range = (start, end)

        if not isinstance(params, dict):
            raise ValueError("params must be a dictionary of numeric values")

        normalized_params: Dict[str, float] = {}
        if kind == "beamUniform":
            if "Wy" not in params:
                raise ValueError("params.Wy is required for beamUniform")
            normalized_params["Wy"] = _require_numeric("Wy", params["Wy"])
            if "Wz" in params:
                normalized_params["Wz"] = _require_numeric("Wz", params["Wz"])
            if "Wx" in params:
                normalized_params["Wx"] = _require_numeric("Wx", params["Wx"])
        else:
            if "Py" not in params or "xL" not in params:
                raise ValueError("params.Py and params.xL are required for beamPoint")
            normalized_params["Py"] = _require_numeric("Py", params["Py"])
            normalized_params["xL"] = _require_numeric("xL", params["xL"])
            if "Pz" in params:
                normalized_params["Pz"] = _require_numeric("Pz", params["Pz"])
            if "Px" in params:
                normalized_params["Px"] = _require_numeric("Px", params["Px"])

        if pid is not None:
            try:
                pid = int(pid)
            except (TypeError, ValueError) as exc:
                raise ValueError("pid must be an integer") from exc
        else:
            pid = 0

        self.kind = kind
        self.ele_tags = ele_tags
        self.ele_range = ele_range
        self.params = normalized_params
        self.pid = pid
        self.element_mask = element_mask

    def _selector_tcl(self) -> str:
        if self.ele_tags is not None:
            tags_str = " ".join(str(e) for e in self.ele_tags)
            return f"-ele {tags_str}"
        assert self.ele_range is not None
        start, end = self.ele_range
        return f"-range {start} {end}"

    def to_tcl(self) -> str:
        if self.element_mask is not None:
            ids = self.element_mask.to_list()
            tags = self.element_mask.to_tags()
            sel = "-ele " + " ".join(str(t) for t in tags)
        else:
            sel = self._selector_tcl()

        if self.kind == "beamUniform":
            parts: List[str] = ["eleLoad", sel, "-type", "-beamUniform"]
            if "Wy" in self.params:
                parts.append(str(self.params["Wy"]))
            if "Wz" in self.params:
                parts.append(str(self.params["Wz"]))
            if "Wx" in self.params:
                parts.append(str(self.params["Wx"]))
            cmd = " ".join(parts)
        else:
            parts = ["eleLoad", sel, "-type", "-beamPoint"]
            parts.append(str(self.params["Py"]))
            if "Pz" in self.params:
                parts.append(str(self.params["Pz"]))
            parts.append(str(self.params["xL"]))
            if "Px" in self.params:
                parts.append(str(self.params["Px"]))
            cmd = " ".join(parts)

        pid = self.pid
        if self.element_mask is not None and hasattr(
            self.element_mask._mesh, "element_id_to_index"
        ):
            mesh = self.element_mask._mesh
            if ids:
                first = int(ids[0])
                if first in mesh.element_id_to_index:
                    pid = int(mesh.core_ids[mesh.element_id_to_index[first]])

        if pid is not None:
            return f"if {{$pid == {pid}}} {{ {cmd} }}"
        return cmd


__all__ = ["ElementLoad"]
