# Femora Tapis app (Stampede3 pilot)

This is the deployment package for the existing Femora workflow runner, not a
new workflow API. It executes a bundle remotely from start to finish, including
model creation, OpenSees tasks, Python post-processing, and final comparisons.
No Git pulls, pip installs, credentials, or shared-directory writes happen in a job.

## Contents

- `build_app.py` creates `app.zip`, `app.json`, and a sample `job.json` offline.
- `tapisjob_app.sh` loads the installed modules and starts one coordinator.
- `run_workflow.py` invokes replay, collects outputs, and propagates failure.

The app uses Tapis v3 ZIP/BATCH with `isMpi=false`: Femora, not the outer Tapis
launcher, dispatches MPI tasks. Do not run the wrapper with `ibrun` or set
`isMpi=true`; that would start multiple workflow coordinators.

## Before registration

First check authentication and visibility of the two system definitions locally:

```bash
python deploy/tapis/check_access.py
```

Use your own interactive terminal. This requires `tapipy`, prompts for a hidden
password, and keeps tokens only in memory until exit. It never uploads files or
registers/submits anything. Do not send credentials or tokens in chat. Successful
system-definition checks do not establish remote filesystem or scheduler access.

To also test directory listings without displaying private filenames:

```bash
python deploy/tapis/check_access.py --files
```

This checks the shared Stampede3 installation and the authenticated user's My
Data directory. Override `--stampede-dir` for a different native installation
path. Listing success does not prove write permission or allocation access.

Use an existing Tapis execution system configured for Stampede3 with Slurm and
ZIP support. Verify its effective Unix identity is the submitting user's account,
its working directory is that user's scratch area, and its queue/profile generates
the intended node/task layout. A shared app does NOT automatically supply each
user with a TACC account, allocation, system permission, or SSH credentials.

Never expose arbitrary workflow bundles through an execution system using the app
owner's shared Unix account. Bundles execute arbitrary code with the effective
user's permissions. This app is not a sandbox. Keep authentication tokens out of
bundles and job environment variables.

The existing Femora module must include the jobs implementation through commit
`d2c365d` (or a tested later release). All compute nodes need access to the same
module paths, environment, and workspace. Freeze the shared checkout during jobs;
use a versioned module and installation before broad/public deployment. The current
editable environment under `$WORK` is the user's pilot setup, not an endorsement
of that storage choice for large-scale Python workloads.

Defaults follow the previously downloaded SimCenter ShakerMaker app definition
(`simcenter-shakermaker-stampede3`, version `1.0.0`): execution system `stampede3`,
archive system `designsafe.storage.default`, and per-user archive paths using
`${EffectiveUserId}/tapis-jobs-archive/${JobCreateDate}/${JobUUID}`. Its app assets
were published in `designsafe.storage.community/SimCenter/Software/tapisV3/`.
This reference is a downloaded snapshot, not a check of the live registered app.

Differences are intentional: the Femora pilot uses the tested `skx` queue, not
ShakerMaker's `spr` queue, and separates inputs, scratch intermediates, and final
outputs instead of archiving everything in the working directory. Allocation and
archive settings stay in each job request. Default results go to the user's My
Data archive; use `--archive-system` and `--archive-dir` for a shared project.
The supplied allocation must belong to the submitting user.

## Build

Run from the repository root. Replace ALL uppercase placeholders first:

```bash
python deploy/tapis/build_app.py \
  --output dist/tapis/femora-0.1.0 \
  --app-id YOUR_UNIQUE_FEMORA_APP_ID \
  --allocation YOUR_ALLOCATION \
  --image /work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0/app.zip \
  --bundle-url tapis://designsafe.storage.default/YOUR_USERNAME/YOUR_INPUT_DIRECTORY/mpi.zip
```

Defaults match the modules tested in this conversation: `python/3.12.11`,
`femora`, `opensees/3.8.0`, using `/work2/08189/amnp95/modules`. Override these
with the builder's module flags for another installation. The ZIP has Unix
executable permissions and LF shell scripts even when built on Windows.

