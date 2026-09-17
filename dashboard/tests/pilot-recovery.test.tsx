import {describe, expect, it, vi} from "vitest";
import {render, screen, within, waitFor, fireEvent, act} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {PilotRecoveryPanel} from "../src/components/PilotRecoveryPanel";
import {App} from "../src/App";
import * as pilotRecoveryModule from "../src/api/pilot-recovery";
import type {Audit, DashboardApi, Schemas} from "../src/api/types";
import type {PilotBaseline, PilotRecoveryApi, PilotSimulation, PilotSimulationRequest} from "../src/api/pilot-recovery";
import {ApiError} from "../src/api/validation";
import {audit, baselines, clone, simulation} from "./pilot-recovery.fixtures";

function dashboard(): DashboardApi {
  return {getHealth: vi.fn(async () => ({service: "ok", contract_version: "0.4", data_status: "ready", data_fingerprint: audit().provenance.data_fingerprint, agent_status: "unavailable", mode: "synthetic_fixture"})),
    listRecommendations: vi.fn(async () => ({provenance: audit().provenance, items: []})),
    getOverview: vi.fn(async () => ({provenance: audit().provenance, price_book_version: "original-test", usd_per_gpu_hour: 3.25, allocated_gpu_hours: 20, job_count: 1, outcomes: [], warnings: []})),
    createAudit: vi.fn(async (body: Schemas["AuditRequest"]) => ({...audit(), client_request_id: body.client_request_id, scenario: body.scenario})),
    explainAudit: vi.fn(async () => {throw new Error("C must never be used");}),
    askBaseChat: vi.fn(async () => {throw new Error("Chat must never be used");}),
  } as unknown as DashboardApi;
}
function pilotApi(modify?: (result: PilotSimulation) => void): PilotRecoveryApi {
  let count = 0;
  return {getBaselines: vi.fn(async (scope: Audit) => ({...baselines(), audit_client_request_id: scope.client_request_id})),
    simulate: vi.fn(async (_audit: Audit, baseline: PilotBaseline, input: PilotSimulationRequest) => {
      const result = simulation(input.outcome); result.inputs = clone(input); result.client_request_id = input.client_request_id;
      result.simulation_id = `original-test-simulation-${++count}`; result.baseline = clone(baseline);
      result.failure_details.requested_failure_reason = input.failure_reason;
      result.failure_details.effective_failure_reason = input.outcome === "success" ? null : input.failure_reason;
      modify?.(result); return result;
    })};
}
async function fill(outcome: PilotSimulationRequest["outcome"] = "success", unknown = false) {
  await screen.findByText("Frozen baseline for this proposal");
  const user = userEvent.setup();
  const entries: [string, string][] = [["Proposed change", "Isolated CPU replacement"], ["Correctness check", "Compare output hash and declared tolerance"],
    ["Requested CPU trial hours", outcome === "success" ? "12" : "3"], ["Maximum trial hours", "15"], ["Maximum trial spend ($)", "20"]];
  if (!unknown) entries.push(["CPU price ($ per vCPU-hour)", "0.1"], ["Setup cost ($)", "2"], ["Extra queue time (hours)", "2"]);
  for (const [label, value] of entries) fireEvent.change(screen.getByLabelText(label, {exact: true}), {target: {value}});
  await user.selectOptions(screen.getByLabelText("Assumed outcome"), outcome);
  if (outcome !== "success") fireEvent.change(screen.getByLabelText("Failure reason (assumption)"), {target: {value: "Output mismatch needs investigation"}});
  if (!unknown) await user.click(screen.getByLabelText("I assume the original GPU reference rate includes its host and CPU costs."));
  return user;
}
const resultRegion = () => screen.getByRole("region", {name: "Saved simulation result"});
const summaryValue = (label: string) => within(resultRegion()).getByText(label, {selector: "dt"}).nextElementSibling;

