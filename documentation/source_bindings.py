"""Rebind declared thread revisions only against exact native retained sources."""
from copy import deepcopy
import hashlib


def rebind_thread(process, expected_spans, retained_sources):
    result = deepcopy(process)
    thread = result.get("process", {}).get("thread")
    if not thread:
        return result, []
    selected = {}

    def source(service, source_id, text_digest):
        key = (service, source_id)
        if key in selected:
            record = selected[key]
            if record["textDigest"] != text_digest:
                raise ValueError("conflicting declared source digest")
            return record
        expected = expected_spans.get(source_id)
        record = retained_sources.get(key)
        if expected is None or record is None:
            raise ValueError("thread source binding is unavailable")
        for field in ("id", "service", "file", "startLine", "endLine", "textDigest"):
            if expected.get(field) != record.get(field):
                raise ValueError("thread source changed; regenerate its declaration")
        if record["service"] != service or record["textDigest"] != text_digest:
            raise ValueError("thread source differs from declared method")
        text = record.get("text")
        if (record.get("authority") != "EXACT_SNAPSHOT_TEXT"
                or not isinstance(text, str)
                or record["textDigest"] != "sha256:" + hashlib.sha256(text.encode()).hexdigest()
                or record["endLine"] - record["startLine"] + 1 != len(text.splitlines())
                or not isinstance(record.get("revision"), str)
                or len(record["revision"]) != 40
                or any(c not in "0123456789abcdef" for c in record["revision"])):
            raise ValueError("native retained source binding is invalid")
        selected[key] = record
        return record

    for method in thread["methods"]:
        source(method["service"], method["sourceId"], method["textDigest"])
    updates = []
    for contract in thread.get("boundaryContracts", []):
        for evidence in contract["evidence"].values():
            record = source(evidence["service"], evidence["sourceId"], evidence["textDigest"])
            if not (record["startLine"] <= evidence["startLine"]
                    <= evidence["endLine"] <= record["endLine"]):
                raise ValueError("contract citation escapes retained source")
            previous = evidence["revision"]
            evidence["revision"] = record["revision"]
            updates.append({"service": record["service"], "sourceId": record["id"],
                            "textDigest": record["textDigest"],
                            "previousRevision": previous, "revision": record["revision"]})
    return result, updates