The sample job requests one node and 48 single-CPU rank slots for the SKX pilot;
use `--nodes`, `--cores-per-node`, and `--minutes` for a different layout. The
job uses Tapis `nodeCount` and `coresPerNode` for resource allocation, not raw
Slurm task-count options (Tapis rejects `--ntasks` in schedulerOptions). Only
the user's allocation is supplied as an extra scheduler option. The pilot relies
on the system's single-CPU-per-task layout; confirm the generated Slurm script
and environment during acceptance testing. The runner refuses to invent an allocation when
`SLURM_NTASKS` is absent. Do not assume 48 cores on other queues/machines.

## Install app assets

Upload the generated `app.zip` to the EXACT remote path supplied as `--image`.
For a build performed on Stampede3, for example:

```bash
mkdir -p /work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0
cp -n dist/tapis/femora-0.1.0/app.zip /work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0/app.zip
chmod 755 /work2/08189/amnp95/stampede3/femora-tapis/app /work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0
chmod 644 /work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0/app.zip
```

Parent directories must be traversable. Do not overwrite a deployed archive;
publish a new version instead. Upload the WORKFLOW bundle (`mpi.zip`) separately
to the storage URL supplied as `--bundle-url`. It is not the app archive.

## Register and submit

### Interactive helper

`manage.py` performs one explicit operation per invocation, prompts privately for
login, and retains tokens only until exit. Write operations require typing `yes`.
Submission now runs `TACCSubmitter` preflight against the registered app and live
system queue limits before sending the job. The client-side Femora checkout must
include `jobs.platforms`; the deployed app does not need to change. Known errors
block submission; unchecked bundle requirements, permissions, and environment
checks are printed as unverified. Upload is still a separate explicit operation.
It neither shares the app nor automatically retries writes. Uploads check for
existing destinations, but this is not an atomic create-only operation; never
upload concurrently to the same path. File paths below are relative to each
system's effective root, not necessarily its native filesystem root.

For the current amnp95 pilot (run these in order after building):

```powershell
python deploy/tapis/manage.py upload dist/tapis/femora-0.1.0/app.zip --system stampede3 --path work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0/app.zip
python deploy/tapis/manage.py upload example_outputs/tapis-mpi.zip --system designsafe.storage.default --path amnp95/femora-workflows/pilot-0.1.0/mpi.zip
python deploy/tapis/manage.py register dist/tapis/femora-0.1.0/app.json
python deploy/tapis/manage.py submit dist/tapis/femora-0.1.0/job.json
python deploy/tapis/manage.py status JOB_UUID_FROM_SUBMIT
python deploy/tapis/manage.py status JOB_UUID_FROM_SUBMIT --history
```

Build the matching local artifacts first (no remote calls):

```powershell
python examples/workflows/tacc_mpi_smoke.py --bundle example_outputs/tapis-mpi.zip
python deploy/tapis/build_app.py --output dist/tapis/femora-0.1.0 --app-id amnp95-femora-workflow-stampede3 --allocation DesignSafe-SimCenter --image /work2/08189/amnp95/stampede3/femora-tapis/app/0.1.0/app.zip --bundle-url tapis://designsafe.storage.default/amnp95/femora-workflows/pilot-0.1.0/mpi.zip
```

These are pilot-specific paths and allocation, not shared-app requirements.
Each submit call creates a new job and may charge the requested allocation.
Record the printed UUID and use `status` rather than submitting again. If a
write times out, check DesignSafe before retrying. Error output omits SDK
exception bodies to avoid exposing credentials. Successful upload still needs
a second-user permissions check before the application is shared.

### Existing authenticated client

Use your existing authenticated Tapis client. For example, with a short-lived
token in `TAPIS_TOKEN` and the appropriate tenant in `TAPIS_BASE_URL`:

```bash
curl --fail-with-body -X POST "$TAPIS_BASE_URL/v3/apps" \
  -H "X-Tapis-Token: $TAPIS_TOKEN" -H 'Content-Type: application/json' \
  --data-binary @dist/tapis/femora-0.1.0/app.json

curl --fail-with-body -X POST "$TAPIS_BASE_URL/v3/jobs/submit" \
  -H "X-Tapis-Token: $TAPIS_TOKEN" -H 'Content-Type: application/json' \
  --data-binary @dist/tapis/femora-0.1.0/job.json
```

