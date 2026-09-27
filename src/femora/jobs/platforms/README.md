# Submission platforms

This initial layer supplies provider-neutral `Platform`, `PlatformValidator`,
`JobHandle`, and `JobStatus` contracts, plus structured validation reports.
It is separate from `jobs.backends`, which launches tasks inside an allocation.
`fm.submit()` now accepts a configured platform object and either a top-level
workflow factory (`function=`), source file (`source=`), or existing ZIP (`bundle=`).
`TACCPlatform` implements staging, validated submission, and job handles. No
AWS/Azure implementation or provider-string registry is claimed yet.

`TACCValidator` implements the read-only validator contract, not the complete
`Platform` interface. It accepts an already authenticated Tapis client; credentials
and tenant selection are not stored in settings or workflow bundles. Future AWS
and Azure implementations should implement the shared contracts with their own
settings and checks, not inherit TACC's queues or launcher assumptions.

```python
from femora.jobs.platforms import TACCSettings, TACCValidator

validator = TACCValidator(authenticated_client)
print(validator.queues("stampede3"))
settings = TACCSettings(
    system="stampede3", queue="skx-dev", allocation="YOUR_PROJECT",
    nodes=1, cores_per_node=48, minutes=20,
)
report = validator.validate(workflow, settings)
for issue in report.issues:
    print(issue.severity, issue.field, issue.message)
report.raise_for_errors()
```

Limits use `batchLogicalQueues` and logical queue names from the selected system's
current metadata. No machine-wide 48-core default exists. Missing, malformed, or
negative bounds are unverified, not inferred hardware limits. `valid` means no
known errors, not that every check passed. Allocation eligibility, storage access,
installed software, and memory needs remain explicitly unverified. Scheduling
can still fail after preflight. No remote resources are created by validation.

Submission revalidates resource settings before uploading, and again before job
submission. It does not import the factory locally: generated task requirements
are unverified until the remote runner constructs and checks the real workflow.
The job request carries the selected logical queue and resource settings.

## Public API

In your existing workflow file, keep the factory and tasks at module scope and
put local plotting, authentication, and submission under the main guard:

```python
import femora as fm
from femora.jobs.platforms import TACCPlatform, TACCSettings

# def build_workflow(): ... existing stages and task callbacks ...

if __name__ == "__main__":
    # Obtain authenticated_client privately; never hardcode credentials here.
    target = TACCPlatform(
        authenticated_client,
        app_id="YOUR_REGISTERED_APP", app_version="0.1.0",
        storage_system="designsafe.storage.default",
        input_directory="YOUR_USERNAME/femora-workflows/submissions",
    )
    job = fm.submit(
        function=build_workflow, platform=target,
        settings=TACCSettings("stampede3", "skx-dev", "YOUR_ALLOCATION", 1, 48, 20),
    )
    print(job.id)
    print(job.status())
    # After termination: job.download("outputs.zip")
    # To cancel explicitly: job.cancel()
```

The API packages the whole function's source file, not a pickle of live objects.
Use `inputs={...}` for JSON-serializable factory inputs and `files=[...]` for
declared source-relative data. Existing bundle mode rejects these overrides.
Do not include secrets in source, inputs, or data. Factories must be top-level
functions in real Python files; closures and notebook cells are not supported.
Companion importable packages must be installed remotely; declaring a data file
does not automatically turn it into an importable package.

Use `target.job(saved_uuid)` after authenticating in another session to reconnect
without resubmitting. Handles retain the client in memory, not saved credentials.
Downloads stream to an exclusive `.part` file, validate ZIP format, and refuse
overwrites; they do not extract output. Keep credentials refreshed through the
client for long-lived sessions. A new submit call always means a new job.

Each input bundle goes into a UUID-specific storage directory; staged inputs are
retained on failures. Submission transport failures raise `RemoteSubmissionError`
with the job name and input URL so users can investigate before retrying. This is
not an exactly-once submission guarantee. Live acceptance of this new public API
is still required even though the lower-level Tapis app was tested successfully.

## Staged-job submission

`TACCSubmitter(client).submit_request(job_request)` now revalidates resources
against live system metadata and submits only if there are no known errors.
`preflight(job_request)` returns a normalized copy and a validation report without
submitting. The deployment helper's `submit` command uses this adapter.

The request carries `execSystemLogicalQueue`, `nodeCount`, `coresPerNode`, and
`maxMinutes`. Older requests may inherit the registered app's default system and
queue; the normalized request always makes them explicit. App and selected system
must match. The pilot requires `isMpi=false` and allows only one `-A PROJECT`
extra scheduler option so raw flags cannot bypass resource validation. Missing
or inaccessible app/system metadata blocks submission; missing individual limits
remain explicitly unverified. No automatic write retry is performed.

This lower-level adapter accepts an already-staged workflow URL. It does not execute the
bundle locally or claim its task requirements were validated: the remote runner
checks those. `TACCPlatform` wraps this adapter with local bundle integrity checks,
uploading and the concrete `TACCJob` handle.

For interactive use, `TACCPlatform.login(app_id="...", app_version="0.1.0")`
prompts for a username and hidden password and returns a configured target.
The default tenant/storage are DesignSafe; other Tapis deployments can supply
`base_url`, `storage_system`, and `input_directory`. Login alone never submits.
Passwords are cleared after authentication, tokens remain in memory for job
operations, and no credentials are written to disk. Noninteractive applications
should continue passing an authenticated client to the constructor.

`fm.submit(function=build_workflow, platform=target, settings=settings, files=...)`
packages supporting files itself. In addition to the existing relative-path
list, `files` accepts a mapping from workspace-relative destinations to explicit
local files, for example `{"motions/input.acc": Path("/local/data/input.acc")}`.
Mapping sources may be outside the workflow directory; destinations may not
escape the remote workspace. Only declared files are included. Keep the submit
call under `if __name__ == "__main__":` to prevent remote recursive submission.
# Simple Submission

Use `fm.submit(platform="tacc", settings={...}, function=build_workflow)`
to select the TACC adapter automatically. The dictionary requires `app_id`,
`system`, `queue`, `allocation`, `nodes`, `cores_per_node`, and `minutes`.
Optional connection settings are `app_version` (default `0.1.0`), `base_url`
(default `https://designsafe.tapis.io`), `storage_system` (default
`designsafe.storage.default`), and `input_directory` (default: your username
followed by `/femora-workflows/submissions`).

Login prompts for credentials; never put passwords or tokens in the dictionary.
You can load this dictionary from JSON with `json.load()` before submitting.
Passing a JSON filename directly as `settings` is not supported.
Only the `tacc` name is currently supported. Provider-specific conversion lives
under `jobs/platforms`, not in the workflow or runner. Authenticated platform
objects with typed settings remain supported for noninteractive use and reuse.
