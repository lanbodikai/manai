import {describe, expect, it, vi} from "vitest";
import {createPilotRecoveryApi} from "../src/api/pilot-recovery";
import {audit, baselines, clone, json, request, simulation} from "./pilot-recovery.fixtures";

describe("Pilot & Recovery HTTP boundary", () => {
  it("reads the frozen baseline and all three original synthetic result examples without C", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(json(baselines()));
    const api = createPilotRecoveryApi({fetcher});
    expect(await api.getBaselines(audit())).toEqual(baselines());
    for (const outcome of ["success", "failure_recovered", "failure_unavailable"] as const) {
      const result = simulation(outcome); fetcher.mockResolvedValueOnce(json(result));
      expect(await api.simulate(audit(), result.baseline, result.inputs)).toEqual(result);
    }
    expect(fetcher.mock.calls.map(([path]) => path)).toEqual([
      "/api/audits/synthetic-pilot-audit/pilot-baselines",
      ...Array(3).fill("/api/audits/synthetic-pilot-audit/pilot-simulations"),
    ]);
    for (const [, options] of fetcher.mock.calls) expect(options).toMatchObject({redirect: "error"});
  });
  it.each(["audit_id", "audit_client_request_id", "data_fingerprint", "source_version", "synthetic"] as const)("rejects a mismatched %s before display", async key => {
    const payload = baselines(); Object.assign(payload, {[key]: key === "synthetic" ? false : "different"});
    const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json(payload))});
    await expect(api.getBaselines(audit())).rejects.toMatchObject({code: "PILOT_SCOPE_MISMATCH", status: 409});
  });
  it("rejects missing records and duplicate evidence IDs", async () => {
    for (const payload of [{...baselines(), total: 2}, {...baselines(), total: 2, items: [baselines().items[0], baselines().items[0]]}]) {
      const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json(payload))});
      await expect(api.getBaselines(audit())).rejects.toMatchObject({code: "PILOT_BASELINES_INVALID"});
    }
  });
  it("rejects stale request, rewritten inputs and a changed frozen baseline", async () => {
    for (const mutate of [
      (v: ReturnType<typeof simulation>) => {v.client_request_id = "old-request";},
      (v: ReturnType<typeof simulation>) => {v.inputs.cpu_vcpus = 99;},
      (v: ReturnType<typeof simulation>) => {v.baseline.recorded_gpu_hours = 99;},
      (v: ReturnType<typeof simulation>) => {v.baseline.synthetic = false;},
    ]) {
      const payload = simulation(); mutate(payload);
      const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json(payload))});
      await expect(api.simulate(audit(), baselines().items[0], request())).rejects.toBeInstanceOf(Error);
    }
  });
  it("preserves unknown and negative server values, without recalculation", async () => {
    const payload = simulation("failure_recovered"); payload.costs.net_benefit_usd = -123.45;
    payload.timing.completion_change_hours = null; payload.costs.total_cost_to_complete_usd = null;
    const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json(payload))});
    const result = await api.simulate(audit(), payload.baseline, payload.inputs);
    expect(result.costs.net_benefit_usd).toBe(-123.45); expect(result.costs.total_cost_to_complete_usd).toBeNull(); expect(result.timing.completion_change_hours).toBeNull();
  });
  it("requires a closed, finite request and failure details without sending bad inputs", async () => {
    const fetcher = vi.fn(); const api = createPilotRecoveryApi({fetcher});
    for (const bad of [{cpu_hours: NaN}, {cpu_hours: Infinity}, {cpu_vcpus: 1.5}, {cpu_hours: 0},
      {proposal: " "}, {correctness_check: ""}, {outcome: "failure_recovered", failure_reason: " "}, {checkpoint_verified: true}])
      await expect(api.simulate(audit(), baselines().items[0], {...request(), ...bad} as ReturnType<typeof request>)).rejects.toMatchObject({code: "PILOT_INPUT_INVALID", status: 422});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("rejects contract drift and false claims of workload execution", async () => {
    for (const change of [{feature_version: "0.2"}, {execution_performed: true}, {extra_field: 1}]) {
      const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json({...simulation(), ...change}))});
      await expect(api.simulate(audit(), baselines().items[0], request())).rejects.toMatchObject({code: "PILOT_RESPONSE_INVALID"});
    }
  });
  it.each([404, 409, 422, 503])("preserves a structured %s response instead of substituting a simulation", async status => {
    const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json({error: {code: "TEST_FAILURE", message: "Original test error", retryable: status === 503, request_id: "test"}}, status))});
    await expect(api.getBaselines(audit())).rejects.toMatchObject({code: "TEST_FAILURE", status, retryable: status === 503});
  });
  it("normalizes malformed JSON and malformed error responses", async () => {
    for (const response of [new Response("not json"), json({message: "bad"}, 404)]) {
      const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(response)});
      await expect(api.getBaselines(audit())).rejects.toMatchObject({code: "PILOT_RESPONSE_INVALID", status: 502});
    }
  });
  it("bounds response size even without a content-length", async () => {
    const api = createPilotRecoveryApi({fetcher: vi.fn().mockResolvedValue(json(baselines())), maxBytes: 20});
    await expect(api.getBaselines(audit())).rejects.toMatchObject({code: "PILOT_RESPONSE_TOO_LARGE"});
  });
  it("times out noncooperating fetchers and cancels the request", async () => {
    let signal: AbortSignal | undefined;
    const fetcher = vi.fn((_url, init) => {signal = init.signal; return new Promise<Response>(() => {});});
    const api = createPilotRecoveryApi({fetcher, timeoutMs: 10});
    await expect(api.getBaselines(audit())).rejects.toMatchObject({code: "PILOT_REQUEST_TIMEOUT", status: 504});
    expect(signal?.aborted).toBe(true);
  });
  it("aborts outdated requests without retrying or touching the reviewer", async () => {
    const controller = new AbortController(); const fetcher = vi.fn(() => new Promise<Response>(() => {}));
    const api = createPilotRecoveryApi({fetcher}); const pending = api.getBaselines(audit(), controller.signal);
    controller.abort(); await expect(pending).rejects.toMatchObject({code: "PILOT_REQUEST_CANCELLED"}); expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
