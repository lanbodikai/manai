"""Exercise actual stdio cancellation and scoped-evidence failure, not a fake client."""
import asyncio
import json
from pathlib import Path
import time
from service.audits import Snapshot
from service.analysis_routes import ServiceError
from service.base_chat.chat import answer_base_chat


def mcp_processes():
    found = set()
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                if b'mcp_layer.server' in (p / 'cmdline').read_bytes(): found.add(p.name)
            except OSError:
                pass
    return found


async def main():
    audit = json.loads(Path('private-eval/analysis/audit.json').read_text())
    # Deliberately omit membership: real tool output must never become a valid citation.
    snapshot = Snapshot(json.dumps(audit), {}, ())
    before = mcp_processes()
    outcomes = []
    for timeout, expected in ((.05, 504), (10, 502)):
        start = time.monotonic()
        try:
            await answer_base_chat(snapshot, {'client_request_id': 'cleanup-check', 'question': 'Why this pilot?'},
                                   lambda: None, Path('private-eval/base-chat'), time_limit=timeout)
            raise AssertionError('Expected explicit MCP failure')
        except ServiceError as exc:
            assert exc.status == expected, (exc.status, exc.code)
            outcomes.append({'status': exc.status, 'code': exc.code, 'elapsed_ms': round((time.monotonic() - start) * 1000)})
        assert not (mcp_processes() - before), 'Leaked MCP subprocess'
    Path('private-eval/analysis/mcp-cleanup.json').write_text(json.dumps(outcomes, indent=2))
    print(json.dumps({'M03_real_transport': 'PASS cancellation and wrong-scope evidence', 'orphan_processes': 0, 'outcomes': outcomes}, indent=2))


if __name__ == '__main__': asyncio.run(main())
