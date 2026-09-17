import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { App } from "../src/App";
import { createMockApi, initialAudit, type Fault } from "../src/mock/api";
import type { Runtime } from "../src/api/types";

function runtime(fault: Fault = "none"): Runtime {
  return {
    api: createMockApi({ delay: 0, fault }),
    mode: "mock",
    initialScenario: initialAudit.scenario,
  };
}

describe("CFO journey", () => {
  it("preserves the source overview while unfinished recommendations are unavailable", async () => {
    const rt = runtime();
    rt.initialScenario = undefined;
    rt.api.listRecommendations = async () => {
      throw new Error("Bootstrap recommendations are not implemented.");
    };
    render(<App runtime={rt} />);
    expect(await screen.findByText("Where the money goes")).toBeVisible();
    expect(
      await screen.findByText(/Pilot recommendations are not available yet/),
    ).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "Source data unavailable" }),
    ).not.toBeInTheDocument();
  });
  it("shows mandatory labeling and opens the dollar-to-source path", async () => {
    render(<App runtime={runtime()} />);
    expect(
      screen.getByText("Synthetic demo — no live data or MCP"),
    ).toBeVisible();
    expect(screen.getByText("Loading the spending overview…")).toBeVisible();
    const recovery = await screen.findByRole("button", {
      name: "Inspect recovery value and evidence",
    });
    expect(recovery).toHaveTextContent("$15–$45");
    fireEvent.click(recovery);
    fireEvent.click(
      await screen.findByRole("button", { name: /Synthetic completed job J1/ }),
    );
    expect(await screen.findByText("Source and joins")).toBeVisible();
    expect(screen.getByText("Not source-data-derived.")).toBeVisible();
  });
  it("ignores delayed superseded results and keeps pending inputs separate", async () => {
    const rt = runtime();
    rt.api = createMockApi({
      delay: 0,
      auditDelay: (r) => (r.scenario.recovery_fraction.high === 0.8 ? 120 : 0),
    });
    render(<App runtime={rt} />);
    await screen.findByRole("button", {
      name: "Inspect recovery value and evidence",
    });
    fireEvent.change(screen.getByLabelText("Low recovery (%)"), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByLabelText("High recovery (%)"), {
      target: { value: "80" },
    });
    expect(screen.getByText(/Pending changes/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Model scenario" }));
    fireEvent.change(screen.getByLabelText("Low recovery (%)"), {
      target: { value: "30" },
    });
    fireEvent.change(screen.getByLabelText("High recovery (%)"), {
      target: { value: "90" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Model scenario" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", {
          name: "Inspect recovery value and evidence",
        }),
      ).toHaveTextContent("$22.5–$67.5"),
    );
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 170));
    });
    expect(
      screen.getByRole("button", {
        name: "Inspect recovery value and evidence",
      }),
    ).toHaveTextContent("$22.5–$67.5");
  });
  it("shows validation without clearing an existing calculation", async () => {
    render(<App runtime={runtime()} />);
    await screen.findByRole("button", {
      name: "Inspect recovery value and evidence",
    });
    fireEvent.change(screen.getByLabelText("Low recovery (%)"), {
      target: { value: "99" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Model scenario" }));
    expect(screen.getByRole("alert")).toHaveTextContent("INVALID_SCENARIO");
    expect(
      screen.getByRole("button", {
        name: "Inspect recovery value and evidence",
      }),
    ).toHaveTextContent("$15–$45");
  });
  it.each([
    "reviewer-unavailable",
    "reviewer-timeout",
    "reviewer-malformed",
  ] as const)(
    "keeps base chat and export available after %s",
    async (fault) => {
      render(<App runtime={runtime(fault)} />);
      await screen.findByRole("button", {
        name: "Inspect recovery value and evidence",
      });
      fireEvent.click(screen.getByText("Open optional advanced reviewer"));
      fireEvent.change(screen.getByLabelText("Advanced review question"), {
        target: { value: "Why this pilot?" },
      });
      fireEvent.click(
        screen.getByRole("button", { name: "Ask advanced reviewer" }),
      );
      expect(await screen.findByRole("alert")).toBeVisible();
      fireEvent.click(
        screen.getByRole("button", { name: "What could go wrong?" }),
      );
      expect(
        await screen.findByText(/Synthetic example: 30 eligible/),
      ).toBeVisible();
      expect(
        screen.getByRole("button", { name: "Download synthetic claims" }),
      ).toBeEnabled();
    },
  );
  it.each(["source-unavailable", "not-found"] as const)(
    "shows evidence failure %s without removing the audit",
    async (fault) => {
      render(<App runtime={runtime(fault)} />);
      fireEvent.click(
        await screen.findByRole("button", {
          name: "Inspect recovery value and evidence",
        }),
      );
      fireEvent.click(
        await screen.findByRole("button", {
          name: /Synthetic completed job J1/,
        }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        fault === "not-found" ? "404" : "503",
      );
      fireEvent.click(screen.getByRole("button", { name: "Close evidence" }));
      expect(
        screen.getByRole("button", { name: "Download synthetic claims" }),
      ).toBeEnabled();
    },
  );
  it.each(["conflict", "invalid"] as const)(
    "shows %s creation errors without fabricating a result",
    async (fault) => {
      render(<App runtime={runtime(fault)} />);
      expect(await screen.findByRole("alert")).toHaveTextContent(
        fault === "conflict" ? "409" : "422",
      );
      expect(
        screen.queryByRole("button", { name: "Download synthetic claims" }),
      ).not.toBeInTheDocument();
      expect(screen.getByText("Not modeled")).toBeVisible();
    },
  );
  it("shows empty cohort as zero and downside as unknown", async () => {
    render(<App runtime={runtime("empty")} />);
    expect(
      await screen.findByText("No eligible jobs in this calculation."),
    ).toBeVisible();
    expect(screen.getByText("Not measured")).toBeVisible();
    expect(
      screen.getByRole("button", {
        name: "Inspect recovery value and evidence",
      }),
    ).toHaveTextContent("$0–$0");
  });
});
