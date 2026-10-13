#!/usr/bin/env python3
"""Capture fresh native evidence; prose is supplied by the caller's agent."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True, type=Path)
parser.add_argument("--clew", default="clew")
args = parser.parse_args()
repository = Path(__file__).resolve().parents[1]
root = args.root.expanduser().resolve()
if root == repository or repository in root.parents or root in repository.parents:
    parser.error("documentation root must be separate from the source checkout")
if root.exists():
    parser.error("use a new documentation root; existing evidence is never replaced")
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
    if result.returncode and not (arguments[:2] == ["docs", "check"] and value.get("status") == "CHECKED" and not value.get("unresolved")):
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
check = invoke(["docs", "check", "--root", str(root)])
services = check.get("services", {})
if check.get("status") != "CHECKED" or check.get("unresolved") or set(services) != {"places", "forecasts", "dashboard"}:
    raise SystemExit("native capture is incomplete; inspect saved check output")
if any(service.get("revision") != revision for service in services.values()):
    raise SystemExit("native capture revision differs from the selected source checkout")
receipt = {"schema": "clew-weather-fresh-native-capture/1.0", "version": version, "revision": revision, "targetRef": target, "snapshot": check["snapshot"], "status": check["status"], "runtimeMode": capabilities["runtimeMode"], "launcherAuthority": contract["launcherAuthority"], "sourceFallbackAllowed": False, "freshCallerState": True, "sourceCacheImported": False, "modelInvoked": False, "proseAuthored": False, "services": services}
(receipts / "capture.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps(receipt))
