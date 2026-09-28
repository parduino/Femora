# =============================================================================
# Femora: Fast Efficient Meta-modeling for OpenSees-based Resilience Analysis
# Copyright 2026 Amin Pakzad and Pedro Arduino
# Developed at the UW Geotechnical Lab
# SPDX-License-Identifier: Apache-2.0
# =============================================================================

# femora-colab-input: examples/inputs/motions/ricker_surface.acc
# femora-colab-input: examples/inputs/motions/ricker_surface.time
# femora-postprocess: examples/soil_structure_interaction/dynamic_pile_soil_interaction_postprocess.py

# %% [markdown]
# # Boundary Effects in Dynamic Pile-Soil Interaction
#
# Apply the same H5DRM wave field to a pile-soil model with either a fixed,
# PML, or Rayleigh absorbing boundary. Comparing the pile-head histories shows
# how waves reflected by a finite boundary can influence the structural
# response.

# %%
"""Compare boundary treatments locally or as a remote Femora workflow.

Set the submission settings at the bottom, then run this file to submit.
The task functions receive their paths from workflow context. The workflow allocates
8 MPI ranks to Fixed and 16 each to Rayleigh and PML. It generates the common
DRM input once, waits for all three solves, then writes plots and CSV histories.
"""

from __future__ import annotations

import importlib.util

import femora as fm
import math
from pathlib import Path

from femora import Model
from femora.tools.transferFunction import TimeHistory, TransferFunction
from femora.utils.paths import motions_dir
import numpy as np
import pyvista as pv


SOIL_BOUNDS = (-8.0, 8.0, -3.0, 3.0, -8.0, 0.0)
SOIL_DIVISIONS = (12, 5, 12)
PILE_BOTTOM = -5.0
PILE_HEAD = 2.0
PILE_ELEMENTS = 16
PILE_DIAMETER = 1.0
FINAL_TIME = 12.0
DYNAMIC_DT = 0.001

POSTPROCESS = "dynamic_pile_soil_interaction_postprocess.py"


# Femora calls these task functions with a context; it is not a Python keyword.
# context.workspace is the shared run directory on the execution machine.
# context.output_dir is this task's folder: workspace / stage name / task name.
# context.inputs contains submitted values (unused in this tutorial).
# context.result(stage, task) retrieves an earlier task's returned value.
# Use these paths rather than assuming a particular current working directory.
def create_drm(context):
    """Generate the shared DRM file and return its path to later tasks."""
    drm_file = context.output_dir / "drmload.h5drm"
    motion_dir = context.workspace / "motions"
    # Each horizontal quadrant has nx by ny cells. Together they form a
    # uniform box with 2*nx by 2*ny cells and nz cells over the full depth.
    # These are the same bounds and divisions used by build_model below.
    x_min, x_max, y_min, y_max, z_min, z_max = SOIL_BOUNDS
    nx, ny, nz = SOIL_DIVISIONS
    soil_box = pv.RectilinearGrid(
        np.linspace(x_min, x_max, 2 * nx + 1),
        np.linspace(y_min, y_max, 2 * ny + 1),
        np.linspace(z_min, z_max, nz + 1),
    ).cast_to_unstructured_grid()
    gravity = 9.81
    motion_dir = Path(motion_dir)
    surface_motion = TimeHistory.load(
        acc_file=str(motion_dir / "ricker_surface.acc"),
        time_file=str(motion_dir / "ricker_surface.time"),
        unit_in_g=True,
        gravity=gravity,
    )
    drm_profile = [
        {
            "h": 2.0,
            "vs": 190.0,
            "rho": 19.9 * 1000.0 / gravity,
            "damping": 0.0,
        },
        {
            "h": 6.0,
            "vs": 240.0,
            "rho": 19.1 * 1000.0 / gravity,
            "damping": 0.0,
        },
    ]
    transfer_function = TransferFunction(
        soil_profile=drm_profile,
        rock={"vs": 8000.0, "rho": 2000.0, "damping": 0.0},
        f_max=180.0,
    )
    incident_motion, _, _ = transfer_function.deconvolve(
        surface_motion,
        return_all=True,
    )
    drm_file = Path(drm_file)
    drm_file.parent.mkdir(parents=True, exist_ok=True)
    transfer_function.createDRM(
        soil_box,
        props={"shape": "box"},
        time_history=incident_motion,
        filename=str(drm_file),
    )

    return drm_file



