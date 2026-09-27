# Submission platforms

This initial layer supplies provider-neutral `Platform`, `PlatformValidator`,
`JobHandle`, and `JobStatus` contracts, plus structured validation reports.
It is separate from `jobs.backends`, which launches tasks inside an allocation.
No public `fm.submit()` or complete bundle-uploading `Platform` is implemented yet.
The tested deployment scripts remain the submission route during this phase.

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

The future submission implementation must revalidate before remote writes and
validate the actual packaged workflow, not an unrelated local workflow instance.
Its job request must carry the selected logical queue and resource settings.

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

This adapter accepts an already-staged workflow URL. It does not execute the
bundle locally or claim its task requirements were validated: the remote runner
checks those. It is deliberately not presented as a complete `Platform`, since
packaging/uploading and a concrete job handle remain future integration work.
