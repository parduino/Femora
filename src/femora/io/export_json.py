# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

from __future__ import annotations

import json
import os
import weakref
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

SCHEMA_VERSION = 1
FORMAT_NAME = "femora_model_snapshot"


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, str, int, float)):
        return value
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _json_safe(value.item())
        return [_json_safe(v) for v in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


def _related_tag(obj: Any) -> Optional[int]:
    if obj is None:
        return None
    tag = getattr(obj, "tag", None)
    return int(tag) if tag is not None else None


def _add_identity_fields(data: Dict[str, Any], obj: Any) -> Dict[str, Any]:
    tag = getattr(obj, "tag", None)
    if tag is not None:
        data["tag"] = int(tag)

    user_name = getattr(obj, "user_name", None)
    if user_name is not None and str(user_name).strip():
        data["user_name"] = str(user_name)

    name = getattr(obj, "name", None)
    if name is not None and str(name).strip():
        if data.get("user_name") != name:
            data["name"] = str(name)

    data["type"] = obj.__class__.__name__
    return data


def _add_opensees_class(data: Dict[str, Any], obj: Any) -> None:
    for attr in (
        "material_name",
        "section_name",
        "pattern_type",
        "series_type",
        "motion_type",
        "recorder_type",
        "element_type",
    ):
        value = getattr(obj, attr, None)
        if value is not None and str(value).strip():
            data["opensees_class"] = str(value)
            return

    transformation_type = getattr(obj, "transformation_type", None)
    if transformation_type is None:
        transformation_type = getattr(obj, "_transformation_type", None)
    if transformation_type is not None and str(transformation_type).strip():
        data["opensees_class"] = str(transformation_type)


def _serialize_object(obj: Any, extra_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    _add_identity_fields(data, obj)
    _add_opensees_class(data, obj)
    if extra_fields:
        data.update(extra_fields)
    return _json_safe(data)


def _serialize_manager_values(items: Iterable[Any]) -> List[Dict[str, Any]]:
    values = list(items)
    values.sort(key=lambda obj: (getattr(obj, "tag", float("inf")), obj.__class__.__name__))
    return [_serialize_object(obj) for obj in values]


def _manager_items(manager: Any) -> List[Any]:
    if hasattr(manager, "get_all"):
        return list(manager.get_all().values())
    for attr in ("_items", "_instances"):
        items = getattr(manager, attr, None)
        if isinstance(items, dict):
            return list(items.values())
    return []


def _mesh_summary(mesh: Any) -> Optional[Dict[str, Any]]:
    if mesh is None:
        return None
    point_arrays = sorted(mesh.point_data.keys()) if hasattr(mesh, "point_data") else []
    cell_arrays = sorted(mesh.cell_data.keys()) if hasattr(mesh, "cell_data") else []
    return _json_safe(
        {
            "n_points": int(mesh.n_points),
            "n_cells": int(mesh.n_cells),
            "bounds": [float(v) for v in mesh.bounds],
            "point_data_arrays": list(point_arrays),
            "cell_data_arrays": list(cell_arrays),
        }
    )


def _serialize_material(material: Any) -> Dict[str, Any]:
    extra = {
        "material_type": getattr(material, "material_type", None),
    }
    return _serialize_object(material, extra)


def _serialize_element(element: Any) -> Dict[str, Any]:
    extra = {
        "ndof": getattr(element, "_ndof", None),
        "material_tag": _related_tag(getattr(element, "_material", None)),
        "section_tag": _related_tag(getattr(element, "_section", None)),
        "transformation_tag": _related_tag(getattr(element, "_transformation", None)),
    }
    return _serialize_object(element, extra)


def _serialize_section(section: Any) -> Dict[str, Any]:
    extra = {"section_type": getattr(section, "section_type", None)}
    return _serialize_object(section, extra)


def _serialize_region(region: Any) -> Dict[str, Any]:
    damping = getattr(region, "damping", None)
    extra = {"damping_tag": _related_tag(damping)}
    return _serialize_object(region, extra)


def _serialize_pattern(pattern: Any) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    time_series = getattr(pattern, "time_series", None)
    if time_series is not None:
        extra["time_series_tag"] = _related_tag(time_series)
    return _serialize_object(pattern, extra)


def _serialize_load(load: Any) -> Dict[str, Any]:
    extra = {"pattern_tag": getattr(load, "pattern_tag", None)}
    return _serialize_object(load, extra)


def _serialize_recorder(recorder: Any) -> Dict[str, Any]:
    return _serialize_object(recorder)


def _serialize_damping(damping: Any) -> Dict[str, Any]:
    return _serialize_object(damping)


def _serialize_transformation(transformation: Any) -> Dict[str, Any]:
    extra = {
        "dimension": getattr(transformation, "_dimension", None),
    }
    return _serialize_object(transformation, extra)


def _serialize_interface(interface: Any) -> Dict[str, Any]:
    return _serialize_object(interface)


def _serialize_sp_constraint(constraint: Any) -> Dict[str, Any]:
    extra = {
        "node_tag": getattr(constraint, "node_tag", None),
        "dofs": getattr(constraint, "dofs", None),
    }
    return _serialize_object(constraint, extra)


def _serialize_mp_constraint(constraint: Any) -> Dict[str, Any]:
    extra = {
        "master_node": getattr(constraint, "master_node", None),
        "slave_nodes": getattr(constraint, "slave_nodes", None),
    }
    return _serialize_object(constraint, extra)


def _serialize_analysis_component(component: Any) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    for attr in ("system_type", "integrator_type", "algorithm_type", "handler_type", "test_type"):
        value = getattr(component, attr, None)
        if value is not None:
            extra["component_kind"] = str(value)
            break
    return _serialize_object(component, extra)


def _serialize_analysis(analysis: Any) -> Dict[str, Any]:
    extra = {
        "analysis_type": getattr(analysis, "analysis_type", None),
        "constraint_handler_tag": _related_tag(getattr(analysis, "constraint_handler", None)),
        "numberer_tag": _related_tag(getattr(analysis, "numberer", None)),
        "system_tag": _related_tag(getattr(analysis, "system", None)),
        "algorithm_tag": _related_tag(getattr(analysis, "algorithm", None)),
        "test_tag": _related_tag(getattr(analysis, "test", None)),
        "integrator_tag": _related_tag(getattr(analysis, "integrator", None)),
    }
    return _serialize_object(analysis, extra)


def _serialize_meshpart(meshpart: Any) -> Dict[str, Any]:
    element = getattr(meshpart, "element", None)
    region = getattr(meshpart, "region", None)
    mesh = getattr(meshpart, "mesh", None)
    extra = {
        "mesh_type": getattr(meshpart, "mesh_type", None),
        "category": getattr(meshpart, "category", None),
        "region_tag": _related_tag(region),
        "element_tag": _related_tag(element),
    }
    data = _serialize_object(meshpart, extra)
    if mesh is not None:
        data.update(_mesh_summary(mesh))
    else:
        data["n_points"] = 0
        data["n_cells"] = 0
        data["bounds"] = []
        data["point_data_arrays"] = []
        data["cell_data_arrays"] = []
    return data


def _serialize_assembly_section(section: Any) -> Dict[str, Any]:
    meshpart_tags = [
        int(part.tag)
        for part in getattr(section, "meshparts_list", [])
        if getattr(part, "tag", None) is not None
    ]
    data = _serialize_object(
        section,
        {
            "meshpart_names": list(getattr(section, "meshparts", [])),
            "meshpart_tags": meshpart_tags,
            "num_partitions": int(getattr(section, "num_partitions", 1)),
            "merge_points": bool(getattr(section, "merge_points", True)),
            "partition_algorithm": str(getattr(section, "partition_algorithm", "")),
        },
    )
    mesh_summary = _mesh_summary(getattr(section, "mesh", None))
    if mesh_summary is not None:
        data["mesh_summary"] = mesh_summary
    return data


def _resolve_process_component(component_ref: Any) -> Any:
    if isinstance(component_ref, weakref.ref):
        return component_ref()
    return component_ref


def _serialize_process(process: Any) -> Dict[str, Any]:
    steps: List[Dict[str, Any]] = []
    for index, step in enumerate(getattr(process, "steps", [])):
        component = _resolve_process_component(step.get("component"))
        step_data: Dict[str, Any] = {
            "index": index,
            "description": step.get("description", "") or "",
        }
        if component is None:
            step_data["type"] = "Unknown"
        else:
            step_data["type"] = component.__class__.__name__
            tag = getattr(component, "tag", None)
            if tag is not None:
                step_data["tag"] = int(tag)
            name = getattr(component, "name", None) or getattr(component, "user_name", None)
            if name is not None and str(name).strip():
                step_data["name"] = str(name)
        steps.append(_json_safe(step_data))
    return {"num_steps": len(steps), "steps": steps}


def build_model_snapshot(model: Any) -> Dict[str, Any]:
    assembled_mesh = getattr(model, "assembled_mesh", None)
    assembled_summary: Dict[str, Any] = {"exists": assembled_mesh is not None}
    if assembled_mesh is not None:
        assembled_summary.update(_mesh_summary(assembled_mesh))

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "format": FORMAT_NAME,
        "model": {
            "class": "Model",
            "model_name": getattr(model, "model_name", None),
            "model_path": getattr(model, "model_path", None),
            "results_folder": model.get_results_folder() if hasattr(model, "get_results_folder") else "",
        },
        "tag_starts": {
            "node": int(getattr(model, "_start_nodetag", 1)),
            "element": int(getattr(model, "_start_ele_tag", 1)),
            "core": int(getattr(model, "_start_core_tag", 0)),
        },
        "managers": {
            "materials": [_serialize_material(m) for m in model.material.get_all().values()],
            "elements": [_serialize_element(e) for e in model.element.get_all().values()],
            "sections": [_serialize_section(s) for s in model.section.get_all().values()],
            "regions": [_serialize_region(r) for r in model.region.get_all().values()],
            "time_series": _serialize_manager_values(model.time_series.get_all().values()),
            "ground_motions": _serialize_manager_values(model.ground_motion.get_all().values()),
            "patterns": [_serialize_pattern(p) for p in model.pattern.get_all().values()],
            "loads": [_serialize_load(load) for load in model.load.get_all().values()],
            "dampings": [_serialize_damping(d) for d in model.damping.get_all().values()],
            "recorders": [_serialize_recorder(r) for r in model.recorder.get_all().values()],
            "interfaces": [_serialize_interface(i) for i in model.interface.get_all().values()],
            "transformations": [_serialize_transformation(t) for t in model.transformation.get_all().values()],
            "constraints": {
                "sp": [_serialize_sp_constraint(c) for c in model.constraint.sp.get_all().values()],
                "mp": [_serialize_mp_constraint(c) for c in model.constraint.mp.get_all().values()],
            },
            "analyses": {
                "system": [_serialize_analysis_component(c) for c in _manager_items(model.analysis.system)],
                "numberer": [_serialize_analysis_component(c) for c in _manager_items(model.analysis.numberer)],
                "constraints": [_serialize_analysis_component(c) for c in _manager_items(model.analysis.constraint)],
                "integrator": [_serialize_analysis_component(c) for c in _manager_items(model.analysis.integrator)],
                "algorithm": [_serialize_analysis_component(c) for c in _manager_items(model.analysis.algorithm)],
                "test": [_serialize_analysis_component(c) for c in _manager_items(model.analysis.test)],
                "analysis": [_serialize_analysis(a) for a in model.analysis.get_all().values()],
            },
        },
        "meshparts": [_serialize_meshpart(p) for p in model.meshpart.get_all().values()],
        "assembly_sections": [_serialize_assembly_section(s) for s in model.assembler.get_all().values()],
        "assembled_mesh": assembled_summary,
        "process": _serialize_process(model.process),
    }
    return _json_safe(snapshot)


def export_to_json(model: Any, filename: Optional[str] = None, indent: int = 2) -> bool:
    """Export a lightweight structural snapshot of the model to JSON."""
    if filename is None:
        if model.model_name is None or model.model_path is None:
            raise ValueError("Either provide a filename or set model_name and model_path")
        filename = os.path.join(model.model_path, f"{model.model_name}.json")

    if not str(filename).endswith(".json"):
        filename = f"{filename}.json"

    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

    snapshot = build_model_snapshot(model)
    with open(filename, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=indent)
        handle.write("\n")
    return True


__all__ = ["SCHEMA_VERSION", "FORMAT_NAME", "build_model_snapshot", "export_to_json"]
