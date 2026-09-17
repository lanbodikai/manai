# Imported upstream provenance

Official repository: https://github.com/MantisGridAI/hackathon-2026-official
Pinned commit: `314cca0bba49e1bb137aa9094d1dac4cdf7e4490`.

`upstream-manifest.json` records each imported source, destination and original Git-blob SHA-256 (canonical LF for text; binaries exact). Both Linux generator binaries were verified against the supplied SHA256SUMS before execution. Changes to imported files must be recorded below; the manifest remains the original reference.

Notices are preserved verbatim in docs/upstream/{LICENSE,ATTRIBUTION.md,PARTICIPANT_AGREEMENT.md}. Copying the agreement does not sign it on anyone's behalf. Official guide copies retain original relative links; use the pinned online source for their original navigation context.

## Team changes

- Text checkout line endings are normalized to LF by .gitattributes; content matches upstream Git blobs.
- Root Compose: preserve official API/data/preparation/generation; make notebook optional; add team analysis service and a temporary bootstrap verification page.
- No official data/API/rule semantics intentionally changed.
- Team service, MCP probe, bootstrap page and tests are original additions. Data remains local and is not part of the image build context.
