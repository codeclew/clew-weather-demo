#!/usr/bin/env python3
"""Reject a stale or incomplete reference bundle before it reaches Pages."""

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent


class FieldTables(HTMLParser):
    """Parse actual HTML elements; strings in script templates are not tables."""

    def __init__(self):
        super().__init__()
        self.inside = False
        self.tables = 0
        self.fields = []
        self.headers = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table' and 'dm-fields' in attrs.get('class', '').split():
            self.inside = True
            self.tables += 1
        if self.inside and tag == 'th' and attrs.get('scope') == 'col':
            self.headers += 1
        if self.inside and tag == 'a' and attrs.get('href', '').startswith('#field-'):
            self.fields.append(attrs['href'][7:])

    def handle_endtag(self, tag):
        if tag == 'table':
            self.inside = False


def checked(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root, expected_version, expected_commit=None, inputs=HERE, expected_selection=None):
    config = json.loads((inputs / 'inputs.json').read_text())
    identity = json.loads((root / 'reference-render.json').read_text())
    manifest = json.loads((root / 'pages-manifest.json').read_text())
    checked(identity['generator']['version'] == expected_version.lstrip('v'), 'stale generator version')
    if expected_commit:
        checked(identity['generator']['sourceRevision'] == expected_commit, 'different generator commit')
    if expected_selection:
        checked(identity['generator']['selection'] == expected_selection, 'different renderer selection mode')
    checked(manifest['publication'] == config['publication'], 'different frozen publication')
    checked(manifest['snapshot'] == config['snapshot'], 'different retained snapshot')
    checked(manifest['documentationLanguage'] == config['language'], 'different output language')
    checked(identity['publication'] == config['publication'] and identity['snapshot'] == config['snapshot'], 'different published evidence identity')
    checked(identity['language'] == config['language'] and identity['inputSha256'] == config['inputSha256'], 'different published input identity')
    for name, digest in config['inputSha256'].items():
        checked(sha(inputs / name) == digest, 'changed accepted input: ' + name)
        checked(sha(root / 'reference-inputs' / name) == digest, 'different exported input: ' + name)
    for entry in manifest['files']:
        relative = Path(entry['path'])
        checked(not relative.is_absolute() and '..' not in relative.parts, 'unsafe manifest path')
        checked('sha256:' + sha(root / relative) == entry['digest'], 'changed output: ' + entry['path'])
    indexed = {entry['path'] for entry in manifest['files']}
    required = {'data-model.json'}
    required.update('data-model/' + model + '.html' for model in config['expectedModels'])
    required.update('scenarios/' + scenario + suffix for scenario in config['expectedDataFlow'] for suffix in ['.html', '.json'])
    checked(required <= indexed, 'reference pages absent from output manifest')
    model = json.loads((root / 'data-model.json').read_text())
    actual = {m['id']: [f['id'] for f in m['fields']] for m in model['models']}
    checked(actual == config['expectedModels'], 'missing or changed canonical model field inventory')
    for model_id, fields in config['expectedModels'].items():
        parser = FieldTables()
        parser.feed((root / 'data-model' / (model_id + '.html')).read_text())
        checked(parser.tables == 1 and parser.headers == 2, 'field table missing overview headers: ' + model_id)
        checked(parser.fields == fields, 'field table missing visible rows: ' + model_id)
    for scenario in config['expectedDataFlow']:
        payload = json.loads((root / 'scenarios' / (scenario + '.json')).read_text())
        flow = payload.get('processDataFlow', {})
        checked(flow.get('request', {}).get('enabled') is True, 'Data Flow opt-in lost: ' + scenario)
        checked(bool(flow.get('models')) and bool(flow['request'].get('stages')), 'Data Flow inventory lost: ' + scenario)
        checked(payload.get('questionReader', {}).get('presentation') == 'SEQUENTIAL', 'sequential reader lost: ' + scenario)
        html = (root / 'scenarios' / (scenario + '.html')).read_text()
        checked('CodeclewDataModel' in html and 'processDataFlow' in html, 'Data Flow runtime missing: ' + scenario)
    links = json.loads((inputs / config['serviceModelLinks']).read_text())
    for service, models in links.items():
        payload = json.loads((root / 'services' / (service + '.json')).read_text())
        checked([m['id'] for m in payload.get('serviceModelLinks', [])] == models, 'service field-table navigation missing: ' + service)
    return {'status': 'PASS', 'generator': identity['generator'], 'models': len(actual),
            'fields': sum(map(len, actual.values())), 'processDataFlow': config['expectedDataFlow'],
            'scope': 'Static artifact coverage and identity; interactive browser acceptance is separate.'}


def verify_publication(root, policy_path, inputs=HERE, latest_version=None, latest_commit=None):
    policy = json.loads(policy_path.read_text())
    checked(policy.get('schema') == 'weather-reference-publication/1.0', 'unsupported publication policy')
    checked((root / 'reference-publication.json').read_bytes() == policy_path.read_bytes(), 'published policy differs')
    mode = policy.get('mode')
    if mode == 'latest-release':
        checked(bool(latest_version) and bool(latest_commit), 'latest release identity is required')
        report = verify(root, latest_version, latest_commit, inputs, 'INSTALLED_RELEASE')
    elif mode == 'accepted-source':
        renderer = policy['renderer']
        checked(bool(re.fullmatch(r'[0-9a-f]{40}', renderer['sourceRevision'])), 'source pin must be a full commit')
        checked(bool(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', renderer['version'])), 'source build version is invalid')
        report = verify(root, renderer['version'], renderer['sourceRevision'], inputs, 'SOURCE_CANDIDATE')
        pin_path = inputs / policy['acceptedFiles']
        checked(pin_path.parent == inputs and pin_path.name.endswith('.json'), 'unsafe accepted file index')
        checked(sha(pin_path) == policy['acceptedFilesSha256'], 'accepted file index changed')
        pins = json.loads(pin_path.read_text())
        manifest = json.loads((root / 'pages-manifest.json').read_text())
        required = {entry['path'] for entry in manifest['files']}
        required.update(['pages-manifest.json', 'reference-render.json', 'reference-checks.json',
                         'reference-inputs/inputs.json', 'reference-inputs/rendered-data-model-plan.json'])
        required.update('reference-inputs/' + name for name in json.loads((inputs / 'inputs.json').read_text())['inputSha256'])
        checked(required <= pins.keys(), 'accepted file index omits required artifact bytes')
        for name, digest in pins.items():
            relative = Path(name)
            checked(not relative.is_absolute() and '..' not in relative.parts, 'unsafe accepted artifact path')
            checked(sha(root / relative) == digest, 'accepted artifact changed: ' + name)
        report['acceptedFileCount'] = len(pins)
    else:
        raise ValueError('publication mode must be latest-release or accepted-source')
    for name, digest in policy.get('siteFilesSha256', {}).items():
        relative = Path(name)
        checked(not relative.is_absolute() and '..' not in relative.parts, 'unsafe site metadata path')
        checked(sha(root / relative) == digest, 'site provenance changed: ' + name)
    report['publicationMode'] = mode
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--expected-version')
    parser.add_argument('--expected-commit')
    parser.add_argument('--publication-policy', type=Path)
    args = parser.parse_args()
    try:
        if args.publication_policy:
            report = verify_publication(args.root, args.publication_policy,
                                        latest_version=args.expected_version, latest_commit=args.expected_commit)
        else:
            if not args.expected_version:
                parser.error('--expected-version or --publication-policy is required')
            report = verify(args.root, args.expected_version, args.expected_commit)
        print(json.dumps(report, indent=2))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, str(error) + '\n')
