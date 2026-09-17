import type { components } from "./generated";
import type { DatasetApi } from "./dataset";
import type { OptimizationApi } from "./optimization";
import type { HardwareApi } from "./hardware";
export type Schemas = components["schemas"];
export type Audit = Schemas["Audit"];
export type Scenario = Schemas["Scenario"];
export type Overview = Schemas["Overview"];
export type EvidenceDetail = Schemas["EvidenceDetail"];
export type Explanation = Schemas["Explanation"];
export type PageInput = { limit?: number; cursor?: string };
export interface DashboardApi {
  /** Separate cpu-hardware-1 simulation; never canonical recovery/claims. */
  hardware?: HardwareApi;
  /** Optional frontend preview capability; not a frozen v0.3 route extension. */
  datasets?: DatasetApi;
  /** Proposed modeled-action interface; not an adopted v0.3/v0.4 extension. */
  optimization?: OptimizationApi;
  getHealth(): Promise<Schemas["Health"]>;
  getOverview(): Promise<Overview>;
  listRecommendations(): Promise<Schemas["Recommendations"]>;
  createAudit(request: Schemas["AuditRequest"]): Promise<Audit>;
  getAudit(auditId: string): Promise<Audit>;
  listEvidence(
    auditId: string,
    page?: PageInput,
  ): Promise<Schemas["EvidencePage"]>;
  getEvidence(auditId: string, evidenceId: string): Promise<EvidenceDetail>;
  askBaseChat(
    auditId: string,
    request: Schemas["ExplanationRequest"],
  ): Promise<Explanation>;
  explainAudit(
    auditId: string,
    request: Schemas["ExplanationRequest"],
  ): Promise<Explanation>;
  exportClaims(auditId: string, team: string): Promise<Schemas["Claims"]>;
}
export interface DemoPresentation {
  baselineUsd: number;
  targetUsd: number;
  gapLow: number;
  gapHigh: number;
  contributionLow: number;
  contributionHigh: number;
}
export interface Runtime {
  api: DashboardApi;
  mode: "mock" | "http" | "local";
  initialScenario?: Scenario;
  demoPresentation?: (overview: Overview, audit: Audit) => DemoPresentation;
}
