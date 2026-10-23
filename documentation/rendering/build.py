#!/usr/bin/env python3
"""Compose an additive capability showcase over unchanged frozen Weather inputs."""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = '/clew-weather-demo/'
SHOW = BASE + 'rendering/'
BASELINE = 'ff017959d968235bf3e5ef31dcd25f0770745d41'
CURRENT = 'c8b9fba4520262ea4994c751b0fc39e96e055283'
HISTORICAL = '31a559851b947d5eda90afc003f2bfb2b2c27130'
CANDIDATE = '17224661d68056b502c50c6c9431efb40aca2b4a'
WEATHER = 'https://github.com/codeclew/clew-weather-demo'
PRODUCT = 'https://github.com/codeclew/codeclew'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def doc(path):
    return BASE + path.removeprefix('docs/')


def source(path, revision=CURRENT, line=None):
    if revision in {'ac55263474000924d489acfbbabb9e7adf8bf72a', '6f52d11fc780c243b4b79adece3db76905c2db6e'}:
        return {'label': path + ' · producer ' + revision[:8] + ' source not publicly available (provenance retained)',
                'href': SHOW + 'source/renderer-provenance-gaps.json'}
    return {'label': path + (':' + str(line) if line else ''),
            'href': PRODUCT + '/blob/' + revision + '/' + path + ('#L' + str(line) if line else '')}


def page(title, body, script=True):
    current = (ROOT / 'documentation/current/publication.json').is_file()
    native = 'current/native/overview.html' if current else 'overview.html'
    mdx = 'current/docusaurus/' if current else 'docusaurus/review.html'
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns=%22http://www.w3.org/2000/svg%22%20viewBox=%220%200%2032%2032%22%3E%3Ctext%20y=%2226%22%20font-size=%2228%22%3EW%3C/text%3E%3C/svg%3E"><title>' + html.escape(title) + ' · Weather rendering</title><link rel="stylesheet" href="' + SHOW + 'site.css">'
            '<header><nav aria-label="Showcase"><a class="brand" href="' + SHOW + '">Weather / Rendering</a>'
            '<a href="' + BASE + native + '">' + ('Latest HTML' if current else 'Native docs') + '</a><a href="' + BASE + mdx + '">' + ('Latest Docusaurus' if current else 'Docusaurus') + '</a>'
            '<a href="' + BASE + 'render-catalog/index.html">Historical catalogue</a></nav></header><main>'
            '<p id="errors" class="note warning" role="alert" hidden></p>' + body + '</main>'
            '<footer><div>Real retained examples. Source, authored interpretation and historical observations keep separate authority. '
            '<a href="' + SHOW + 'manifest.json">Capability manifest</a> · <a href="' + SHOW + 'source/build.py.txt">Composition source</a></div></footer>'
            + ('<script src="' + SHOW + 'app.js" defer></script>' if script else '') + '</html>')


def nearest_manifest(path):
    parent = (ROOT / 'docs' / path.split('#')[0]).parent
    while parent.is_relative_to(ROOT / 'docs'):
        for name in ['pages-manifest.json', 'manifest.json', 'export-manifest.json']:
            if (parent / name).is_file():
                return parent / name
        parent = parent.parent
    return None


