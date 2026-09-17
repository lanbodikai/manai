# Discussion queue — v0.2

Answer decision questions before starting the dependent work. Data questions are answered by inspection, not by asking the user to guess.

## Round 1 — answered

1. Track and scope? **Track 2, complete package, one verified recommendation.**
2. Contribution? **Audit savings with evidence and downside.**
3. Staffing? **Two builders/Codex sessions.**

## Round 2 — answered

1. First cohort: **completed zero-compute jobs, with CPU-placement pilot as the proposed action.**
2. Stack: **official Python API + React/TypeScript dashboard.**
3. Agent role: **dashboard-first; MCP agent explains and challenges evidence.**

## Round 3 — settle before split

4. Who is Builder A, who is Builder B, and who is final merger/demo presenter?
5. What is the current remaining time and is Docker working on the integration machine? If not, which teammate can host the required final container smoke test?
6. What model/provider credentials are available for Track 2 agent calls? Never paste keys in this document. Are there event-specific Track 2 constraints to preserve?
7. Approve the Contract v0.1 shape, A/B ownership and evaluation gates, or specify changes.
8. Activate starter import and implementation? Authorize branch publishing/draft PRs now or keep local until review? This is a workflow boundary requested by the user, not an inferred need for extra approvals.

## Exact research questions for our one recommendation

RQ1. Which unique jobs satisfy the selected rule, with what missing-data exclusions and measurement coverage?
RQ2. Does the supplied recommendation cite that same cohort? Which findings overlap, and at what grain?
RQ3. What eligible GPU-hours can we recompute from job/card records without adding mixed impacts?
RQ4. Which fractions could a pilot actually recover, and which assumptions are currently unmeasured?
RQ5. What false-positive action would harm useful work, and what operational guardrail would limit it?
RQ6. Does the recommendation survive lower recovery assumptions, a different reference price and explicit cancellation policy?
RQ7. Can an SRE reproduce the headline by following its evidence path?
RQ8. Can the agent explain both support and counterevidence without inventing numbers or hiding uncertainty?

## Questions for organizers if needed

- Which claims fields are mandatory given the schema/prose conflict?
- Is the detailed default-branch submission rule current?
- How should teams publish the required claims/report without violating the source-data redistribution restrictions? Do not treat an example output as blanket permission to publish raw excerpts.
- Is a bounded MCP explanation agent sufficient for Track 2's agent expectation?

Do not block independent scaffolding on every organizer answer. Record unresolved facts, use the stricter operational contract where compatible, and keep unsupported claims out of the result.
