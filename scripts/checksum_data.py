#!/usr/bin/env python3
"""Check that your Track 2 data matches everyone else's.

    python scripts/checksum_data.py              # compare against data/checksums.txt
    python scripts/checksum_data.py --write      # rewrite it from the current data

findings.json is checked by the SHA-256 of the file: it is the same byte for byte
on every machine. The .parquet files are checked by the SHA-256 of the values
inside them, column by column in file order. Their bytes legitimately differ from
machine to machine -- the compression library encodes the same data differently
on Intel and ARM -- so a hash of the file would report a mismatch where there
is none.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

DATA = Path(__file__).resolve().parent.parent / "data"
FILES = ["prepped/jobs.parquet", "prepped/gpus.parquet",
         "synthetic/resources.parquet", "synthetic/edges.parquet",
         "synthetic/findings.json"]
HEADER = """\
# Track 2 data checksums -- check yours with `make check-data` (see README.md).
# findings.json: SHA-256 of the file. The .parquet files: SHA-256 of the values
# inside them (scripts/checksum_data.py), because their bytes differ by machine.
"""


def digest(path: Path) -> str:
    h = hashlib.sha256()
    if path.suffix == ".json":
        h.update(path.read_bytes())
        return h.hexdigest()
    table = pq.read_table(path)
    for name in table.column_names:
        values = table.column(name).to_pylist()
        h.update(json.dumps([name, values], default=str, separators=(",", ":")).encode())
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--expect", type=Path, help="default: <data>/checksums.txt")
    ap.add_argument("--write", action="store_true", help="write the expected values")
    args = ap.parse_args()
    expect = args.expect or args.data / "checksums.txt"

    missing = [f for f in FILES if not (args.data / f).exists()]
    if missing:
        for f in missing:
            print(f"  missing   data/{f}")
        print("\nGenerate the data first -- data/README.md, steps 1 to 3.")
        sys.exit(1)
    got = {f: digest(args.data / f) for f in FILES}

    if args.write:
        expect.write_text(HEADER + "".join(f"{got[f]}  {f}\n" for f in FILES))
        print(f"wrote {expect}")
        return

    want = {}
    for line in expect.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            h, f = line.split()
            want[f] = h
    bad = [f for f in FILES if got[f] != want.get(f)]
    for f in FILES:
        print(f"  {'ok' if f not in bad else 'MISMATCH':9} data/{f}")
    print()
    if not bad:
        print("Your data matches.")
        return
    if any(f.startswith("prepped/") for f in bad):
        print("The prepared tables differ, so everything after them will too. Check that "
              "data/raw/ holds the two files from step 1, then re-run step 2.")
    else:
        print("The prepared tables match but the generated files do not. Make sure you "
              "have the current generator release (step 3) and re-run it.")
    sys.exit(1)


if __name__ == "__main__":
    main()
