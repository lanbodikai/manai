"""Canonical local data validation; no inferred operational savings."""
import hashlib
import json
from pathlib import Path
from scripts.checksum_data import FILES, digest

def file_signature(data: Path):
    return tuple((name, (data/name).stat().st_size, (data/name).stat().st_mtime_ns)
                 for name in [*FILES, "checksums.txt"])

def inspect_data(data: Path):
    try:
        before = file_signature(data)
    except FileNotFoundError:
        return {"status": "missing", "fingerprint": None, "signature": None}
    try:
        expected = {}
        for line in (data/"checksums.txt").read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                sha, name = line.split()
                expected[name] = sha
        actual = {name: digest(data/name) for name in FILES}
        if actual != expected or before != file_signature(data):
            raise ValueError("Canonical data mismatch")
        fingerprint = hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()
        return {"status": "ready", "fingerprint": fingerprint, "signature": before}
    except (OSError, ValueError, KeyError):
        return {"status": "invalid", "fingerprint": None, "signature": None}

def current_status(data, snapshot):
    try:
        signature = file_signature(data)
    except FileNotFoundError:
        return "missing"
    if snapshot["status"] != "ready" or snapshot["signature"] != signature:
        return "invalid"
    return "ready"
