"""Independent high-precision reference; no production model/cohort imports."""
from decimal import Decimal, ROUND_CEILING, getcontext
getcontext().prec = 40
D = lambda x: Decimal(str(x))


def reference(row, action, case, allocation, price):
    h, seconds, cards, p = D(row['gpu_hours']), D(row['walltime_sec'] or 0), D(row['gpu_count'] or 0), D(price)
    elapsed = seconds / 3600
    out = dict(gross_reference_usd=D(0), intervention_reference_usd=D(0), enrolled_gpu_hours=D(0),
               released_gpu_hours=D(0), avoided_replay_gpu_hours=D(0), overhead_gpu_hours=D(0), cpu_core_hours=D(0))
    if action == 'cpu-placement':
        cores = D(48) if allocation == 'whole_node' else max(D(row['cpus_req']), (D(row['mem_req_total_mb']) / 4000).to_integral_value(rounding=ROUND_CEILING))
        out.update(gross_reference_usd=h*p, intervention_reference_usd=elapsed*cores*p*D(case['cpu_price_ratio']),
                   enrolled_gpu_hours=h, released_gpu_hours=h, cpu_core_hours=elapsed*cores)
        failure = -out['intervention_reference_usd']
    elif action == 'timeouts':
        interval = D(case['interval_minutes'])*60
        count = max(0, int((seconds/interval).to_integral_value(rounding=ROUND_CEILING))-1)
        saved_seconds = count*interval
        coverage, replay = D(case['checkpoint_enrollment']), D(case['replay_fraction'])
        overhead_seconds = count*D(case['checkpoint_minutes'])*60+D(case['restart_minutes'])*60
        preserved = h*saved_seconds/seconds*coverage*replay
        overhead = overhead_seconds/3600*cards*coverage
        out.update(gross_reference_usd=preserved*p, intervention_reference_usd=overhead*p,
                   enrolled_gpu_hours=h*coverage, avoided_replay_gpu_hours=preserved, overhead_gpu_hours=overhead)
        failure = -overhead*p
    elif action == 'idle-sessions':
        coverage = D(case['idle_enrollment'])
        release_seconds = D(case['release_hours'])*3600
        tail_fraction = max(D(0), (seconds-release_seconds)/seconds)
        avoided = h*tail_fraction*coverage
        retry = h*coverage*D(case['mistake_fraction']) if tail_fraction > 0 else D(0)
        out.update(gross_reference_usd=avoided*p, intervention_reference_usd=retry*p,
                   enrolled_gpu_hours=h*coverage, released_gpu_hours=avoided, overhead_gpu_hours=retry)
        failure = (avoided-(h*coverage if tail_fraction > 0 else D(0)))*p
    else:
        s=case['screening'][action];enrolled=h*D(s['enrollment'])
        added=enrolled*D(s['added_cost_fraction'])*p
        out.update(gross_reference_usd=enrolled*D(s['avoided_fraction'])*p,intervention_reference_usd=added,
                   enrolled_gpu_hours=enrolled,released_gpu_hours=enrolled*D(s['avoided_fraction']))
        failure=-added-enrolled*D(s['failure_cost_fraction'])*p
    out['net_reference_usd'] = out['gross_reference_usd']-out['intervention_reference_usd']
    out['failure_net_reference_usd'] = failure
    return out


def close(actual, expected):
    assert actual is not None
    assert abs(D(actual)-D(expected)) <= max(D('1e-8'), abs(D(expected))*D('1e-9')), (actual, str(expected))
