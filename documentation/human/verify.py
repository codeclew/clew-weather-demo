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
ARCHIVES = {f'codeclew-{platform}.tar.gz' for platform in
            ['macos-arm64', 'macos-x86_64', 'linux-x86_64']}
SUFFIXES = {'.html', '.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff2'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root=ROOT, *, exported=None, required=False, official=False):
    root = Path(root)
    policy = root / 'documentation/human/publication.json'
    site = Path(exported) if exported is not None else policy.parent / 'site'
    if not policy.exists():
        require(not required and not site.exists(), 'Human export has no publication record')
        return None
    require(not policy.is_symlink(), 'Symlink publication record')
    p = json.loads(policy.read_text())
    require(set(p) == {'schema', 'renderer', 'source', 'services', 'language',
                       'entrypoint', 'filesSha256'}, 'Unexpected publication fields')
    require(p['schema'] == 'weather-human-publication/1.0', 'Wrong publication schema')
    r, source = p['renderer'], p['source']
    require(set(r) == {'version', 'sourceRevision', 'skillDigest', 'package', 'packageSha256'},
            'Unexpected renderer fields')
    require(set(source) == {'repository', 'revision'} and source['repository'] == REPOSITORY,
            'Human source must be the public Weather repository')
    require(re.fullmatch(r'\d+\.\d+\.\d+', r['version']), 'Invalid release version')
    for revision in [r['sourceRevision'], source['revision']]:
        require(re.fullmatch('[0-9a-f]{40}', revision), 'Invalid public revision')
    require(re.fullmatch('sha256:[0-9a-f]{64}', r['skillDigest']), 'Invalid skill digest')
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
                      'renderer': publication['renderer'], 'source': publication['source'],
                      'scope': 'Accepted export identity and bytes; not semantic completeness'}))