def build_model(context, boundary):
    """Build one boundary case in this task\'s folder and return its Tcl path."""
    drm_file = context.result("input", "drm")
    BOUNDARY_TYPE = {"fixed": "Fixed", "rayleigh": "Rayleigh", "pml": "PML"}.get(boundary.lower(), boundary)
    if BOUNDARY_TYPE not in {"Fixed", "Rayleigh", "PML"}:
        raise ValueError("boundary must be Fixed, Rayleigh, or PML")
    # Partition the inner soil box and pile over 8 ranks in every case.
    # Fixed has no absorber. Rayleigh and PML each add 8 absorber ranks.
    physical_parts = 8
    absorber_parts = 0 if BOUNDARY_TYPE == "Fixed" else 8
    ranks = physical_parts + absorber_parts  # Fixed=8, Rayleigh=16, PML=16.
    CASE_DIR = context.output_dir.resolve()
    RESULTS_DIR = CASE_DIR / "results"
    drm_file = Path(drm_file).resolve()
    if not drm_file.is_file():
        raise FileNotFoundError(drm_file)
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    model = Model(
        model_name="dynamic_pile_soil_interaction",
        model_path=str(CASE_DIR),
    )
    model.clear_model()
    model.set_results_folder(RESULTS_DIR.resolve().as_posix())

    gravity = 9.81
    # Physical soil is undamped; damping is assigned only to outer absorbers.
    soil_region = model.region.element(
        user_name="physical_soil",
    )

    soil_layers = (
        ("soft_soil", 190.0, 19.9, -2.0, 0.0),
        ("stiff_soil", 240.0, 19.1, -8.0, -2.0),
    )
    soil_parts = []
    for name, vs, unit_weight, z_min, z_max in soil_layers:
        density = unit_weight * 1000.0 / gravity
        shear_modulus = density * vs**2
        material = model.material.nd.elastic_isotropic(
            user_name=f"{name}_material",
            E=2.0 * shear_modulus * 1.3,
            nu=0.3,
            rho=density,
        )
        element = model.element.brick.std(ndof=3, material=material)
        x_min, x_max, y_min, y_max, _, _ = SOIL_BOUNDS
        nx, ny, nz_total = SOIL_DIVISIONS
        layer_nz = round(nz_total * (z_max - z_min) / 8.0)
        for block_name, block_x_min, block_x_max, block_y_min, block_y_max in (
            ("sw", x_min, 0.0, y_min, 0.0),
            ("se", 0.0, x_max, y_min, 0.0),
            ("nw", x_min, 0.0, 0.0, y_max),
            ("ne", 0.0, x_max, 0.0, y_max),
        ):
            part_name = f"{name}_{block_name}"
            model.meshpart.volume.geometric_rectangular_grid(
                user_name=part_name,
                element=element,
                region=soil_region,
                x_min=block_x_min,
                x_max=block_x_max,
                y_min=block_y_min,
                y_max=block_y_max,
                z_min=z_min,
                z_max=z_max,
                nx=nx,
                ny=ny,
                nz=layer_nz,
                x_ratio=1.0,
                y_ratio=1.0,
                z_ratio=1.0,
            )
            soil_parts.append(part_name)
    # --8<-- [end:soil-domain]


    # %% [markdown]
    # ## Define and couple the pile

    # %%
    # --8<-- [start:pile-and-interface]
    radius = PILE_DIAMETER / 2.0
    pile_E = 1.0e10
    pile_nu = 0.3
    pile_G = pile_E / (2.0 * (1.0 + pile_nu))
    pile_area = math.pi * PILE_DIAMETER**2 / 4.0
    pile_I = math.pi * PILE_DIAMETER**4 / 64.0
    pile_J = math.pi * PILE_DIAMETER**4 / 32.0

    pile_section = model.section.beam.elastic(
        user_name="pile_section",
        E=pile_E,
        A=pile_area,
        Iz=pile_I,
        Iy=pile_I,
        G=pile_G,
        J=pile_J,
    )
    transformation = model.transformation.transformation3d(
        transf_type="PDelta",
        vecxz_x=-1.0,
        vecxz_y=0.0,
        vecxz_z=0.0,
    )
    pile_element = model.element.beam.disp(
        ndof=6,
        section=pile_section,
        transformation=transformation,
        numIntgrPts=5,
    )
    model.meshpart.line.single_line(
        user_name="pile",
        element=pile_element,
        x0=0.0,
        y0=0.0,
        z0=PILE_BOTTOM,
        x1=0.0,
        y1=0.0,
        z1=PILE_HEAD,
        number_of_lines=PILE_ELEMENTS,
    )

    pile_soil_interface = model.interface.beam_solid_interface(
        name="pile_soil_interface",
        beam_part="pile",
        solid_parts=soil_parts,
        radius=radius,
        n_peri=8,
        n_long=3,
        penalty_param=1.0e12,
        g_penalty=True,
    )

    model.mass.meshpart.closest_point(
        meshpart_name="pile",
        xyz=(0.0, 0.0, PILE_HEAD),
        mass_vec=(25_000.0, 0.0, 0.0),
        combine="override",
    )
    # --8<-- [end:pile-and-interface]


    # %% [markdown]
    # ## Assemble the model and choose the outer boundary
    #
    # The physical soil box is only a finite portion of the surrounding ground.
    # ``BOUNDARY_TYPE`` selects what lies between the DRM layer and the fixed
    # exterior side and bottom faces:
    #
    # - ``Fixed`` adds no absorbing elements and provides the reflective baseline.
    # - ``PML`` adds perfectly matched layers to reduce outgoing-wave reflection.
    # - ``Rayleigh`` adds strongly damped elastic layers for the same purpose.
    #
    # Only this boundary treatment changes between comparison runs.

    # %%
    # --8<-- [start:boundary-treatment]
    if BOUNDARY_TYPE == "PML":
        model.interface.boundary.absorber(
            num_layers=3,
            num_partitions=absorber_parts,
            partition_algo="kd-tree",
            geometry="Rectangular",
            rayleigh_damping=0.10,
            match_damping=False,
            boundary_type="PML",
        )
    elif BOUNDARY_TYPE == "Rayleigh":
        model.interface.boundary.absorber(
            num_layers=5,
            num_partitions=absorber_parts,
            partition_algo="kd-tree",
            geometry="Rectangular",
            rayleigh_damping=0.95,
            match_damping=False,
            boundary_type=BOUNDARY_TYPE,
        )
    # --8<-- [end:boundary-treatment]
    # --8<-- [start:assembly]
    model.assembler.create_section(
        meshparts=soil_parts + ["pile"],
        num_partitions=physical_parts,
        partition_algorithm="kd-tree",
        merge_points=True,
        tolerance=1.0e-6,
    )
    model.assembler.assemble(merge_points=True, progress_callback=lambda *_: None)

    actual_cores = set(int(core) for core in model.assembled_mesh.cell_data["Core"])
    if actual_cores != set(range(ranks)):
        raise ValueError(f"Expected ranks 0..{ranks - 1}, exported cores: {sorted(actual_cores)}")

    # The outer faces are outside the absorbing layer when one is present.
    outer_fixity = [1] * (9 if BOUNDARY_TYPE == "PML" else 3)
    model.constraint.sp.fix_macro_x_min(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_x_max(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_y_min(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_y_max(dofs=outer_fixity, tol=1.0e-6)
    model.constraint.sp.fix_macro_z_min(dofs=outer_fixity, tol=1.0e-6)
    # --8<-- [end:assembly]


    # %% [markdown]
    # ## Apply the shared DRM wave input
    #
    # The preceding workflow stage has already generated the H5DRM file.
    # Every boundary case reads that same file; none regenerates it.

    # %%
    # --8<-- [start:drm-input]

    # Tcl accepts forward slashes on every supported operating system, including Windows.
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


    # %% [markdown]
    # ## Configure recording and dynamic analysis

    # %%
    # --8<-- [start:analysis-and-process]
    response_recorder = model.recorder.vtkhdf(
        file_base_name="dynamic_pile_response.vtkhdf",
        resp_types=["disp", "vel", "accel"],
        delta_t=0.005,
    )
    interface_recorder = model.recorder.embedded_beam_solid_interface(
        interface=[pile_soil_interface],
        dt=0.005,
    )

    constraint_handler = model.analysis.constraint.plain()
    numberer = model.analysis.numberer.parallelrcm()
    system = model.analysis.system.mumps()
    test = model.analysis.test.energyincr(
        tol=1.0e-4,
        max_iter=10,
        print_flag=5,
    )
    algorithm = model.analysis.algorithm.modifiednewton(factor_once=True)
    integrator = model.analysis.integrator.newmark(
        gamma=0.5,
        beta=0.25,
        form="D",
    )

    dynamic_analysis = model.analysis.transient(
        name="dynamic_boundary_response",
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
    model.process.add_step(h5_pattern, "Apply the common H5DRM wave field")
    model.process.add_step(response_recorder, "Record displacement, velocity, and acceleration")
    model.process.add_step(interface_recorder, "Record the embedded pile-soil interface")
    model.process.add_step(dynamic_analysis, "Run the dynamic analysis")
    # --8<-- [end:analysis-and-process]


    # %% [markdown]
    # ## Export and optionally execute

    # %%
    # --8<-- [start:export-and-run]
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    tcl_file = CASE_DIR / "model.tcl"
    model.export_to_tcl(filename=str(tcl_file.resolve()), progress_callback=lambda *_: None)

    print("\nDynamic pile-soil interaction boundary study")
    print(f"  Boundary:    {BOUNDARY_TYPE}")
    print(f"  Nodes:       {model.assembled_mesh.n_points}")
    print(f"  Elements:    {model.assembled_mesh.n_cells}")
    print(f"  Soil parts:  {len(soil_parts)} uniform blocks")
    print(f"  Pile:        {PILE_ELEMENTS} beam elements")
    print(f"  DRM input:   {drm_file.resolve()}")
    print(f"  Tcl model:   {tcl_file.resolve()}")

    return tcl_file



def compare_cases(context):
    import matplotlib

    matplotlib.use("Agg")
    spec = importlib.util.spec_from_file_location("pile_postprocess", context.workspace / POSTPROCESS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_results(
        results_root=context.workspace / "build", output_dir=context.output_dir,
        require_all=True, movies=True,
    )


def build_workflow():
    """Build remotely, solve concurrently, then compare all three responses."""
    # First create a workflow with a descriptive name. This labels its manifest;
    # it does not choose the remote working directory.
    workflow = fm.Workflow("dynamic-pile-boundaries")

    # Stage 1: create the common DRM input from the soil box, with no pile or
    # absorbing layers. create_drm writes input/drm/drmload.h5drm in its task
    # folder and returns the path. Later tasks get it with context.result().
    workflow.add(
        "input",
        tasks=[fm.tasks.Python("drm", create_drm)],
    )

    # Stage 2: add a stage named "build". tasks lists the work for this stage.
    # parallel=False runs tasks one after another in the listed order.
    # All three read the input created in stage 1. We build sequentially to keep
    # model generation simple; the numerical solves will run concurrently.
    #
    # Python("fixed", build_model, kwargs={"boundary": "Fixed"}) names the task,
    # selects its function, and supplies task-specific arguments. Femora calls:
    # build_model(context, boundary="Fixed"). Pass the function without ().
    # context.workspace is the shared run directory; context.output_dir is this
    # task's folder (build/fixed, build/rayleigh, or build/pml).
    # build_model exports there and returns its Tcl path as the task result.
    workflow.add(
        "build",
        parallel=False,
        tasks=[
            fm.tasks.Python("fixed", build_model, kwargs={"boundary": "Fixed"}),
            fm.tasks.Python("rayleigh", build_model, kwargs={"boundary": "Rayleigh"}),
            fm.tasks.Python("pml", build_model, kwargs={"boundary": "PML"}),
        ],
    )

    # Stage 3 starts after the entire build stage succeeds. parallel=True runs
    # the three solvers concurrently: 8 + 16 + 16 = 40 MPI ranks in total.
    # OpenSees(task_name, script, ranks=...) launches the exported Tcl file.
    # The script path is relative to the shared workspace.
    # Solvers run in solve/<task_name>, with stdout.log saved in that folder.
    # The model's recorders explicitly write to build/<case>/results instead.
    workflow.add(
        "solve",
        parallel=True,
        tasks=[
            fm.tasks.OpenSees("fixed", "build/fixed/model.tcl", ranks=8),
            fm.tasks.OpenSees("rayleigh", "build/rayleigh/model.tcl", ranks=16),
            fm.tasks.OpenSees("pml", "build/pml/model.tcl", ranks=16),
        ],
    )

    # Stage 4 starts only after every solver succeeds. Stages never overlap.
    # The "responses" task calls compare_cases(context), which writes plots and
    # CSV histories into context.output_dir: compare/responses.
    workflow.add(
        "compare",
        tasks=[fm.tasks.Python("responses", compare_cases)],
    )

    # outputs() selects existing files for the results archive. It does not
    # create files or run tasks. Paths are relative to the shared workspace:
    #   compare/responses/* : plots and CSV files directly inside that folder
    #   **/stdout.log       : solver logs at any directory depth
    #   build/*/model.tcl   : Tcl models inside each build task folder
    # * matches within one path component; ** searches nested directories.
    workflow.outputs("compare/responses/*", "**/stdout.log", "build/*/model.tcl")

    # Plots, CSVs, and movies are collected above. Raw files stay in the remote
    # workspace for postprocessing. Uncomment to also download the large files.
    # workflow.outputs("build/*/results/**/*")
    return workflow


if __name__ == "__main__":
    # Running this file submits the study. Set your app and allocation here.
    # Femora selects the TACC adapter and prompts for login; no password is stored.
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
