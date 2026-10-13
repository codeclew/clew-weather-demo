#!/usr/bin/env python3
"""Capture fresh native evidence; prose is supplied by the caller's agent."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True, type=Path)
parser.add_argument("--clew", default="clew")
parser.add_argument("--include-observations", action="store_true")
parser.add_argument("--include-processes", action="store_true")
args = parser.parse_args()
repository = Path(__file__).resolve().parents[1]
root = args.root.expanduser().resolve()
if root == repository or repository in root.parents or root in repository.parents:
    parser.error("documentation root must be separate from the source checkout")
if root.exists():
    parser.error("use a new documentation root; existing evidence is never replaced")
if not root.parent.is_dir():
    parser.error("documentation root parent must already exist; create it before capture")
launcher = shutil.which(args.clew)
if launcher is None:
    parser.error("installed clew launcher is unavailable")
receipts = root.parent / (root.name + "-capture-receipts")
receipts.mkdir(mode=0o700, exist_ok=False)
environment = os.environ.copy()
environment["CODECLEW_HOME"] = str(receipts / "state")
version = subprocess.check_output([launcher, "--version"], env=environment, text=True).strip()
match = re.fullmatch(r"clew (\d+)\.(\d+)\.(\d+)", version)
if not match or tuple(map(int, match.groups())) < (0, 13, 27):
    parser.error("TypeScript source-syntax capture requires Codeclew 0.13.27 or newer")
process_inputs = []
if args.include_processes:
    process_inputs = [json.loads(p.read_text()) for p in
                      sorted((repository / "documentation/processes").glob("*.json"))]
    if (any(p.get("process", {}).get("thread") for p in process_inputs)
            and tuple(map(int, match.groups())) < (0, 13, 29)):
        parser.error("C# and TypeScript process threads require Codeclew 0.13.29 or newer")
capabilities = json.loads(subprocess.check_output([launcher, "capabilities"], env=environment, text=True))
contract = capabilities.get("agentContract", {})
if (capabilities.get("runtimeMode") != "RELEASE"
        or contract.get("schema") != "codeclew-agent-contract/1.0"
        or contract.get("launcherAuthority") != "INSTALLED_RELEASE"
        or contract.get("sourceFallbackAllowed") is not False):
    parser.error("use an installed public release")
target = subprocess.check_output(["git", "symbolic-ref", "--short", "HEAD"], cwd=repository, text=True).strip()
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
sequence = 0

def invoke(arguments):
    global sequence
    sequence += 1
    result = subprocess.run([launcher, *arguments], cwd=repository, env=environment, capture_output=True)
    prefix = receipts / f"{sequence:02d}"
    prefix.with_suffix(".stdout.json").write_bytes(result.stdout)
    prefix.with_suffix(".stderr.log").write_bytes(result.stderr)
    value = json.loads(result.stdout)
    saved_check = arguments[:2] in (["docs", "check"], ["docs", "recompose"])
    if result.returncode and not (saved_check and result.returncode in (3, 4) and value.get("status") == "CHECKED" and not value.get("unresolved")):
        raise SystemExit(f"native command failed ({result.returncode}); inspect {prefix}.stdout.json")
    return value

invoke(["docs", "init", "--root", str(root), "--title", "Weather"])
for service in ("places", "forecasts", "dashboard"):
    config = json.loads((repository / "documentation/services" / f"{service}.json").read_text())
    config["targetRef"] = target
    input_path = receipts / f"{service}-service.json"
    input_path.write_text(json.dumps(config, indent=2) + "\n")
    digest = invoke(["docs", "service", "list", "--root", str(root)])["inputDigest"]
    invoke(["docs", "service", "add", "--root", str(root), "--input", str(input_path), "--expected-input-digest", digest])
    invoke(["docs", "bind", "--root", str(root), "--service", service, "--repo", str(repository)])
if args.include_observations:
    for name, service in (("validator-node24", "dashboard"), ("kafka-replay", "dashboard"), ("broker-outage", "places")):
        source = repository / "documentation/observations" / (name + ".json")
        contents = source.read_bytes()
        observation = json.loads(contents)
        if (observation.get("schema") != "clew-weather-runtime-observation/1.0"
                or observation.get("compilerEvidence") is not False):
            raise SystemExit("invalid imported runtime observation")
        association = {
            "schema": "codeclew-documentation-note-association/1.0",
            "id": "runtime-" + name,
            "title": source.name,
            "service": service,
            "path": "notes/runtime-" + name + ".md",
            "targets": ["service:" + service + "/section-overview"],
            "classification": "mixed",
            "period": observation.get("startedAt", observation.get("nodeVersion", "historical")),
            "tags": ["imported-context"],
            "metadata": {"sourceSha256": hashlib.sha256(contents).hexdigest(), "compilerEvidence": False}
        }
        input_path = receipts / (name + "-association.json")
        input_path.write_text(json.dumps(association, indent=2) + "\n")
        digest = invoke(["docs", "service", "list", "--root", str(root)])["inputDigest"]
        invoke(["docs", "note", "import", "--root", str(root), "--input", str(input_path),
                "--source", str(source), "--expected-input-digest", digest])
declarations = {"interaction": [], "process": []}
original_capture = None
retained_sources = {}
source_binding_updates = []
if args.include_processes:
    threaded = [p for p in process_inputs if p.get("process", {}).get("thread")]
    if threaded:
        bindings = json.loads((repository / "documentation/source-spans.json").read_text())
        if bindings.get("schema") != "clew-weather-source-spans/1.0":
            raise SystemExit("invalid portable source span bindings")
        expected_spans = bindings["sources"]
        needed = {}
        for process in threaded:
            thread = process["process"]["thread"]
            for method in thread["methods"]:
                needed.setdefault(method["service"], set()).add(method["sourceId"])
            for contract in thread.get("boundaryContracts", []):
                for evidence in contract["evidence"].values():
                    needed.setdefault(evidence["service"], set()).add(evidence["sourceId"])
        original_capture = invoke(["docs", "check", "--root", str(root)])
        if (original_capture.get("status") != "CHECKED" or original_capture.get("unresolved")
                or set(original_capture.get("services", {})) != {"places", "forecasts", "dashboard"}
                or any(s.get("revision") != revision for s in original_capture["services"].values())):
            raise SystemExit("fresh source capture is incomplete")
        for service, source_ids in sorted(needed.items()):
            ordered = sorted(source_ids)
            for offset in range(0, len(ordered), 8):
                command = ["docs", "context", "--root", str(root), "--snapshot", original_capture["snapshot"],
                           "--service", service]
                for source_id in ordered[offset:offset + 8]:
                    command.extend(["--source", source_id])
                context = invoke(command)
                if context.get("nextCursor") or context.get("omitted"):
                    raise SystemExit("thread source context is incomplete")
                for item in context["items"]:
                    if item["kind"] == "SOURCE":
                        record = item["record"]
                        if record["revision"] != revision:
                            raise SystemExit("thread source revision differs from fresh capture")
                        retained_sources[(record["service"], record["id"])] = record
        spec = importlib.util.spec_from_file_location("source_bindings", Path(__file__).with_name("source_bindings.py"))
        source_bindings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(source_bindings)
    for kind, directory, schema in (
        ("interaction", "interactions", "codeclew-documentation-interaction/1.0"),
        ("process", "processes", "codeclew-documentation-process/1.0"),
    ):
        for source in sorted((repository / "documentation" / directory).glob("*.json")):
            contents = source.read_bytes()
            declaration = json.loads(contents)
            if declaration.get("schema") != schema or declaration.get("id") != source.stem:
                raise SystemExit("invalid portable process declaration")
            effective_source = source
            if kind == "process" and declaration.get("process", {}).get("thread"):
                declaration, updates = source_bindings.rebind_thread(declaration, expected_spans, retained_sources)
                effective_source = receipts / (source.stem + "-source-bound.json")
                effective_source.write_text(json.dumps(declaration, indent=2) + "\n")
                source_binding_updates.extend(updates)
            digest = invoke(["docs", "service", "list", "--root", str(root)])["inputDigest"]
            invoke(["docs", kind, "put", "--root", str(root), "--input", str(effective_source),
                    "--expected-input-digest", digest])
            declaration_receipt = {"id": declaration["id"],
                                   "sha256": hashlib.sha256(contents).hexdigest()}
            if effective_source != source:
                declaration_receipt["effectiveSha256"] = hashlib.sha256(effective_source.read_bytes()).hexdigest()
            declarations[kind].append(declaration_receipt)
check = invoke(["docs", "recompose", "--root", str(root), "--snapshot", original_capture["snapshot"]]
               if original_capture else ["docs", "check", "--root", str(root)])
services = check.get("services", {})
if check.get("status") != "CHECKED" or check.get("unresolved") or set(services) != {"places", "forecasts", "dashboard"}:
    raise SystemExit("native capture is incomplete; inspect saved check output")
if any(service.get("revision") != revision for service in services.values()):
    raise SystemExit("native capture revision differs from the selected source checkout")
receipt = {"schema": "clew-weather-fresh-native-capture/1.0", "version": version, "revision": revision, "targetRef": target, "snapshot": check["snapshot"], "status": check["status"], "runtimeMode": capabilities["runtimeMode"], "launcherAuthority": contract["launcherAuthority"], "sourceFallbackAllowed": False, "freshCallerState": True, "sourceCacheImported": False, "modelInvoked": False, "proseAuthored": False, "services": services}
receipt["stateDirectory"] = environment["CODECLEW_HOME"]
receipt["historicalRuntimeObservationsImported"] = args.include_observations
receipt["portableProcessDeclarationsImported"] = args.include_processes
if args.include_processes:
    receipt["declarations"] = declarations
    receipt["interactionAuthority"] = "AGENT_PROPOSAL_NOT_RUNTIME_VERIFIED"
if original_capture:
    receipt["sourceCaptureSnapshot"] = original_capture["snapshot"]
    receipt["threadSourceRevisionBindings"] = source_binding_updates
    receipt["threadBindingAuthority"] = "EXACT_RETAINED_SOURCE_MATCH_NOT_NATIVE_THREAD_ADMISSION"
if args.include_observations:
    receipt["observationAuthority"] = "HUMAN_OR_IMPORTED_UNVERIFIED"
    receipt["observationCompilerEvidence"] = False
(receipts / "capture.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
