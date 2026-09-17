import {act, fireEvent, render, screen, waitFor} from "@testing-library/react";
import {describe, it, expect, vi} from "vitest";
import {ChatPanel} from "../src/components/ChatPanel";
import {createMockApi, initialAudit} from "../src/mock/api";
import type {Explanation} from "../src/api/types";

describe("pilot conversation", () => {
  it("retains earlier replies and retries a failed turn without duplicating the user message", async () => {
    const api=createMockApi({delay:0});
    const audit=await api.createAudit({client_request_id:"test", expected_data_fingerprint:"synthetic-fixture-v1", recommendation_id:"cpu-placement-pilot", scenario:initialAudit.scenario});
    const ask=api.askBaseChat;
    api.askBaseChat=vi.fn().mockImplementationOnce(ask).mockRejectedValueOnce(new Error("Connection lost")).mockImplementation(ask);
    render(<ChatPanel api={api} audit={audit} mock onEvidence={()=>{}}/>);
    fireEvent.click(screen.getByRole("button",{name:"Why this pilot?"}));
    await screen.findByText(/Synthetic example: 30 eligible/);
    const composer=screen.getByLabelText("Base chat question");
    fireEvent.change(composer,{target:{value:"Which jobs are eligible?"}});
    fireEvent.keyDown(composer,{key:"Enter"});
    expect(await screen.findByRole("alert")).toHaveTextContent("Connection lost");
    expect(screen.getAllByText(/Synthetic example: 30 eligible/)).toHaveLength(1);
    fireEvent.click(screen.getByRole("button",{name:"Retry question"}));
    await waitFor(()=>expect(screen.getAllByText(/Synthetic example: 30 eligible/)).toHaveLength(2));
    expect(screen.getAllByText("Which jobs are eligible?",{exact:true})).toHaveLength(1);
  });
  it("discards an in-flight reply after starting a new chat", async () => {
    const api=createMockApi({delay:0});
    const audit=await api.createAudit({client_request_id:"test", expected_data_fingerprint:"synthetic-fixture-v1", recommendation_id:"cpu-placement-pilot", scenario:initialAudit.scenario});
    const ask=api.askBaseChat;
    let finish:()=>void=()=>{};
    api.askBaseChat=(id,request)=>new Promise<Explanation>(resolve=>{
      finish=()=>void ask(id,request).then(resolve);
    });
    render(<ChatPanel api={api} audit={audit} mock onEvidence={()=>{}}/>);
    fireEvent.click(screen.getByRole("button",{name:"Why this pilot?"}));
    fireEvent.click(screen.getByRole("button",{name:"New chat"}));
    await act(async()=>{finish(); await new Promise(resolve=>setTimeout(resolve,30));});
    expect(screen.getByRole("heading",{name:"What would you like to know?"})).toBeVisible();
    expect(screen.queryByText(/Synthetic example: 30 eligible/)).not.toBeInTheDocument();
  });
});