def build(output):
    if output.exists():
        raise ValueError('Use a new output directory; preserve prior candidates.')
    output.mkdir(parents=True)
    target = output / 'rendering'
    target.mkdir()
    for name in ['site.css', 'app.js']:
        shutil.copy2(HERE / name, target / name)
    source_dir = target / 'source'
    source_dir.mkdir()

    def input_link(path, label=None):
        path = Path(path)
        destination = source_dir / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, destination)
        return {'label': label or path.as_posix(), 'href': SHOW + 'source/' + path.as_posix()}

    inputs = read(ROOT / 'documentation/reference/inputs.json')
    publication, snapshot = inputs['publication'], inputs['snapshot']
    native = read(ROOT / 'docs/reference-render.json')
    docusaurus = read(ROOT / 'documentation/docusaurus/publication.json')['identity']
    catalogue = read(ROOT / 'docs/render-catalog/catalogue.json')
    provenance = read(ROOT / 'docs/render-catalog/provenance.json')
    raw = 'generated/' + publication + '/'
    raw_binding = read(ROOT / ('docs/' + raw + 'bindings.json'))
    reference_inputs = [input_link('documentation/reference/' + name) for name in ['inputs.json', *inputs['inputSha256']]]
    generation_source = input_link('documentation/reference/build.py')
    freeze_source = input_link('documentation/docusaurus/variant.py')
    overlay_source = input_link('documentation/rendering/docusaurus.config.mjs')
    export_manifest = input_link('documentation/docusaurus/project/export-manifest.json', 'Actual frozen Docusaurus export manifest')
    old_recipe_source = input_link('documentation/render-catalog/build_gallery.py')
    historical_inputs = [input_link('documentation/render-catalog/render-conditions.json'),
                         input_link('documentation/render-catalog/coverage-examples.json')]
    source_dir.joinpath('build.py.txt').write_text(Path(__file__).read_text())
    shutil.copy2(HERE / 'renderer-provenance-gaps.json', source_dir / 'renderer-provenance-gaps.json')

    common = {'Source repository': WEATHER, 'Snapshot': snapshot, 'Publication': publication,
              'Capture boundary': 'Retained historical capture; no recapture or runtime replay for this showcase.'}
    placeholder = ('Requires the original operational DOCS_ROOT with retained immutable objects and this publication. '
                   'The website preserves portable evidence and inputs, but not the complete operational store. '
                   'Use an empty output directory. Reproduction is unavailable from website files alone.')
    command = ('clew docs pages render --root DOCS_ROOT --snapshot SNAPSHOT --publication PUBLICATION '
               '--reading-plan READING_PLAN_JSON --contract-comparison COMPARISON_JSON --data-model MODEL_PLAN_JSON '
               '--language en --format FORMAT --output EMPTY_OUTPUT_DIRECTORY')
    rows = []

    def add(id, category, title, description, example=None, family='publication', status='DEMO_EXAMPLE',
            identity=None, command_text=None, supplied_inputs=None, outputs=None, limits='', action='', sources=None):
        identity = identity or {'Renderer': '0.13.46 source candidate', 'Renderer revision': CANDIDATE}
        label = identity.get('Renderer', '') + ' · ' + identity.get('Renderer revision', 'release revision not retained')
        row = {'id': id, 'category': category, 'title': title, 'description': description, 'example': example,
               'family': family, 'status': status, 'identityLabel': label, 'action': action,
               'recipe': {'identity': {**common, **identity}, 'command': command_text or command,
                          'commandAuthority': 'Family template with explicitly labelled placeholders. Exact construction code is linked below; an absent original argv is not reconstructed as a measured command.',
                          'availability': placeholder, 'inputs': supplied_inputs if supplied_inputs is not None else reference_inputs + [generation_source, freeze_source],
                          'outputs': outputs or [export_manifest,
                                                 {'label': 'Docusaurus identity', 'href': BASE + 'docusaurus/variant-identity.json'}],
                          'source': sources or [
                              {'label': 'Current0.13.48 CLI support contract (not the historical producer)', 'href': PRODUCT + '/blob/' + CURRENT + '/crates/clew/src/documentation/static_pages.rs#L200'},
                              {'label': 'Actual frozen Docusaurus reader implementation', 'href': WEATHER + '/blob/' + BASELINE + '/documentation/docusaurus/project/src/components/ClewReaders.jsx'}],
                          'limits': limits or 'Retained source and authored interpretation do not prove live execution. Historical review labels and gaps remain those of the example.'}}
        rows.append(row)
        return row

    raw_row = add('format-publication', 'Rendering families', 'Saved publication · docs render',
                 'Read the original saved Save City page before a full Pages export. Its renderer schema is retained; its producer release and commit were not recorded.',
                 doc(raw + 'scenarios/dashboard-save-city.html'), identity={'Renderer': raw_binding['renderer'], 'Renderer revision': 'UNRECORDED — provenance gap', 'Producer release': 'UNRECORDED'},
                 command_text='clew docs render --root DOCS_ROOT --snapshot SNAPSHOT', supplied_inputs=[input_link('docs/' + raw + 'inputs.json')],
                 outputs=[{'label': 'Original publication', 'href': doc(raw + 'publication.json')}, {'label': 'Original bindings', 'href': doc(raw + 'bindings.json')}],
                 limits='The exact original invocation and producer commit are unavailable. The saved publication is the actual example. docs render would publish a new result; it is not a byte-for-byte replay recipe.')
    raw_row['recipe']['identity']['Editorial inputs'] = 'Original publication inputs are linked. No later Pages reading-plan, data-model or comparison overlay is asserted for this saved render.'
    standalone = add('format-standalone', 'Rendering families', 'Full Pages · standalone HTML',
                     'Save City with sequential reading, adjacent failure paths and optional Data Flow. This is the existing official 0.13.39 export, with its recorded editorial inputs.',
                     doc('scenarios/dashboard-save-city.html'), identity={'Renderer': '0.13.39 · installed official release', 'Renderer revision': native['generator']['sourceRevision']},
                     command_text=command.replace('FORMAT', 'standalone'), outputs=[{'label': 'Standalone pages manifest', 'href': doc('pages-manifest.json')}, {'label': 'Actual generation identity', 'href': doc('reference-render.json')}])
    standalone['recipe']['identity']['Editorial inputs'] = 'Explicit reading-plan.json, rendered data-model plan and contract-comparison.json. Not the same input set as the original docs render shell.'
    add('format-docusaurus', 'Rendering families', 'Full Pages · Docusaurus',
        'The same retained Save City process in a production-built MDX site, with source readers and domain model navigation. Layout and optional inputs differ across exports.',
        doc('docusaurus/scenarios/dashboard-save-city.html'), command_text=command.replace('FORMAT', 'docusaurus'),
        supplied_inputs=reference_inputs + [generation_source, freeze_source, overlay_source, input_link('documentation/docusaurus/README.md')])
    rows[-1]['recipe']['identity']['Editorial inputs'] = 'Explicit reading plan, data-model overlay and contract comparison. The demo adds a React-consistent navigation config overlay; frozen MDX/inputs are unchanged.'

    for original in catalogue['items']:
        mode = original['renderConditions']['mode']
        path = posixpath.normpath('render-catalog/' + original['path'])
        example = doc(path) if mode != 'unsupported' else None
        manifest = nearest_manifest(path)
        payload = read(manifest) if manifest else {}
        identity = {'Renderer': '0.13.33 source build (historical collection)', 'Renderer revision': provenance['sourceRevision'],
                    'Collection revision': HISTORICAL, 'Source repository': WEATHER}
        if original['id'] == 'page-syntax':
            identity.update({'Renderer': '0.13.32 earlier source-syntax build', 'Renderer revision': '6f52d11fc780c243b4b79adece3db76905c2db6e'})
        if original.get('rendererSourceRevision'):
            identity['Renderer revision'] = original['rendererSourceRevision']
            identity['Renderer'] = '0.13.33 source build; per-example producer override'
        family_commands = {'publication': 'clew docs pages render --root DOCS_ROOT --snapshot SNAPSHOT --publication PUBLICATION --output EMPTY_OUTPUT_DIRECTORY',
                           'selection': 'clew docs pages render --root DOCS_ROOT --snapshot SNAPSHOT --input SELECTIONS_JSON --output EMPTY_OUTPUT_DIRECTORY',
                           'answer': 'clew docs work explain --root DOCS_ROOT --work WORK_HANDLE --input ANSWER_JSON --output-dir EMPTY_OUTPUT_DIRECTORY',
                           'dsl': 'clew docs dsl render --root DOCS_ROOT --snapshot SNAPSHOT --service SERVICE_ID --profile PROFILE_JSON --output EMPTY_OUTPUT_DIRECTORY',
                           'unsupported': 'No supported command: the UpdateDeal prototype is not a rendering mode.'}
        output_links = [{'label': 'Original catalogue entry and conditions', 'href': doc('render-catalog/catalogue.json')},
                        {'label': 'Historical collection provenance', 'href': doc('render-catalog/provenance.json')},
                        {'label': 'Real source repositories, native results and remaining gaps', 'href': doc('render-catalog/coverage-provenance.json')}]
        if manifest:
            output_links.insert(0, {'label': 'Actual output manifest', 'href': doc(str(manifest.relative_to(ROOT / 'docs')))})
            for key in ['snapshot', 'publication']:
                if payload.get(key):
                    identity[key.title()] = payload[key]
            if mode in {'answer', 'dsl'} and not payload.get('snapshot'):
                identity['Snapshot'] = 'Not recorded in this manifest; consult the exact packet/profile and provenance. The collection snapshot is not substituted.'
            if mode != 'publication':
                identity['Publication'] = 'Not a full publication output. Retains its own packet/profile/selection authority.'
        sources = [source(catalogue['conditionSources'][key]['path'], catalogue['conditionSources'][key].get('sourceRevision', HISTORICAL), catalogue['conditionSources'][key]['line'])
                   for key in original['renderConditions']['sourceReferences'] if key in catalogue['conditionSources']]
        row = add(original['id'], 'Historical ' + original['category'].lower(), original['title'], original['description'], example,
                  mode, 'UNSUPPORTED' if mode == 'unsupported' else 'HISTORICAL_EXAMPLE', identity,
                  family_commands[mode], historical_inputs + [old_recipe_source], output_links,
                  ' · '.join(str(original['renderConditions'].get(k, '')) for k in ['requiredInputs', 'renderWhen', 'otherwise', 'limits'] if original['renderConditions'].get(k)), original['action'], sources)
        row['historicalRecord'] = original
        row['recipe']['identity']['Original status'] = original['status']
        repositories = read(ROOT / 'docs/render-catalog/coverage-provenance.json')['repositories']
        repository_key = next((label for marker, label in [('petclinic-accessors', 'Spring Petclinic Kotlin'), ('petclinic-java-flow', 'Spring Petclinic REST'), ('shared-queue', 'Mjedynak concurrency examples'), ('voltdb-dsl', 'VoltDB examples')] if marker in path), 'Weather')
        origin = repositories[repository_key]['repository']
        row['recipe']['identity']['Source repository'] = origin if origin.startswith('https://') else 'https://github.com/' + origin
        if original.get('evidence') and (ROOT / 'docs/render-catalog' / original['evidence']).is_file():
            row['recipe']['inputs'].append({'label': 'Per-example provenance', 'href': doc('render-catalog/' + original['evidence'])})
        bundles = {
            'places-native': ['places-selection.json'],
            'shared-queue': ['coverage-inputs/shared-queue-selection.json', 'coverage-inputs/shared-queue-service.json'],
            'petclinic-accessors': ['coverage-inputs/petclinic-selection.json'],
            'petclinic-java-flow': ['coverage-inputs/java-rest-process.json'],
            'weather-compiler-all': ['coverage-inputs/forecast-all-selections.json'],
            'weather-instructions': ['coverage-inputs/instructions-dashboard-selection.json', 'coverage-inputs/readme-dashboard-association.json'],
            'weather-maintained': ['coverage-inputs/maintained-selection.json'],
            'voltdb-dsl': ['coverage-inputs/voltdb-orderproc-profile.json', 'coverage-inputs/voltdb-service.json'],
            'weather-coverage': ['coverage-inputs/weather-place-entity.json', 'coverage-inputs/dashboard-place-lineage.json', 'coverage-inputs/places-publisher-states.json', 'coverage-inputs/consumer-visual-request.json'],
        }
        for bundle, files in bundles.items():
            if '/'+bundle+'/' in '/'+path:
                for filename in files:
                    candidate = 'documentation/render-catalog/' + filename
                    if (ROOT / candidate).is_file():
                        row['recipe']['inputs'].append(input_link(candidate))
        if manifest:
            for filename in ['answer.json', 'reader-packet.json', 'packet.json', 'profile.json', 'selection.json', 'review-provenance.json', 'meaning-review.json']:
                candidate = manifest.parent / filename
                if candidate.is_file():
                    row['recipe']['inputs'].append({'label': 'Retained ' + filename, 'href': doc(str(candidate.relative_to(ROOT / 'docs')))})
            if mode == 'answer' and payload.get('reviewRun'):
                row['recipe']['command'] = 'clew docs work explain --root DOCS_ROOT --work WORK_HANDLE --review-run REVIEW_RUN_ID --output-dir EMPTY_OUTPUT_DIRECTORY'
                row['recipe']['commandAuthority'] = 'Saved approved review-run export; --input draft rendering does not reproduce this approval provenance. Requires the original durable Work, checkpoint and review-run state.'
                row['recipe']['identity']['Work'] = payload.get('work', 'Not recorded')
                row['recipe']['identity']['Review run'] = payload['reviewRun']
                row['recipe']['identity']['Retained meaning review'] = payload.get('nativeMeaningReview', 'Consult review provenance')
        row['recipe']['availability'] = 'Historical prerequisites vary by packet, selection, repository and compiler capture. Original full argv and producer identities are not recorded uniformly. The retained manifest, source conditions and linked recipe are the authority; a current clew upgrade is not implied.'
        companion_mdx = (ROOT / 'docs' / path.split('#')[0]).with_suffix('.mdx')
        if mode == 'selection' and companion_mdx.is_file():
            row['recipe']['outputs'].append({'label': 'Actual inert selected-declaration MDX', 'href': doc(str(companion_mdx.relative_to(ROOT / 'docs')))})
            row['recipe']['limits'] += ' Selected-declaration MDX is inert native JSX, not a full Docusaurus export/project.'
        if original['id'] == 'page-native':
            row['description'] += ' Its companion inert MDX is linked in How it was made; it is distinct from a full Docusaurus site.'

    modern = [
        ('page-system-guide', 'Page types', 'System reading guide', 'Start from the accepted system story and follow services, process outcomes and evidence limits.', 'docusaurus/index.html', ''),
        ('presentation-sequential', 'Presentations', 'SEQUENTIAL process reading', 'Ordered steps, nearby failures and optional technical disclosures from an explicit reading plan.', 'docusaurus/scenarios/dashboard-save-city.html', 'Expand a technical disclosure, then follow the receiving handler.'),
        ('page-model', 'Page types', 'Domain model and field descriptions', 'Purpose, fields, declared representations and canonical model links have dedicated evidence-bound pages.', 'docusaurus/data-model/place.html', 'Follow a field to its representations and source.'),
        ('page-city-records', 'Page types', 'Source-backed City lookup records', 'Three actual literal records, unknown-ID behavior and exact retained Places source.', 'docusaurus/data-model/city-lookup.html', 'Expand a reference record and open its retained source.'),
        ('option-data-flow', 'Input and source options', 'Optional process Data Flow', 'An explicit data-model input enables process Data Flow. This is separate from historical typed entity-dataflow visuals.', 'docusaurus/scenarios/dashboard-save-city.html', 'Select Data Flow; no deployment or causality claim is added.'),
        ('field-stage-overview', 'Blocks and navigation', 'Field-by-stage overview', 'Inspect source-bound field use across the selected process stages.', 'docusaurus/scenarios/dashboard-save-city.html', 'Open Data Flow and inspect the field/stage matrix.'),
        ('field-stage-filters', 'Blocks and navigation', 'Stage and contract filters', 'Focus a field-use matrix on a stage or contract while keeping its evidence context.', 'docusaurus/scenarios/dashboard-save-city.html', 'Use the stage and contract filters in Data Flow.'),
        ('field-unknown', 'Blocks and navigation', 'Unknown and unmapped inventory', 'A separate inventory retains missing or unsupported field mappings rather than assigning invented ownership.', 'docusaurus/scenarios/dashboard-save-city.html', 'Inspect Unknown / unmapped in Data Flow.'),
        ('field-focused', 'Blocks and navigation', 'Focused field claims and bounded source', 'A focused field links its authored explanation to exact retained source and context.', 'docusaurus/data-model/save-city-request.html', 'Open city-id, inspect evidence and follow the process context.'),
        ('field-context-return', 'Blocks and navigation', 'Return to reading context', 'Model and source links preserve the process/field reading context when available.', 'docusaurus/data-model/city-lookup.html', 'Open a process/model link, then use its contextual return control.'),
        ('page-kafka', 'Blocks and navigation', 'Kafka producer and consumer continuation', 'Follow a real retained topic and its declared producer/consumer boundaries.', 'docusaurus/scenarios/forecasts-place-requested-consumer.html', 'Follow the place-requested topic or related producer/consumer.'),
        ('page-comparison', 'Page types', 'OpenAPI comparison and authority', 'Declared contracts, retained observations and compiler/source interpretation keep separate authority.', 'docusaurus/comparisons/places.html', 'Expand request/response evidence and compare source limits.'),
        ('option-embedded', 'Input and source options', 'Embedded source attachments', 'This demo retains embedded source. Source pages display exact revision, file, range and text digest.', 'docusaurus/sources/c267a4a78e8949194aeb00d9acfa74a5a9a90a34ddabb3a97ae3d4a7eed0a2fa.html', 'Open Complete original source binding.'),
        ('option-language-en', 'Input and source options', 'Documentation language: en or ru', 'Language is an option, not a new theme. This demo is English. Existing authored prose is not automatically translated.', 'docusaurus/help.html', 'Inspect the language and missing-translation rules.'),
    ]
    for id, category, title, description, href, action in modern:
        add(id, category, title, description, doc(href), action=action)

    gaps = [
        ('presentation-questions', 'Presentations', 'QUESTIONS reading presentation', 'Supported alongside SEQUENTIAL. No retained Weather reading-plan input in this demo explicitly selects QUESTIONS.', 'clew docs pages render --root DOCS_ROOT --snapshot SNAPSHOT --publication PUBLICATION --reading-plan QUESTIONS_PLAN_JSON --output EMPTY_OUTPUT_DIRECTORY', 'crates/clew/src/documentation/static_pages/question_reading.rs'),
        ('option-remote', 'Input and source options', 'Remote source links', 'Supported; this frozen Weather export uses embedded source. Remote mode removes automatic source attachments and source-outline diagrams; authored quotations remain. No remote Weather output is presented as demonstrated.', 'clew docs pages render --root DOCS_ROOT --snapshot SNAPSHOT --publication PUBLICATION --source-mode remote --source-map SOURCE_MAP_JSON --output EMPTY_OUTPUT_DIRECTORY', 'docs/operations/source-link-export.md'),
        ('option-export-subject', 'Input and source options', 'Selected service or process export', 'Current 0.13.48 supports --export-subject service:ID / scenario:ID only with a saved publication and remote mode. This older demo contains no such admitted export.', 'clew docs pages render --root DOCS_ROOT --snapshot SNAPSHOT --publication PUBLICATION --source-mode remote --export-subject scenario:dashboard-save-city --output EMPTY_OUTPUT_DIRECTORY', 'crates/clew/src/documentation/source_export.rs'),
        ('page-external-registry', 'Page types', 'Declared external service and process actor', 'Current 0.13.48 supports external registry information pages without source capture. This Weather input set has no externalServices registry; existing external calls do not create one.', 'clew docs external put --root DOCS_ROOT --expected-input-digest INPUT_DIGEST --input EXTERNAL_SERVICE_JSON', 'crates/clew/src/documentation/external_services.rs'),
        ('dsl-operation-queue', 'Rendering families', 'Java operation-queue DSL subtype', 'The historical real VoltDB sample demonstrates builder-chain only. No admissible operation-queue constructor/registry sample is retained. This is a demonstration gap, not an unsupported product family.', 'Requires a genuine admitted operation-queue source capture and explicit profile; no fabricated sample is generated.', 'crates/clew/src/documentation/flow_dsl.rs'),
    ]
    for id, category, title, description, cmd, file in gaps:
        add(id, category, title, description, status='DEMO_GAP', family='option', identity={'Renderer': 'Current support baseline 0.13.48; no new demo output', 'Renderer revision': CURRENT}, command_text=cmd,
            sources=[source(file)], limits=description)

    # New, bounded examples use the installed release over the old saved capture.
    # They are separate from all frozen historical exports and original acceptance.
    example_base = HERE / 'examples'
    if example_base.is_dir():
        shutil.copytree(example_base, target / 'examples')
        for frozen_manifest in example_base.glob('*/pages-manifest.json'):
            for record in read(frozen_manifest)['files']:
                rel = Path(record['path'])
                assert not rel.is_absolute() and '..' not in rel.parts
                assert 'sha256:' + sha(frozen_manifest.parent / rel) == record['digest'], record['path']
        new_inputs = [input_link('documentation/rendering/inputs/' + path.name) for path in sorted((HERE / 'inputs').glob('*.json'))]
        def actual_example(row_id, name, page_path, title, description):
            row = next((value for value in rows if value['id'] == row_id), None)
            if row is None:
                row = add(row_id, 'Blocks and navigation', title, description)
            receipt = read(example_base / name / 'demo-receipt.json')
            row.update(title=title, description=description, status='DEMO_EXAMPLE', example=SHOW + 'examples/' + name + '/' + page_path,
                       identityLabel='Official 0.13.48 · ' + receipt['status'] + ' · ' + CURRENT)
            row['recipe'].update(command=' '.join(receipt['command']),
                commandAuthority='Actual installed-launcher invocation with only private local path values replaced by labelled placeholders. No analyzer recapture was run. External declarations are explicitly authored demo inputs.',
                availability='This exact output is retained. Replaying requires an operational store containing the original capture/publication; the downloadable site alone is not that store. External declarations were changed only in an isolated store copy.',
                inputs=new_inputs + [generation_source],
                outputs=[{'label': 'Producer manifest · private output path omitted', 'href': SHOW + 'examples/' + name + '/pages-manifest.json'},
                         {'label': 'Actual command, producer and manifest projection receipt', 'href': SHOW + 'examples/' + name + '/demo-receipt.json'},
                         {'label': 'Portable frozen evidence bindings', 'href': SHOW + 'examples/' + name + '/frozen-bindings.json'}])
            row['recipe']['identity'].update({'Renderer':'0.13.48 official installed release','Renderer revision':CURRENT,
                'Snapshot':receipt['snapshot'],'Publication':receipt['publication'],'Native render status':receipt['status'],
                'Source capture':'Original retained 9b865365 capture; no re-verification. New external snapshots are declaration recompositions.'})
            row['recipe']['limits']=' '.join(receipt['limits']) + ' The public manifest omits only its private output-directory field; original digest and exact projection are recorded in the demo receipt.'
            return row
        actual_example('option-remote', 'remote-selected', 'scenarios/dashboard-save-city.html', 'Remote source links',
            'A real 0.13.48 remote export of Save City: exact GitHub source links replace automatic source attachments. Authored quotations and original evidence limits remain.')
        actual_example('option-export-subject', 'remote-selected', 'overview.html', 'Selected service or process export',
            'A real bounded remote export selects Save City plus explicit Dashboard and Places pages, preserving the receiving-service journey. Other subjects and translation gaps remain explicit in the manifest.')
        actual_example('presentation-questions', 'questions', 'scenarios/dashboard-save-city.html', 'QUESTIONS reading presentation',
            'A real QUESTIONS rendering reuses the accepted Save City blocks with presentation changed. The full-publication result is PARTIAL: pre-existing stale/unassessed narratives and translation gaps remain visible.')
        for id, title in [('page-external-registry', 'Declared external-service information'), ('process-external-actor', 'Declared external process actor')]:
            row = next((value for value in rows if value['id'] == id), None)
            if row is None:
                row = add(id, 'Blocks and navigation', title, '', status='DEMO_GAP')
            row.update(title=title, example=None, status='DEMO_GAP', identityLabel='Supported in official0.13.48 · Weather legacy-store rendering gap',
                description='Real MET declaration inputs and recompose are retained, but a new publication is blocked by missing complete source for the unrelated old dashboard-request-refresh thread. No external page or actor output is claimed demonstrated.')
            row['recipe']['inputs'] = new_inputs
            row['recipe']['outputs'] = [input_link('documentation/rendering/inputs/external-demo-gap.json', 'Actual bounded attempts and native blocker'),
                                       input_link('documentation/rendering/inputs/met-source-evidence.json', 'Exact retained MET source coordinates')]
            row['recipe']['availability'] = 'Registry/interaction/process inputs were authored only in an isolated clone. Exporting the old publication omits the new declarations. Materializing a new publication failed on an unrelated incomplete retained thread; no broad repair or recapture was undertaken.'
            row['recipe']['command'] = 'clew docs external put --root DOCS_ROOT --expected-input-digest INPUT_DIGEST --input MET_EXTERNAL_JSON\nclew docs recompose --root DOCS_ROOT --snapshot ORIGINAL_SNAPSHOT\nclew docs render --root DOCS_ROOT --snapshot RECOMPOSED_SNAPSHOT'
            row['recipe']['limits'] = 'Current product support and demonstration availability are separate. Declarations are agent-proposal metadata, not target source, runtime proof or approval. See the exact missing-callable error in the linked gap record.'


    custom = add('custom-save-city', 'Authored composition', 'Custom page · where city coordinates come from',
                 'A demo-owned HTML layout with an interactive literal lookup, per-claim evidence, exact retained sources and downloadable authored code.',
                 SHOW + 'custom-save-city.html', family='demo-composition', identity={'Renderer': 'Demo-owned HTML composition; not a clew PageFormat or reading-plan presentation', 'Renderer revision': 'Authored source and content hashes in this showcase manifest'},
                 command_text='python3 -I -S documentation/rendering/build.py --output EMPTY_OUTPUT_DIRECTORY',
                 supplied_inputs=[{'label': 'Authored HTML source', 'href': SHOW + 'source/custom-save-city.html.txt'}, {'label': 'Per-claim evidence mapping', 'href': SHOW + 'source/custom-map.json'}, generation_source],
                 outputs=[{'label': 'Showcase manifest', 'href': SHOW + 'manifest.json'}, {'label': 'Retained City model author input', 'href': doc('data-model/city-lookup.original.json')}],
                 limits='This is demo-owned metadata, not clew registration, freshness checking, semantic validation, meaning approval or runtime proof. Arbitrary CUSTOM_HTML is not an accepted reading-plan presentation.')
    custom['recipe']['source'] = [{'label': 'Actual authored HTML source', 'href': SHOW + 'source/custom-save-city.html.txt'}, {'label': 'Actual site composition source', 'href': SHOW + 'source/build.py.txt'}]
    custom['recipe']['availability'] = 'Replay the additive composition from the public Weather repository with Python 3.11+ and the frozen Docusaurus production build. No analyzer, model authoring or Codeclew upgrade is required.'
    current_policy = ROOT / 'documentation/current/publication.json'
    if current_policy.is_file():
        current = read(current_policy)
        renderer = current['renderer']
        current_producer = 'installed official release' if renderer['selection'] == 'INSTALLED_RELEASE' and current['publicReleaseClaim'] else 'local source preview; not a public release'
        current_identity = {'Renderer': renderer['version'] + ' · ' + current_producer,
                            'Renderer revision': renderer['sourceRevision']}
        current_inputs = [input_link('documentation/markdown-tables/' + name) for name in
                          ['reading-plan.json', 'data-model-plan.json', 'rendered-data-model-plan.json', 'input-provenance.json']]
        current_inputs.append(input_link('documentation/current/render.py', 'Actual current export recipe'))
        current_inputs.append(input_link('documentation/reference/service-model-links.json', 'Explicit service-to-model navigation overlay'))
        for id, title, path, description in [
            ('current-standalone', 'Current standalone HTML · Save City', 'native/scenarios/dashboard-save-city.html', 'Read the current process with Markdown tables, complete field comments and source navigation.'),
            ('current-docusaurus', 'Current Docusaurus · Save City', 'docusaurus/scenarios/dashboard-save-city', 'Read the current production MDX process, field tables and optional Data Flow.'),
            ('current-readable', 'Current authored reading · Markdown table', 'docusaurus/scenarios/dashboard-save-city#question-request', 'Open Request fields to compare the original field, readable name and complete source-bound comment.'),
            ('current-model-fields', 'Current domain fields · Place', 'docusaurus/data-model/place#fields-and-representations', 'Compare original field spelling, readable names and complete comments, then open exact evidence and representations.'),
        ]:
            row = add(id, 'Current release', title, description, BASE + 'current/' + path,
                      identity=current_identity, supplied_inputs=current_inputs,
                      outputs=[{'label': 'Current renderer and input identity', 'href': BASE + 'current/producer.json'},
                               {'label': 'Current native export manifest', 'href': BASE + 'current/native/pages-manifest.json'}],
                      sources=[source('docs/operations/markdown-and-field-tables.md', renderer['sourceRevision'])])
            row['currentRender'] = True
            producer_description = 'an installed official release' if current['publicReleaseClaim'] else 'a local source preview (not a public release)'
            row['recipe']['availability'] = 'Newly rendered from the retained publication and snapshot using ' + producer_description + '. Reproduction requires the operational documentation store; no recapture or runtime replay was performed.'
            row['recipe']['command'] = 'python3 -I -S documentation/current/render.py --root DOCS_ROOT --clew INSTALLED_CLEW --version VERSION --release-commit RELEASE_COMMIT --output EMPTY_OUTPUT_DIRECTORY'
            row['recipe']['commandAuthority'] = 'This command is a template with path placeholders. The actual export recipe and producer record are linked below.'
            if id == 'current-readable':
                row['openDisclosure'] = 'Request fields'
                row['action'] = 'Choose Show Markdown table above the reader. It opens Request fields in step 1 and scrolls to the complete table.'
        equivalents = {'block-readable': 'current-readable', 'format-standalone': 'current-standalone',
                       'format-docusaurus': 'current-docusaurus', 'page-model': 'current-model-fields'}
        for row in rows:
            if row['id'] in equivalents:
                row['currentEquivalent'] = equivalents[row['id']]
                if row['id'] == 'block-readable':
                    row['currentLinkLabel'] = 'Open current Markdown table example'
                row['title'] = 'Historical · ' + row['title']
                row['status'] = 'HISTORICAL_EXAMPLE'
    custom_map = read(HERE / 'custom-map.json')
    for reference in custom_map['sources']:
        original = read(ROOT / 'documentation/docusaurus/project/static/clew-data/objects' / (reference['object'] + '.json'))['value']
        assert all(original[key] == reference[key] for key in ['id', 'revision', 'file', 'startLine', 'endLine', 'textDigest', 'authority'])
        assert 'sha256:' + hashlib.sha256(original['text'].encode()).hexdigest() == reference['textDigest']
    for name in ['custom-save-city.html', 'custom-map.json']:
        shutil.copy2(HERE / name, source_dir / (name + '.txt' if name.endswith('.html') else name))
    (target / 'custom-save-city.html').write_text((HERE / 'custom-save-city.html').read_text())
    index = '''<div class="hero"><span class="eyebrow">Real Weather documentation · inspect the inputs</span><h1>See what clew can render.</h1><p class="lead">Choose a rendering family, explore a real example, then inspect the source, evidence and recipe that created it. Historical examples keep their original identities.</p><a class="button" href="custom-save-city.html">Explore a custom evidence-bound page</a></div>
<section class="panel section" aria-labelledby="compare"><h2 id="compare">One process. Three ways to read it.</h2><p>Follow Save City in the saved publication, standalone Pages and Docusaurus. The publication identity is shared; renderer revisions and optional editorial inputs differ. This is a comparison, not a visual-parity claim.</p><div class="format-tabs" role="group" aria-label="Rendering family"><button data-format="format-publication" aria-pressed="false">Saved publication</button><button data-format="format-standalone" aria-pressed="true">Standalone Pages</button><button data-format="format-docusaurus" aria-pressed="false">Docusaurus</button></div><div class="format-detail"><h3 id="format-title"></h3><p id="format-description"></p><p id="format-identity" class="meta"></p><div id="format-actions" class="actions"></div></div></section>
<div class="grid section"><article class="card"><span class="badge">Two PageFormat values</span><h3>Formats are containers</h3><p>Standalone HTML and Docusaurus are full Pages export formats. Native declaration selection, Flow DSL and OperationAnswer are specialized families with their own inputs.</p><a href="#inventory-heading">Browse rendering families</a></article><article class="card"><span class="badge">Optional input</span><h3>Data Flow is opt-in</h3><p>Process Data Flow and field-use matrices come from an explicit model plan. Historical typed entity-dataflow diagrams are a separate visual kind.</p><a href="recipe.html?id=option-data-flow">Inspect the model-plan recipe</a></article><article class="card"><span class="badge gap">Visible gaps</span><h3>Coverage has boundaries</h3><p>The catalogue retains 93 historical entries. Newer support and unrepresented cases are listed separately. No exhaustive cross-product or full-coverage badge is claimed.</p><a href="recipe.html?id=dsl-operation-queue">Why operation-queue has no example</a></article></div>
<section class="section" aria-labelledby="inventory-heading"><h2 id="inventory-heading">Explore the capability inventory</h2><p>Search a page type, block, diagram, option or specialized family. Every entry links to its creation record; unsupported and undemonstrated cases explain their limits.</p><div class="filters"><label class="search">Find a capability<input id="search" type="search" placeholder="Try: Kafka, field, source, sequence"></label><label>Category<select id="category"><option value="">All categories</option></select></label><label>Availability<select id="status"><option value="">All entries</option><option value="DEMO_EXAMPLE">Current demo example</option><option value="HISTORICAL_EXAMPLE">Historical example</option><option value="DEMO_GAP">Not demonstrated</option><option value="UNSUPPORTED">Unsupported prototype</option></select></label></div><p id="count" class="count" role="status"></p><div id="inventory" class="inventory"></div></section>'''
    (target / 'index.html').write_text(page('Capabilities and creation recipes', index))
    if current_policy.is_file():
        file = target / 'index.html'
        content = file.read_text().replace('data-format="format-standalone"', 'data-format="current-standalone"').replace('data-format="format-docusaurus"', 'data-format="current-docusaurus"')
        content = content.replace('<section class="panel section" aria-labelledby="compare">',
            '<section class="panel section"><h2>Current Codeclew ' + html.escape(renderer['version']) + '</h2><p>Markdown and complete domain field tables · ' + html.escape(current_producer) + '. Historical examples below retain their original producer identities.</p><div class="actions"><a class="button" href="' + BASE + 'current/native/overview.html">Latest HTML</a><a class="button secondary" href="' + BASE + 'current/docusaurus/">Latest Docusaurus</a><a href="' + BASE + 'current/">Renderer and inputs</a></div></section><section class="panel section" aria-labelledby="compare">', 1)
        file.write_text(content)
    heading = '<a href="' + SHOW + '">← Capability showcase</a><h1 id="page-title"></h1><p id="page-description" class="lead"></p>'
    (target / 'recipe.html').write_text(page('How it was made', heading + '<article id="recipe" class="panel"></article>'))
    (target / 'view.html').write_text(page('Retained example', heading + '<div id="viewer-actions" class="actions viewer-bar"></div><p id="try-action" class="note"></p><iframe id="example-frame" class="viewer" title="Retained example"></iframe>'))
    manifest = {'schema': 'weather-rendering-showcase/1.0', 'weatherBaseline': BASELINE,
                'capabilitySourceRevision': CURRENT, 'capabilityRelease': '0.13.48', 'historicalCount': len(catalogue['items']),
                'scope': 'Additive demo composition. Current product support is separate from the producer identity of every retained example.',
                'priorAcceptanceAppliesToNewPages': False, 'capabilities': rows,
                'composition': {'repository': WEATHER, 'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                                'workingTreeDirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
                                'sourceFiles': {name: sha(HERE / name) for name in ['build.py', 'site.css', 'app.js', 'custom-save-city.html', 'custom-map.json', 'docusaurus.config.mjs']}},
                'customMapping': 'source/custom-map.json', 'frozenInputsRegenerated': False}
    if current_policy.is_file():
        manifest['currentPublication'] = {'renderer': renderer, 'publicReleaseClaim': current['publicReleaseClaim'],
                                          'producer': BASE + 'current/producer.json',
                                          'defaultExamples': {'standalone': 'current-standalone', 'docusaurus': 'current-docusaurus', 'markdown': 'current-readable'}}
    write(target / 'manifest.json', manifest)
    return manifest


