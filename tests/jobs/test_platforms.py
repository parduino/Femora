"""Submission preflight is read-only and independent of a compute allocation."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from femora.jobs import Workflow, tasks
from femora.jobs.platforms import TACCSettings, TACCValidator
from femora.jobs.platforms import TACCSubmitter, SubmissionValidationError


@pytest.fixture
def client():
    client = Mock()
    client.systems.getSystem.return_value = dict(enabled=True, canExec=True, batchLogicalQueues=[
        dict(name="skx-dev", hpcQueueName="skx-dev", minNodeCount=1, maxNodeCount=16,
             minCoresPerNode=1, maxCoresPerNode=48, minMinutes=1, maxMinutes=120),
        dict(name="spr", hpcQueueName="spr", minNodeCount=1, maxNodeCount=32,
             minCoresPerNode=1, maxCoresPerNode=112, minMinutes=1, maxMinutes=2880),
    ])
    return client


def settings(**changes):
    return replace(TACCSettings("stampede3", "skx-dev", "PROJECT", 1, 48, 20), **changes)


def workflow(parallel=True):
    return Workflow().add("solve", parallel=parallel, tasks=[
        tasks.OpenSees("a", "a.tcl", ranks=30), tasks.OpenSees("b", "b.tcl", ranks=30)])


def test_valid_sequential_and_capacity_failure(client):
    validator = TACCValidator(client)
    assert validator.validate(workflow(False), settings()).valid
    report = validator.validate(workflow(), settings())
    assert not report.valid
    with pytest.raises(ValueError, match="60 rank slots"):
        report.raise_for_errors()
    assert all(call[0] == "systems.getSystem" for call in client.mock_calls)


def test_queue_specific_limits(client):
    validator = TACCValidator(client)
    report = validator.validate(workflow(), settings(cores_per_node=100))
    assert any(i.field == "cores_per_node" and "48" in i.message for i in report.errors)
    assert validator.validate(workflow(), settings(queue="spr", cores_per_node=100)).valid


@pytest.mark.parametrize("changes,field", [
    ({"nodes": 17}, "nodes"), ({"minutes": 121}, "minutes"),
    ({"queue": "not-exposed"}, "queue"), ({"nodes": True}, "nodes"),
    ({"cores_per_node": 0}, "cores_per_node"), ({"allocation": "x;cmd"}, "allocation"),
])
def test_invalid_requests(client, changes, field):
    report = TACCValidator(client).validate(workflow(False), settings(**changes))
    assert any(issue.field == field for issue in report.errors)


def test_missing_limits_are_unverified(client):
    del client.systems.getSystem.return_value["batchLogicalQueues"][0]["maxCoresPerNode"]
    report = TACCValidator(client).validate(workflow(False), settings())
    assert report.valid
    assert any(i.field == "cores_per_node" and i.severity == "unverified" for i in report.issues)


def test_auth_failure_blocks_without_leaking(client):
    client.systems.getSystem.side_effect = RuntimeError("SECRET")
    report = TACCValidator(client).validate(workflow(False), settings())
    assert not report.valid and "SECRET" not in str(report)


def test_object_response_and_discovery(client):
    data = client.systems.getSystem.return_value
    client.systems.getSystem.return_value = SimpleNamespace(
        **{**data, "batchLogicalQueues": [SimpleNamespace(**q) for q in data["batchLogicalQueues"]]})
    assert TACCValidator(client).queues("stampede3")[1].max_cores_per_node == 112


def test_unsupported_python_parallel_and_disabled_system(client):
    wf = Workflow().add("python", parallel=True, tasks=[tasks.Python("p", print)])
    client.systems.getSystem.return_value["enabled"] = False
    report = TACCValidator(client).validate(wf, settings())
    assert {i.field for i in report.errors} == {"stages.python", "system"}


def request(client, **overrides):
    client.apps.getApp.return_value = dict(jobAttributes=dict(
        execSystemId="stampede3", execSystemLogicalQueue="skx-dev", isMpi=False))
    return dict(appId="pilot", appVersion="0.1", nodeCount=1, coresPerNode=48,
                maxMinutes=20, parameterSet={"schedulerOptions": [{"arg": "-A PROJECT"}]},
                **overrides)


def test_submit_invalid_has_no_remote_writes(client):
    data = request(client)
    data["coresPerNode"] = 100
    with pytest.raises(SubmissionValidationError, match="48"):
        TACCSubmitter(client).submit_request(data)
    client.jobs.submitJob.assert_not_called()
    assert all(c[0] in ("apps.getApp", "systems.getSystem") for c in client.mock_calls)


def test_submit_queue_override_rechecks_limits_and_does_not_mutate(client):
    data = request(client, execSystemLogicalQueue="spr")
    data["coresPerNode"] = 100
    report_callback = Mock()
    TACCSubmitter(client).submit_request(data, on_validation=report_callback)
    sent = client.jobs.submitJob.call_args.kwargs
    assert sent["execSystemLogicalQueue"] == "spr" and sent["coresPerNode"] == 100
    assert "execSystemId" not in data
    assert any(i.field == "workflow" and i.severity == "unverified"
               for i in report_callback.call_args.args[0].issues)
    client.systems.getSystem.return_value["batchLogicalQueues"][1]["maxCoresPerNode"] = 80
    with pytest.raises(SubmissionValidationError):
        TACCSubmitter(client).submit_request(data)
    assert client.jobs.submitJob.call_count == 1


@pytest.mark.parametrize("arg", ["--ntasks=100", "--partition=spr", "-A X; evil"])
def test_reject_scheduler_bypass(client, arg):
    data = request(client)
    data["parameterSet"]["schedulerOptions"].append({"arg": arg})
    with pytest.raises(SubmissionValidationError):
        TACCSubmitter(client).submit_request(data)
    client.jobs.submitJob.assert_not_called()


def test_app_failure_and_system_mismatch_fail_closed(client):
    data = request(client, execSystemId="another-machine")
    with pytest.raises(SubmissionValidationError, match="installation"):
        TACCSubmitter(client).submit_request(data)
    client.apps.getApp.side_effect = RuntimeError("secret-token")
    with pytest.raises(SubmissionValidationError) as error:
        TACCSubmitter(client).submit_request(data)
    assert "secret-token" not in str(error.value)
    client.jobs.submitJob.assert_not_called()
