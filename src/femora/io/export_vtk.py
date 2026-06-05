from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

from femora.io.export_json import SCHEMA_VERSION


def build_vtk_info_snapshot(model, vtk_filename: str):
    payload = {
        "schema_version": SCHEMA_VERSION,
        "format": "femora_vtk_info",
        "vtk_file": os.path.basename(vtk_filename),
    }
    registry = getattr(model, "_part_registry", None)
    if registry is not None:
        payload.update(registry.build_snapshot(used_tags=_used_femora_part_tags(model.assembled_mesh)))
    return payload


def _used_femora_part_tags(mesh):
    if mesh is None or "FemoraPartTag" not in mesh.cell_data:
        return None
    return np.unique(np.asarray(mesh.cell_data["FemoraPartTag"], dtype=np.int32))


def _attach_femora_part_field_data(model, mesh) -> None:
    registry = getattr(model, "_part_registry", None)
    if registry is None:
        return
    registry.attach_field_data(mesh, used_tags=_used_femora_part_tags(mesh))


def _info_json_filename(vtk_filename: str) -> str:
    path = Path(vtk_filename)
    return str(path.with_name(f"{path.stem}_info.json"))


def export_to_vtk(model, filename=None, write_info_json=False, indent=2):
    '''
    Export the model to a vtk file

    Args:
        model: Femora Model instance with an assembled mesh.
        filename (str, optional): The filename to export to. If None,
                                uses model_name in model_path
        write_info_json (bool, optional): When True, also write a lightweight
                                sidecar JSON file with region and meshpart info.
        indent (int, optional): JSON indentation level for sidecar info.

    Returns:
        bool: True if export was successful, False otherwise
    '''
    # Determine the full file path
    if filename is None:
        if model.model_name is None or model.model_path is None:
            raise ValueError("Either provide a filename or set model_name and model_path")
        filename = os.path.join(model.model_path, f"{model.model_name}.vtk")

    # check if the end is not .vtk then add it
    if not filename.endswith('.vtk'):
        filename += '.vtk'
    # Ensure the directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)

    # Get the assembled content
    if model.assembled_mesh is None:
        print("No mesh found")
        raise ValueError("No mesh found\n Please assemble the mesh first")

    _attach_femora_part_field_data(model, model.assembled_mesh)

    # export to vtk
    # model.assembled_mesh.save(filename, binary=True)
    try:
        model.assembled_mesh.save(filename, binary=True)
    except Exception as e:
        raise e

    if write_info_json:
        info_filename = _info_json_filename(filename)
        payload = build_vtk_info_snapshot(model, filename)
        with open(info_filename, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=indent)
            handle.write("\n")
    return True
