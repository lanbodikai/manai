"""Write a private independent report without introducing a new public API shape."""
import argparse
import asyncio
import json
from pathlib import Path

from reviewer.clients import AnalysisClient, OfficialMCP
from reviewer.settings import Settings
from reviewer.validation import validate_audit


async def run(audit_id):
    settings = Settings.from_env()
    async with asyncio.timeout(settings.timeout_seconds):
        audit, details, coverage = await AnalysisClient(
            settings.analysis_url, max_pages=settings.max_pages,
            max_evidence=settings.max_evidence).load(audit_id)
        context = await OfficialMCP(settings.repo_root, context_mode=settings.mcp_context).inspect()
        result = validate_audit(audit, details, coverage, context)
        result["tool_summary"] = context
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-id", required=True)
    parser.add_argument("--output", required=True, type=Path, help="Private output location; never commit source reports")
    args = parser.parse_args()
    result = asyncio.run(run(args.audit_id))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Private permissions and exclusive creation avoid overwriting an existing report.
    import os
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