def compose(output, docusaurus):
    manifest = build(output)
    # Existing exporter-owned sources and their acceptance policies are never edited.
    shutil.copytree(ROOT / 'docs', output, dirs_exist_ok=True)
    shutil.copytree(docusaurus, output / 'docusaurus')
    current_build = ROOT / 'documentation/current/project/build'
    if current_build.is_dir():
        shutil.copytree(ROOT / 'documentation/current/site', output / 'current')
        shutil.copytree(current_build, output / 'current/docusaurus')
    edits, mdx_edits = [], []
    current = current_build.is_dir()
    native_paths = ['index.html', 'overview.html', 'catalog.html']
    if current:
        native_paths = sorted({*native_paths, *(item['path'] for item in read(ROOT / 'docs/pages-manifest.json')['files'] if item['path'].endswith('.html'))})
    for path in native_paths:
        file = output / path
        before = file.read_text()
        if current:
            destination = BASE + 'current/native/' + path if (output / 'current/native' / path).is_file() else BASE + 'current/native/overview.html'
            addition = historical_navigation('Historical HTML · official Codeclew 0.13.39', destination,
                                             path in {'index.html', 'overview.html', 'catalog.html'})
            body = re.search(r'<body[^>]*>', before)
            assert body, path
            after = before[:body.end()] + addition + before[body.end():]
        else:
            marker = '<div class="reader-links">'
            if before.count(marker) != 1:
                raise ValueError('Native navigation insertion point changed: ' + path)
            addition = '<a data-weather-showcase="true" href="' + SHOW + '">Rendering showcase</a>'
            after = before.replace(marker, marker + addition, 1)
        file.write_text(after)
        edits.append({'path': path, 'beforeSha256': hashlib.sha256(before.encode()).hexdigest(), 'afterSha256': sha(file), 'insertion': addition})
    assert SHOW in (output / 'docusaurus/review.html').read_text(), 'Build Docusaurus with the additive config overlay first'
    if current:
        for file in sorted((output / 'docusaurus').rglob('*.html')):
            rel = file.relative_to(output / 'docusaurus')
            destination = BASE + 'current/docusaurus/' + ('' if rel.as_posix() == 'index.html' else rel.with_suffix('').as_posix())
            if not (current_build / rel).is_file():
                destination = BASE + 'current/docusaurus/'
            before = file.read_text()
            body = re.search(r'<body[^>]*>', before)
            assert body, str(rel)
            addition = historical_navigation('Historical Docusaurus · Codeclew 0.13.46 source candidate', destination,
                                             rel.as_posix() in {'index.html', 'review.html', 'catalog.html'})
            file.write_text(before[:body.end()] + addition + before[body.end():])
            mdx_edits.append({'path': 'docusaurus/' + rel.as_posix(), 'beforeSha256': hashlib.sha256(before.encode()).hexdigest(), 'afterSha256': sha(file), 'insertion': addition})
    write(output / 'rendering/navigation-overlay.json', {'schema': 'weather-showcase-navigation/1.0', 'scope': 'Current reader entry redirects and historical-reader banners are additive navigation overlays. Frozen source, descriptions, evidence and producer identities remain unchanged.', 'changes': edits, 'docusaurusChanges': mdx_edits, 'docusaurusConfigOverlay': {'path': 'documentation/rendering/docusaurus.config.mjs', 'sha256': sha(HERE / 'docusaurus.config.mjs')}})
    return manifest


