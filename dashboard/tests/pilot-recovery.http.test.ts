import {beforeAll, describe, expect, it} from "vitest";
import {createHttpApi} from "../src/api/http";
import {createPilotRecoveryApi, type PilotBaseline, type PilotOutcome, type PilotSimulationRequest} from "../src/api/pilot-recovery";
import type {Audit} from "../src/api/types";

// Opt-in real-socket integration against our ORIGINAL SYNTHETIC fixture server.
// Explicitly refuses real-source mode; never substitutes for the five-file gate.
const url = process.env.MANAI_PILOT_HTTP_URL;
describe.skipIf(!url)("A routes → B HTTP adapter: original synthetic integration", () => {
  const calls: string[] = [];
  const fetcher: typeof fetch = (input, init) => {calls.push(String(input)); return fetch(input, init);};
  const api = createHttpApi({baseUrl: url, fetcher});
  const pilot = createPilotRecoveryApi({baseUrl: url, fetcher});
  let audit: Audit, baseline: PilotBaseline;

  beforeAll(async () => {
    const health = await api.getHealth();
    expect(health.mode).toBe("synthetic_fixture");
    const overview = await api.getOverview();
    expect(overview.provenance.synthetic).toBe(true);
    audit = await api.createAudit({client_request_id: crypto.randomUUID(),
      expected_data_fingerprint: health.data_fingerprint!, recommendation_id: "cpu-placement-pilot",
      scenario: {recovery_fraction: {low: 0, point: 0, high: 0}, usd_per_gpu_hour: 2.5,
        cancelled_policy: "exclude", interval_kind: "scenario", assumption_note: "Original synthetic HTTP test only"}});
    const list = await pilot.getBaselines(audit);
    expect(list.synthetic).toBe(true);
    expect(list.total).toBe(1);
    baseline = list.items[0];
    expect(baseline.original_reference_cost_usd).toBe(50);
  });

  function request(outcome: PilotOutcome): PilotSimulationRequest {
    return {client_request_id: crypto.randomUUID(), baseline_evidence_id: baseline.evidence_id,
      proposal: "Original test: move this invented workload to four CPU cores",
      correctness_check: "Invented test: final output must match the reference within the owner-approved tolerance",
      cpu_vcpus: 4, cpu_hours: outcome === "success" ? 12 : 3, cpu_vcpu_hour_usd: .1,
      max_runtime_hours: 20, max_trial_spend_usd: 100, setup_cost_usd: 0, extra_queue_hours: 0,
      baseline_host_costs_included: true, outcome,
      failure_reason: outcome === "success" ? "" : "Assumed output mismatch",
      recovery_note: "Original synthetic recovery-availability assumption"};
  }

  it.each(["success", "failure_recovered", "failure_unavailable"] as const)("validates and preserves %s across the HTTP boundary", async outcome => {
    const result = await pilot.simulate(audit, baseline, request(outcome));
    expect(result.execution_performed).toBe(false);
    expect(result.baseline).toEqual(baseline);
    expect(result.recovery.checkpoint_verified).toBe(false);
    if (outcome === "success") {
      expect(result.costs.total_cost_to_complete_usd).toBeCloseTo(4.8);
      expect(result.costs.net_benefit_usd).toBeCloseTo(45.2);
      expect(result.timing.completion_change_hours).toBe(2);
    } else if (outcome === "failure_recovered") {
      expect(result.costs.recovery_cost_usd).toBe(50);
      expect(result.costs.total_cost_to_complete_usd).toBeCloseTo(51.2);
      expect(result.costs.net_benefit_usd).toBeCloseTo(-1.2);
      expect(result.timing.completion_change_hours).toBe(3);
    } else {
      expect(result.status).toBe("paused");
      expect(result.costs.cost_so_far_usd).toBeCloseTo(1.2);
      expect(result.costs.total_cost_to_complete_usd).toBeNull();
      expect(result.costs.net_benefit_usd).toBeNull();
      expect(result.timing.completion_change_hours).toBeNull();
    }
  });

  it("enforces a simulated cap and leaves the canonical audit/claims unchanged without C", async () => {
    const claims = await api.exportClaims(audit.audit_id, "Original synthetic test");
    const result = await pilot.simulate(audit, baseline, {...request("success"), max_runtime_hours: 1});
    expect(result.effective_outcome).toBe("failure_recovered");
    expect(result.stop_reason).toBe("runtime_limit");
    expect(result.costs.net_benefit_usd).toBeCloseTo(-.4);
    expect(await api.getAudit(audit.audit_id)).toEqual(audit);
    expect(await api.exportClaims(audit.audit_id, "Original synthetic test")).toEqual(claims);
    expect(calls.some(path => /\/(explanations|chat)(?:\?|$)/.test(path))).toBe(false);
  });

  it("preserves unknown price and queue through the actual A response", async () => {
    const result = await pilot.simulate(audit, baseline, {...request("success"), cpu_vcpu_hour_usd: null, extra_queue_hours: null});
    expect(result.costs.net_benefit_usd).toBeNull();
    expect(result.timing.completion_change_hours).toBeNull();
    expect(result.limits.spend_limit_status).toBe("unverified");
  });
});
