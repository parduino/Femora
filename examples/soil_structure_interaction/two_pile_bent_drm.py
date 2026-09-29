# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

# femora-postprocess: examples/soil_structure_interaction/two_pile_bent_drm_postprocess.py

# %% [markdown]
# # Two-Pile Bent under DRM Loading
#
# Two vertical piles (`x = -2.5 and +2.5 m`) connected by a two-segment cap beam at
# `z = 3.0 m` support a mass at the beam center. A ground-motion pulse excites
# the surrounding soil, which transfers motion to the piles through embedded
# interfaces. PML layers at the edges of the soil absorb outgoing waves.
#
# The workflow generates the DRM input, builds and solves the model, and
# extracts response histories, pile profiles, forces, and a movie remotely.

# %%
"""Two-pile bent tutorial with a minimal remote Femora workflow.

Stages: input/drm -> build/bent -> solve/bent (16 ranks) -> postprocess (responses, movie).
Task functions are context callbacks; importing this module runs no simulation.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import femora as fm
import numpy as np
import pyvista as pv
from femora import Model
from femora.tools.transferFunction import TimeHistory, TransferFunction
from femora.utils.paths import motions_dir


# --8<-- [start:model-constants]
SOIL_E = 2.0e8
SOIL_NU = 0.4
SOIL_RHO = 2100.0
SOIL_BOUNDS = (-8.0, 8.0, -3.0, 3.0, -8.0, 0.0)
SOIL_DIVISIONS = (32, 12, 16)  # 0.5 m brick spacing

PILE_DIAMETER = 1.5
PILE_E = 1.0e10
PILE_NU = 0.3
PILE_ELEMENTS = 16
PILE_BOTTOM = -5.0
PILE_TOP = 3.0
PILE_X = 2.5
CAP_Z = 3.0
CAP_ELEMENTS = 16
LUMPED_MASS = 25_000.0

FINAL_TIME = 4.0
DYNAMIC_DT = 0.001
RECORDER_DT = 0.005

PHYSICAL_PARTITIONS = 8
ABSORBER_PARTITIONS = 8
RANKS = PHYSICAL_PARTITIONS + ABSORBER_PARTITIONS  # 16
ABSORBER_LAYERS = 4

POSTPROCESS = "two_pile_bent_drm_postprocess.py"
RESPONSE_FILE = "two_pile_bent_response.vtkhdf"
# --8<-- [end:model-constants]


def create_drm(context):
    """Create the DRM wave input from the surface pulse and return its path."""
    drm_file = context.output_dir / "drmload.h5drm"
    motion_dir = Path(context.workspace) / "motions"
    x_min, x_max, y_min, y_max, z_min, z_max = SOIL_BOUNDS
    nx, ny, nz = SOIL_DIVISIONS
    soil_box = pv.RectilinearGrid(
        np.linspace(x_min, x_max, nx + 1),
        np.linspace(y_min, y_max, ny + 1),
        np.linspace(z_min, z_max, nz + 1),
    ).cast_to_unstructured_grid()
    # --8<-- [start:incoming-motion]
    gravity = 9.81
    surface_motion = TimeHistory.load(
        acc_file=str(motion_dir / "ricker_surface.acc"),
        time_file=str(motion_dir / "ricker_surface.time"),
        unit_in_g=True,
        gravity=gravity,
    )
    # Use the same soil stiffness, density, and depth as the 3D model.
    shear_modulus = SOIL_E / (2.0 * (1.0 + SOIL_NU))
    vs_soil = math.sqrt(shear_modulus / SOIL_RHO)
    drm_profile = [
        {"h": 8.0, "vs": vs_soil, "rho": SOIL_RHO, "damping": 0.0},
    ]
    transfer_function = TransferFunction(
        soil_profile=drm_profile,
        rock={"vs": 8000.0, "rho": 2000.0, "damping": 0.0},
        f_max=180.0,
    )
    incident_motion, _, _ = transfer_function.deconvolve(
        surface_motion, return_all=True
    )
    drm_file = Path(drm_file)
    drm_file.parent.mkdir(parents=True, exist_ok=True)
    transfer_function.createDRM(
        soil_box,
        props={"shape": "box"},
        time_history=incident_motion,
        filename=str(drm_file),
    )
    # --8<-- [end:incoming-motion]
    return drm_file


def build_model(context):
    """Build the single PML two-pile bent case and return its Tcl path."""
    drm_file = Path(context.result("input", "drm")).resolve()
    if not drm_file.is_file():
        raise FileNotFoundError(drm_file)
    case_dir = Path(context.output_dir).resolve()
    results_dir = case_dir / "results"
    case_dir.mkdir(parents=True, exist_ok=True)
    model = Model(model_name="two_pile_bent_drm", model_path=str(case_dir))
    model.clear_model()
    model.set_results_folder(results_dir.resolve().as_posix())

    # --8<-- [start:soil]
    soil_material = model.material.nd.elastic_isotropic(
        user_name="soil_mat",
        E=SOIL_E,
        nu=SOIL_NU,
        rho=SOIL_RHO,
    )  # zero physical damping: linear elastic, no viscous terms
    soil_element = model.element.brick.std(ndof=3, material=soil_material)
    x_min, x_max, y_min, y_max, z_min, z_max = SOIL_BOUNDS
    nx, ny, nz = SOIL_DIVISIONS
    model.meshpart.volume.uniform_rectangular_grid(
        user_name="soil",
        element=soil_element,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        z_min=z_min,
        z_max=z_max,
        nx=nx,
        ny=ny,
        nz=nz,
    )
    # --8<-- [end:soil]

    # --8<-- [start:piles]
    radius = PILE_DIAMETER / 2.0
    pile_g = PILE_E / (2.0 * (1.0 + PILE_NU))
    pile_area = math.pi * PILE_DIAMETER**2 / 4.0
    pile_i = math.pi * PILE_DIAMETER**4 / 64.0
    pile_j = math.pi * PILE_DIAMETER**4 / 32.0
    pile_section = model.section.beam.elastic(
        user_name="pile_section",
        E=PILE_E,
        A=pile_area,
        Iz=pile_i,
        Iy=pile_i,
        G=pile_g,
        J=pile_j,
    )
    # vecxz=(0,1,0) is perpendicular to both vertical piles and horizontal beams.
    transformation = model.transformation.transformation3d(
        transf_type="PDelta",
        vecxz_x=0.0,
        vecxz_y=1.0,
        vecxz_z=0.0,
    )
    beam_element = model.element.beam.disp(
        ndof=6,
        section=pile_section,
        transformation=transformation,
        numIntgrPts=5,
    )
    model.meshpart.line.single_line(
        user_name="pile_left",
        element=beam_element,
        x0=-PILE_X, y0=0.0, z0=PILE_BOTTOM,
        x1=-PILE_X, y1=0.0, z1=PILE_TOP,
        number_of_lines=PILE_ELEMENTS,
    )
    model.meshpart.line.single_line(
        user_name="pile_right",
        element=beam_element,
        x0=PILE_X, y0=0.0, z0=PILE_BOTTOM,
        x1=PILE_X, y1=0.0, z1=PILE_TOP,
        number_of_lines=PILE_ELEMENTS,
    )
    model.meshpart.line.single_line(
        user_name="cap_left",
        element=beam_element,
        x0=-PILE_X, y0=0.0, z0=CAP_Z,
        x1=0.0, y1=0.0, z1=CAP_Z,
        number_of_lines=CAP_ELEMENTS,
    )
    model.meshpart.line.single_line(
        user_name="cap_right",
        element=beam_element,
        x0=PILE_X, y0=0.0, z0=CAP_Z,
        x1=0.0, y1=0.0, z1=CAP_Z,
        number_of_lines=CAP_ELEMENTS,
    )
    # --8<-- [end:piles]

    # --8<-- [start:interface]
    interface_left = model.interface.beam_solid_interface(
        name="pile_soil_interface_left",
        beam_part="pile_left",
        solid_parts=["soil"],
        radius=radius,
        n_peri=8,
        n_long=3,
        penalty_param=1.0e12,
        g_penalty=True,
    )
    interface_right = model.interface.beam_solid_interface(
        name="pile_soil_interface_right",
        beam_part="pile_right",
        solid_parts=["soil"],
        radius=radius,
        n_peri=8,
        n_long=3,
        penalty_param=1.0e12,
        g_penalty=True,
    )
    model.mass.meshpart.closest_point(
        meshpart_name="cap_left",
        xyz=(0.0, 0.0, CAP_Z),
        mass_vec=(LUMPED_MASS, 0.0, 0.0),
        combine="override",
    )
    # --8<-- [end:interface]

    # --8<-- [start:assembly]
    # --8<-- [start:boundary]
    model.interface.boundary.absorber(
        num_layers=ABSORBER_LAYERS,
        num_partitions=ABSORBER_PARTITIONS,
        partition_algo="kd-tree",
        geometry="Rectangular",
        rayleigh_damping=0.05,  # Supplementary damping in PML only; physical soil stays undamped
        match_damping=False,
        boundary_type="PML",
    )
    model.assembler.create_section(
        meshparts=["soil", "pile_left", "pile_right", "cap_left", "cap_right"],
        num_partitions=PHYSICAL_PARTITIONS,
        partition_algorithm="kd-tree",
        merge_points=True,
        tolerance=1.0e-6,
    )
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)

    actual_cores = set(int(core) for core in model.assembled_mesh.cell_data["Core"])
    if actual_cores != set(range(RANKS)):
        raise ValueError(
            f"Expected ranks 0..{RANKS - 1}, exported cores: {sorted(actual_cores)}"
        )

    outer_fixity = [1] * 9  # PML outer faces carry 9 DOFs per node
    model.constraint.sp.fix_macro_x_min(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_x_max(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_y_min(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_y_max(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_z_min(dofs=outer_fixity, tol=1.0e-6)
    # --8<-- [end:boundary]
    # --8<-- [end:assembly]

    # --8<-- [start:drm-input]
    drm_tcl_path = drm_file.resolve().as_posix()
    h5_pattern = model.pattern.h5drm(
        filepath=drm_tcl_path,
        factor=1.0,
        crd_scale=1.0,
        distance_tolerance=0.01,
        do_coordinate_transformation=1,
        transform_matrix=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        origin=[0.0, 0.0, 0.0],
    )
    # --8<-- [end:drm-input]

    # --8<-- [start:analysis]
    response_recorder = model.recorder.vtkhdf(
        file_base_name=RESPONSE_FILE,
        # Trial beam end actions in VTKHDF. Keep XML/interface recorders until
        # the installed OpenSees build and mixed-element mapping are verified.
        resp_types=["disp", "vel", "accel", "force3D", "localForce3D"],
        delta_t=RECORDER_DT,
    )
    interface_recorder = model.recorder.embedded_beam_solid_interface(
        interface=[interface_left, interface_right],
        dt=RECORDER_DT,
    )
    pile_force_recorder = model.recorder.beam_force(
        meshparts=["pile_left", "pile_right"],
        force_type="globalForce",
        file_prefix="pile_force",
        output_format="xml",
        include_time=True,
        delta_t=RECORDER_DT,
        precision=16,
    )
    pile_local_force_recorder = model.recorder.beam_force(
        meshparts=["pile_left", "pile_right"],
        force_type="localForce",
        file_prefix="pile_local_force",
        output_format="xml",
        include_time=True,
        delta_t=RECORDER_DT,
        precision=16,
    )
    cap_force_recorder = model.recorder.beam_force(
        meshparts=["cap_left", "cap_right"],
        force_type="globalForce",
        file_prefix="cap_force",
        output_format="xml",
        include_time=True,
        delta_t=RECORDER_DT,
        precision=16,
    )

    constraint_handler = model.analysis.constraint.plain()
    numberer = model.analysis.numberer.parallelrcm()
    system = model.analysis.system.mumps()
    test = model.analysis.test.energyincr(tol=1.0e-4, max_iter=10, print_flag=5)
    algorithm = model.analysis.algorithm.modifiednewton(factor_once=True)
    integrator = model.analysis.integrator.newmark(gamma=0.5, beta=0.25, form="D")

    dynamic_analysis = model.analysis.transient(
        name="dynamic_bent_response",
        constraint_handler=constraint_handler,
        numberer=numberer,
        system=system,
        test=test,
        algorithm=algorithm,
        integrator=integrator,
        dt=DYNAMIC_DT,
        final_time=FINAL_TIME,
        max_retries=0,
    )

    model.process.add_step(model.actions.set_time(0.0), "Start dynamic time at zero")
    model.process.add_step(h5_pattern, "Apply the H5DRM wave field")
    model.process.add_step(response_recorder, "Record displacement, velocity, acceleration")
    model.process.add_step(interface_recorder, "Record the embedded pile-soil interfaces")
    model.process.add_step(pile_force_recorder, "Record both piles' global end forces and moments")
    model.process.add_step(pile_local_force_recorder, "Record pile end actions in local beam axes")
    model.process.add_step(cap_force_recorder, "Record cap end actions for pile-head balance checks")
    model.process.add_step(dynamic_analysis, "Run the dynamic analysis")
    # --8<-- [end:analysis]

    # --8<-- [start:export-and-run]
    case_dir.mkdir(parents=True, exist_ok=True)
    tcl_file = case_dir / "model.tcl"
    model.export_to_tcl(filename=str(tcl_file.resolve()), progress_callback=lambda *_: None)

    # Match XML element tags to real geometry, not recorder/file ordering.
    mesh = model.assembled_mesh
    pile_geometry = {}
    for name in ("pile_left", "pile_right"):
        part = model.meshpart.get(name)
        cells = np.flatnonzero(mesh.cell_data["MeshPartTag_celldata"] == part.tag)
        pile_geometry[name] = [
            {"tag": int(model._start_ele_tag + cell),
             "core": int(mesh.cell_data["Core"][cell]),
             "ends_m": mesh.get_cell(int(cell)).points.tolist()}
            for cell in cells if mesh.celltypes[cell] == pv.CellType.LINE
        ]
    (case_dir / "pile_geometry.json").write_text(
        json.dumps(pile_geometry, indent=2), encoding="utf-8"
    )

    print("\nTwo-pile bent DRM response")
    print(f"  Nodes:       {model.assembled_mesh.n_points}")
    print(f"  Elements:    {model.assembled_mesh.n_cells}")
    print(f"  Piles:       2 x {PILE_ELEMENTS} elements (d={PILE_DIAMETER} m)")
    print(f"  Cap:         2 x {CAP_ELEMENTS} elements at z={CAP_Z} m")
    print(f"  DRM input:   {drm_file.resolve()}")
    print(f"  Tcl model:   {tcl_file.resolve()}")

    return tcl_file
    # --8<-- [end:export-and-run]


def postprocess_results(context, movies=False):
    """Run response extraction or movie rendering in a separate remote task."""
    import matplotlib

    matplotlib.use("Agg")
    spec = importlib.util.spec_from_file_location(
        "bent_postprocess", context.workspace / POSTPROCESS
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if movies:
        return module.render_bent_movie(
            results_root=context.workspace / "build", output_dir=context.output_dir,
        )
    return module.generate_results(
        results_root=context.workspace / "build",
        output_dir=context.output_dir,
        profiles=True,
        forces=True,
    )


# --8<-- [start:workflow]
def build_workflow():
    """Minimal single-case workflow: input -> build -> solve -> postprocess."""
    workflow = fm.Workflow("two-pile-bent-drm")
    # All tasks run remotely. Each stage waits for the previous one to finish.
    # context.output_dir is workspace / stage name / task name.
    workflow.add("input", tasks=[fm.tasks.Python("drm", create_drm)])
    workflow.add("build", parallel=False, tasks=[fm.tasks.Python("bent", build_model)])
    workflow.add(
        "solve",
        parallel=False,
        tasks=[fm.tasks.OpenSees("bent", "build/bent/model.tcl", ranks=RANKS)],
    )
    workflow.add(
        "postprocess", tasks=[
            fm.tasks.Python("responses", postprocess_results),
            fm.tasks.Python("movie", postprocess_results, kwargs={"movies": True}),
        ]
    )
    # Return derived results and diagnostic logs, not the large raw recorder files.
    workflow.outputs("postprocess/responses/*", "postprocess/movie/*",
                     "**/stdout.log", "build/*/model.tcl", "build/*/pile_geometry.json")
    return workflow
# --8<-- [end:workflow]


# --8<-- [start:submission]
if __name__ == "__main__":
    # Set an app and allocation accessible to your account before submitting.
    job = fm.submit(
        function=build_workflow,
        platform="tacc",
        settings={
            "app_id": "amnp95-femora-workflow-stampede3",
            "system": "stampede3",
            "queue": "skx-dev",
            "allocation": "DesignSafe-SimCenter",
            "nodes": 1,
            "cores_per_node": 48,
            "minutes": 120,
        },
        files={
            POSTPROCESS: Path(__file__).with_name(POSTPROCESS),
            "motions/ricker_surface.acc": motions_dir() / "ricker_surface.acc",
            "motions/ricker_surface.time": motions_dir() / "ricker_surface.time",
        },
    )
    print(f"Job UUID: {job.id}")
# --8<-- [end:submission]
