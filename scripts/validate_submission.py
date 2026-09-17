#!/usr/bin/env python3
"""Check a Track 2 submission before it is submitted.

A submission that does not run cannot be judged, and judging day is the wrong
place to find that out. Run this first.

Usage:
    python scripts/validate_submission.py --claims claims.json
    python scripts/validate_submission.py --claims claims.json --url http://localhost:3000
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import jsonschema

SCHEMA = Path(__file__).resolve().parent.parent / "starter" / "claims.schema.json"

# Top-level fields of claims.json that are not claims.
NOT_CLAIMS = {"team", "notes", "_comment"}

ok, warn, err = [], [], []


def check_claims(path: Path) -> dict | None:
    if not path.exists():
        err.append(f"{path} not found -- claims.json is required")
        return None
    try:
        claims = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        err.append(f"{path} is not valid JSON: {e}")
        return None
    ok.append(f"{path.name} parses")

    schema = json.loads(SCHEMA.read_text())
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(claims),
                    key=lambda e: list(e.path))
    if errors:
        for e in errors[:8]:
            loc = "/".join(str(p) for p in e.path) or "(root)"
            err.append(f"schema: {loc}: {e.message}")
        return claims
    ok.append("validates against claims.schema.json")

    r = claims.get("recoverable_gpu_hours") or {}
    if isinstance(r, dict):
        if r.get("low") is None or r.get("high") is None:
            warn.append("recoverable_gpu_hours has no interval -- calibration is 25% of "
                        "the grade and a bare point estimate cannot score above 2 there")
        if not r.get("basis"):
            warn.append("recoverable_gpu_hours has no 'basis' -- judges read it, and this "
                        "claim is scored on reasoning rather than on the number")

    fields = [k for k in json.loads(SCHEMA.read_text()).get("properties", {})
              if k not in NOT_CLAIMS and not k.endswith(("_confidence", "_rationale",
                                                        "_reasoning"))]
    answered = [f for f in fields if f in claims]
    ok.append(f"{len(answered)}/{len(fields)} claims answered -- leaving out one you "
              f"did not investigate is fine")
    if not answered:
        warn.append("no claims answered at all -- claims.json is how most of the "
                    "calibration score is earned")

    stated = [k for k in claims if k.endswith("_confidence")]
    if not stated:
        warn.append("no confidence stated anywhere -- calibration cannot be scored at all")
    if not claims.get("team"):
        warn.append("no 'team' field -- name yourselves so we can attribute the score")
    return claims


def check_dashboard(url: str) -> None:
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            if 200 <= r.status < 400:
                ok.append(f"dashboard responded {r.status} at {url}")
            else:
                err.append(f"dashboard returned {r.status} at {url}")
    except (urllib.error.URLError, OSError) as e:
        err.append(f"dashboard unreachable at {url}: {e}. "
                   f"It must come up with one command and stay up.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", type=Path, default=Path("claims.json"))
    ap.add_argument("--url", help="dashboard URL to probe, e.g. http://localhost:3000")
    args = ap.parse_args()

    check_claims(args.claims)
    if args.url:
        check_dashboard(args.url)
    else:
        warn.append("no --url given, so the dashboard was not checked. Bring it up and "
                    "re-run with --url before you submit.")

    for m in ok:
        print(f"  ok    {m}")
    for m in warn:
        print(f"  warn  {m}")
    for m in err:
        print(f"  FAIL  {m}")

    print()
    if err:
        print(f"{len(err)} problem(s) must be fixed before submitting.")
        sys.exit(1)
    print("Submission looks structurally sound."
          + (f" {len(warn)} warning(s) worth reading." if warn else ""))


if __name__ == "__main__":
    main()