For DesignSafe the tenant URL is normally `https://designsafe.tapis.io`; use the
tenant in which your systems and credentials are registered. Do not share tokens
or put them in JSON, Git, the application archive, or the shared environment.
Registration is deliberately not automatic and the app is not published publicly.
First inspect the response, then run the smoke test privately with your own account.

## Results and failures

Download completed job outputs locally (also supported for failed jobs):

```powershell
python deploy/tapis/manage.py download JOB_UUID --output example_outputs/tapis-job-output.zip
```

This streams the Jobs output ZIP to disk, refuses existing files, and does not
extract it. Open that archive to find `run-status.json`, logs, and the nested
`results.zip`. Interrupted downloads retain a `.part` file; use a new destination
or inspect/remove that partial file before retrying. This command never resubmits.

For the intentional failure acceptance test, create a separate bundle:

```powershell
python examples/workflows/tacc_failure_smoke.py --bundle example_outputs/tapis-failure.zip
python deploy/tapis/manage.py upload example_outputs/tapis-failure.zip --system designsafe.storage.default --path amnp95/femora-workflows/pilot-0.1.0/failure.zip
```

Create a separate job JSON from the smoke-test request, changing `name` to
`femora-failure-smoke` and the workflow `sourceUrl` to the uploaded `failure.zip`.
Keep the existing registered app/version; no app re-upload or registration is
needed. Submit this job explicitly, then inspect status/history and download its
outputs. Expected: Tapis `FAILED`, `run-status.json` status `failed`, a nonzero
workflow exit code, and logs containing `FEMORA_EXPECTED_FAILURE`. The
`blocked-stage` task must not run. This still requests a real allocation and
consumes queue time. Local tests do not replace this remote acceptance test.

Each job gets a UUID-specific scratch directory. The input is staged as
`inputs/workflow.zip`; replay uses a fresh `work/` directory. The `output/`
directory contains `results.zip`, `workflow.log`, `run-status.json`, the Tapis
application logs, and an exit-code file.

`results.zip` preserves workspace-relative paths for files selected by
`workflow.outputs(...)`, plus `manifest.json` and per-task logs/drivers for
diagnostics. Unselected large result files remain in scratch. Directory names and
paths escaping the workspace are not accepted as archive artifacts.

Tapis archives `output/` into the job's requested archive directory with the job
UUID appended. Archiving is requested even on application failure. A failed replay
or packaging step remains a nonzero app exit, not a successful job. Setup failures
before Python starts appear in the Tapis logs and exit-code file. Scheduler kills
or wall-time expiry may prevent final packaging; raw partial files remain in scratch
subject to its retention policy. Download through the configured storage system's
Files API or DesignSafe data browser; do not assume results return automatically
to the submitting laptop.

For smoke validation, open `compare/summary/comparison.txt` inside `results.zip`.
Expect the 2/2/3-rank tests to pass. Also run a deliberately failing bundle and
verify Tapis reports failure while retaining logs. Repeat with a second authorized
user to check identity, allocation charging, shared module access, and archive
permissions. Live registration/schema/scheduler validation still requires Tapis;
the local tests do not replace this acceptance test.

To test a different exposed queue, set `execSystemLogicalQueue` in a separate job
JSON, for example `skx-dev`, and keep `coresPerNode` within its reported limit and
`maxMinutes` within its wall-time limit. This overrides the app's default queue
without re-registering it. Do not change `execSystemId` to use an app installation
on a different machine. New generated job JSON files include system and queue
explicitly; older job files fall back to the registered app defaults.

## References

- [Tapis application attributes](https://tapis.readthedocs.io/en/latest/technical/apps.html)
- [Tapis ZIP runtime](https://tapis.readthedocs.io/en/latest/technical/jobs.html#zip)
- [Tapis resource sharing](https://tapis.readthedocs.io/en/latest/technical/sharing.html)
