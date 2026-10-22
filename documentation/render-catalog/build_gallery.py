"""Build a research gallery from real rendered Weather blocks, without authoring behavior."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'docs/render-catalog')
parser.add_argument('--current-documentation', default='../index.html')
parser.add_argument('--orientation-only', action='store_true', help='Add local historical orientation to a retained gallery without regenerating its records')
args = parser.parse_args()
OUT = args.output.resolve()
CURRENT = html.escape(args.current_documentation, quote=True)
HISTORICAL = '<aside class="historical-orientation"><strong>Historical renderer example collection</strong><p>These retained examples document earlier renderer revisions. Counts and missing view types apply to this collection; they do not describe current Weather or Docusaurus capability coverage.</p><a href="' + CURRENT + '">Return to current documentation</a></aside>'
if args.orientation_only:
    originals = {}
    for name in ['index.html', 'conditions.html']:
        path = OUT / name
        original = path.read_text()
        originals[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if 'class="historical-orientation"' not in original:
            path.write_text(original.replace('<header>', '<header>' + HISTORICAL, 1))
    (OUT / 'orientation.json').write_text(json.dumps({
        'scope': 'Local historical-gallery orientation only; retained examples and provenance unchanged',
        'currentDocumentation': args.current_documentation, 'originalWrapperSha256': originals
    }, indent=2) + '\n')
    raise SystemExit(0)
SOURCE = '31a559851b947d5eda90afc003f2bfb2b2c27130'
PUBLIC = 'https://codeclew.github.io/clew-weather-demo/'
blocks = json.loads((ROOT / 'documentation/render-catalog/captured-blocks.json').read_text())
blocks += json.loads((ROOT / 'documentation/render-catalog/captured-coverage-blocks.json').read_text())
lookup = {(f['family'], k): (v, f['url']) for f in blocks for k, v in f['blocks'].items()}
capture_styles = {}
styles = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', (OUT / 'examples/weather/services/dashboard.html').read_text(), re.S))
# The captured publication and current native output have the same UI assets and data.
original = (ROOT / 'docs/services/dashboard.html').read_text()
current = (OUT / 'examples/weather/services/dashboard.html').read_text()
assert re.findall(r'<style[^>]*>(.*?)</style>', original, re.S) == re.findall(r'<style[^>]*>(.*?)</style>', current, re.S)
assert re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', original, re.S) == re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', current, re.S)
(OUT / 'previews').mkdir(exist_ok=True)
(OUT / 'preview.css').write_text(styles + '''\nbody{display:block!important;padding:20px!important;min-width:0!important}main{margin:0!important;padding:0!important;width:auto!important;max-width:none!important}.source-panel,[aria-label="Selected source evidence"]{position:static!important;display:block!important;width:auto!important;max-width:none!important;height:auto!important;max-height:none!important;transform:none!important}.preview-note{font:13px system-ui;color:#56665c;margin-bottom:18px}pre{max-width:100%;overflow:auto}svg{max-width:100%;height:auto}button{pointer-events:none}[hidden]{display:block!important}''')
items = []
def item(id, category, title, description, path, action='', capture=None, status='EXAMPLE', renderer='documentation/app.js'):
    row = dict(id=id, category=category, title=title, description=description, path=path, action=action, status=status, renderer=renderer)
    if capture:
        markup, url = lookup[capture]
        # Read-only excerpts: open disclosures, preserve text, resolve links to their original publication.
        markup = re.sub(r'<details\b([^>]*)>', lambda m: '<details' + re.sub(r'\sopen(?:="[^"]*")?', '', m[1]) + ' open>', markup)
        markup = re.sub(r'\shidden(?:="[^"]*")?', '', markup)
        markup = re.sub(r'(href|src)="([^"]*)"', lambda m: f'{m[1]}="{html.escape(urljoin(url, html.unescape(m[2])), quote=True)}"', markup)
        file = f'previews/{id}.html'
        stylesheet = capture_styles.get(capture, '../examples/places-native/style.css' if capture[0]=='native' else '../preview.css')
        (OUT / file).write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><link rel="stylesheet" href="{stylesheet}"><style>body{{display:block!important;margin:0!important;padding:20px!important;min-width:0!important}}main{{margin:0!important;padding:0!important;max-width:none!important}}.preview-note{{font:13px system-ui;color:#56665c;margin-bottom:18px}}pre{{max-width:100%;overflow:auto}}</style><body><p class="preview-note">Read-only excerpt from real native output. Open the full example for source interactions and review status.</p><main>{markup}</main></body></html>')
        row['preview'] = file
        row['captureUrl'] = url
        row['capturedHtmlDigest'] = 'sha256:' + hashlib.sha256(lookup[capture][0].encode()).hexdigest()
    items.append(row)
W='examples/weather/'
D=W+'services/dashboard.html'
S=W+'scenarios/dashboard-save-city.html'
C=W+'scenarios/dashboard-forecast-updated-consumer.html'
N='examples/places-native/'
# Balanced element extraction preserves the original renderer HTML without rewriting prose.
def element_at(markup, start, tag):
    depth = 0
    for match in re.finditer(r'</?' + tag + r'\b[^>]*>', markup[start:]):
        depth += -1 if match[0].startswith('</') else 1
        if depth == 0:
            return markup[start:start + match.end()]
    raise ValueError('Unbalanced captured element: ' + tag)
def element_with(markup, opening, tag):
    match = re.search(opening, markup)
    assert match, opening
    return element_at(markup, match.start(), tag)
# Page families. These links open complete native output, not a gallery reconstruction.
for id,title,path,desc in [
 ('page-overview','Documentation overview',W+'overview.html','Services and saved scenarios across the real Weather repository.'),
 ('page-catalog','Searchable catalogue',W+'catalog.html','Cross-service metadata catalogue and filters.'),
 ('page-service','Service reader',D+'#section-overview','Dashboard service sections, operations, contracts and source.'),
 ('page-operation','HTTP operation reader',D+'#dashboard-ad968c2137fedea90215','Canonical POST /api/places with behavior and Contract tabs.'),
 ('page-scenario','Interaction scenario reader',C+'#dashboard-forecast-updated-consumer','The saved forecast-updated consumer narrative.'),
 ('page-process','Source-bound process reader',S+'#process-overview','Dashboard-to-Places thread with complete retained method bodies.'),
 ('page-fragment','Receiving service fragment',W+'services/places.html#service-fragment-dashboard-save-city:places-save-handler','Places handler within the same saved thread.'),
 ('page-native','Native compiler declaration pages',N+'places-save-overview.html','Places.Save selected compiler declaration, exact call sites and source outline.'),
 ('page-syntax','Native syntax declaration pages','../variants/dashboard-consume-message/dashboard-consume-message-overview.html','Existing source-syntax consumeMessage variant. Rendered with earlier source 6f52d11; syntax authority only.'),
 ('page-sources','Native source appendix',N+'sources.html','Exact retained source fragments and reverse documentation-context links.'),
 ('page-history','Publication history',W+'history.html','Recorded publication history.'),
 ('page-help','Reader help',W+'help.html','Explanation of the native reader controls and authority labels.')]: item(id,'Pages',title,desc,path,renderer='static_pages/full.rs or static_pages/publish.rs')
for id,title,family,key,path,desc,action in [
 ('block-profile','Service profile','service','profile',D+'#section-overview','Four accepted service summaries in a profile grid.',''),
 ('block-responsibilities','Responsibilities card','service','responsibilities',D+'#section-responsibilities','Accepted responsibility prose with source and review status.',''),
 ('block-entity-summary','Entity and storage-shape summary','service','entitiesSummary',D+'#section-entities','Existing prose about shapes; this is not an entity identity or ownership model.',''),
 ('block-ingress','Entry-point summary','service','ingressSummary',D+'#section-ingress','Declared entry-point and registration summary.',''),
 ('block-egress','External calls and storage summary','service','egressSummary',D+'#section-egress','Accepted source interpretation of external calls and storage.',''),
 ('block-summary','Operation summary and trigger','consumer','summary',C+'#dashboard-forecast-updated-consumer','Accepted consumer summary and operation heading.',''),
 ('block-readable','Readable behavior','consumer','readable',C+'#dashboard-forecast-updated-consumer','Full ordered narrative with Note, If, Otherwise and Message rows; evidence button on each row.',''),
 ('diagram-sequence','Responsive sequence diagram','consumer','sequence',C+'#dashboard-forecast-updated-consumer','Visible messages and alt/else frames. Hidden Notes remain in Readable behavior.','Open “Sequence diagram”.'),
 ('block-implementation','Implementation commentary','consumer','implementation',C+'#dashboard-forecast-updated-consumer','Accepted commentary and supporting source links.','Open “Implementation details and source commentary”.'),
 ('block-scope','Scope and evidence boundaries','consumer','limits',C+'#dashboard-forecast-updated-consumer','Retained limits displayed separately from behavior.','Open “Scope and evidence boundaries”.'),
 ('block-freshness','Evidence contexts and freshness','consumer','freshness',C+'#dashboard-forecast-updated-consumer','Selected snapshot, source revisions, retained explanation context and meaning review.','Open the disclosures in Evidence contexts.'),
 ('block-kafka','Source-derived Kafka interface table','kafka-contract','contract',C+'#dashboard-forecast-updated-consumer','The real topic association and code-level event checks.','Select “Contract”.'),
 ('block-http','HTTP interpretation and OpenAPI tables','http-contract','contract',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','Source-derived interface card, request body, response schemas, constraints, declared access and raw contract.','Responses and Complete operation contract are expandable.'),
 ('block-external-call','External call details','external-call','call',D+'#dashboard-ad968c2137fedea90215','Declared target, boundary contract and provenance of the exact POST /places call.','Expand Contract and Declaration and provenance.'),
 ('block-process-intro','Process introduction','thread','introduction',S+'#process-overview','Accepted overview, trigger, participants, selected method count and declared scope.',''),
 ('block-connections','Declared service connections','thread','connections',S+'#process-overview','Real saved declarations with transport, source links and unresolved checks.',''),
 ('block-boundary','Boundary contract','thread','boundary',S+'#thread-contract-dashboard-save-http','Request, response, failure and guarantee claims bound to the two retained handlers.',''),
 ('block-steps','Nested process steps','thread','steps',S+'#thread-steps','Forward call, receiving handler and detailed source-bound steps.','Expand Detailed steps, or follow the receiving entrypoint link.'),
 ('block-branches','Guarded process branches','thread','branches',S+'#thread-step-places-save-handler','Real IF_ELSE arms of Places.Save: city is null and Otherwise.',''),
 ('block-effects','Declared effect labels','thread','effects',S+'#thread-step-dashboard-save-forward','Source-linked external-call and return labels.',''),
 ('block-thread-source','Complete selected methods','thread','source',S+'#thread-source','Both method bodies, exact line anchors, revisions and source bindings.',''),
 ('block-thread-limits','Thread scope and unresolved boundaries','thread','limits',S+'#thread-limits','Retained limits for the selected wrapper scope.',''),
 ('block-note','Imported note and separate assessment','note','note',D+'#assessment-runtime-kafka-replay','Historical real Weather replay record, its metadata and the separate accepted assessment. No current runtime rerun is implied.',''),
 ('block-source-panel','Exact source panel','evidence','source',D+'#dashboard-ad968c2137fedea90215','Exact retained source, line numbers, Git revision, text and evidence digests.','Click Source on the full operation page.'),
 ('block-process-list','Saved process cards','process-catalog','catalog',D+'#process-catalog','Existing process titles, declared triggers, freshness and authoring state.',''),
 ('block-coverage','Coverage and analysis authority','coverage','coverage',D+'#section-overview','Source counts, syntax/compiler provider details, declared interactions and revision vector.','Click “Coverage and evidence”.'),
 ('block-inventory','Source and API inventory table','inventory','inventory',D+'#section-overview','Trigger, operation, coverage and exact identity for all 12 retained Dashboard entrypoints.','Click “Source and API inventory 12”.')]: item(id,'Diagrams' if id.startswith('diagram') else 'Blocks',title,desc,path,action,(family,key))
# Individual blocks inside the real HTTP and imported-note views.
http_html,http_url=lookup[('http-contract','contract')]
for key,opening,tag in [('interface',r'<section class="contract-card"','section'),('raw',r'<details class="contract-raw"','details')]:
    lookup[('http-parts',key)]=(element_with(http_html,opening,tag),http_url)
for key,label in [('parameters','Request parameters'),('request','Request body'),('responses','Responses'),('access','Declared access and servers')]:
    lookup[('http-parts',key)]=(element_with(http_html,r'<section class="contract-section"><h3>'+label,'section'),http_url)
note_html,note_url=lookup[('note','note')]
for key,opening,tag in [('record',r'<pre class="note-original"','pre'),('metadata',r'<details','details'),('assessment',r'<section class="gap-card"','section')]:
    lookup[('note-parts',key)]=(element_with(note_html,opening,tag),note_url)
for id,title,family,key,path,desc,action in [
 ('block-http-interface','Source-derived HTTP interface card','http-parts','interface',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','The accepted interpretation and evidence table, distinct from the parsed OpenAPI fields.',''),
 ('block-request-parameters','OpenAPI request parameters','http-parts','parameters',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','This real POST operation declares no parameters; the renderer displays the empty case explicitly.',''),
 ('block-request-body','OpenAPI request body and field constraints','http-parts','request',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','Real required cityId field, string type and declared enumeration.',''),
 ('block-responses','OpenAPI response schemas','http-parts','responses',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','Declared 200, 400, 415, 500 and 503 responses. The preview opens each response.',''),
 ('block-access','Declared access and servers','http-parts','access',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','The real contract has null security and server records. This demonstrates the actual empty declaration case.',''),
 ('block-raw-contract','Complete operation contract','http-parts','raw',D+'#dashboard:contract-operation:46eb1353d8493620edc8bfcb','The retained machine-readable OpenAPI operation, opened as a disclosure.',''),
 ('block-original-note','Original imported runtime record','note-parts','record',D+'#assessment-runtime-kafka-replay','The exact historical Weather replay record, preserved without converting it to compiler evidence.',''),
 ('block-note-metadata','Imported note metadata and associations','note-parts','metadata',D+'#assessment-runtime-kafka-replay','Original classification, timestamp and captured input associations.',''),
 ('block-assessment','Separate agent assessment','note-parts','assessment',D+'#assessment-runtime-kafka-replay','Existing accepted assessment with its own evidence, review and freshness status.','')]: item(id,'Blocks',title,desc,path,action,(family,key))
# Native compiler output. All examples come from the current source launcher, retained real Places source.
for id,title,path,desc in [
 ('native-declaration','Compiler declaration and signature',N+'places-save-endpoint.html','The actual C# PlacesController.Save declaration and exact source citation.'),
 ('native-outline','Cited C# source outline',N+'places-save-endpoint.html','Actual local source structure: calls, city-null guard, BadRequest and Ok returns. A text outline, not a compiler CFG.'),
 ('native-calls','Retained exact call-site list',N+'places-save-endpoint.html','Compiler target status, exact spans and source citations for Places.Save calls.'),
 ('native-expanded','Expanded source-call bodies',N+'source-calls.html','Five real retained methods, including repository Save, InsertRequest, City and Open.'),
 ('native-context','Examined documentation context',N+'source-calls.html','Documentation-context links retained for the selected method bodies; not runtime impact.'),
 ('native-limits','Question and local limits',N+'places-save-diagnostic.html','Projection authority and unavailable behavior/state/relationship claims.'),
 ('native-source-index','Native catalogue and source index',N+'index.html','Native source index, selected declaration search and links to all output pages.')]: item(id,'Blocks',title,desc,path,renderer='static_pages/publish.rs')
native_url=PUBLIC+'render-catalog/'+N+'places-save-overview.html'
native_html=(OUT/N/'places-save-overview.html').read_text()
for key,opening in [('outline',r'<section><h3>Cited C# source outline'),('calls',r'<section><h3>Retained exact call sites')]:
    lookup[('native',key)]=(element_with(native_html,opening,'section'),native_url)
for row in items:
    if row['id'] in ['native-outline','native-calls']:
        key='outline' if row['id']=='native-outline' else 'calls'
        # Reuse the preview generation helper; replace the existing inventory row in place.
        item(row['id'],row['category'],row['title'],row['description'],row['path'],capture=('native',key),renderer=row['renderer'])
        replacement=items.pop()
        row.update(replacement)
# Supported renderers without an admissible populated Weather example. Do not substitute test fixtures.
for id,title,reason,renderer in [
 ('gap-execution','Authored execution-flow diagram','No accepted typed execution-flow visual in this Weather publication.','visuals.rs + app.js visualGraph'),
 ('gap-dependency','Authored dependency-map diagram','No accepted typed dependency-map visual in this Weather publication.','visuals.rs + app.js visualGraph'),
 ('gap-decision','Authored decision table','No accepted typed decision-table visual with hit policy in this Weather publication.','visuals.rs + app.js visualCard'),
 ('gap-state','Declared state diagram','No captured process-state model. Cannot infer business states from event names.','render.rs + app.js PROCESS'),
 ('gap-transitions','Activity on lifecycle transitions','No captured lifecycle/state model or selected lifecycle operations.','render.rs + app.js PROCESS'),
 ('gap-entity','Domain identity and ownership cards','No explicit domain entity identities or service relations in the publication. Summary prose above is a different block.','app.js section-entities'),
 ('gap-dataflow','Typed entity data-flow diagram','No declared entity-dataflow view, nodes, edges or protected annotations.','app.js dataflowDiagram'),
 ('gap-findings','Static finding cards','No populated findings arrays in the published Weather operations.','app.js findings'),
 ('gap-extraction','Extracted evidence envelope and compiler bindings','No retained processExtraction packet on these saved Weather scenarios.','app.js processExtractionCard'),
 ('gap-source-flow','Qualified local flow graph','Forecasts has a real Kotlin outline SVG, but causal=false: it is a gap placeholder, not a qualified flow example.','app.js processOutlineCard'),
 ('gap-cfg','Compiler local CFG node/edge tables','The saved Forecasts profile is source-syntax; the selected C# projection is declaration-only. Neither admits a populated compiler CFG.','static_pages/publish.rs control_flow_panel'),
 ('gap-data-state','Field/state transformation tables','No SOURCE_BEHAVIOR data-state projection in this selected demo bundle. Declaration sources are not field/state analysis.','static_pages/data_state.rs + publish.rs'),
 ('gap-bindings','Compiler argument/return mappings and accessor attempts','Exact C# call targets exist, but richer populated per-occurrence mapping/accessor panels have not been demonstrated in this bundle.','static_pages/publish.rs'),
 ('gap-handoff','Shared queue wiring and handoff/correlation','No admitted selected endpoint/worker shared-queue projection in this demo bundle.','static_pages/source/handoff.rs'),
 ('gap-authored','Native maintained paragraphs and operational instructions','No such records attached to the current native Places selection. The imported note is a separate representation.','static_pages/authored.rs + publish.rs'),
 ('gap-dsl','Java flow-DSL process pages','Weather contains TypeScript, C# and Kotlin; no real Java builder-chain/operation-queue DSL to select.','flow_dsl/publish.rs'),
 ('gap-answer','OperationAnswer business reader','No admitted, reviewed OperationAnswer demo bundle here. Its summary, outline, glossary, predicates, shared preparations, ordered/nested behavior, decision outcomes, data movement, packet-fact tables, block-evidence map, uncertainties, review provenance and source appendix require that contract. The private UpdateDeal reference is not a demo repository.','operation_answer.rs'),
 ('gap-template','Exact UpdateDeal presentation','Deferred draft on a separate branch; not in source 31a5598. The earlier Weather comparison was rejected by the user and is not an accepted design example.','deferred draft 1ad767f')]: item(id,'Coverage gaps',title,reason,'',status='NO_WEATHER_EXAMPLE',renderer=renderer)
# Extend the original inventory with populated, source-backed examples.
coverage = json.loads((ROOT / 'documentation/render-catalog/coverage-examples.json').read_text())
coverage_provenance = json.loads((OUT / 'coverage-provenance.json').read_text())
for example in coverage['items']:
    capture = tuple(example['domCapture']) if example.get('domCapture') else None
    if spec := example.get('nativeCapture'):
        source = (OUT / spec['file']).read_text()
        if spec.get('scopeOpening'):
            source = element_with(source, spec['scopeOpening'], 'section')
        capture = ('coverage', example['id'])
        lookup[capture] = (element_with(source, spec['opening'], spec['tag']), PUBLIC+'render-catalog/'+spec['file'])
        if spec.get('embeddedCss'):
            css_file = 'previews/style-'+example['id']+'.css'
            (OUT / css_file).write_text('\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', source, re.S)))
            capture_styles[capture] = Path(css_file).name
        else:
            capture_styles[capture] = '../'+spec['css']
    item(example['id'], example['category'], example['title'], example['description'], example['path'],
         capture=capture, status=example['status'], renderer=example['renderer'])
    rendered = items.pop()
    rendered.update({k:v for k,v in example.items() if k not in ['nativeCapture']})
    existing = next((row for row in items if row['id']==example['id']), None)
    if existing is None:
        items.append(rendered)
    else:
        existing.clear()
        existing.update(rendered)
conditions = json.loads((ROOT / 'documentation/render-catalog/render-conditions.json').read_text())
assert conditions['sourceRevision'] == SOURCE
assert set(conditions['items']) == {row['id'] for row in items}
for row in items:
    rule = conditions['items'][row['id']]
    assert rule['mode'] in conditions['policies']
    assert all(rule[key].strip() for key in ['requiredInputs', 'renderWhen', 'otherwise'])
    assert rule['sourceReferences']
    assert all(ref in conditions['sourceReferences'] for ref in rule['sourceReferences'])
    row['renderConditions'] = rule
(OUT / 'render-conditions.json').write_text(json.dumps(conditions, indent=2, ensure_ascii=False)+'\n')
registry = {'schema':'weather-render-catalog/1.0','sourceRevision':SOURCE,'repository':'codeclew/clew-weather-demo','scope':'Weather first; real public external examples where Weather cannot admit the renderer. No synthetic compiler fixtures or private UpdateDeal content.','renderingPolicies':conditions['policies'],'conditionSources':conditions['sourceReferences'],'items':items}
(OUT/'catalogue.json').write_text(json.dumps(registry,indent=2)+'\n')
# Source recipe/provenance stays separate from the visual wrapper.
prov = {'schema':'weather-render-catalog-provenance/1.0','sourceRevision':SOURCE,'launcher':'SOURCE_BUILD ./clew','snapshot':'sha256:9b865365a0095af0f38eb4a8440069643404e40f2ec19c5b9397a126a84f1b40/86956','publication':'14e7b47bb795b5ff5f95ebd9b24b783d1fd18e6eeda962b31cd5edc5e6bf38a8','nativeBundles':[str(p.relative_to(OUT)) for p in sorted((OUT/'examples').glob('*/pages-manifest.json'))]+[str(p.relative_to(OUT)) for p in sorted((OUT/'examples').glob('*/manifest.json'))],'previewAuthority':'READ_ONLY_EXCERPTS_OF_REAL_NATIVE_OUTPUT_NOT_A_NEW_CLEW_TEMPLATE','previewChanges':['Extract displayed HTML blocks','Open disclosures','Resolve original source links','Make source panel static inside preview'],'capturedUiAssetsMatchCurrentNativeOutput':True,'businessProseAuthored':True,'newAuthoring':'Luna Max; accepted typed visuals, an unassessed dataflow, an approved GET answer and an explicitly unreviewed refresh draft. Existing accepted Weather prose is preserved.','coverageEvidence':'coverage-provenance.json','fullReaderCommand':['./clew','docs','pages','render','--root','DOCS_ROOT','--snapshot','SNAPSHOT','--publication','PUBLICATION','--output','docs/render-catalog/examples/weather'],'nativeCommand':['./clew','docs','pages','render','--root','DOCS_ROOT','--snapshot','SNAPSHOT','--input','documentation/render-catalog/places-selection.json','--output','EMPTY_OUTPUT_DIRECTORY'],'existingProvenance':['../render-provenance.json','../guide-provenance.json'],'captureDigest':'sha256:'+hashlib.sha256((ROOT/'documentation/render-catalog/captured-blocks.json').read_bytes()).hexdigest(),'coverageCaptureDigest':'sha256:'+hashlib.sha256((ROOT/'documentation/render-catalog/captured-coverage-blocks.json').read_bytes()).hexdigest()}
prov['renderingConditions'] = {'metadata':'render-conditions.json','sourceRevision':SOURCE,'authority':'SOURCE_RESEARCH_NOT_NEW_NATIVE_OUTPUT_OR_MEANING_REVIEW','itemCount':len(conditions['items']),'digest':'sha256:'+hashlib.sha256((ROOT/'documentation/render-catalog/render-conditions.json').read_bytes()).hexdigest()}
(OUT/'provenance.json').write_text(json.dumps(prov,indent=2)+'\n')
css='''*{box-sizing:border-box}body{margin:0;background:#f4f6f3;color:#173429;font:16px/1.5 system-ui,sans-serif}header,main,footer{max-width:1320px;margin:auto;padding:24px}header{padding-top:48px}h1{font-size:clamp(30px,4vw,48px);line-height:1.1;margin:12px 0}h2{font-size:24px}p{max-width:85ch}a{color:#25634e;text-underline-offset:3px}.eyebrow{font-size:12px;letter-spacing:.1em;text-transform:uppercase}.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:24px}input,select{font:inherit;padding:12px;border:1px solid #becdbf;border-radius:8px;background:white}input{flex:1;min-width:200px}.counts{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}.counts span{border:1px solid #cfdbd0;padding:8px 12px;border-radius:99px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,380px),1fr));gap:20px}.card{background:white;border:1px solid #cbd9cd;border-radius:14px;padding:20px;min-width:0;scroll-margin-top:20px}.card h3{font-size:20px;margin:8px 0}.card p{font-size:14px}.tag{font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:#506b5b}.gap{background:#fff9eb}.card iframe{width:100%;height:430px;border:1px solid #dde5dc;border-radius:8px;margin:14px 0;background:#fffdf8}.action{color:#5b665e}.muted{color:#597063}summary{cursor:pointer}.card[hidden]{display:none}.native-link{font-weight:600}.diagram-preview{width:100%;max-height:480px;object-fit:contain;margin:14px 0;border:1px solid #dde5dc;background:#fffdf8}.source-ref{font:12px ui-monospace,monospace;overflow-wrap:anywhere}nav{display:flex;gap:14px;flex-wrap:wrap}button{font:inherit;padding:10px 14px;cursor:pointer;border:1px solid #becdbf;border-radius:8px;background:white}footer{padding-bottom:48px}@media(max-width:600px){header,main,footer{padding:18px}.card iframe{height:360px}}'''
css+='''\n.render-conditions{margin:16px 0;padding:14px;border:1px solid #cedbd1;border-radius:8px;background:#f6f9f5}.render-conditions summary{font-weight:650}.condition-fields{margin:12px 0;font-size:14px}.condition-fields dt{font-weight:650;margin-top:12px}.condition-fields dd{margin:3px 0 0;overflow-wrap:anywhere}.condition-rule{font-size:14px}.condition-sources{font-size:12px}.policy{scroll-margin-top:24px}.conditions-grid .card{scroll-margin-top:24px}.conditions-grid .card h2{font-size:20px;margin:8px 0}code{overflow-wrap:anywhere}'''
(OUT/'gallery.css').write_text(css)
def condition_markup(row):
    rule = row['renderConditions']
    labels = [('requiredInputs','Required inputs'),('renderWhen','Shows populated content when'),('otherwise','If inputs are missing or rejected'),('limits','Authority and limits')]
    fields = ''.join(f'<dt>{label}</dt><dd>{html.escape(rule[key])}</dd>' for key,label in labels if rule.get(key))
    sources = []
    for ref in rule['sourceReferences']:
        source = conditions['sourceReferences'][ref]
        revision = source.get('sourceRevision', SOURCE)
        sources.append(f'<li><code>{html.escape(source["path"])}:{source["line"]}</code> · {html.escape(source["symbol"])} · {revision[:7]}</li>')
    revision = rule.get('sourceRevision', SOURCE)
    return f'<p class="condition-rule">Common admission rule: <a href="conditions.html#mode-{rule["mode"]}">{html.escape(conditions["policies"][rule["mode"]]["title"])}</a>.</p><dl class="condition-fields">{fields}</dl><details class="condition-sources"><summary>Source of this rule · {revision[:7]}</summary><ul>{"".join(sources)}</ul></details>'
cards=[]
for r in items:
    preview = f'<iframe loading="lazy" sandbox="allow-same-origin" title="{html.escape(r["title"])} preview" src="{r["preview"]}"></iframe>' if 'preview' in r else ''
    if media := r.get('media'):
        preview = f'<a href="{media}" target="_blank"><img class="diagram-preview" src="{media}" alt="{html.escape(r["title"])}"></a>'
    links = f'<p><a class="native-link" href="{html.escape(r["path"],quote=True)}" target="_blank" rel="noopener">Open full native example ↗</a></p>' if r['path'] else ''
    if r['path'] and not preview:
        links+=f'<details><summary>Show live page preview</summary><iframe loading="lazy" title="{html.escape(r["title"])}" src="{html.escape(r["path"],quote=True)}"></iframe></details>'
    if evidence := r.get('evidence'):
        links += f'<p><a href="{evidence}">Exact evidence record</a></p>'
    repository = r.get('repository', 'Weather')
    badge = repository+' · '+r['status'].replace('_',' ').lower() if r['id'].startswith('gap-') or 'repository' in r else 'Real Weather example'
    render_conditions = f'<details class="render-conditions"><summary>When it renders</summary>{condition_markup(r)}</details>'
    preview = render_conditions + preview
    cards.append(f'<article id="{r["id"]}" class="card {"gap" if not r["path"] else ""}" data-category="{r["category"]}"><div class="tag">{r["category"]} · {html.escape(badge)}</div><h3><a href="#{r["id"]}">{html.escape(r["title"])}</a></h3><p>{html.escape(r["description"])}</p>{preview}{links}<p class="action">{html.escape(r["action"])}</p><details><summary>Renderer and provenance</summary><p class="source-ref">{html.escape(r["renderer"])}</p><a href="provenance.json">Catalogue provenance</a>{" · <a href="+chr(34)+"previews/"+r["id"]+".html"+chr(34)+" target="+chr(34)+"_blank"+chr(34)+">Open block excerpt</a>" if r.get("preview") else ""}</details></article>')
counts={c:sum(i['category']==c for i in items) for c in ['Pages','Blocks','Diagrams','Coverage gaps','Deferred']}
(OUT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Weather · render catalogue</title><link rel="stylesheet" href="gallery.css"><header>'''+HISTORICAL+'''<div class="eyebrow">Codeclew rendering research · actual demo repository</div><h1>Rendering catalogue, from real repositories</h1><p>Browse pages, isolated blocks and diagrams produced by Codeclew. The base examples use source-built Codeclew <code>31a5598</code>. Weather is used wherever its real source admits the renderer; Petclinic supplies Java flow and Kotlin accessor examples. Existing accepted descriptions and provenance are preserved. New authored examples state their review status.</p><p class="muted">This gallery is a research wrapper. Block previews are read-only excerpts of the existing reader, with disclosures opened. The full example retains interactive source links and complete provenance. Of the original 18 gaps, 15 now have real examples, two remain open, and the unsupported UpdateDeal prototype is listed separately. The 15 include the OperationAnswer family; its richer refresh draft is explicitly unreviewed.</p><nav><a href="examples/weather/overview.html">Native Weather overview ↗</a><a href="examples/places-native/places-save-overview.html">New C# source example ↗</a><a href="catalogue.json">Machine-readable inventory</a><a href="provenance.json">Provenance</a></nav><div class="counts">'''+''.join(f'<span>{n} {c}</span>' for c,n in counts.items())+'''</div><div class="tools"><input id="search" type="search" aria-label="Find a page, block or diagram" placeholder="Find a page, block or diagram"><select id="category" aria-label="Category"><option value="">All categories</option><option>Pages</option><option>Blocks</option><option>Diagrams</option><option>Coverage gaps</option><option>Deferred</option></select><button id="reset">Reset filters</button><span id="visible-count" aria-live="polite"></span></div></header><main><div class="grid">'''+''.join(cards)+'''</div></main><footer><p>Preserved source and narrative authority: exact snapshot text, source structure, compiler declarations, authored interpretation and historical runtime notes remain distinct. A gallery example is not a new review or runtime verification.</p><p>UpdateDeal design work is deferred. Its private reference and the rejected comparison are not counted as accepted Weather templates.</p></footer><script>const cards=[...document.querySelectorAll('.card[data-category]')], search=document.getElementById('search'), category=document.getElementById('category');function filter(){let count=0;for(const c of cards){c.hidden=!(c.textContent.toLowerCase().includes(search.value.toLowerCase())&&(!category.value||c.dataset.category===category.value));if(!c.hidden)count++}document.getElementById('visible-count').textContent=count+' historical examples in this collection'}search.addEventListener('input',filter);category.addEventListener('change',filter);document.getElementById('reset').addEventListener('click',()=>{search.value='';category.value='';filter()});filter()</script></html>''')
print('Catalogue:',len(items),'items',counts)

# A text-only companion makes all rules readable without loading example iframes.
index_path = OUT / 'index.html'
index_html = index_path.read_text()
resolution = coverage_provenance['originalGapResolution']
index_html = index_html.replace('Of the original 18 gaps, 15 now have real examples, two remain open, and the unsupported UpdateDeal prototype is listed separately. The 15 include the OperationAnswer family; its richer refresh draft is explicitly unreviewed.', f'Of the original {resolution["original"]} gaps, {resolution["withRealExamples"]} now have real examples, {resolution["open"]} remain open, and the unsupported UpdateDeal prototype is listed separately. The real examples include the OperationAnswer family; its richer refresh draft is explicitly unreviewed.')
index_html = index_html.replace('Petclinic supplies Java flow and Kotlin accessor examples.', 'Petclinic supplies Java flow and Kotlin accessor examples. The Mjedynak queue example retains its exact upstream Java files in an explicitly separate Java 17 capture build. Additional examples identify their own source renderer revision in provenance.')
index_html = index_html.replace('New authored examples state their review status.', 'New authored examples state their review status. VoltDB contributes its unchanged OrderProc callback chain, rendered with source-built ac55263.')
index_html = index_html.replace('</p><nav>', '</p><p class="muted">Example coverage is counted by catalogue entry. The real Java DSL sample demonstrates builder-chain construction; the separate operation-queue family still has no admissible real sample. <a href="voltdb-dsl-provenance.json">DSL coverage and limits</a>.</p><nav>', 1)
index_html = index_html.replace('<nav><a href="examples/weather/overview.html">', '<p class="condition-rule">Every card now includes <b>When it renders</b>: required data, the populated-content condition, missing-data behavior and source-backed limits. <a href="conditions.html">Read all 93 rendering conditions without previews →</a></p><nav><a href="conditions.html">Rendering conditions · all 93 types</a><a href="examples/weather/overview.html">', 1)
index_path.write_text(index_html)
policy_cards = []
for key, policy in conditions['policies'].items():
    fields = ''.join(f'<dt>{label}</dt><dd>{html.escape(policy[field])}</dd>' for field,label in [('inputs','Input route'),('gate','Admission'),('limits','Limits')])
    policy_cards.append(f'<details class="card policy" id="mode-{key}"><summary>{html.escape(policy["title"])}</summary><dl class="condition-fields">{fields}</dl></details>')
condition_cards = []
for row in items:
    example = f'<p><a href="{html.escape(row["path"], quote=True)}">Open real native example ↗</a></p>' if row['path'] else '<p>No admissible real example is currently linked.</p>'
    condition_cards.append(f'<article class="card" id="{row["id"]}" data-category="{row["category"]}"><div class="tag">{html.escape(row["category"])}</div><h2><a href="#{row["id"]}">{html.escape(row["title"])}</a></h2>{condition_markup(row)}{example}<p><a href="index.html#{row["id"]}">View catalogue card and provenance</a></p></article>')
tools_html = re.search(r'<div class="tools">.*?</div></header>', index_html, re.S)[0].removesuffix('</header>')
filter_script = re.search(r'<script>const cards=.*?</script>', index_html, re.S)[0]
(OUT / 'conditions.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Weather · rendering conditions</title><link rel="stylesheet" href="gallery.css"><header>'+HISTORICAL+'<div class="eyebrow">Source-backed rendering research · '+SOURCE[:7]+'</div><h1>When each documentation type renders</h1><p>Conditions for every one of the 93 catalogue entries: pages, blocks and diagrams, including the two supported families still lacking a real demo and the unsupported deferred template. Each rule states the required input, the condition for populated content, and what happens when data is absent or rejected.</p><p>A page shell or a gap placeholder is not a populated example. Rendering, source freshness, meaning review and runtime verification are separate. These rules describe source revision <code>'+SOURCE+'</code>; they do not create or modify native output, accepted business prose or provenance.</p><nav><a href="index.html">Examples catalogue</a><a href="render-conditions.json">Machine-readable conditions</a><a href="provenance.json">Provenance</a></nav><h2>Common admission rules</h2><p>Each entry below names one of these routes. Apply its admission rule before the entry-specific display condition.</p><div class="grid">'+''.join(policy_cards)+'</div><h2>All 93 types</h2>'+tools_html+'</header><main><div class="grid conditions-grid">'+''.join(condition_cards)+'</div></main><footer><p>Rule references name the implementation file, line and function at the recorded source revision. Optional blocks remain optional; absence of a block does not prove absence of the underlying business behavior.</p></footer>'+filter_script+'</html>')
condition_path = OUT / 'conditions.html'
condition_path.write_text(condition_path.read_text().replace('including the two supported families still lacking a real demo and the unsupported deferred template', f'including {resolution["open"]} open coverage entries and the unsupported deferred template').replace('These rules describe source revision', 'Unless an entry states a newer renderer revision, these rules describe source revision'))
