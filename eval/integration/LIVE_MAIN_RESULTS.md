# Localhost live testing after main merge

Base: main `c34f1b2`. Host: http://127.0.0.1:13121. C excluded.

The running analysis main/review files matched the merged source exactly.
Initial `node eval/integration/portfolio.cjs` failed on the non-CPU Decisions
Model link: the parent row's `aria-disabled=true` disabled descendant links.
Removed that row-level attribute; unimplemented action checkboxes remain disabled.
Winston requested direct main modifications. The correction is in main's checkout.

Commands and results:

- `node node_modules/vitest/vitest.mjs run tests/optimization.test.tsx`: 14/14 PASS.
- Rebuild isolated dashboard with `docker compose ... up -d --build --no-deps --wait dashboard`: PASS; analysis/data services unchanged.
- `node eval/integration/portfolio.cjs http://127.0.0.1:13121 private-eval/live-main/portfolio-navfix-01`: all seven grouped checks PASS. Shared eight-action result; cross-page drafts/deep links; recalculation; matching export/evidence; exclusive assignments after deselection; invalid-input/service-error retention and retry; desktop/390px layout without browser errors. Mobile screenshot inspected.

These cover U01–U04 behaviors in the simulation flow, not independent timed U05
or actual workload outcomes. Browser/provider checks from the release remain
documented in FEATHERLESS_WRAPUP.md. Initial failed receipt was preserved privately.
User feedback on review readability and evidence coverage is a separate follow-up.

Follow-up: removed disabled-row styling when a simulation is available and labeled
those rows "Simulation available". Live browser verified all eight rows have full
opacity, Model deep links work, and the seven unimplemented action selectors stay
disabled. Rebuilt only the dashboard; 14/14 decision tests and build/typecheck pass.
