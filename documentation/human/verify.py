#!/usr/bin/env python3
"""Verify the accepted public Weather human-page export without authoring it."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'https://github.com/codeclew/clew-weather-demo'
PRODUCT = 'https://github.com/codeclew/codeclew'
ARCHIVES = {f'codeclew-{platform}.tar.gz' for platform in
            ['macos-arm64', 'macos-x86_64', 'linux-x86_64']}
SUFFIXES = {'.html', '.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff2'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_digest(files):
    """Identity of the exact accepted reader-file map, not an operational root."""
    raw = json.dumps(files, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def acquisition(publication):
    return publication['renderer'] if publication['schema'] == 'weather-human-publication/1.0' else publication['acquisition']


def verify(root=ROOT, *, exported=None, required=False, official=False):
    root = Path(root)
    policy = root / 'documentation/human/publication.json'
    site = Path(exported) if exported is not None else policy.parent / 'site'
    if not policy.exists():
        require(not required and not site.exists(), 'Human export has no publication record')
        return None
    require(not policy.is_symlink(), 'Symlink publication record')
    p = json.loads(policy.read_text())
    legacy = p.get('schema') == 'weather-human-publication/1.0'
    require(legacy or p.get('schema') == 'weather-human-publication/1.1', 'Wrong publication schema')
    common = {'schema', 'source', 'services', 'language', 'entrypoint', 'filesSha256'}
    require(set(p) == common | ({'renderer'} if legacy else {'capture', 'acquisition', 'treatment', 'export'}),
            'Unexpected publication fields')
    r, source = acquisition(p), p['source']
    require(isinstance(r, dict) and set(r) == {'version', 'sourceRevision', 'package', 'packageSha256'} | ({'skillDigest'} if legacy else {'kind'}),
            'Unexpected renderer fields' if legacy else 'Unexpected acquisition fields')
    if legacy:
        require(re.fullmatch('sha256:[0-9a-f]{64}', r['skillDigest']), 'Invalid skill digest')
    else:
        require(r['kind'] == 'official-release', 'Acquisition must retain official release identity')
        capture, treatment, exported_identity = p['capture'], p['treatment'], p['export']
        require(isinstance(capture, dict) and set(capture) == {'kind', 'snapshot', 'producerVersion', 'recaptured'}
                and capture['kind'] == 'retained-snapshot' and capture['recaptured'] is False,
                'Expected retained historical capture without recapture')
        require(isinstance(capture['snapshot'], str) and re.fullmatch(r'sha256:[0-9a-f]{64}/[1-9][0-9]*', capture['snapshot']), 'Invalid retained snapshot')
        require(capture['producerVersion'] is None or isinstance(capture['producerVersion'], str) and re.fullmatch(r'\d+\.\d+\.\d+', capture['producerVersion']),
                'Invalid historical capture version')
        require(isinstance(treatment, dict) and set(treatment) == {'kind', 'repository', 'commit', 'tree', 'skillDigest', 'runtimeVersion'}
                and treatment['kind'] == 'accepted-unreleased-skill' and treatment['repository'] == PRODUCT,
                'Expected explicit accepted unreleased skill treatment')
        require(all(isinstance(treatment[k], str) and re.fullmatch('[0-9a-f]{40}', treatment[k]) for k in ['commit', 'tree'])
                and isinstance(treatment['skillDigest'], str) and re.fullmatch('sha256:[0-9a-f]{64}', treatment['skillDigest']), 'Incomplete treatment hashes')
        require(treatment['runtimeVersion'] == r['version'], 'Treatment runtime version mismatch')
        require(treatment['commit'] != r['sourceRevision'], 'Unreleased treatment conflates official acquisition identity')
        require(isinstance(exported_identity, dict) and set(exported_identity) == {'kind', 'digest', 'fileCount'} and exported_identity['kind'] == 'frozen-export'
                and isinstance(exported_identity['digest'], str) and re.fullmatch('sha256:[0-9a-f]{64}', exported_identity['digest'])
                and type(exported_identity['fileCount']) is int, 'Incomplete frozen export identity')
    require(set(source) == {'repository', 'revision'} and source['repository'] == REPOSITORY,
            'Human source must be the public Weather repository')
    require(re.fullmatch(r'\d+\.\d+\.\d+', r['version']), 'Invalid release version')
    for revision in [r['sourceRevision'], source['revision']]:
        require(re.fullmatch('[0-9a-f]{40}', revision), 'Invalid public revision')
    require(re.fullmatch('[0-9a-f]{64}', r['packageSha256']), 'Invalid package digest')
    require(r['package'] in ARCHIVES, 'Unknown official package')
    require(sorted(p['services']) == ['dashboard', 'forecasts', 'places'], 'Wrong service scope')
    require(p['language'] in {'en', 'ru'}, 'Choose one documentation language')
    files = p['filesSha256']
    require(isinstance(files, dict) and files, 'Empty human export')
    require(p['entrypoint'] in files and p['entrypoint'].endswith('.html'), 'Missing HTML entrypoint')
    require(site.is_dir() and not site.is_symlink(), 'Missing or unsafe human export')
    actual = set()
    for file in site.rglob('*'):
        require(not file.is_symlink(), 'Symlink in human export')
        if file.is_file():
            actual.add(file.relative_to(site).as_posix())
    staged = exported is not None
    require(actual == set(files) | ({'publication.json'} if staged else set()),
            'Missing or unlisted human export files')
    for name, expected in files.items():
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in name
                and str(path) == name and path.suffix in SUFFIXES
                and not any(part.startswith('.') for part in path.parts), 'Unsafe export path')
        require(re.fullmatch('[0-9a-f]{64}', expected), 'Invalid file digest')
        file = site / name
        require(digest(file) == expected, 'Changed human export file: ' + name)
        if path.suffix in {'.html', '.css', '.js', '.svg'}:
            text = file.read_text()
            require(not re.search(r'file://|/(?:Users|home)/|CODECLEW_HOME|[.]codeclew/', text),
                    'Local workspace reference in public export: ' + name)
    if not legacy:
        require(p['export']['fileCount'] == len(files) and p['export']['digest'] == export_digest(files),
                'Frozen export identity differs')
    if staged:
        require((site / 'publication.json').read_bytes() == policy.read_bytes(),
                'Staged publication record changed')
    if official:
        def api(path):
            return json.loads(subprocess.check_output(['gh', 'api', 'repos/' + path], text=True))
        release = api('codeclew/codeclew/releases/tags/v' + r['version'])
        require(not release['draft'] and not release['prerelease'], 'Release is not public stable')
        require(api('codeclew/codeclew/commits/v' + r['version'])['sha'] == r['sourceRevision'],
                'Official release revision differs')
        assets = [a for a in release['assets'] if a['name'] == r['package']]
        require(len(assets) == 1 and assets[0]['digest'] == 'sha256:' + r['packageSha256'],
                'Official package digest differs')
        require(api('codeclew/clew-weather-demo/commits/' + source['revision'])['sha'] == source['revision'],
                'Weather source revision is not public')
    return p


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official-release', action='store_true')
    args = parser.parse_args()
    publication = verify(required=True, official=args.official_release)
    print(json.dumps({'status': 'PASS', 'files': len(publication['filesSha256']),
                      **({'renderer': publication['renderer']} if publication['schema'].endswith('/1.0') else
                         {key: publication[key] for key in ['capture', 'acquisition', 'treatment', 'export']}),
                      'source': publication['source'],
                      'scope': 'Accepted export identity and bytes; not semantic completeness'}))
