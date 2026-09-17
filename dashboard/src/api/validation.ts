import Ajv2020 from "ajv/dist/2020";
import contract from "../../../contracts/openapi.json";
import type { Schemas } from "./types";

const ajv = new Ajv2020({ allErrors: true, strict: false, strictNumbers: true });
ajv.addSchema({ $id: "manai-contract", components: contract.components });
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status = 0,
    public retryable = false,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export function parse<K extends keyof Schemas>(
  name: K,
  value: unknown,
): Schemas[K] {
  const validate = ajv.getSchema(`manai-contract#/components/schemas/${name}`)!;
  if (!validate(value))
    throw new ApiError(
      "UPSTREAM_RESPONSE_INVALID",
      `Invalid ${name} payload: ${ajv.errorsText(validate.errors)}`,
      502,
    );
  return value as Schemas[K];
}
export function validateAuditRequest(value: unknown) {
  let request: Schemas["AuditRequest"];
  try {
    request = parse("AuditRequest", value);
  } catch {
    throw new ApiError(
      "INVALID_SCENARIO",
      "Enter valid recovery percentages, a positive price, and an assumption note.",
      422,
    );
  }
  const { low, point, high } = request.scenario.recovery_fraction;
  if (!(low <= point && point <= high))
    throw new ApiError(
      "INVALID_SCENARIO",
      "Recovery must be ordered: low ≤ point ≤ high.",
      422,
    );
  const pilot = request.scenario.cpu_pilot;
  if (pilot && (pilot.mode === "replacement_success" && pilot.cpu_hours <= 0 ||
      pilot.trial_cap_hours != null && pilot.cpu_hours > pilot.trial_cap_hours))
    throw new ApiError("INVALID_SCENARIO", "Successful replacement needs positive CPU duration; duration must not exceed the assumed cap.", 422);
  return request;
}

/**
 * v0.4 is deliberately not wire-compatible with v0.3.  Keep this check close
 * to the parser so a stale service is reported as a connection issue instead
 * of being rendered as partial data.
 */
export function assertV04<T extends { contract_version: string }>(value: T): T {
  if (value.contract_version !== "0.4")
    throw new ApiError(
      "UNSUPPORTED_CONTRACT_VERSION",
      `This dashboard requires API v0.4; received v${value.contract_version}.`,
      426,
      true,
    );
  return value;
}
export function assertAuditId<T extends { audit_id: string }>(
  value: T,
  id: string,
): T {
  if (value.audit_id !== id)
    throw new ApiError(
      "AUDIT_ID_MISMATCH",
      "The response belongs to another calculation. Please retry.",
      502,
    );
  return value;
}
export function assertRequestId<T extends { client_request_id: string }>(
  value: T,
  id: string,
): T {
  if (value.client_request_id !== id)
    throw new ApiError(
      "REQUEST_ID_MISMATCH",
      "The response does not match your request.",
      502,
    );
  return value;
}
export const errorMessage = (error: unknown) =>
  error instanceof ApiError
    ? `${error.status || "Network"} · ${error.code}: ${error.message}`
    : error instanceof Error
      ? error.message
      : "The request could not be completed.";
