#!/usr/bin/env python3
"""Verify the separately frozen current Weather HTML and MDX publication."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserved(expected, actual):
    if isinstance(expected, dict):
        if expected.get('kind') == 'SOURCE':
            assert actual['kind'] == 'SELECTED_SOURCE'
            for key in ['service', 'textDigest']:
                assert expected[key] == actual['source'][key]
            assert expected['sourceId'] == actual['source']['id']
            for key in ['startLine', 'endLine']:
                assert expected[key] == actual[key]
            return
        for key, value in expected.items():
            preserved(value, actual[key])
    elif isinstance(expected, list):
        assert len(expected) == len(actual)
        for before, after in zip(expected, actual):
            preserved(before, after)
    else:
        assert expected == actual


def verify(version, revision):
    policy = json.loads((HERE / 'publication.json').read_text())
    assert policy['renderer'] == {'version': version.removeprefix('v'), 'sourceRevision': revision,
                                  'selection': 'INSTALLED_RELEASE'}
    assert policy['publicReleaseClaim'] is True
    assert policy['releasePackage']['sourceRevision'] == revision
    for name, expected in policy['inputSha256'].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in policy['filesSha256'].items():
        assert digest(ROOT / name) == expected, name
    for folder, manifest_name in [(HERE / 'site/native', 'pages-manifest.json'),
                                  (HERE / 'project', 'export-manifest.json')]:
        manifest = json.loads((folder / manifest_name).read_text())
        assert manifest['publication'] == policy['publication']
        assert manifest['snapshot'] == policy['snapshot']
        for item in manifest['files']:
            assert 'sha256:' + digest(folder / item['path']) == item['digest'], item['path']
    models = json.loads((ROOT / 'documentation/markdown-tables/data-model-plan.json').read_text())['models']
    count = 0
    for model in models:
        actual = json.loads((HERE / 'site/native/data-model' / (model['id'] + '.original.json')).read_text())
        fields = {field['id']: field for field in actual['fields']}
        for field in model['fields']:
            for key in ['path', 'meaning', 'representations', 'originalName', 'readableName']:
                preserved(field.get(key), fields[field['id']].get(key))
            count += 1
    assert len(models) == 6 and count == 23
    return {'status': 'PASS', 'models': len(models), 'completeFields': count,
            'renderer': policy['renderer'], 'verifiedFiles': len(policy['filesSha256'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.version, args.revision), indent=2))
