import pytest

from femora.components.analysis.analysis import Analysis
from femora.core.model import Model
from femora.core.analysis_manager import AnalysisManager


@pytest.fixture
def mesh_maker():
    mk = Model()
    mk.clear_model()
    return mk


def _build_transient_stack(am: AnalysisManager):
    handler = am.constraint.plain()
    numberer = am.numberer.parallelrcm()
    system = am.system.bandgeneral()
    algorithm = am.algorithm.newton()
    test = am.test.normunbalance(tol=1e-6, max_iter=25)
    integrator = am.integrator.newmark(gamma=0.5, beta=0.25)
    return handler, numberer, system, algorithm, test, integrator


def test_analysis_manager_model_owned(mesh_maker):
    assert isinstance(mesh_maker.analysis, AnalysisManager)
    assert mesh_maker.analysis._mesh_maker is mesh_maker


def test_duplicate_analysis_manager_rejected(mesh_maker):
    with pytest.raises(ValueError, match="already owns an analysis manager"):
        AnalysisManager(mesh_maker)


def test_components_are_manager_scoped(mesh_maker):
    am = mesh_maker.analysis
    system = am.system.bandgeneral()
    assert system.tag == 1
    assert system._owner is am.system


def test_unmanaged_analysis_has_no_tag(mesh_maker):
    am = mesh_maker.analysis
    handler, numberer, system, algorithm, test, integrator = _build_transient_stack(am)
    analysis = Analysis(
        "raw",
        "Transient",
        handler,
        numberer,
        system,
        algorithm,
        test,
        integrator,
        num_steps=5,
        dt=0.01,
    )
    assert analysis.tag is None
    assert analysis._owner is None


def test_add_analysis_tags_and_tcl(mesh_maker):
    am = mesh_maker.analysis
    handler, numberer, system, algorithm, test, integrator = _build_transient_stack(am)
    analysis = am.add(
        Analysis(
            "TransientRun",
            "Transient",
            handler,
            numberer,
            system,
            algorithm,
            test,
            integrator,
            num_steps=10,
            dt=0.01,
        )
    )
    assert analysis.tag == 1
    assert analysis._owner is am
    tcl = analysis.to_tcl()
    assert "analysis Transient" in tcl
    assert "constraints Plain" in tcl
    assert "wipeAnalysis" in tcl


def test_direct_submanager_api(mesh_maker):
    am = mesh_maker.analysis
    assert "Plain" in am.constraint.plain().to_tcl()
    assert "ParallelRCM" in am.numberer.parallelrcm().to_tcl()
    assert "Mumps" in am.system.mumps(icntl14=10).to_tcl()
    assert "ModifiedNewton" in am.algorithm.modifiednewton(factor_once=True).to_tcl()
    assert "EnergyIncr" in am.test.energyincr(tol=1e-3, max_iter=5).to_tcl()
    assert "Newmark" in am.integrator.newmark(gamma=0.6, beta=0.3).to_tcl()


def test_clear_model_resets_analysis(mesh_maker):
    am = mesh_maker.analysis
    handler, numberer, system, algorithm, test, integrator = _build_transient_stack(am)
    am.add(
        Analysis(
            "a",
            "Transient",
            handler,
            numberer,
            system,
            algorithm,
            test,
            integrator,
            num_steps=1,
            dt=0.01,
        )
    )
    am.system.mumps()
    assert len(am.get_all()) == 1
    assert len(am.system.get_all()) >= 1
    mesh_maker.clear_model()
    assert len(mesh_maker.analysis.get_all()) == 0
    assert len(mesh_maker.analysis.system.get_all()) == 0


def test_submanager_clear(mesh_maker):
    am = mesh_maker.analysis
    am.algorithm.newton()
    am.clear()
    assert len(am.algorithm.get_all()) == 0
    assert len(am.get_all()) == 0
