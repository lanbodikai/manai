import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { buildDecisionTable } from "../tools/decision-summary";
import { demoDecisionJobs, demoDecisionFindings } from "../src/mock/optimization";
import { createMockApi } from "../src/mock/api";
import { createOptimizationHttpApi, decisionPayload, receiptPayload, type OptimizeRequest, type DecisionTable } from "../src/api/optimization";
import { CostOptimization } from "../src/components/CostOptimization";

const sample = (ids: string[] = []) => buildDecisionTable(demoDecisionJobs,demoDecisionFindings,"test-version",ids,true);
const request: OptimizeRequest = {contract_version:"optimization-preview-1",client_request_id:"original-request",expected_dataset_version:"test-version",mode:"model_only",cancelled_policy:"exclude",fix_ids:["cpu-placement"]};
const receipt = {contract_version:"optimization-preview-1",client_request_id:request.client_request_id,dataset_version:request.expected_dataset_version,mode:"model_only",fix_ids:request.fix_ids,optimization_id:"server-model-1",status:"accepted",synthetic:false};
const json = (body: unknown,status=200) => new Response(JSON.stringify(body),{status,headers:{"Content-Type":"application/json"}});

describe("decision accounting", () => {
  it("uses source job hours, excludes cancelled/synthetic matches and deduplicates across fixes", () => {
    const table = sample(["cpu-placement","idle-sessions","timeouts"]);
    expect(table.total_gpu_hours).toBe(100);
    expect(table.rows.find(r => r.id === "idle-sessions")).toMatchObject({allocated_share_pct:10,affected_jobs:1,excluded_cancelled_jobs:1});
    expect(table.selection).toMatchObject({gpu_hours:30,share_pct:30,unique_jobs:2,overlapping_gpu_hours:10});
    const duplicated = buildDecisionTable(demoDecisionJobs,[...demoDecisionFindings,demoDecisionFindings[0],{...demoDecisionFindings[0],synthetic:1}],"test-version",["cpu-placement"]);
    expect(duplicated.selection.gpu_hours).toBe(10);
    expect(duplicated.excluded_synthetic_findings).toBe(2);
  });
  it("fails closed on unresolved jobs, invalid accounting and a false CPU cohort", () => {
    expect(() => buildDecisionTable(demoDecisionJobs,[{...demoDecisionFindings[0],job_id:"missing"}],"v",[])).toThrow();
    expect(() => buildDecisionTable([...demoDecisionJobs,demoDecisionJobs[0]],[],"v",[])).toThrow();
    expect(() => buildDecisionTable([{...demoDecisionJobs[0],gpu_hours:Infinity}],[],"v",[])).toThrow();
    expect(() => buildDecisionTable([{...demoDecisionJobs[0],sm_max:2}], [demoDecisionFindings[0]],"v",[])).toThrow();
  });
  it("reports zero exposure for an empty source, without nonfinite percentages", () => {
    const table = buildDecisionTable([],[],"v",[]);
    expect(table.rows.every(r => r.allocated_share_pct === 0)).toBe(true);
    expect(decisionPayload(table,"v",[]).selection.share_pct).toBe(0);
  });
  it("rejects stale identity, invalid percentages and fabricated selection unions", () => {
    expect(() => decisionPayload(sample(),"other",[])).toThrow();
    const table = sample(["cpu-placement"]);
    expect(() => decisionPayload(table,"test-version",["timeouts"])).toThrow();
    expect(() => decisionPayload({...table,total_gpu_hours:NaN},"test-version",["cpu-placement"])).toThrow();
    table.selection.gpu_hours=0; table.selection.share_pct=0; table.selection.overlapping_gpu_hours=10;
    expect(() => decisionPayload(table,"test-version",["cpu-placement"])).toThrow();
  });
});
describe("backend optimization adapter", () => {
  it("posts only explicit modeling inputs and validates the matching backend receipt", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(json(receipt));
    const result = await createOptimizationHttpApi({fetcher}).submit(request);
    expect(result.optimization_id).toBe("server-model-1");
    expect(fetcher).toHaveBeenCalledWith("/api/optimizations",expect.objectContaining({method:"POST",body:JSON.stringify(request)}));
  });
  it.each([404,409,422,503])("preserves HTTP %i as a visible failure without fallback", async status => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(json({error:"unavailable"},status));
    await expect(createOptimizationHttpApi({fetcher}).submit(request)).rejects.toMatchObject({status});
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("rejects wrong selection/version, unexpected success and synthetic live receipts", async () => {
    for (const invalid of [{...receipt,fix_ids:["timeouts"]},{...receipt,dataset_version:"stale"},{...receipt,status:"completed"}])
      expect(() => receiptPayload(invalid,request)).toThrow();
    await expect(createOptimizationHttpApi({fetcher:vi.fn<typeof fetch>().mockResolvedValue(json({...receipt,synthetic:true}))}).submit(request)).rejects.toMatchObject({code:"SYNTHETIC_OPTIMIZATION_REJECTED"});
  });
  it("rejects empty selection and bounds a backend that never responds", async () => {
    const fetcher = vi.fn<typeof fetch>().mockImplementation(() => new Promise(() => {}));
    const api = createOptimizationHttpApi({fetcher,timeoutMs:10});
    await expect(api.submit({...request,fix_ids:[]})).rejects.toMatchObject({status:422});
    expect(fetcher).not.toHaveBeenCalled();
    await expect(api.submit(request)).rejects.toMatchObject({status:504,code:"OPTIMIZATION_TIMEOUT"});
  });
});
describe("decision table interactions", () => {
  it("selects fixes, shows a deduplicated percentage, and preserves selection after a backend error", async () => {
    const user=userEvent.setup(), api=createMockApi({delay:0});
    const original=api.optimization!.submit;
    const submit=vi.fn().mockRejectedValueOnce(new Error("Backend unavailable")).mockImplementation(original);
    api.optimization!.submit=submit;
    render(<CostOptimization api={api} />);
    await screen.findByRole("checkbox",{name:"Select CPU placement pilot"});
    expect(screen.getByRole("button",{name:"Model selected changes"})).toBeDisabled();
    await user.click(screen.getByRole("checkbox",{name:"Select CPU placement pilot"}));
    await user.click(screen.getByRole("checkbox",{name:"Select Idle interactive sessions"}));
    await waitFor(() => expect(within(screen.getByRole("region",{name:"Optimization context"})).getByText("5.0%")).toBeVisible());
    await user.click(screen.getByRole("button",{name:"Model selected changes"}));
    expect(await screen.findByRole("alert")).toHaveTextContent("Backend unavailable");
    expect(screen.getByRole("checkbox",{name:"Select CPU placement pilot"})).toBeChecked();
    await user.click(screen.getByRole("button",{name:"Retry optimization request"}));
    await screen.findByText("Synthetic example — request accepted");
    expect(submit.mock.calls[0][0]).toEqual(submit.mock.calls[1][0]);
    expect(submit.mock.calls[0][0].fix_ids).toEqual(["cpu-placement","idle-sessions"]);
    expect(screen.getByText("Not modeled")).toBeVisible();
  });
  it("ignores an earlier selection summary arriving after the current summary", async () => {
    const user=userEvent.setup(), api=createMockApi({delay:0}), original=api.optimization!.decisions;
    let late: (value: DecisionTable) => void = () => {};
    api.optimization!.decisions=vi.fn((version:string,selected:string[]) => selected.length === 1 ? new Promise<DecisionTable>(resolve => {late=resolve;}) : original(version,selected));
    render(<CostOptimization api={api} />);
    await user.click(await screen.findByRole("checkbox",{name:"Select CPU placement pilot"}));
    await user.click(screen.getByRole("checkbox",{name:"Select Idle interactive sessions"}));
    await waitFor(() => expect(screen.getByRole("button",{name:"Model selected changes"})).toBeEnabled());
    late(await original("demo-dataset-v1",["cpu-placement"]));
    await waitFor(() => expect(screen.getByRole("button",{name:"Model selected changes"})).toBeEnabled());
    expect(screen.getByRole("heading",{name:"2 fixes selected"})).toBeVisible();
  });
});

