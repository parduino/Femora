import inspect

import pytest

from femora.components.MeshMaker import MeshMaker
from femora.components.ground_motion import (
    InterpolatedGroundMotion,
    PlainGroundMotion,
)
from femora.core.ground_motion_manager import GroundMotionManager


@pytest.fixture(autouse=True)
def mesh_maker():
    mesh_maker = MeshMaker.get_instance()
    mesh_maker.clear_model()
    yield mesh_maker
    mesh_maker.clear_model()


def constant_series(mesh_maker):
    return mesh_maker.time_series.constant(factor=1.0)


def test_plain_ground_motion_is_not_self_registering(mesh_maker):
    ts = constant_series(mesh_maker)
    manager = mesh_maker.ground_motion
    gm = PlainGroundMotion(accel=ts)

    assert gm.tag is None
    assert manager.get_all() == {}


def test_ground_motion_manager_is_owned_by_mesh_maker(mesh_maker):
    assert mesh_maker.ground_motion is mesh_maker.ground_motion
    with pytest.raises(TypeError, match="mesh_maker must be a MeshMaker instance"):
        GroundMotionManager(mesh_maker=object())


def test_manager_assigns_sequential_tags(mesh_maker):
    ts = constant_series(mesh_maker)
    manager = mesh_maker.ground_motion

    gm1 = manager.plain(accel=ts)
    gm2 = manager.plain(disp=ts)

    assert gm1.tag == 1
    assert gm2.tag == 2
    assert manager.get(1) is gm1
    assert manager.get(2) is gm2


def test_manager_tag_start_and_reassignment(mesh_maker):
    ts = constant_series(mesh_maker)
    manager = mesh_maker.ground_motion
    manager.set_tag_start(10)

    gm1 = manager.plain(accel=ts)
    gm2 = manager.plain(vel=ts)
    gm3 = manager.plain(disp=ts)

    assert [gm1.tag, gm2.tag, gm3.tag] == [10, 11, 12]

    manager.remove(11)

    assert gm1.tag == 10
    assert gm3.tag == 11
    assert manager.get_all() == {10: gm1, 11: gm3}
    assert gm2.tag is None


def test_manager_can_add_explicit_instance(mesh_maker):
    ts = constant_series(mesh_maker)
    manager = mesh_maker.ground_motion
    gm = PlainGroundMotion(accel=ts)

    returned = manager.add(gm)

    assert returned is gm
    assert gm.tag == 1


def test_plain_ground_motion_to_tcl(mesh_maker):
    accel = mesh_maker.time_series.constant()
    disp = mesh_maker.time_series.constant()
    manager = mesh_maker.ground_motion
    gm = manager.plain(
        accel=accel,
        disp=disp,
        integrator="Trapezoidal",
        factor=2.5,
    )

    assert gm.to_tcl() == "groundMotion 1 Plain -accel 1 -disp 2 -int Trapezoidal -fact 2.5"


def test_interpolated_ground_motion_to_tcl(mesh_maker):
    ts = constant_series(mesh_maker)
    manager = mesh_maker.ground_motion
    gm1 = manager.plain(accel=ts)
    gm2 = manager.plain(disp=ts)
    interpolated = manager.interpolated(
        ground_motions=[gm1, gm2],
        factors=[0.25, 0.75],
    )

    assert isinstance(interpolated, InterpolatedGroundMotion)
    assert interpolated.to_tcl() == "groundMotion 3 Interpolated 1 2 -fact 0.25 0.75"


def test_manager_instance_convenience_methods(mesh_maker):
    ts = constant_series(mesh_maker)
    manager = mesh_maker.ground_motion

    gm = manager.plain(accel=ts)

    assert gm.tag == 1
    assert manager.get(1) is gm


def test_manager_factory_signatures_follow_constructors(mesh_maker):
    plain_signature = inspect.signature(mesh_maker.ground_motion.plain)
    constructor_signature = inspect.signature(PlainGroundMotion.__init__)

    assert list(plain_signature.parameters) == list(constructor_signature.parameters)[1:]
    assert plain_signature.parameters["accel"].default is None
    assert plain_signature.parameters["factor"].default == 1.0


def test_interpolated_factory_signature_follows_constructor(mesh_maker):
    interpolated_signature = inspect.signature(mesh_maker.ground_motion.interpolated)
    constructor_signature = inspect.signature(InterpolatedGroundMotion.__init__)

    assert list(interpolated_signature.parameters) == list(constructor_signature.parameters)[1:]
    assert "ground_motions" in interpolated_signature.parameters
    assert "factors" in interpolated_signature.parameters
