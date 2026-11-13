"""Reader landing page; publication identities come from retained manifests."""
import hashlib
import html
import json

BASE = '/clew-weather-demo/'


def render(root, human):
    previous = json.loads((root / 'documentation/current/publication.json').read_text())
    language = human.get('language', 'ru')
    if language not in ('en', 'ru'):
        raise ValueError('Unsupported human guide language')

    def t(ru, en):
        return ru if language == 'ru' else en

    esc = html.escape
    previous_version = esc(previous['renderer']['version'])
    revision = esc(human['source']['revision'])
    entry = BASE + 'human/' + esc(human['entrypoint'], quote=True)
    classic = BASE + 'generated/' + previous['publication'] + '/overview.html'
    schema = human.get('schema', 'weather-human-publication/1.0')
    if schema not in ('weather-human-publication/1.0', 'weather-human-publication/1.1'):
        raise ValueError('Unsupported human publication schema')
    if schema == 'weather-human-publication/1.1':
        # Acquisition is official; the independent skill treatment is not a release.
        identity = ''
        capture = human['capture']
        producer = capture['producerVersion'] or t('не записана', 'unrecorded')
        rows = [
            t('Версия производителя захвата: ', 'Capture producer version: ') + producer,
            t('Снимок: ', 'Snapshot: ') + capture['snapshot'],
            t('Повторный захват не выполнялся.', 'No source recapture was performed.'),
            t('Официальный runtime чтения: Codeclew ', 'Official acquisition runtime: Codeclew ') + human['acquisition']['version'],
            t('Принятый неопубликованный навык: ', 'Accepted unreleased skill treatment: ') + human['treatment']['commit'],
            t('Дерево навыка: ', 'Treatment tree: ') + human['treatment']['tree'],
            t('Отпечаток навыка: ', 'Skill digest: ') + human['treatment']['skillDigest'],
            t('Экспорт: ', 'Export: ') + str(human['export']['fileCount']) + t(' файлов · ', ' files · ') + human['export']['digest'],
        ]
        build_details = '<ul>' + ''.join('<li>' + esc(row) + '</li>' for row in rows) + '</ul>'
    else:
        version = esc(human['renderer']['version'])
        identity = t('Собрано Codeclew ', 'Generated with Codeclew ') + version + ' · '
        build_details = ''

    # Choose only destinations present in the admitted reader file map. Historical
    # and current names coexist here; a missing task is omitted, never guessed.
    files = human.get('filesSha256', {})
    tasks = [
        (('process-add-place.html', 'dashboard-save-place-route.html'),
         t('Что происходит после выбора города?', 'What happens after choosing a city?'),
         t('Проследить сохранение города от Dashboard до Places.', 'Follow the request from Dashboard to Places.'),
         t('Сохранение города →', 'Add a place →')),
        (('process-refresh-place.html', 'event-flow.html'),
         t('Как обновляется прогноз?', 'How does a forecast refresh?'),
         t('Проследить запрос обновления и передачу событий.', 'Follow the refresh request and its events.'),
         t('Обновление прогноза →', 'Refresh a forecast →')),
        (('forecast-data.html', 'events-data.html'),
         t('Какие данные передаются?', 'What data is exchanged?'),
         t('Посмотреть представления данных и назначение полей.', 'Inspect data representations and field meanings.'),
         t('Данные и поля →', 'Data and fields →')),
    ]
    cards = []
    for candidates, title, description, label in tasks:
        target = next((name for name in candidates if name in files), None)
        if target is not None:
            cards.append(f'<article class="card"><h3>{title}</h3><p>{description}</p><a href="{BASE}human/{target}">{label}</a></article>')
    task_section = (f'<section class="section" aria-labelledby="tasks"><h2 id="tasks">{t("Найти ответ", "Find an answer")}</h2>'
                    + '<div class="grid">' + ''.join(cards) + '</div></section>') if cards else ''
    return f'''<!doctype html>
<html lang="{language}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{t('Weather — документация и форматы', 'Weather — documentation and formats')}</title>
<link rel="icon" href="{BASE}human/favicon.svg">
<link rel="stylesheet" href="{BASE}rendering/site.css"></head>
<body>
<header><nav aria-label="{t('Основная навигация', 'Main navigation')}"><a class="brand" href="{BASE}">Weather / {t('Документация', 'Documentation')}</a>
<a href="{entry}">{t('Руководство', 'Guide')}</a><a href="#formats">{t('Другие форматы', 'Other formats')}</a><a href="{BASE}rendering/">{t('Примеры рендеринга', 'Rendering examples')}</a></nav></header>
<main id="content">
<section class="hero" aria-labelledby="welcome"><p class="eyebrow">{t('Демо Codeclew · Weather', 'Codeclew demo · Weather')}</p>
<h1 id="welcome">{t('Как устроен Weather', 'How Weather works')}</h1>
<p class="lead">{t('Сохранение города, обновление прогноза и передача событий между Dashboard, Places и Forecasts. Выберите руководство для чтения или другой формат для сравнения.', 'Adding a place, refreshing its forecast and passing events between Dashboard, Places and Forecasts. Start with the guide or compare the other formats.')}</p>
<div class="panel"><span class="badge">{t('Рекомендуем начать здесь', 'Start here')}</span>
<h2>{t('Актуальное руководство', 'Current guide')}</h2>
<p>{t('Последовательные объяснения процессов, страницы сервисов, HTTP-входы, Kafka-переходы и таблицы полей. На русском языке; ссылки на исходники доступны рядом с объяснениями.', 'Step-by-step processes, service pages, HTTP entries, Kafka interactions and field tables. Written in English, with source links alongside the explanations.')}</p>
<p class="meta">{identity}{t('исходники Weather', 'Weather source')} <a href="https://github.com/codeclew/clew-weather-demo/tree/{revision}">{revision[:8]}</a></p>
<a class="button" href="{entry}">{t('Читать руководство →', 'Read the guide →')}</a></div>
</section>
{task_section}
<section class="section" aria-labelledby="formats"><h2 id="formats">{t('Другие форматы документации', 'Other documentation formats')}</h2>
<p>{t('Это сохранённые сборки для сравнения. Их состав и описания могут отличаться от актуального руководства.', 'These are retained exports for comparison. Their coverage and explanations may differ from the current guide.')}</p>
<div class="grid">
<article class="card"><span class="badge">{t('Предыдущая сборка', 'Previous export')} · {previous_version} · EN</span><h3>Pages · standalone HTML</h3><p>{t('Готовый статический сайт: процессы, контракты, модель данных и дополнительный Data Flow использования полей в сценариях сохранения города и обновления карточки.', 'Static pages with processes, contracts, a data model and additional field Data Flow views for saving a place and updating its card.')}</p><a href="{BASE}current/native/overview.html">{t('Открыть HTML Pages →', 'Open HTML Pages →')}</a></article>
<article class="card"><span class="badge">{t('Предыдущая сборка', 'Previous export')} · {previous_version} · EN</span><h3>Pages · MDX / Docusaurus</h3><p>{t('Документация в оболочке Docusaurus: страницы и боковая навигация, перекрёстные ссылки, модель данных и дополнительный Data Flow тех же сценариев.', 'The same scenarios in Docusaurus, with sidebar navigation, cross-links, a data model and additional Data Flow views.')}</p><a href="{BASE}current/docusaurus/">{t('Открыть Docusaurus →', 'Open Docusaurus →')}</a></article>
<article class="card"><span class="badge">{t('Архив', 'Archive')} · EN</span><h3>{t('Классический docs render', 'Classic docs render')}</h3><p>{t('Прежний интерфейс с разделами сервисов, операциями и сохранёнными процессами. Точная версия производителя этого снимка не записана.', 'The earlier interface with service sections, operations and saved processes. The exact producer version was not recorded.')}</p><a href="{classic}">{t('Открыть классический вид →', 'Open the classic view →')}</a></article>
</div>
<p class="meta">{t('Data Flow использования полей есть в предыдущих Pages-сборках. В актуальном руководстве представлены таблицы полей и поток событий; отдельный Data Flow туда не перенесён.', 'Field Data Flow views remain in the previous Pages exports. The current guide has field tables and event flows; it does not include those separate Data Flow views.')}</p>
</section>
<section class="section" aria-labelledby="examples"><h2 id="examples">{t('Возможности и история', 'Examples and history')}</h2>
<p><a href="{BASE}rendering/">{t('Каталог рендеринга', 'Rendering catalog')}</a> — {t('примеры страниц, блоков, диаграмм и способов их создания. Каталог объединяет материалы разных версий; это витрина возможностей, а не единая актуальная сборка.', 'examples of pages, blocks, diagrams and how to create them. It combines material from different versions as a feature showcase.')}</p>
<details><summary>{t('Архив и сведения о сборке', 'Archive and build details')}</summary>{build_details}<ul>
<li><a href="{BASE}render-catalog/index.html">{t('Исторический каталог блоков', 'Historical block catalog')}</a></li>
<li><a href="{BASE}history.html">{t('История документации', 'Documentation history')}</a></li>
<li><a href="{BASE}human-history/0.14.8-186544d2/index.html">{t('Предыдущее руководство', 'Previous human guide')} · 0.14.8 · RU</a></li>
<li><a href="{BASE}retained-index.html">{t('Прежняя стартовая страница', 'Previous landing page')}</a></li>
<li><a href="{BASE}human/publication.json">{t('Версия и состав актуального руководства', 'Current guide version and files')}</a></li>
</ul><p>{t('«Актуальное» означает последнюю опубликованную сборку на этом сайте. Её привязки зафиксированы на указанной ревизии исходников; работа развёрнутой системы здесь не проверяется.', 'Current means the latest published guide on this site. Its source bindings refer to the recorded revision; deployed system behavior is not verified here.')}</p></details>
</section></main>
<footer><div>{t('Weather — публичный демо-проект Codeclew.', 'Weather is a public Codeclew demo.')} <a href="https://github.com/codeclew/clew-weather-demo">{t('Репозиторий', 'Repository')}</a></div></footer>
</body></html>'''


def stage(output, root, human):
    if not human:
        return None
    original = output / 'index.html'
    retained = output / 'retained-index.html'
    if retained.exists():
        raise ValueError('Retained landing destination already exists')
    original.rename(retained)
    original.write_text(render(root, human))
    return {'path': 'index.html', 'original': 'retained-index.html',
            'beforeSha256': hashlib.sha256(retained.read_bytes()).hexdigest(),
            'afterSha256': hashlib.sha256(original.read_bytes()).hexdigest()}


def verify(output, record):
    if record is None:
        return
    assert record['path'] == 'index.html'
    assert record['original'] == 'retained-index.html'
    for key, digest in [('path', 'afterSha256'), ('original', 'beforeSha256')]:
        assert hashlib.sha256((output / record[key]).read_bytes()).hexdigest() == record[digest]
