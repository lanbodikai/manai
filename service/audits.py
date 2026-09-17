"""Bounded immutable audit snapshots and scoped evidence pagination."""
from collections import OrderedDict
from dataclasses import dataclass
import base64
import json
import threading
from types import MappingProxyType
import uuid

from analysis.core import build_audit


@dataclass(frozen=True)
class Snapshot:
    audit_json: str
    evidence: object
    refs: tuple

    @property
    def audit(self):
        return json.loads(self.audit_json)


class AuditStore:
    def __init__(self, capacity=128):
        self.capacity = capacity
        self.items = OrderedDict()
        self.lock = threading.Lock()

    def create(self, request, context):
        aid = uuid.uuid4().hex
        audit = build_audit(aid, request, context["cohort"], context["impacts"], context["evidence"], context["provenance"])
        # Evidence strings are immutable and shared across snapshots of this source.
        snapshot = Snapshot(json.dumps(audit, allow_nan=False), context["encoded_evidence"], context["refs"])
        with self.lock:
            self.items[aid] = snapshot
            while len(self.items) > self.capacity:
                self.items.popitem(last=False)
        return snapshot

    def get(self, aid):
        with self.lock:
            return self.items.get(aid)


def freeze_evidence(context):
    context["encoded_evidence"] = MappingProxyType({k: json.dumps(v, allow_nan=False) for k, v in context["evidence"].items()})
    context["refs"] = tuple(json.dumps(v["evidence"]) for v in sorted(context["evidence"].values(), key=lambda d: (d["evidence"]["kind"], d["evidence"]["source_id"])))
    return context


def resolve_evidence(snapshot, aid, eid):
    if eid not in snapshot.evidence:
        raise KeyError(eid)
    return {"audit_id": aid, **json.loads(snapshot.evidence[eid])}


def list_evidence(snapshot, aid, limit=25, cursor=None):
    offset = 0
    if cursor:
        try:
            decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if set(decoded) != {"audit_id", "offset"} or decoded["audit_id"] != aid:
                raise ValueError()
            offset = decoded["offset"]
            if type(offset) is not int or not 0 < offset < len(snapshot.refs):
                raise ValueError()
        except Exception as exc:
            raise ValueError("Invalid audit-scoped cursor") from exc
    end = offset + limit
    next_cursor = None if end >= len(snapshot.refs) else base64.urlsafe_b64encode(json.dumps({"audit_id": aid, "offset": end}).encode()).decode()
    return {"audit_id": aid, "items": [json.loads(r) for r in snapshot.refs[offset:end]],
            "total": len(snapshot.refs), "next_cursor": next_cursor}
