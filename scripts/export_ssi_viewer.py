from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv


def _build_interface_mesh(pile: pv.DataSet, tol: float = 1e-3, radius: float = 0.5) -> pv.PolyData:
    pts = pile.cell_centers().points
    theta_count = 8
    z_count = 4

    xy_groups = np.round(pts[:, :2] / tol) * tol
    theta = np.linspace(0, 2 * np.pi, theta_count, endpoint=False)
    circle = np.c_[radius * np.cos(theta), radius * np.sin(theta)]
    all_pts = []

    for xy in np.unique(xy_groups, axis=0):
        ids = np.where((xy_groups == xy).all(axis=1))[0]
        zs = np.sort(np.unique(np.round(pts[ids, 2] / tol) * tol))
        dz = np.median(np.diff(zs)) if len(zs) > 1 else 1.0

        pile_pts = np.vstack(
            [
                np.c_[xy + circle, np.full(theta_count, zz)]
                for eid in ids
                for zz in np.linspace(pts[eid, 2] - dz / 2, pts[eid, 2] + dz / 2, z_count, endpoint=False)
            ]
        )
        all_pts.append(pile_pts)

    return pv.PolyData(np.vstack(all_pts))


def load_scene(vtk_path: Path) -> dict[str, pv.DataSet]:
    mesh = pv.read(vtk_path)

    structure = mesh.extract_cells(mesh["Region"] == 1)
    pileblock = mesh.extract_cells(mesh["Region"] == 0)
    basin = mesh.extract_cells(mesh["Region"] == 2)
    pml = mesh.extract_cells(mesh["Region"] == 9)
    pile = mesh.extract_cells(mesh["Region"] == 10)

    drm_blocks = pv.MultiBlock()
    soil_blocks = pv.MultiBlock()

    for region in range(3, 9):
        layer = mesh.extract_cells(mesh["Region"] == region)
        centers = layer.cell_centers()
        xmin, xmax, ymin, ymax, zmin, zmax = centers.bounds
        zavg = (zmin + zmax) / 2

        ids = []
        ids.append(layer.find_cells_intersecting_line((xmin, ymin, zavg), (xmax, ymin, zavg)))
        ids.append(layer.find_cells_intersecting_line((xmin, ymax, zavg), (xmax, ymax, zavg)))
        ids.append(layer.find_cells_intersecting_line((xmin, ymin, zavg), (xmin, ymax, zavg)))
        ids.append(layer.find_cells_intersecting_line((xmax, ymin, zavg), (xmax, ymax, zavg)))

        if region == 3:
            mask = np.isclose(centers.points[:, 2], zmin)
            ids.append(np.where(mask)[0])

        ids = np.unique(np.concatenate(ids))
        drm_blocks.append(layer.extract_cells(ids))
        soil_blocks.append(layer.extract_cells(ids, invert=True))

    return {
        "structure": structure,
        "pileblock": pileblock,
        "basin": basin,
        "drm": drm_blocks.combine(),
        "soil": soil_blocks.combine(),
        "pml": pml,
        "pile": pile,
        "interface": _build_interface_mesh(pile),
    }


def build_plotter(scene: dict[str, pv.DataSet], title: str) -> pv.Plotter:
    plotter = pv.Plotter(off_screen=True, window_size=(1400, 1000))
    plotter.set_background("#07111d", top="#0c1725")

    plotter.add_mesh(
        scene["soil"],
        name="soil",
        color="#d8e1ea",
        opacity=0.12,
        smooth_shading=True,
        specular=0.08,
    )
    plotter.add_mesh(scene["basin"], name="basin", color="#5d7ea5", opacity=0.16)
    plotter.add_mesh(scene["pileblock"], name="pileblock", color="#7f8792", opacity=0.32)
    plotter.add_mesh(
        scene["drm"],
        name="drm",
        color="#54d0c2",
        opacity=0.16,
        show_edges=True,
        edge_color="#89fff3",
        line_width=1.0,
    )
    plotter.add_mesh(scene["pml"], name="pml", color="#30506f", opacity=0.09)
    plotter.add_mesh(
        scene["pile"],
        name="pile",
        color="#f59e0b",
        show_edges=True,
        edge_color="#ffd284",
        line_width=1.2,
    )
    plotter.add_mesh(
        scene["structure"],
        name="structure",
        color="#8ec5ff",
        show_edges=True,
        edge_color="#d7ecff",
        line_width=1.4,
    )
    plotter.add_mesh(
        scene["interface"],
        name="interface",
        color="#6ff2c8",
        point_size=6,
        render_points_as_spheres=True,
        opacity=0.8,
    )

    plotter.add_text(title, position="upper_left", font_size=12, color="white")
    plotter.add_text("Femora SSI mesh viewer", position="upper_right", font_size=10, color="#b7c9de")
    plotter.view_isometric()
    plotter.camera.zoom(1.18)
    plotter.enable_anti_aliasing("msaa")
    return plotter


def export_viewer(vtk_path: Path, output_html: Path, title: str, poster_path: Path | None) -> None:
    scene = load_scene(vtk_path)
    plotter = build_plotter(scene, title)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    plotter.export_html(str(output_html))
    if poster_path is not None:
        poster_path.parent.mkdir(parents=True, exist_ok=True)
        plotter.screenshot(str(poster_path))
    plotter.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a Femora SSI VTK scene as a web viewer.")
    parser.add_argument(
        "--vtk",
        default=str(Path("website") / "ssi-source" / "scene.vtk"),
        help="Path to the VTK file to render.",
    )
    parser.add_argument(
        "--output",
        default=str(Path("website") / "public" / "ssi-viewer" / "index.html"),
        help="Path to the exported interactive HTML file.",
    )
    parser.add_argument(
        "--poster",
        default=str(Path("website") / "public" / "ssi-viewer" / "poster.png"),
        help="Optional screenshot poster path. Pass an empty string to skip.",
    )
    parser.add_argument(
        "--title",
        default="Femora SSI model",
        help="Title overlay rendered into the web scene.",
    )
    args = parser.parse_args()

    vtk_path = Path(args.vtk)
    output_html = Path(args.output)
    poster_path = Path(args.poster) if args.poster else None

    export_viewer(vtk_path, output_html, args.title, poster_path)
    print(f"Exported {vtk_path} -> {output_html}")


if __name__ == "__main__":
    main()
