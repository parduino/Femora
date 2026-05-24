from __future__ import annotations

import json
import os
from pathlib import Path

from femora.io.export_json import SCHEMA_VERSION, _serialize_meshpart, _serialize_region


def build_vtk_info_snapshot(model, vtk_filename: str):
    return {
        "schema_version": SCHEMA_VERSION,
        "format": "femora_vtk_info",
        "vtk_file": os.path.basename(vtk_filename),
        "regions": [_serialize_region(region) for region in model.region.get_all().values()],
        "meshparts": [_serialize_meshpart(meshpart) for meshpart in model.meshpart.get_all().values()],
    }


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
