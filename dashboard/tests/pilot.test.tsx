import {describe,it,expect} from "vitest";
import {render,screen,within} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {modelPilot,initialPilotInputs,type PilotInputs} from "../src/pilot-model";
import {CpuPilotPlanner} from "../src/components/CpuPilotPlanner";
const source={version:"original-synthetic",synthetic:true,cohortHours:100,totalHours:1000,gpuPrice:2.5};
const inputs:PilotInputs={pilotPercent:"10",cpuPrice:"0.1",cpuLow:"10",cpuPoint:"20",cpuHigh:"30",recoveryLow:"0",recoveryPoint:"50",recoveryHigh:"100",implementation:"2",retryReserve:"1",worstSlowdown:"50",maxSlowdown:"25",maxSpend:"5",basis:"Original synthetic cost assumptions for test."};
describe("bounded CPU pilot planning",() => {
  it("preserves negative benefit, charges replacement costs, and compares one pilot to the same-window target",() => {
    const r=modelPilot(source,inputs);
    expect(r.pilotHours).toBe(10);expect(r.baseline).toBe(25);
    expect(r.scenarios.map(s => s.net)).toEqual([-6,7.5,21]);
    expect(r.scenarios.map(s => s.afterCost)).toEqual([31,17.5,4]);
    expect(r.target).toBe(500);expect(r.gap).toBe(492.5);expect(r.targetProgress).toBe(1.5);
    expect(r.extraSpend).toBe(6);expect(r.breakEvenCpuHours).toBe(95);
    expect(r.spendBreached).toBe(true);expect(r.slowdownBreached).toBe(true);
  });
  it("does not call a loss target progress and handles zero CPU prices",() => {
    const loss=modelPilot(source,{...inputs,implementation:"100"});
    expect(loss.contribution).toBe(0);expect(loss.gap).toBe(500);expect(loss.breakEvenPossible).toBe(false);
    expect(modelPilot(source,{...inputs,cpuPrice:"0"}).breakEvenCpuHours).toBeNull();
  });
  it("rejects unknown costs, inverted scenarios, empty cohorts, invalid scope and overflowing values",() => {
    expect(() => modelPilot(source,initialPilotInputs)).toThrow();
    for(const bad of [{cpuPrice:""},{cpuHigh:"1"},{recoveryPoint:"101"},{pilotPercent:"0"},{pilotPercent:"101"},{basis:" "},{implementation:"-1"},{cpuPrice:"Infinity"},{cpuPrice:"1e308"},{cpuPrice:"1e-320"}]) expect(() => modelPilot(source,{...inputs,...bad})).toThrow();
    expect(() => modelPilot({...source,cohortHours:0},inputs)).toThrow();
    expect(() => modelPilot({...source,totalHours:50},inputs)).toThrow();
  });
  it("keeps last calculated results separate from edited assumptions and shows breached safeguards",async () => {
    const user=userEvent.setup();render(<CpuPilotPlanner source={source}/>);
    await user.click(screen.getByRole("button",{name:"Compare pilot scenarios"}));
    expect(screen.getByRole("alert")).toHaveTextContent("Complete every numeric assumption");
    for(const [label,value] of [["Pilot size (% of eligible GPU-hours)","10"],["CPU price ($/core-hour)","0.1"],["CPU core-hours — low","10"],["CPU core-hours — base","20"],["CPU core-hours — high","30"],["Implementation cost ($)","2"],["Extra retry / rollback reserve ($)","1"],["Worst modeled slowdown (%)","50"],["Maximum extra pilot spend ($)","5"],["Assumption source / evidence","Synthetic test assumptions"]]) {
      const field=screen.getByLabelText(label,{exact:true});await user.clear(field);await user.type(field,value);
    }
    await user.click(screen.getByRole("button",{name:"Compare pilot scenarios"}));
    expect(screen.getByRole("heading",{name:"Revise this pilot before approval"})).toBeVisible();
    const results=screen.getByRole("region",{name:"Calculated pilot result"});
    expect(within(results).getByText("-$6–$21")).toBeVisible();
    expect(within(results).getByText("Unpriced downside")).toBeVisible();
    await user.clear(screen.getByLabelText("Implementation cost ($)"));
    expect(screen.getByRole("status")).toHaveTextContent("Unsaved assumptions");
    expect(within(results).getByText("-$6–$21")).toBeVisible();
    await user.click(screen.getByRole("button",{name:"Compare pilot scenarios"}));
    expect(screen.getByRole("alert")).toBeVisible();
    expect(within(results).getByText("-$6–$21")).toBeVisible();
  });
});
