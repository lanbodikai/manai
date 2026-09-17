# Workstream A methodology

## Question and falsification

Can completed zero-SM jobs justify proposing an opt-in CPU-placement pilot? Historical eligibility supports investigation, not CPU compatibility or realized savings. Falsify accounting if independent job identities/card sums disagree, mixed scopes enter capacity, or source fingerprints differ. A future pilot must separately test output validity, runtime, CPU/queue capacity and rollback; failure or owner-agreed limits stop that pilot. No workload execution is implemented.

## Accounting and scope

Use the pinned official preparation and five-file canonical checker. Select unique `id_job` with COMPLETED state, finite valid average/peak SM equal to zero and recorded `gpu_hours > 1`. Missing required measurements are excluded with reasons. Invalid utilization ordering and negative duration are excluded; inconsistent duplicate identities fail. Cancelled jobs are excluded. Recorded GPU-hours are summed once per job and independently reconciled against card records. Scheduler duration is not a replacement for recorded GPU-hours.

Findings join through `metadata.job_id`. Only job-scope unused-capacity references contribute to the overlap diagnostic; other kinds/scopes are counted as exclusions. The diagnostic contrasts repeated versus unique linked allocations, not a sum of organizer impact estimates. Recovery always uses the physical eligible allocation once. Organizer findings, source judgments, observed job fields, synthetic incidents and our scenario assumptions remain distinct. Individual researchers are not ranked.

The gpu-not-needed finding cohort aligns with our predicate. The organizer `rec_lowutil` uses sub-10-percent activity, another detector and a 35-percent conversion assumption for shared allocation. Its cohort/action cannot be aligned to this CPU pilot; we do not claim to correct it or borrow its recovery fraction. The CPU remedy already appears upstream.

## Recovery and downside

Multiply eligible allocation by explicit finite ordered recovery fractions; multiply those values by the positive reference USD/GPU-hour input. Preserve numeric precision in the API and export; clients only round display. All results are scenario intervals, not calibrated probabilities or cash savings.

The lead selected final fractions **0/0/1** when recoverability has no empirical basis: zero low and point, and a high equal to the physical eligibility ceiling. The high is not an expected outcome; a positive fraction is an exploratory assumption. Use the official reference rate. D06 also requires B's final displayed audit/report/export agreement, which A-side tests alone cannot establish.

Canonical downside is qualitative under v0.3: potential CPU failure/slowdown, queue pressure and retry/rollback work. Money remains null. Workload-owner opt-in, original placement availability, output/runtime comparison and owner-agreed stop limits are proposed guardrails; enforcement is untested. C may explain or challenge these fields but cannot alter them.

## Identity and interfaces

Active API is v0.3. Each creation returns a new opaque immutable snapshot; numeric values and evidence membership are deterministic for equal source/semantic inputs. Cache capacity is 128 snapshots, FIFO eviction, no persistence. Missing/evicted IDs return 404. Evidence content is stored as immutable serialized values shared within a source version; responses are freshly decoded. Cursors bind audit identity and stable ordering. Missing/changed source prevents old evidence/export from silently joining replacement data (409). New calculations require the expected fingerprint.

The proposed v0.4 contract at ce6a44e remains gated on B's recorded acceptance. No proposed fields are inserted into v0.3. CPU cost/delay will be single-job accounting separate from cohort claims when adopted.

## Reproduction and privacy

Run `python -m unittest discover -s tests/analysis -v`, inherited bootstrap tests, and `python -m eval.analysis.verify_live` in the pinned service runtime with canonical data read-only. The live harness calls the actual service, independently loops over source records, reconciles GPU-row hours, paginates evidence and evaluates three recovery settings at two prices. It writes private review rows, snapshots and claims under ignored `private-eval/analysis/`. Inspect five included and three boundary records before marking D04 passed.

Official attribution prohibits redistribution of generated data. Public tests contain only invented records; public result notes contain methods, gate outcomes and source versions. Generated claims and source records remain local pending the submission publication decision. CPU compatibility, operational savings and human usability remain separate unproven claims.
