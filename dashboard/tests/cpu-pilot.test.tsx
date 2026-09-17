import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CpuPilot } from "../src/components/CpuPilot";
import { createMockApi } from "../src/mock/api";
import { parse, validateAuditRequest } from "../src/api/validation";
import fixture from "../../contracts/examples/audit-response.json";
import requestFixture from "../../contracts/examples/audit-request.json";
import type { Scenario } from "../src/api/types";

describe("v0.4 single-job pilot", () => {
  it("submits explicit assumptions while retaining unknown price/queue and cohort fractions", async () => {
    const audit = parse("Audit", structuredClone(fixture));
    delete audit.scenario.cpu_pilot;
    audit.downside.cpu_pilot = null;
    const api = createMockApi({ delay: 0 });
    api.listEvidence = vi.fn().mockResolvedValue({audit_id:audit.audit_id,items:audit.evidence_preview,total:2,next_cursor:null});
    const submit = vi.fn<(s: Scenario) => void>();
    render(<CpuPilot api={api} audit={audit} busy={false} onSubmit={submit} onEvidence={() => {}} />);
    await waitFor(() => expect(screen.getByLabelText("Baseline eligible job")).toBeEnabled());
    fireEvent.change(screen.getByLabelText("Baseline eligible job"), {target:{value:"job:J2"}});
    fireEvent.change(screen.getByLabelText("CPU vCPUs"), {target:{value:"4"}});
    fireEvent.change(screen.getByLabelText("CPU duration (hours)"), {target:{value:"12"}});
    fireEvent.change(screen.getByLabelText("CPU assumptions and source"), {target:{value:"Invented test assumptions; not a measured workload."}});
    fireEvent.click(screen.getByRole("button", {name:"Model CPU pilot"}));
    expect(submit).toHaveBeenCalledOnce();
    expect(submit.mock.calls[0][0]).toMatchObject({recovery_fraction:audit.scenario.recovery_fraction,
      cpu_pilot:{baseline_evidence_id:"job:J2",cpu_vcpus:4,cpu_hours:12,cpu_vcpu_hour_usd:null,extra_queue_hours:null,baseline_host_costs_included:false}});
  });
  it("preserves signed loss/earlier completion and shows null as unknown", async () => {
    const audit = parse("Audit", structuredClone(fixture));
    audit.downside.cpu_pilot!.net_reference_value_usd = -12;
    audit.downside.cpu_pilot!.added_cpu_reference_usd = null;
    audit.downside.cpu_pilot!.completion_change_hours_including_extra_queue = -2;
    const api = createMockApi({delay:0});
    api.listEvidence = vi.fn().mockResolvedValue({audit_id:audit.audit_id,items:[],total:0,next_cursor:null});
    const evidence = vi.fn();
    render(<CpuPilot api={api} audit={audit} busy={false} onSubmit={() => {}} onEvidence={evidence} />);
    expect(screen.getByTestId("cpu-net")).toHaveTextContent("-$12");
    expect(screen.getByTestId("cpu-cost")).toHaveTextContent("Unknown");
    expect(screen.getByTestId("cpu-delay")).toHaveTextContent("-2 h");
    fireEvent.click(screen.getByRole("button",{name:"Inspect CPU baseline evidence"}));
    expect(evidence).toHaveBeenCalledWith("job:J2");
    await screen.findByText("No eligible baseline jobs in this audit.");
  });
  it("rejects nonfinite numbers, nonpositive successful duration and cap violations", () => {
    for (const patch of [{cpu_hours:0}, {cpu_hours:Infinity}, {cpu_vcpus:1.5}, {cpu_vcpu_hour_usd:NaN}, {trial_cap_hours:1}]) {
      const value = structuredClone(requestFixture);
      Object.assign(value.scenario.cpu_pilot,patch);
      expect(() => validateAuditRequest(value)).toThrow();
    }
  });
});
