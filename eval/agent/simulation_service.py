"""Simulation-only A entrypoint: original A I/O/calculators, synthetic labels.

The full-flow runner copies this into an isolated runtime with invented data.
Only provenance labels are adapted: readiness, checksums, HTTP routes, audit
storage, calculators, official API and MCP remain actual implementations.
"""
from pathlib import Path

from service import main, analysis_routes
from service.audits import freeze_evidence

if not (Path(__file__).resolve().parents[2] / 'data/SIMULATION_ONLY').is_file():
    raise RuntimeError('Refusing simulation entrypoint without isolated synthetic data marker')


def label(provenance):
    provenance.update(synthetic=True, source_version='original-full-flow-simulation-v1',
                      sample_label='SYNTHETIC SIMULATION: two invented jobs, not organizer telemetry',
                      window_label='Invented ten-hour window')
    provenance['caveats'] = ['Simulation only; no workload executed or savings measured.']


prepare = analysis_routes.prepare_context
map_overview = main.map_overview


def synthetic_context(*args):
    context = prepare(*args)
    label(context['provenance'])
    for detail in context['evidence'].values():
        label(detail['provenance'])
        detail['evidence']['synthetic'] = True
    return freeze_evidence(context)


def synthetic_overview(*args):
    result = map_overview(*args)
    label(result['provenance'])
    result['warnings'].append('SYNTHETIC SIMULATION ONLY')
    return result


analysis_routes.prepare_context = synthetic_context
main.map_overview = synthetic_overview
app = main.app
