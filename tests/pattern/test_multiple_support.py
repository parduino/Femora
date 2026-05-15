from femora.core.ground_motion_manager import GroundMotionManager
from femora.core.pattern_manager import PatternManager
from femora.core.time_series_manager import TimeSeriesManager


def test_multiple_support_pattern_to_tcl():
    time_series = TimeSeriesManager()
    ground_motions = GroundMotionManager()
    patterns = PatternManager()

    accel = time_series.path(dt=0.01, filePath="support_x.acc", factor=9.81)
    disp = time_series.path(dt=0.01, filePath="support_x.disp")
    ground_motion = ground_motions.plain(accel=accel, disp=disp)

    pattern = patterns.multiple_support()
    pattern.add_imposed_motion(node_tag=10, dof=1, ground_motion=ground_motion)

    assert pattern.to_tcl() == "\n".join(
        [
            "pattern MultipleSupport 1 {",
            "\tgroundMotion 1 Plain -accel 1 -disp 2",
            "\timposedMotion 10 1 1",
            "}",
        ]
    )


def test_multiple_support_includes_interpolated_dependencies_first():
    time_series = TimeSeriesManager()
    ground_motions = GroundMotionManager()
    patterns = PatternManager()

    ts = time_series.constant()
    gm1 = ground_motions.plain(accel=ts)
    gm2 = ground_motions.plain(disp=ts)
    interpolated = ground_motions.interpolated(
        ground_motions=[gm1, gm2],
        factors=[0.25, 0.75],
    )

    pattern = patterns.multiple_support()
    pattern.add_imposed_motion(node_tag=20, dof=2, ground_motion=interpolated)

    assert pattern.to_tcl() == "\n".join(
        [
            "pattern MultipleSupport 1 {",
            "\tgroundMotion 1 Plain -accel 1",
            "\tgroundMotion 2 Plain -disp 1",
            "\tgroundMotion 3 Interpolated 1 2 -fact 0.25 0.75",
            "\timposedMotion 20 2 3",
            "}",
        ]
    )
