#!/usr/bin/env python3
"""Verify the accepted public Weather human-page export without authoring it."""
import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile

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


def helper_digest(files):
    """The frozen author's indented file-map identity, not the installer digest."""
    raw = (json.dumps(files, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def release_skill_digest(identity):
    """Verify the actual official archive before reading its bundled skill bytes."""
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run(['gh', 'release', 'download', 'v' + identity['version'],
                        '--repo', 'codeclew/codeclew', '--pattern', identity['package'],
                        '--dir', folder], check=True, capture_output=True)
        archive = Path(folder) / identity['package']
        require(digest(archive) == identity['packageSha256'], 'Downloaded validation package digest differs')
        prefix = 'codeclew/source/skills/codeclew/'
        rows = []
        with tarfile.open(archive, 'r:gz') as bundle:
            for member in bundle.getmembers():
                if not member.name.startswith(prefix) or member.isdir():
                    continue
                name = member.name[len(prefix):]
                require(member.isfile() and name and '..' not in PurePosixPath(name).parts,
                        'Unsafe validation skill member')
                rows.append((name, bundle.extractfile(member).read(), 0o755 if member.mode & 0o111 else 0o644))
        require(rows and len({name for name, _, _ in rows}) == len(rows)
                and any(name == 'SKILL.md' for name, _, _ in rows), 'Missing validation skill')
        result = hashlib.sha256()
        for name, content, mode in sorted(rows):
            result.update(name.encode()); result.update(b'\0')
            result.update(str(mode).encode()); result.update(b'\0')
            result.update(content); result.update(b'\0')
        return 'sha256:' + result.hexdigest()


def acquisition(publication):
    return publication['renderer'] if publication['schema'] == 'weather-human-publication/1.0' else publication['acquisition']


def legacy_redirects(root, publication):
    """Only missing former reader paths may point to their exact archived page."""
    if publication.get('schema') != 'weather-human-publication/1.2':
        return {}
    record = publication['legacyRedirects']
    require(isinstance(record, dict) and set(record) == {'archive', 'publicationSha256', 'exportDigest', 'files'}
            and isinstance(record['archive'], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', record['archive']),
            'Invalid legacy redirect archive')
    archive = Path(root) / 'documentation/human/history' / record['archive']
    policy = archive / 'publication.json'
    require(policy.is_file() and not policy.is_symlink() and digest(policy) == record['publicationSha256'], 'Legacy archive publication pin differs')
    require(json.loads(policy.read_text()).get('schema') in {'weather-human-publication/1.0', 'weather-human-publication/1.1'},
            'Legacy archive must precede assisted publication')
    old = verify(root, exported=archive, publication=policy, required=True)
    require(export_digest(old['filesSha256']) == record['exportDigest'], 'Legacy archive export pin differs')
    missing = set(old['filesSha256']) - set(publication['filesSha256'])
    require(isinstance(record['files'], dict) and set(record['files']) == missing
            and all(name == target and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.html', name)
                    for name, target in record['files'].items()), 'Legacy redirect map differs from missing old paths')
    result = {}
    for name in sorted(missing):
        target = '../human-history/' + record['archive'] + '/' + name
        escaped = html.escape(target, quote=True)
        result[name] = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                        '<meta name="viewport" content="width=device-width,initial-scale=1">'
                        '<title>Archived guide</title><link rel="canonical" href="' + escaped + '">'
                        '<p>This saved guide is archived. <a href="' + escaped + '">Open the saved page</a>.</p>'
                        '<script>location.replace(' + json.dumps(target) + '+location.search+location.hash);</script></html>\n').encode()
    return result


def verify(root=ROOT, *, exported=None, required=False, official=False, publication=None):
    root = Path(root)
    require(publication is None or exported is not None, 'Explicit publication requires an export directory')
    policy = Path(publication) if publication is not None else root / 'documentation/human/publication.json'
    site = Path(exported) if exported is not None else policy.parent / 'site'
    if not policy.exists():
        require(not required and not site.exists(), 'Human export has no publication record')
        return None
    require(not policy.is_symlink(), 'Symlink publication record')
    p = json.loads(policy.read_text())
    legacy = p.get('schema') == 'weather-human-publication/1.0'
    assisted = p.get('schema') == 'weather-human-publication/1.2'
    require(legacy or assisted or p.get('schema') == 'weather-human-publication/1.1', 'Wrong publication schema')
    common = {'schema', 'source', 'services', 'language', 'entrypoint', 'filesSha256'}
    require(set(p) == common | ({'renderer'} if legacy else {'capture', 'acquisition', 'treatment', 'export'})
            | ({'validation', 'legacyRedirects'} if assisted else set()),
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
        if assisted:
            require(isinstance(treatment, dict) and set(treatment) == {'kind', 'repository', 'runtimeVersion', 'authoring', 'assistance'}
                    and treatment['kind'] == 'assisted-retained-export' and treatment['repository'] == PRODUCT,
                    'Expected explicit assisted retained treatment')
            authoring = treatment['authoring']
            require(isinstance(authoring, dict) and set(authoring) == {'helperDigest', 'helperFilesSha256'}
                    and isinstance(authoring['helperFilesSha256'], dict) and authoring['helperFilesSha256'], 'Missing frozen author helper')
            for name, value in authoring['helperFilesSha256'].items():
                path = PurePosixPath(name)
                require(not path.is_absolute() and '..' not in path.parts and '\\' not in name
                        and str(path) == name and all(not part.startswith('.') for part in path.parts)
                        and isinstance(value, str) and re.fullmatch('sha256:[0-9a-f]{64}', value), 'Invalid frozen helper file')
            require(authoring['helperDigest'] == helper_digest(authoring['helperFilesSha256']), 'Frozen author helper digest differs')
            assistance = treatment['assistance']
            require(isinstance(assistance, dict) and set(assistance) == {'targetedAuthorRepairs', 'rootDirectedNormalization', 'autonomousPass'}
                    and assistance['targetedAuthorRepairs'] is True and assistance['rootDirectedNormalization'] is True
                    and assistance['autonomousPass'] is False,
                    'Assisted export must preserve repair and normalization status')
            validation = p['validation']
            require(isinstance(validation, dict) and set(validation) == {'kind', 'version', 'sourceRevision', 'sourceTree', 'package', 'packageSha256', 'skillDigest'}
                    and validation['kind'] == 'official-release', 'Expected separate official validation package')
            require(isinstance(validation['version'], str) and re.fullmatch(r'\d+\.\d+\.\d+', validation['version'])
                    and all(isinstance(validation[k], str) and re.fullmatch('[0-9a-f]{40}', validation[k]) for k in ['sourceRevision', 'sourceTree'])
                    and isinstance(validation['packageSha256'], str) and re.fullmatch('[0-9a-f]{64}', validation['packageSha256'])
                    and validation['package'] in ARCHIVES
                    and isinstance(validation['skillDigest'], str) and re.fullmatch('sha256:[0-9a-f]{64}', validation['skillDigest']),
                    'Incomplete official validation identity')
        else:
            require(isinstance(treatment, dict) and set(treatment) == {'kind', 'repository', 'commit', 'tree', 'skillDigest', 'runtimeVersion'}
                    and treatment['kind'] == 'accepted-unreleased-skill' and treatment['repository'] == PRODUCT,
                    'Expected explicit accepted unreleased skill treatment')
            require(all(isinstance(treatment[k], str) and re.fullmatch('[0-9a-f]{40}', treatment[k]) for k in ['commit', 'tree'])
                    and isinstance(treatment['skillDigest'], str) and re.fullmatch('sha256:[0-9a-f]{64}', treatment['skillDigest']), 'Incomplete treatment hashes')
            require(treatment['commit'] != r['sourceRevision'], 'Unreleased treatment conflates official acquisition identity')
        require(treatment['runtimeVersion'] == r['version'], 'Treatment runtime version mismatch')
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
    redirects = legacy_redirects(root, p)
    require(actual == set(files) | ({'publication.json', *redirects} if staged else set()),
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
        require(all((site / name).read_bytes() == raw for name, raw in redirects.items()), 'Staged legacy redirect bytes differ')
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
        if assisted:
            validation = p['validation']
            validated_release = api('codeclew/codeclew/releases/tags/v' + validation['version'])
            validated_commit = api('codeclew/codeclew/commits/v' + validation['version'])
            require(not validated_release['draft'] and not validated_release['prerelease'], 'Validation release is not public stable')
            require(validated_commit['sha'] == validation['sourceRevision']
                    and validated_commit['commit']['tree']['sha'] == validation['sourceTree'], 'Validation commit or tree differs')
            assets = [a for a in validated_release['assets'] if a['name'] == validation['package']]
            require(len(assets) == 1 and assets[0]['digest'] == 'sha256:' + validation['packageSha256'], 'Official validation package digest differs')
            require(release_skill_digest(validation) == validation['skillDigest'], 'Official validation skill digest differs')
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
