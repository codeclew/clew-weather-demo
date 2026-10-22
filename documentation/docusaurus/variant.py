#!/usr/bin/env python3
"""Freeze, verify and stage the separate Weather Docusaurus review variant."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
BASELINE = 'c2195229942f120744aa3daa03cfb0ec3742a542'
BASE_URL = '/clew-weather-demo/docusaurus/'
IGNORED = {'node_modules', 'build', '.docusaurus', 'clew-reader-packs', '.git', '.DS_Store'}


def checked(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_version(version):
    checked(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version), 'invalid source version')
    return version


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def safe(root, name):
    rel = Path(name)
    checked(not rel.is_absolute() and '..' not in rel.parts and name != '.', 'unsafe artifact path')
    path = root / rel
    checked(not path.is_symlink(), 'artifact symlink refused: ' + name)
    return path


def project_files(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not any(part in IGNORED for part in p.relative_to(root).parts)}


def native_unchanged(repository, baseline=BASELINE):
    """Compare the complete native tree and policy bytes, including extra/ignored files."""
    paths = ['docs', 'documentation/reference/publication.json']
    raw = subprocess.check_output(['git', 'ls-tree', '-rz', baseline, '--', *paths], cwd=repository)
    expected = {}
    for row in raw.split(b'\0'):
        if not row:
            continue
        metadata, name = row.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        checked(kind == 'blob' and mode in {'100644', '100755'}, 'unsupported native baseline entry')
        expected[name.decode()] = oid
    checked(bool(expected), 'native baseline is empty')
    native_paths = list((repository / 'docs').rglob('*'))
    if any(p.is_symlink() for p in native_paths):
        return False
    current = {str(p.relative_to(repository)) for p in native_paths if p.is_file()}
    current.add('documentation/reference/publication.json')
    if current != set(expected) or any(safe(repository, name).is_symlink() for name in current):
        return False
    names = sorted(expected)
    checked(all('\n' not in name for name in names), 'unsupported newline in native path')
    hashes = subprocess.check_output(['git', 'hash-object', '--no-filters', '--stdin-paths'],
                                     input=('\n'.join(names) + '\n').encode(), cwd=repository).decode().splitlines()
    return hashes == [expected[name] for name in names]


def verify_export(project, config, inputs=None):
    manifest = read(project / 'export-manifest.json')
    for key in ['publication', 'snapshot']:
        checked(manifest[key] == config[key], 'different retained ' + key)
    checked(manifest['documentationLanguage'] == config['language'] == 'en', 'different output language')
    checked(manifest['format'] == 'docusaurus', 'different export format')
    if inputs is not None:
        for name, expected in config['inputSha256'].items():
            checked(digest(inputs / name) == expected, 'accepted author input changed: ' + name)
        for name in ['reading-plan.json', 'contract-comparison.json']:
            checked(digest(project / 'inputs' / name) == config['inputSha256'][name],
                    'exported author input changed: ' + name)
        model = read(inputs / 'data-model-plan.json')
        by_id = {row['id']: row for row in model['models']}
        for service, ids in read(inputs / config['serviceModelLinks']).items():
            for model_id in ids:
                by_id[model_id].setdefault('processLinks', []).append({
                    'subject': 'service:' + service, 'anchor': 'section-entities',
                    'label': service + ': field descriptions'})
        checked(read(project / 'inputs/data-model-plan.json') == model,
                'data model overlay changed retained content')
    for item in manifest['files']:
        checked('sha256:' + digest(safe(project, item['path'])) == item['digest'],
                'changed exported file: ' + item['path'])
    checked(manifest['resolvedPayloadParity']['status'] == 'VERIFIED', 'native payload parity not verified')
    return manifest


def review_page(identity, project):
    rows = [
        ('System story and catalog', 'overview.mdx', 'The current reading guide and service/process discovery.'),
        ('Service purpose, inputs, state and rules', 'services/dashboard.mdx', 'Dashboard; Places and Forecasts have the same service reader.'),
        ('Source-bound process and complete selected methods', 'scenarios/dashboard-save-city.mdx', 'Saving a city through Dashboard and Places.'),
        ('Optional process Data Flow', 'scenarios/dashboard-forecast-updated-consumer.mdx', 'Read the account, then select Data Flow; this author input explicitly enables it.'),
        ('Models, field tables and lookup records', 'data-model/city-lookup.mdx', 'The three supported cities and field evidence; follow related Place and forecast models.'),
        ('HTTP schemas and retained comparisons', 'comparisons/places.mdx', 'Declared contracts and retained observations keep separate authority.'),
        ('Kafka consumption and asynchronous continuation', 'scenarios/forecasts-place-requested-consumer.mdx', 'A real place-requested consumer and producer/consumer discovery.'),
        ('Historical runtime note and separate assessment', 'notes/dashboard--assessment-runtime-kafka-replay.mdx', 'A retained replay observation, not a fresh runtime test.'),
        ('Retained source appendix', 'sources/index.mdx', 'Exact retained revision/range bindings and their reading context.'),
        ('Reader help and author recipes', 'help.mdx', 'Navigation, evidence interpretation and explicitly labeled authoring instructions.'),
        ('Publication identity and limits', 'history.mdx', 'The selected publication and snapshot; this export contains no chronology or diff.'),
    ]
    checked(all((project / 'docs' / path).is_file() for _, path, _ in rows), 'review example destination missing')
    text = '---\ntitle: Weather Docusaurus review\nslug: /review\n---\n\nimport {ClewDownload} from \'@site/src/components/ClewReaders\';\n\n# Weather Docusaurus review\n\n'
    text += ('This separate version presents the retained Weather publication with the current renderer candidate. '
             'The original native website remains available at [Weather native documentation · official clew 0.13.39](https://codeclew.github.io/clew-weather-demo/). '
             'This is a source candidate, not a new Codeclew public release or a new runtime observation.\n\n')
    text += f'**Renderer source commit:** `{identity["renderer"]["sourceRevision"]}` · reported source version `{identity["renderer"]["version"]}`.\n\n'
    text += f'**Publication:** `{identity["publication"]}`\n\n**Selected snapshot:** `{identity["snapshot"]}`\n\n'
    text += '## Current MDX capabilities and real examples\n\n| Capability | Real Weather example |\n| --- | --- |\n'
    for title, path, description in rows:
        text += f'| [{title}]({path}) | {description} |\n'
    text += ('\nThese links cover the page types and optional data-flow view actually present in this export. '
             'Source, declarations, interpretations, meaning review and historical observations retain their own limits. '
             'The Help capability table describes module support and admission requirements; this publication does not demonstrate every possible module or prove runtime activation.\n\n'
             '## Historical native examples\n\n'
             '[Open the historical real-example renderer catalog](https://codeclew.github.io/clew-weather-demo/render-catalog/). '
             'It retains native and earlier renderer examples from source revision `31a559851b947d5eda90afc003f2bfb2b2c27130`. '
             'Its inventory and missing view types describe that collection. They are not a claim of current MDX coverage or a list of missing current features.\n\n'
             '<ClewDownload path="/variant-identity.json">Inspect the variant identity</ClewDownload>.\n')
    return text


def freeze(export, project, revision, version, inputs):
    checked(re.fullmatch('[0-9a-f]{40}', revision), 'source revision must be a full SHA')
    validate_version(version)
    checked(not project.exists(), 'project destination must not exist')
    config = read(inputs / 'inputs.json')
    verify_export(export, config, inputs)
    shutil.copytree(export, project, ignore=shutil.ignore_patterns(*IGNORED))
    identity = {'schema': 'weather-docusaurus-review/1.0', 'renderer': {
        'selection': 'SOURCE_CANDIDATE', 'sourceRevision': revision, 'version': version},
        'publication': config['publication'], 'snapshot': config['snapshot'],
        'documentationLanguage': config['language'], 'inputSha256': config['inputSha256'],
        'publicReleaseClaim': False, 'runtimeReexecuted': False, 'baseUrl': BASE_URL}
    write(project / 'static/variant-identity.json', identity)
    (project / 'docs/review.mdx').write_text(review_page(identity, project))
    write(HERE / 'files.json', project_files(project))
    write(HERE / 'publication.json', {'schema': 'weather-docusaurus-publication/1.0',
        'identity': identity, 'files': 'files.json', 'filesSha256': digest(HERE / 'files.json'),
        'acceptance': {'status': 'PENDING', 'scope': 'Native HTML and production Docusaurus browser review required'}})


def verify(project, policy_path, inputs, require_acceptance=True):
    policy = read(policy_path)
    checked(policy['schema'] == 'weather-docusaurus-publication/1.0', 'unsupported variant policy')
    identity = policy['identity']
    checked(identity['renderer']['selection'] == 'SOURCE_CANDIDATE' and identity['publicReleaseClaim'] is False,
            'review variant must preserve source-candidate authority')
    checked(re.fullmatch('[0-9a-f]{40}', identity['renderer']['sourceRevision']), 'invalid source pin')
    validate_version(identity['renderer']['version'])
    config = read(inputs / 'inputs.json')
    verify_export(project, config, inputs)
    for key in ['publication', 'snapshot']:
        checked(identity[key] == config[key], 'different variant ' + key)
    checked(identity['inputSha256'] == config['inputSha256'], 'variant author inputs differ')
    checked(read(project / 'static/variant-identity.json') == identity, 'visible variant identity differs')
    index_path = safe(policy_path.parent, policy['files'])
    checked(digest(index_path) == policy['filesSha256'], 'variant file index changed')
    checked(project_files(project) == read(index_path), 'variant source files changed or omitted')
    if require_acceptance:
        acceptance = policy['acceptance']
        checked(acceptance['status'] == 'PASS', 'independent browser acceptance is pending')
        for role in ['analyst', 'engineer']:
            item = acceptance[role]
            path = safe(policy_path.parent, item['path'])
            checked(digest(path) == item['sha256'], 'acceptance report changed: ' + role)
            checked(bool(path.read_text().strip()), 'empty acceptance report')
    return identity


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value:
                self.urls.append(value)


def verify_build(build):
    checked((build / 'review.html').is_file(), 'built review index missing')
    checked((build / 'variant-identity.json').is_file(), 'built identity missing')
    for page in build.rglob('*.html'):
        parser = Links()
        parser.feed(page.read_text())
        for url in parser.urls:
            if url.startswith('/') and not url.startswith('//'):
                checked(url.startswith(BASE_URL) or url.startswith('/clew-weather-demo/render-catalog/'),
                        'build link escaped deployment base: ' + url)
    return {'status': 'PASS', 'baseUrl': BASE_URL, 'htmlPages': len(list(build.rglob('*.html')))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    mode = sub.add_parser('native-mode'); mode.add_argument('--repository', type=Path, default=HERE.parents[1])
    frozen = sub.add_parser('freeze')
    frozen.add_argument('--export', type=Path, required=True); frozen.add_argument('--revision', required=True)
    frozen.add_argument('--version', required=True)
    check = sub.add_parser('verify'); check.add_argument('--candidate', action='store_true')
    built = sub.add_parser('verify-build'); built.add_argument('--build', type=Path, default=HERE / 'project/build')
    args = parser.parse_args()
    if args.command == 'native-mode':
        print('pinned' if native_unchanged(args.repository.resolve()) else 'policy')
    elif args.command == 'freeze':
        freeze(args.export, HERE / 'project', args.revision, args.version, HERE.parent / 'reference')
    elif args.command == 'verify':
        print(json.dumps(verify(HERE / 'project', HERE / 'publication.json', HERE.parent / 'reference', not args.candidate)))
    else:
        print(json.dumps(verify_build(args.build)))


if __name__ == '__main__':
    main()
