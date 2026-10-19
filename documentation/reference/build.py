#!/usr/bin/env python3
"""Regenerate the reference reader from an explicit retained documentation root."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('verify_reference', HERE / 'verify.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--clew', default='clew')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--generator-commit', required=True)
    parser.add_argument('--source-checkout', type=Path,
                        help='For a local source candidate, require this exact clean checkout')
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}', args.generator_commit):
        parser.error('generator commit must be an exact full SHA')
    output = args.output.resolve()
    if output.exists() or not output.parent.is_dir():
        parser.error('output must not exist and its parent must exist')
    launcher = shutil.which(args.clew)
    if launcher is None:
        parser.error('clew launcher unavailable')
    if args.source_checkout:
        checkout = args.source_checkout.resolve()
        if Path(launcher).resolve() != checkout / 'clew':
            parser.error('source candidate must use its supported ./clew launcher')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout, text=True).strip()
        dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=checkout, text=True)
        if head != args.generator_commit or dirty:
            parser.error('source candidate must match a clean frozen commit')
    try:
        version_output = subprocess.check_output([launcher, '--version'], text=True).strip()
    except subprocess.CalledProcessError as error:
        parser.exit(error.returncode, 'clew --version failed; native diagnostics are above\n')
    if not version_output.startswith('clew '):
        parser.error('unexpected launcher version')
    version = version_output.removeprefix('clew ')
    config = json.loads((HERE / 'inputs.json').read_text())
    for name, digest in config['inputSha256'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            parser.error('accepted input changed: ' + name)
    model = json.loads((HERE / 'data-model-plan.json').read_text())
    original = json.loads(json.dumps(model))
    navigation = json.loads((HERE / config['serviceModelLinks']).read_text())
    by_id = {item['id']: item for item in model['models']}
    for service, model_ids in navigation.items():
        for model_id in model_ids:
            by_id[model_id].setdefault('processLinks', []).append({
                'subject': 'service:' + service, 'anchor': 'section-entities',
                'label': service + ': field descriptions',
            })
    # The overlay only appends navigation; original fields, descriptions and evidence stay exact.
    for before, after in zip(original['models'], model['models']):
        remainder = dict(after)
        remainder['processLinks'] = after['processLinks'][:len(before['processLinks'])]
        if remainder != before:
            parser.error('navigation overlay changed original model content')
    with tempfile.TemporaryDirectory(prefix='.reference-render-', dir=output.parent) as temp:
        staging = Path(temp)
        derived = staging / 'data-model-plan.json'
        derived.write_text(json.dumps(model, ensure_ascii=False, indent=2) + '\n')
        site = staging / 'site'
        command = [launcher, 'docs', 'pages', 'render', '--root', str(args.root.resolve()),
                   '--snapshot', config['snapshot'], '--publication', config['publication'],
                   '--language', config['language'], '--reading-plan', str(HERE / 'reading-plan.json'),
                   '--contract-comparison', str(HERE / 'contract-comparison.json'),
                   '--data-model', str(derived), '--format', 'standalone', '--output', str(site)]
        log_path = output.parent / (output.name + '-render.log')
        with log_path.open('x') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            parser.exit(result.returncode, 'native render failed; inspect ' + str(log_path) + '\n')
        identity = {'schema': 'weather-reference-render/1.0',
                    'generator': {'version': version, 'sourceRevision': args.generator_commit,
                                  'selection': 'SOURCE_CANDIDATE' if args.source_checkout else 'INSTALLED_RELEASE'},
                    'publication': config['publication'], 'snapshot': config['snapshot'],
                    'language': config['language'], 'inputSha256': config['inputSha256']}
        (site / 'reference-render.json').write_text(json.dumps(identity, indent=2) + '\n')
        exported = site / 'reference-inputs'
        exported.mkdir()
        for name in [*config['inputSha256'], 'inputs.json']:
            shutil.copyfile(HERE / name, exported / name)
        shutil.copyfile(derived, exported / 'rendered-data-model-plan.json')
        report = VERIFY.verify(site, version, args.generator_commit)
        (site / 'reference-checks.json').write_text(json.dumps(report, indent=2) + '\n')
        shutil.move(str(site), str(output))
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
