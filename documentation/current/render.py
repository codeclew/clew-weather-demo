#!/usr/bin/env python3
"""Render current Weather tables with an explicitly selected installed release."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def render(root, launcher, version, revision, output):
    assert not output.exists() and output.parent.is_dir(), 'Use a fresh output directory'
    launcher = shutil.which(launcher) or launcher
    assert subprocess.check_output([launcher, '--version'], text=True).strip() == 'clew ' + version
    capabilities = json.loads(subprocess.check_output([launcher, 'capabilities'], text=True))
    assert capabilities['productVersion'] == version and capabilities['runtimeMode'] == 'RELEASE'
    assert capabilities['agentContract']['launcherAuthority'] == 'INSTALLED_RELEASE'
    assert capabilities['agentContract']['sourceFallbackAllowed'] is False
    release_file = Path(launcher).resolve().parent.parent / 'release.json'
    release = json.loads(release_file.read_text())
    assert release['sourceRevision'] == revision and release['version'].removeprefix('v') == version
    inputs = ROOT / 'documentation/markdown-tables'
    identity = json.loads((inputs / 'input-provenance.json').read_text())
    output.mkdir()
    base = ['docs', 'pages', 'render', '--root', str(root.resolve()),
            '--snapshot', identity['snapshot'], '--publication', identity['publication'],
            '--reading-plan', str(inputs / 'reading-plan.json'),
            '--data-model', str(inputs / 'rendered-data-model-plan.json'), '--language', 'en']
    for name, format_name in [('native', 'standalone'), ('docusaurus', 'docusaurus')]:
        with ((output / (name + '-command.json')).open('x') as stdout,
              (output / (name + '-diagnostics.log')).open('x') as stderr):
            result = subprocess.run([launcher, *base, '--format', format_name, '--output', str(output / name)],
                                    stdout=stdout, stderr=stderr)
        response = json.loads((output / (name + '-command.json')).read_text())
        assert result.returncode in [0, 3] and response['status'] in ['RENDERED', 'PARTIAL'], response
    producer = {'schema': 'weather-current-render/1.0', 'renderer': {
        'selection': 'INSTALLED_RELEASE', 'version': version, 'sourceRevision': revision},
        'publicReleaseClaim': True, 'runtimeReexecuted': False,
        'runtime': {key: capabilities[key] for key in ['runtimeMode', 'runtimeKey', 'runtimeManifestDigest']},
        'releasePackage': release,
        'releasePackageMetadataSha256': hashlib.sha256(release_file.read_bytes()).hexdigest(),
        'snapshot': identity['snapshot'], 'publication': identity['publication'],
        'inputSha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                        for name in ['documentation/markdown-tables/reading-plan.json',
                                     'documentation/markdown-tables/data-model-plan.json',
                                     'documentation/markdown-tables/rendered-data-model-plan.json',
                                     'documentation/reference/service-model-links.json']},
        'navigationOverlay': 'The rendered model plan appends the existing explicit service-model-links.json associations as section-entities processLinks. Original field content and model ownership claims are unchanged.',
        'scope': 'Presentation of the retained publication; no recapture or model authoring. Labels retain agent-proposal authority.'}
    (output / 'producer.json').write_text(json.dumps(producer, indent=2) + '\n')
    return producer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--clew', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--release-commit', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.root, args.clew, args.version, args.release_commit, args.output), indent=2))
