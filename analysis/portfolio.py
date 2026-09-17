"""Conditional reference-cost comparisons; never canonical recovery or cash savings."""
from collections import Counter
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import math
from pathlib import Path
import statistics

from analysis.core import finite, native, select_cohort
from analysis.hardware_scenario import resource_fit, positive
from analysis.cpu_pilot import assess_cpu_pilot

VERSION = 'portfolio-simulation-1'
ACTIONS = ('cpu-placement', 'idle-sessions', 'timeouts', 'startup-failures', 'failed-arrays', 'low-utilization', 'gpu-imbalance', 'memory-sizing')
RULES = dict(zip(ACTIONS, ('rules::gpu-not-needed', 'rules::idle-interactive-session', 'rules::wallclock-kill',
                         'rules::gpu-never-computed', 'rules::array-task-failure', 'rules::gpu-low-utilization', 'rules::gpu-imbalance', 'rules::gpu-memory-oversized')))
PRESETS = json.loads((Path(__file__).resolve().parents[1] / 'contracts/portfolio-presets.json').read_text())
FIELDS = ('id_job', 'state_name', 'sm_util_avg', 'sm_util_max', 'gpu_hours', 'gpu_count', 'walltime_sec',
          'max_gpu_mem_used', 'nodes_alloc', 'n_nodes_listed', 'cpus_req', 'mem_req_total_mb', 'job_type')
LIMITATIONS = [
    'Illustrative assumptions, not calibrated probabilities, confidence intervals or measured cash savings.',
    'Enrollment and outcome fractions represent assumed workload shares, not observed or selected job counts.',
    'Checkpoint value is avoided future replay for equivalent work; original timed-out spending is not refunded.',
    'The historical 20% reference-cost target is a benchmark, not a forecast of next-quarter billing.',
    'Idle release is assumed at an elapsed allocation age; whole-job utilization does not locate inactivity.',
    'Idle tails and checkpoint progress prorate recorded GPU-hours by scheduler duration.',
    'CPU compatibility, checkpoint support, owner participation and preserved research performance remain unverified.',
    'Zero monetary overhead inputs mean omitted setup, storage and other costs. Queue effects and business harm are unpriced.',
    'Failure stress includes one full rerun where specified, not unlimited retries or an absolute worst case.',
    'Five screening estimates assume fractional allocation avoided and additional costs; they do not verify a smaller GPU, faster sharding or a diagnosed failure cause.',
]


def prepare(rows, findings=None):
    rows = [{k: native(r.get(k)) for k in FIELDS} for r in rows]
    by_id = {str(r['id_job']): r for r in rows}
    if not rows or len(rows) != len(by_id) or any(r['id_job'] is None or not finite(r['gpu_hours']) or r['gpu_hours'] < 0 for r in rows):
        raise ValueError('Invalid unique-job accounting')
    sets = {'cpu-placement': {str(r['id_job']) for r in select_cohort(rows).jobs},
            'idle-sessions': {str(r['id_job']) for r in rows if r['state_name'] != 'CANCELLED' and r['job_type'] == 'LLSUB:INTERACTIVE'
                              and finite(r['walltime_sec']) and r['walltime_sec'] > 14400 and finite(r['sm_util_avg']) and 0 <= r['sm_util_avg'] < 5},
            'timeouts': {str(r['id_job']) for r in rows if r['state_name'] == 'TIMEOUT'}}
    sets.update({a: set() for a in ACTIONS[3:]})
    if findings is not None:
        for action, rule in RULES.items():
            expected_kind = 'lost' if action == 'timeouts' else 'unused_capacity'
            found = set()
            for f in findings:
                m = f.get('metadata', {})
                if f.get('detectorId') != rule or m.get('synthetic', False):
                    continue
                if m.get('impact_scope') != 'job':
                    if action in ACTIONS[3:]:
                        continue
                    raise ValueError('Unexpected finding scope')
                if action in ACTIONS[:3] and m.get('impact_kind') != expected_kind:
                    raise ValueError('Unexpected finding scope or kind')
                key = str(m.get('job_id'))
                if key not in by_id:
                    raise ValueError('Unresolved finding identity')
                if by_id[key]['state_name'] != 'CANCELLED':
                    found.add(key)
            if action in ACTIONS[3:]:
                sets[action] = found
            elif found != sets[action]:
                raise ValueError('Independent cohort does not match finding identities: ' + action)
    return by_id, sets