def historical_navigation(label, destination, redirect):
    banner = ('<aside data-weather-history="true" style="padding:12px 16px;border-bottom:1px solid #d9bc76;background:#fff8e7;color:#453710;font:14px/1.5 system-ui;overflow-wrap:anywhere">'
              '<strong>' + html.escape(label) + '</strong> · Original descriptions and producer identity retained. '
              '<a data-weather-current href="' + html.escape(destination) + '" style="color:#075fbd">Open the current reader</a> · '
              '<a href="' + SHOW + '" style="color:#075fbd">Rendering showcase</a> · '
              '<a href="' + BASE + 'overview.html?historical=1" style="color:#075fbd">Historical HTML overview</a></aside>')
    destination_json = json.dumps(destination)
    script = '<script data-weather-navigation="true">{const target=new URL(' + destination_json + ',location.href);target.search=location.search;target.searchParams.delete("historical");target.hash=location.hash;document.querySelector("[data-weather-current]").href=target.href;'
    if redirect:
        script += 'if(!new URLSearchParams(location.search).has("historical"))location.replace(target.href);'
    return banner + script + '}</script>'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls, self.ids = [], set()
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src'} and value:
                self.urls.append(value)
            if key == 'id':
                self.ids.add(value)


def verify(output):
    manifest = read(output / 'rendering/manifest.json')
    assert manifest['historicalCount'] == 93
    assert {x['historicalRecord']['id'] for x in manifest['capabilities'] if 'historicalRecord' in x} == {x['id'] for x in read(ROOT / 'docs/render-catalog/catalogue.json')['items']}
    assert not manifest['priorAcceptanceAppliesToNewPages']
    urls = []
    for page_path in (output / 'rendering').rglob('*.html'):
        parser = Links(); parser.feed(page_path.read_text())
        urls.extend((page_path.relative_to(output).as_posix(), url) for url in parser.urls)
    for row in manifest['capabilities']:
        if row['example']:
            urls.append(('rendering/index.html', row['example']))
        for group in ['inputs', 'outputs']:
            urls.extend(('rendering/recipe.html', item['href']) for item in row['recipe'][group])
    checked, missing, dynamic = 0, [], []
    id_cache = {}
    def declared_id(value, fragment):
        if isinstance(value, dict):
            return value.get("id") == fragment or any(declared_id(child, fragment) for key, child in value.items() if key not in {"text", "summary", "source", "sources"})
        return isinstance(value, list) and any(declared_id(child, fragment) for child in value)
    for origin, url in urls:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        path = parsed.path
        if path.startswith('/'):
            assert path.startswith(BASE), url
            relative = path[len(BASE):]
        else:
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(origin), path))
        resolved = output / unquote(relative)
        if resolved.is_dir():
            resolved /= 'index.html'
        elif not resolved.exists() and not resolved.suffix and resolved.with_suffix('.html').is_file():
            resolved = resolved.with_suffix('.html')
        if not resolved.is_file():
            missing.append({'from': origin, 'url': url, 'reason': 'missing file'})
            continue
        if parsed.fragment and resolved.suffix == '.html':
            if resolved not in id_cache:
                parser = Links(); parser.feed(resolved.read_text()); id_cache[resolved] = parser.ids
            fragment = unquote(parsed.fragment)
            if fragment not in id_cache[resolved]:
                companion = resolved.with_suffix('.json')
                if companion.is_file() and 'hashchange' in resolved.read_text():
                    payload = read(companion)
                    admitted = any(declared_id(payload.get(key), fragment) for key in ['operations', 'sections', 'notes', 'savedProcesses', 'serviceFragments', 'process'])
                    thread = payload.get('processThread') or ((payload.get('process') or {}).get('definition') or {}).get('process', {}).get('thread')
                    if thread:
                        admitted |= fragment in {'thread-source', 'thread-steps', 'thread-limits'}
                        if fragment.startswith('thread-step-'):
                            admitted |= declared_id(thread.get('steps'), fragment.removeprefix('thread-step-'))
                        if fragment.startswith('thread-contract-'):
                            admitted |= declared_id(thread.get('boundaryContracts'), fragment.removeprefix('thread-contract-'))
                    if fragment == 'process-catalog':
                        admitted |= bool(payload.get('savedProcesses')) and 'process-catalog' in resolved.read_text()
                    matching = [c for c in payload.get('contracts', []) if c.get('id') == fragment and c.get('normalized', {}).get('sourceMapping') == 'SOURCE_ROUTE_MATCH_ONLY']
                    if len(matching) == 1:
                        entry = matching[0]['normalized'].get('entrypoint')
                        admitted |= bool(entry) and any(declared_id(payload.get(key), entry) for key in ['operations', 'catalogue'])
                else:
                    admitted = False
                if admitted:
                    dynamic.append({'url': url, 'payload': str(companion.relative_to(output)), 'id': fragment})
                else:
                    missing.append({'from': origin, 'url': url, 'reason': 'missing static anchor and unknown reader payload identity'})
        checked += 1
    overlay = read(output / 'rendering/navigation-overlay.json')
    overlays = {x['path']: x for x in overlay['changes']}
    preserved = 0
    for original in (ROOT / 'docs').rglob('*'):
        if not original.is_file():
            continue
        rel = str(original.relative_to(ROOT / 'docs'))
        actual = (output / rel).read_bytes()
        if rel in overlays:
            addition = overlays[rel]['insertion'].encode()
            assert actual.count(addition) == 1
            actual = actual.replace(addition, b'', 1)
        assert actual == original.read_bytes(), rel
        preserved += 1
    for item in overlay.get('docusaurusChanges', []):
        actual = (output / item['path']).read_bytes()
        addition = item['insertion'].encode()
        assert actual.count(addition) == 1
        assert hashlib.sha256(actual.replace(addition, b'', 1)).hexdigest() == item['beforeSha256']
    result = {'status': 'PASS' if not missing else 'FAIL', 'capabilities': len(manifest['capabilities']), 'historicalEntries': 93, 'checkedLocalLinks': checked,
              'missingLinks': missing, 'dynamicPayloadAnchors': dynamic, 'preservedNativeFiles': preserved, 'navigationOnlyChanges': list(overlays),
              'historicalMdxNavigationOverlays': len(overlay.get('docusaurusChanges', [])),
              'limits': 'Focused composition, preservation and local link checks; independent browser acceptance remains separate.'}
    write(output / 'rendering/verification.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--docusaurus', type=Path, default=ROOT / 'documentation/docusaurus/project/build')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if not args.verify_only:
        compose(args.output, args.docusaurus)
    result = verify(args.output)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