describe("Pilot & Recovery panel — original synthetic scenarios", () => {
  it("keeps historical GPU setup separate from the CPU proposal and renders server success without C", async () => {
    const api = dashboard(), pilots = pilotApi(); render(<PilotRecoveryPanel api={api} audit={audit()} pilotApi={pilots}/>);
    const user = await fill();
    expect(screen.getByText("2 GPUs")).toBeVisible(); expect(screen.getByLabelText("CPU vCPUs")).toHaveValue(4);
    expect(pilots.simulate).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    expect(await screen.findByRole("heading", {name: "Successful trial — assumed outcome"})).toBeVisible();
    expect(summaryValue("Net benefit (negative means extra cost)")).toHaveTextContent("$43.20");
    expect(summaryValue("Completion change (positive means later)")).toHaveTextContent("4 h");
    expect(within(resultRegion()).getByRole("list", {name: "Simulated sequence"})).toBeVisible();
    expect(api.createAudit).not.toHaveBeenCalled(); expect(api.explainAudit).not.toHaveBeenCalled(); expect(api.askBaseChat).not.toHaveBeenCalled();
    expect(within(resultRegion()).getByText("Simulation only: no workload was started, stopped, validated or recovered.")).not.toBeVisible();
  });
  it("preserves a failure and negative benefit while edits and retries create independent alternatives", async () => {
    const pilots = pilotApi(); render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilots}/>);
    const user = await fill("failure_recovered"); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    await screen.findByRole("heading", {name: "Failed trial — recovery assumed"});
    expect(summaryValue("Net benefit (negative means extra cost)")).toHaveTextContent("-$3.20");
    fireEvent.change(screen.getByLabelText("Proposed change"), {target: {value: "A revised CPU proposal"}});
    expect(screen.getByRole("status")).toHaveTextContent("Pending draft changes");
    expect(within(resultRegion()).getByText("Isolated CPU replacement")).toBeVisible();
    expect(within(resultRegion()).getByText("Output mismatch needs investigation")).toBeVisible();
    await user.selectOptions(screen.getByLabelText("Assumed outcome"), "success");
    fireEvent.change(screen.getByLabelText("Requested CPU trial hours"), {target: {value: "12"}});
    await user.click(screen.getByRole("button", {name: "Simulate revised alternative"}));
    await screen.findByRole("heading", {name: "Successful trial — assumed outcome"});
    expect(summaryValue("Net benefit (negative means extra cost)")).toHaveTextContent("$43.20");
    await user.click(screen.getByRole("button", {name: /Alternative 1/}));
    expect(screen.getByRole("heading", {name: "Failed trial — recovery assumed"})).toBeVisible();
    expect(summaryValue("Net benefit (negative means extra cost)")).toHaveTextContent("-$3.20");
    expect(pilots.simulate).toHaveBeenCalledTimes(2);
    expect(screen.getByText(/A previous failed simulation is not charged again/)).toBeVisible();
  });
  it("shows an unavailable fallback as paused with unknown completion and explicit owner action", async () => {
    render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilotApi()}/>);
    const user = await fill("failure_unavailable"); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    expect(await screen.findByRole("heading", {name: "Paused — owner action required"})).toBeVisible();
    expect(summaryValue("Total cost to complete")).toHaveTextContent("Unknown");
    expect(summaryValue("Net benefit (negative means extra cost)")).toHaveTextContent("Unknown");
    expect(screen.getByText(/Next owner action: confirm the original configuration/)).toBeVisible();
    expect(screen.getByText("Possible causes — unverified hypotheses")).toBeVisible();
    expect(screen.getAllByText("Next check:").length).toBeGreaterThan(0);
  });
  it("displays the server's cap override and never labels a stopped trial successful", async () => {
    const pilots = pilotApi(result => {const failure = simulation("failure_recovered");
      result.status = "recovered"; result.effective_outcome = "failure_recovered"; result.stop_reason = "runtime_limit";
      result.failure_details = {requested_failure_reason: "", effective_failure_reason: "Stopped at the simulated runtime limit", selected_outcome_changed: true};
      result.costs = failure.costs; result.recovery = failure.recovery; result.timeline = failure.timeline;
      result.timing.effective_cpu_hours = 3; result.limits.runtime_limit_reached = true;
    });
    render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilots}/>);
    const user = await fill(); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    await screen.findByRole("heading", {name: "Failed trial — recovery assumed"});
    expect(screen.getByText(/A trial limit overrode your selected success/)).toBeVisible();
    expect(screen.queryByRole("heading", {name: "Successful trial — assumed outcome"})).not.toBeInTheDocument();
    expect(screen.getByText("runtime limit", {exact: true})).toBeVisible();
  });
  it("preserves missing baseline, cost and queue values and visibly marks an unverifiable budget", async () => {
    const pilots = pilotApi(result => {
      result.costs.cpu_trial_cost_usd = null; result.costs.setup_cost_usd = null; result.costs.trial_cost_usd = null;
      result.costs.original_cost_usd = null; result.costs.cost_so_far_usd = null; result.costs.total_cost_to_complete_usd = null; result.costs.net_benefit_usd = null;
      result.timing.completion_change_hours = null; result.timing.extra_queue_hours = null; result.limits.spend_limit_status = "unverified";
    });
    const baselineList = baselines(); Object.assign(baselineList.items[0], {elapsed_hours: null, original_reference_cost_usd: null, missing_fields: ["elapsed_hours"]});
    vi.mocked(pilots.getBaselines).mockResolvedValue(baselineList);
    render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilots}/>);
    const user = await fill("success", true); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    await screen.findByRole("heading", {name: "Successful trial — assumed outcome"});
    expect(pilots.simulate).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({elapsed_hours: null}), expect.objectContaining({cpu_vcpu_hour_usd: null, setup_cost_usd: null, extra_queue_hours: null, baseline_host_costs_included: false}), expect.any(AbortSignal));
    expect(summaryValue("Original job")).toHaveTextContent("Unknown"); expect(summaryValue("Completion change (positive means later)")).toHaveTextContent("Unknown");
    expect(screen.getByText(/Spending limit unverified/)).toBeVisible(); expect(screen.getByText(/Unknown baseline fields: elapsed_hours/)).toBeVisible();
  });
  it("preserves prior results on API failure and allows a real retry without sample fallback", async () => {
    const pilots = pilotApi(); render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilots}/>);
    const user = await fill(); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    await screen.findByRole("heading", {name: "Successful trial — assumed outcome"});
    vi.mocked(pilots.simulate).mockRejectedValueOnce(new ApiError("UPSTREAM_UNAVAILABLE", "Analysis temporarily unavailable", 503, true));
    await user.click(screen.getByRole("button", {name: "Simulate revised alternative"}));
    expect(await screen.findByRole("alert")).toHaveTextContent("Analysis temporarily unavailable");
    expect(screen.getByRole("heading", {name: "Successful trial — assumed outcome"})).toBeVisible();
    expect(screen.queryByRole("button", {name: /Alternative 2/})).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", {name: "Simulate revised alternative"}));
    expect(await screen.findByRole("button", {name: /Alternative 2/})).toBeVisible();
  });
  it("creates a panel-scoped baseline lookup audit with no recovery assumed and no C dependency", async () => {
    const api = dashboard(), pilots = pilotApi(); render(<PilotRecoveryPanel api={api} pilotApi={pilots}/>);
    await screen.findByText("Frozen baseline for this proposal");
    expect(api.createAudit).toHaveBeenCalledWith(expect.objectContaining({expected_data_fingerprint: audit().provenance.data_fingerprint,
      scenario: {recovery_fraction: {low: 0, point: 0, high: 0}, usd_per_gpu_hour: 3.25, cancelled_policy: "exclude", interval_kind: "scenario", assumption_note: "Baseline lookup only; no cohort recovery assumed"}}));
    expect(screen.getByText(/This panel has its own audit/)).toBeVisible(); expect(api.explainAudit).not.toHaveBeenCalled(); expect(api.askBaseChat).not.toHaveBeenCalled();
  });
  it("handles missing A as a panel error and retries the same genuine baseline lookup", async () => {
    const pilots = pilotApi(); vi.mocked(pilots.getBaselines).mockRejectedValueOnce(new ApiError("UPSTREAM_UNAVAILABLE", "Start the analysis service", 503, true));
    render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilots}/>);
    expect(await screen.findByRole("alert")).toHaveTextContent("Start the analysis service");
    expect(screen.getByRole("button", {name: "Simulate this pilot"})).toBeDisabled();
    await userEvent.click(screen.getByRole("button", {name: "Retry baseline lookup"}));
    await screen.findByText("Frozen baseline for this proposal"); expect(pilots.getBaselines).toHaveBeenCalledTimes(2);
  });
  it("ignores an in-flight result after the audit scope changes", async () => {
    let finish!: (value: PilotSimulation) => void;
    const pilots = pilotApi(), api = dashboard(); vi.mocked(pilots.simulate).mockImplementationOnce(() => new Promise(resolve => {finish = resolve;}));
    const screenView = render(<PilotRecoveryPanel api={api} audit={audit()} pilotApi={pilots}/>);
    const user = await fill(); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    const newer = {...audit(), audit_id: "new-scope"};
    screenView.rerender(<PilotRecoveryPanel api={api} audit={newer} pilotApi={pilots}/>);
    finish(simulation()); await waitFor(() => expect(pilots.getBaselines).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("heading", {name: "Successful trial — assumed outcome"})).not.toBeInTheDocument();
    expect(screen.queryByRole("button", {name: /Alternative 1/})).not.toBeInTheDocument();
  });
  it("downloads a separately labeled immutable history, preserving its prior assumptions", async () => {
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const create = vi.spyOn(URL, "createObjectURL");
    render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilotApi()}/>);
    const user = await fill("failure_recovered"); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
    await screen.findByRole("heading", {name: "Failed trial — recovery assumed"});
    fireEvent.change(screen.getByLabelText("Proposed change"), {target: {value: "Unsimulated revision"}});
    await user.click(screen.getByRole("button", {name: "Download simulation history"}));
    const blob = create.mock.calls.at(-1)![0] as Blob;
    const raw = await new Promise<string>(resolve => {const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.readAsText(blob);});
    const exported = JSON.parse(raw);
    expect(exported).toMatchObject({simulation_only: true, execution_performed: false, for_claims: false, independent_alternatives: true,
      draft_not_simulated: {proposal: "Unsimulated revision"}});
    expect(exported.history[0].result.inputs.proposal).toBe("Isolated CPU replacement"); expect(exported.history[0].result.failure_details.effective_failure_reason).toBe("Output mismatch needs investigation");
    expect(click.mock.instances.at(-1)).toHaveProperty("download", "pilot-recovery-simulations.json");
    click.mockRestore(); create.mockRestore();
  });
  it("mounts lazily and retains simulations when navigating away and back", async () => {
    window.history.replaceState(null, "", "#overview");
    const pilots = pilotApi(), api = dashboard();
    const factory = vi.spyOn(pilotRecoveryModule, "createPilotRecoveryApi").mockReturnValue(pilots);
    try {
      render(<App runtime={{mode: "http", api}}/>);
      await screen.findByText("Where the money goes");
      expect(pilots.getBaselines).not.toHaveBeenCalled();
      await act(async () => {window.history.replaceState(null, "", "#pilot-recovery"); window.dispatchEvent(new HashChangeEvent("hashchange"));});
      const user = await fill("failure_recovered"); await user.click(screen.getByRole("button", {name: "Simulate this pilot"}));
      await screen.findByRole("heading", {name: "Failed trial — recovery assumed"});
      await act(async () => {window.history.replaceState(null, "", "#overview"); window.dispatchEvent(new HashChangeEvent("hashchange"));});
      expect(screen.queryByRole("heading", {name: "Failed trial — recovery assumed"})).not.toBeInTheDocument();
      await act(async () => {window.history.replaceState(null, "", "#pilot-recovery"); window.dispatchEvent(new HashChangeEvent("hashchange"));});
      expect(screen.getByRole("heading", {name: "Failed trial — recovery assumed"})).toBeVisible();
      expect(pilots.getBaselines).toHaveBeenCalledTimes(1); expect(pilots.simulate).toHaveBeenCalledTimes(1);
    } finally {factory.mockRestore(); window.history.replaceState(null, "", "#overview");}
  });
  it("exports the selected baseline's source and audit identity before any simulation exists", async () => {
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    const create = vi.spyOn(URL, "createObjectURL");
    try {
      render(<PilotRecoveryPanel api={dashboard()} audit={audit()} pilotApi={pilotApi()}/>);
      await screen.findByText("Frozen baseline for this proposal");
      fireEvent.change(screen.getByLabelText("Proposed change"), {target: {value: "Untested plan to preserve"}});
      await userEvent.click(screen.getByRole("button", {name: "Download simulation history"}));
      const blob = create.mock.calls.at(-1)![0] as Blob;
      const raw = await new Promise<string>(resolve => {const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.readAsText(blob);});
      const saved = JSON.parse(raw), source = baselines();
      expect(saved.history).toEqual([]);
      expect(saved.selected_baseline_scope).toEqual({feature_version: "0.1", audit_id: source.audit_id,
        audit_client_request_id: source.audit_client_request_id, data_fingerprint: source.data_fingerprint,
        source_version: source.source_version, synthetic: true, simulation_only: true});
      expect(saved.selected_baseline).toEqual(source.items[0]);
      expect(saved.draft_not_simulated.proposal).toBe("Untested plan to preserve");
      expect(saved.for_claims).toBe(false); expect(saved.execution_performed).toBe(false);
    } finally {click.mockRestore(); create.mockRestore();}
  });
});