def discrepancy(row):
    if not positive(row['walltime_sec']) or not positive(row['gpu_count'], True):
        return None
    allocation = row['walltime_sec'] / 3600 * row['gpu_count']
    return abs(row['gpu_hours'] - allocation) / allocation


def evaluability(row, action):
    if action in ACTIONS[3:]:
        return None  # Screening uses recorded allocation only, with no timing/fit claim.
    if action == 'cpu-placement':
        fit = resource_fit(row)
        return None if fit['status'] == 'fits' else fit['reason']
    d = discrepancy(row)
    if d is None:
        return 'invalid_timing_or_gpu_count'
    # Decimal boundary prevents floating rounding from changing the 10% cutoff.
    nominal = Decimal(str(row['walltime_sec'])) / 3600 * Decimal(str(row['gpu_count']))
    if abs(Decimal(str(row['gpu_hours'])) - nominal) > nominal / 10:
        return 'accounting_discrepancy_over_10_percent'
    return None


def job_case(row, action, case, allocation, price):
    h, t, g = row['gpu_hours'], row['walltime_sec'] / 3600 if positive(row['walltime_sec']) else None, row['gpu_count']
    result = dict(gross_reference_usd=0., intervention_reference_usd=0., net_reference_usd=0.,
                  failure_net_reference_usd=0., enrolled_gpu_hours=0., released_gpu_hours=0.,
                  avoided_replay_gpu_hours=0., overhead_gpu_hours=0., cpu_core_hours=0.,
                  modeled_elapsed_change_hours=None, failure_elapsed_change_hours=None,
                  checkpoints=0, preserved_progress_hours=0., released_tail_hours=0.)
    if action == 'cpu-placement':
        cores = resource_fit(row)['memory_adjusted_cores'] if allocation == 'memory_adjusted' else 48
        pilot = dict(mode='replacement_success', baseline_evidence_id='portfolio:' + str(row['id_job']), cpu_vcpus=cores,
                     cpu_hours=t, cpu_vcpu_hour_usd=price * case['cpu_price_ratio'], extra_queue_hours=0,
                     trial_cap_hours=None, baseline_host_costs_included=True, assumption_note='Unchanged runtime; physical-core units.')
        success = assess_cpu_pilot(row, pilot, price)
        failure = assess_cpu_pilot(row, {**pilot, 'mode': 'replacement_failure'}, price)
        result.update(gross_reference_usd=h * price, intervention_reference_usd=success['added_cpu_reference_usd'],
                      enrolled_gpu_hours=h, released_gpu_hours=h, cpu_core_hours=success['added_cpu_vcpu_hours'],
                      failure_net_reference_usd=failure['net_reference_value_usd'], modeled_elapsed_change_hours=0.,
                      failure_elapsed_change_hours=t)
    elif action == 'timeouts':
        e, replay = case['checkpoint_enrollment'], case['replay_fraction']
        interval = Decimal(str(case['interval_minutes'])) * 60
        n = max(0, int((Decimal(str(row['walltime_sec'])) / interval).to_integral_value(rounding=ROUND_CEILING)) - 1)
        saved = float(n * interval / 3600)
        overhead = (n * case['checkpoint_minutes'] + case['restart_minutes']) / 60
        avoided = e * replay * h * saved / t
        overhead_h = e * g * overhead
        result.update(gross_reference_usd=avoided * price, intervention_reference_usd=overhead_h * price,
                      failure_net_reference_usd=-overhead_h * price, enrolled_gpu_hours=e * h,
                      avoided_replay_gpu_hours=avoided, overhead_gpu_hours=overhead_h,
                      checkpoints=n, preserved_progress_hours=saved,
                      modeled_elapsed_change_hours=e * (overhead - replay * saved), failure_elapsed_change_hours=e * overhead)
    elif action == 'idle-sessions':
        e, mistaken = case['idle_enrollment'], case['mistake_fraction']
        tail = max(0., t - case['release_hours'])
        released = e * h * tail / t
        # Jobs ending before the release threshold receive no interruption/rerun.
        rerun = e * mistaken * h if tail > 0 else 0.
        stress_rerun = e * h if tail > 0 else 0.
        result.update(gross_reference_usd=released * price, intervention_reference_usd=rerun * price,
                      failure_net_reference_usd=(released - stress_rerun) * price,
                      enrolled_gpu_hours=e * h, released_gpu_hours=released, released_tail_hours=tail,
                      overhead_gpu_hours=rerun,
                      failure_elapsed_change_hours=e * case['release_hours'] if tail > 0 else 0.)
    else:
        assumptions = case['screening'][action]
        enrolled = h * assumptions['enrollment']
        added = enrolled * assumptions['added_cost_fraction'] * price
        result.update(gross_reference_usd=enrolled * assumptions['avoided_fraction'] * price,
                      intervention_reference_usd=added, enrolled_gpu_hours=enrolled,
                      released_gpu_hours=enrolled * assumptions['avoided_fraction'],
                      failure_net_reference_usd=-(added + enrolled * assumptions['failure_cost_fraction'] * price))
    result['net_reference_usd'] = result['gross_reference_usd'] - result['intervention_reference_usd']
    return result


