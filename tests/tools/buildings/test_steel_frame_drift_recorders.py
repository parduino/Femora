import uuid

from femora.core.model import Model
from femora.components.material.nd import ElasticIsotropicMaterial
from femora.tools.buildings.steel_frame import FEMA_SAC_SteelFrame


def test_steel_frame_story_drift_recorders_core_aware():
    """Smoke test: build a tiny frame, assemble with 2 partitions, and generate drift recorders."""

    model = Model()
    model.clear_model()

    steel = ElasticIsotropicMaterial(
        f"Steel_{uuid.uuid4().hex[:8]}",
        E=29000.0,
        nu=0.3,
    )

    name_prefix = f"TestFrameDrift_{uuid.uuid4().hex[:8]}"
    building = FEMA_SAC_SteelFrame(
        name_prefix=name_prefix,
        x_bays=[1.0, 1.0],
        y_bays=[1.0, 1.0],
        story_heights=[1.0, 1.0],
        n_ele_col=1,
        n_ele_beam=1,
        length_unit_system="m",
    )

    part = building.build(model, steel, material_density=0.0)

    model.assembler.create_section(
        meshparts=[part.user_name],
        num_partitions=2,
        merge_points=True,
    )
    model.assembler.assemble()

    recorders = []
    for story in range(1, building.num_stories + 1):
        i_node = story
        j_node = story + building.num_stories
        for dof in (1, 2):
            recorders.append(
                model.recorder.drift(
                    file_name=f"{name_prefix}_Story{story:02d}_DOF{dof}.out",
                    i_nodes=i_node,
                    j_nodes=j_node,
                    dof=dof,
                    perp_dirn=3,
                    time=True,
                    cores=0,
                )
            )

    assert len(recorders) == building.num_stories * 2

    tcls = [r.to_tcl() for r in recorders]
    for tcl in tcls:
        assert "recorder Drift" in tcl
        assert "-iNode" in tcl
        assert "-jNode" in tcl
        assert "-perpDirn 3" in tcl
        assert "$pid" in tcl
        assert tcl.strip().startswith("if {$pid ==")

    assert any("Story01" in tcl for tcl in tcls)
    assert any("Story02" in tcl for tcl in tcls)
