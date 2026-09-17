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
  return request;
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