def stats(rows):
    durations = sorted(r['walltime_sec'] / 3600 for r in rows if finite(r['walltime_sec']) and r['walltime_sec'] >= 0)
    def quantile(q):
        if not durations:
            return None
        pos = (len(durations) - 1) * q
        lo = math.floor(pos)
        return durations[lo] + (durations[min(lo + 1, len(durations)-1)] - durations[lo]) * (pos-lo)
    ds = [discrepancy(r) for r in rows]
    return {'duration_hours': {'median': quantile(.5), 'q1': quantile(.25), 'q3': quantile(.75)},
            'gpu_counts': dict(Counter(str(r['gpu_count']) if positive(r['gpu_count'], True) else 'unknown' for r in rows)),
            'accounting_discrepancy': dict(Counter('unknown' if d is None else 'over_10_percent' if d > .1 else '0.1_to_10_percent' if d > .001 else 'within_0.1_percent' for d in ds)),
            'gpu_memory': dict(Counter('unknown' if not finite(r['max_gpu_mem_used']) or r['max_gpu_mem_used'] < 0 else 'zero' if r['max_gpu_mem_used'] == 0 else 'positive' for r in rows))}


def calculate(rows, findings, request, fingerprint, price, price_version, synthetic=False):
    by_id, cohorts = prepare(rows, findings)
    selected = set(request['selected_actions'])
    evidence, assigned = [], {a: [] for a in ACTIONS}
    union = set().union(*(cohorts[a] for a in selected))
    for key in sorted(union):
        row = by_id[key]
        candidates = [a for a in ACTIONS if a in selected and key in cohorts[a]]
        exclusions = {a: evaluability(row, a) for a in candidates}
        action = next((a for a in candidates if exclusions[a] is None), None)
        if action:
            assigned[action].append(row)
        evidence.append({'job_id': key, 'diagnoses': candidates, 'assigned_action': action,
                         'exclusions': {a: reason for a, reason in exclusions.items() if reason},
                         'source': row, 'accounting_discrepancy': discrepancy(row),
                         'cases': {c['id']: job_case(row, action, c, request['cpu_allocation'], price) for c in request['cases']} if action else {}})
    baseline = math.fsum(r['gpu_hours'] for r in by_id.values()) * price
    if not positive(baseline) or not positive(price):
        raise ValueError('Invalid baseline')
    action_results = []
    sum_fields = ['gross_reference_usd', 'intervention_reference_usd', 'net_reference_usd', 'failure_net_reference_usd',
                  'enrolled_gpu_hours', 'released_gpu_hours', 'avoided_replay_gpu_hours', 'overhead_gpu_hours', 'cpu_core_hours']
    for action in ACTIONS:
        if action not in selected:
            continue
        diagnosed = [by_id[k] for k in sorted(cohorts[action])]
        rejected = [r for r in diagnosed if evaluability(r, action)]
        cases = []
        for c in request['cases']:
            values = [j['cases'][c['id']] for j in evidence if j['assigned_action'] == action]
            aggregate = {f: math.fsum(v[f] for v in values) for f in sum_fields}
            fixed = math.fsum(request['overheads'][action].values())
            aggregate['intervention_reference_usd'] += fixed
            aggregate['net_reference_usd'] -= fixed
            aggregate['failure_net_reference_usd'] -= fixed
            aggregate['failure_extra_reference_usd'] = -aggregate['failure_net_reference_usd']
            aggregate['fixed_overhead_usd'] = fixed
            aggregate['modeled_elapsed_change_hours'] = (math.fsum(v['modeled_elapsed_change_hours'] for v in values)
                                                         if all(v['modeled_elapsed_change_hours'] is not None for v in values) else None)
            aggregate['failure_elapsed_change_hours'] = math.fsum(v['failure_elapsed_change_hours'] for v in values) if all(v['failure_elapsed_change_hours'] is not None for v in values) else None
            aggregate['checkpoints_per_job_summary'] = {'min': min((v['checkpoints'] for v in values), default=0), 'max': max((v['checkpoints'] for v in values), default=0)}
            cases.append({'id': c['id'], **aggregate})
        standalone = []
        for c in request['cases']:
            values = [job_case(r, action, c, request['cpu_allocation'], price) for r in diagnosed if evaluability(r, action) is None]
            fixed = math.fsum(request['overheads'][action].values())
            standalone.append({'id': c['id'], 'net_reference_usd': math.fsum(v['net_reference_usd'] for v in values)-fixed})
        action_results.append({'id': action, 'model_kind': 'detailed_mechanism' if action in ACTIONS[:3] else 'assumption_only_screening',
                               'standalone_cases': standalone, 'diagnosed_jobs': len(diagnosed), 'diagnosed_gpu_hours': math.fsum(r['gpu_hours'] for r in diagnosed),
                               'evaluable_jobs': len(diagnosed)-len(rejected), 'excluded_jobs': len(rejected),
                               'excluded_gpu_hours': math.fsum(r['gpu_hours'] for r in rejected),
                               'exclusion_reasons': dict(Counter(evaluability(r, action) for r in rejected)),
                               'assigned_jobs': len(assigned[action]), 'assigned_gpu_hours': math.fsum(r['gpu_hours'] for r in assigned[action]),
                               'statistics': stats(diagnosed), 'cases': cases})
    portfolio = []
    for c in request['cases']:
        values = [next(v for v in a['cases'] if v['id'] == c['id']) for a in action_results]
        agg = {f: math.fsum(v[f] for v in values) for f in sum_fields}
        net = agg['net_reference_usd']
        portfolio.append({'id': c['id'], **agg, 'failure_extra_reference_usd': -agg['failure_net_reference_usd'],
                          'baseline_reduction_pct': 100 * net / baseline, 'target_contribution_pct': 100 * net / (.2 * baseline),
                          'remaining_target_reference_usd': max(0., .2 * baseline - net)})
    bounds = {k: {'low': min(c[k] for c in portfolio), 'high': max(c[k] for c in portfolio)} for k in
              ['net_reference_usd', 'failure_extra_reference_usd', 'baseline_reduction_pct', 'target_contribution_pct', 'remaining_target_reference_usd']}
    result = {'contract_version': VERSION, 'dataset_version': request['dataset_version'], 'data_fingerprint': fingerprint,
              'synthetic': synthetic, 'kind': 'scenario_estimate', 'cash_savings_verified': False, 'performance_verified': False,
              'configuration': request, 'price_book_version': price_version, 'gpu_reference_usd_per_hour': price,
              'baseline_reference_usd': baseline, 'target_reference_usd': .2 * baseline, 'actions': action_results,
              'cases': portfolio, 'bounds': bounds, 'limitations': LIMITATIONS,
              'coverage': {'unique_jobs': len(union), 'unique_gpu_hours': math.fsum(by_id[k]['gpu_hours'] for k in union),
                           'assigned_jobs': sum(len(v) for v in assigned.values()),
                           'unassigned_jobs': sum(j['assigned_action'] is None for j in evidence),
                           'unassigned_gpu_hours': math.fsum(j['source']['gpu_hours'] for j in evidence if j['assigned_action'] is None),
                           'overlapping_references_removed': sum(len(cohorts[a]) for a in selected)-len(union),
                           'overlapping_gpu_hours_removed': math.fsum(by_id[k]['gpu_hours'] for a in selected for k in cohorts[a])-math.fsum(by_id[k]['gpu_hours'] for k in union)}}
    result['simulation_id'] = hashlib.sha256(json.dumps({'result': result, 'evidence': evidence}, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return result, evidence
