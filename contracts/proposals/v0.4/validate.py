"""Validate the proposed contract and original fixtures, not a service implementation."""
import copy
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    spec = read(HERE / "openapi.json")
    active = read(ROOT / "contracts/openapi.json")
    require(active["info"]["version"] in {"0.3.0", "0.4.0"}, "Unexpected active version")
    if active["info"]["version"] == "0.4.0":
        require(active == spec, "Adopted contract differs from agreed v0.4 proposal")
    require(spec["info"]["version"] == "0.4.0", "Proposal version missing")

    def validator(name):
        return Draft202012Validator({"$ref": "#/components/schemas/" + name,
                                     "components": spec["components"]})

    for schema in spec["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)
    # Resolve every local reference, not just those reached by happy-path fixtures.
    def refs(value):
        if isinstance(value, dict):
            if "$ref" in value:
                target = spec
                for part in value["$ref"].removeprefix("#/").split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
            for child in value.values():
                refs(child)
        elif isinstance(value, list):
            for child in value:
                refs(child)
    refs(spec)
    examples = HERE / "examples"
    manifest = read(examples / "manifest.json")
    for filename, name in manifest.items():
        validator(name).validate(read(examples / filename))

    cases = read(examples / "pilot-cases.json")
    for case in cases:
        i, r, price = case["input"], case["result"], case["gpu_hour_usd"]
        validator("CpuPilotInput").validate(i)
        validator("CpuPilotResult").validate(r)
        require(i["mode"] == r["mode"], case["name"] + ": wrong mode")
        require(i["baseline_evidence_id"] == r["baseline"]["evidence_id"], "Wrong evidence")
        h, t = r["baseline"]["recorded_gpu_hours"], r["baseline"]["elapsed_hours"]
        released = h if i["mode"] == "replacement_success" else 0
        cpu = i["cpu_vcpus"] * i["cpu_hours"]
        cost = None if i["cpu_vcpu_hour_usd"] is None else cpu * i["cpu_vcpu_hour_usd"]
        net = None if cost is None or not i["baseline_host_costs_included"] else released * price - cost
        runtime = {"replacement_success": i["cpu_hours"] - t,
                   "replacement_failure": i["cpu_hours"], "additional_validation": None}[i["mode"]]
        total = None if runtime is None or i["extra_queue_hours"] is None else runtime + i["extra_queue_hours"]
        expected = dict(released_gpu_hours=released, scenario_gpu_hours=h-released,
                        added_cpu_vcpu_hours=cpu, released_gpu_reference_usd=released*price,
                        added_cpu_reference_usd=cost, net_reference_value_usd=net,
                        run_time_change_hours_excluding_queue=runtime,
                        completion_change_hours_including_extra_queue=total)
        for key, value in expected.items():
            require(r[key] is None if value is None else r[key] is not None and
                    math.isclose(r[key], value, rel_tol=0, abs_tol=1e-9), case["name"] + ": " + key)
        require(i["trial_cap_hours"] is None or i["cpu_hours"] <= i["trial_cap_hours"], "Invalid cap fixture")

    for key, value in [("cpu_vcpus", True), ("cpu_vcpus", 1.5), ("cpu_hours", -1),
                       ("cpu_hours", 0), ("extra_queue_hours", -1), ("mode", "unknown")]:
        invalid = copy.deepcopy(cases[0]["input"])
        invalid[key] = value
        require(not validator("CpuPilotInput").is_valid(invalid), "Invalid input accepted: " + key)
    invalid = copy.deepcopy(cases[0]["result"])
    invalid["compatibility_verified"] = True
    require(not validator("CpuPilotResult").is_valid(invalid), "Scenario certifies compatibility")

    audit = read(examples / "audit-response.json")
    request = read(examples / "audit-request.json")
    evidence = read(examples / "baseline-evidence.json")
    explanation = read(examples / "explanation-response.json")
    require(request["scenario"] == audit["scenario"], "Scenario echo differs")
    require(request["client_request_id"] == audit["client_request_id"], "Request identity differs")
    require(audit["audit_id"] == evidence["audit_id"] == explanation["audit_id"], "Audit identity differs")
    require(evidence["evidence"]["id"] == audit["downside"]["cpu_pilot"]["baseline"]["evidence_id"], "Baseline differs")
    require(set(explanation["supporting_evidence_ids"]) <= {e["id"] for e in audit["evidence_preview"]}, "Invalid citation")
    observations = {o["column"]: o["value"] for o in evidence["observations"]}
    baseline = audit["downside"]["cpu_pilot"]["baseline"]
    require(observations["gpu_hours"] == baseline["recorded_gpu_hours"] and
            observations["walltime_sec"] / 3600 == baseline["elapsed_hours"] and
            observations["gpu_count"] == baseline["gpu_count"], "Evidence measurement mismatch")
    partition = audit["eligibility"]["memory_partition"]
    groups = [partition[k] for k in ("zero_memory", "positive_memory", "unknown_memory")]
    require(sum(g["unique_jobs"] for g in groups) == audit["eligibility"]["unique_jobs"], "Partition counts differ")
    require(sum(g["recorded_gpu_hours"] for g in groups) == audit["eligibility"]["eligible_gpu_hours"], "Partition hours differ")
    old_audit = read(ROOT / "contracts/examples/audit-response.json")
    require(audit["recovery"] == old_audit["recovery"], "Pilot changed cohort recovery")
    claims = read(examples / "claims-response.json")
    require(claims == read(ROOT / "contracts/examples/claims-response.json"), "Pilot changed claims")
    Draft202012Validator(read(ROOT / "starter/claims.schema.json")).validate(claims)
    require(spec["components"]["schemas"]["Claims"] == active["components"]["schemas"]["Claims"], "Claims schema changed")
    require(spec["components"]["schemas"]["Explanation"] == active["components"]["schemas"]["Explanation"], "Explanation schema changed")
    print(f"PASS: proposed schema/references; {len(manifest)} full fixtures; {len(cases)} pilot cases; invalid inputs; identity; partition; official claims")
    print("C01 proposal checks only. Service, UI, MCP and operational-effect checks NOT RUN.")


if __name__ == "__main__":
    main()
