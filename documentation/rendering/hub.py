"""Reader landing page; publication identities come from retained manifests."""
import hashlib
import html
import json

BASE = '/clew-weather-demo/'


def render(root, human):
    previous = json.loads((root / 'documentation/current/publication.json').read_text())
    version = html.escape(human['renderer']['version'])
    previous_version = html.escape(previous['renderer']['version'])
    revision = html.escape(human['source']['revision'])
    entry = BASE + 'human/' + html.escape(human['entrypoint'], quote=True)
    classic = BASE + 'generated/' + previous['publication'] + '/overview.html'
    return f'''<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Weather — документация и форматы</title>
<link rel="icon" href="{BASE}human/favicon.svg">
<link rel="stylesheet" href="{BASE}rendering/site.css"></head>
<body>
<header><nav aria-label="Основная навигация"><a class="brand" href="{BASE}">Weather / Документация</a>
<a href="{entry}">Руководство</a><a href="#formats">Другие форматы</a><a href="{BASE}rendering/">Примеры рендеринга</a></nav></header>
<main id="content">
<section class="hero" aria-labelledby="welcome"><p class="eyebrow">Демо Codeclew · Weather</p>
<h1 id="welcome">Как устроен Weather</h1>
<p class="lead">Сохранение города, обновление прогноза и передача событий между Dashboard, Places и Forecasts. Выберите руководство для чтения или другой формат для сравнения.</p>
<div class="panel"><span class="badge">Рекомендуем начать здесь</span>
<h2>Актуальное руководство</h2>
<p>Последовательные объяснения процессов, страницы сервисов, HTTP-входы, Kafka-переходы и таблицы полей. На русском языке; ссылки на исходники доступны рядом с объяснениями.</p>
<p class="meta">Собрано Codeclew {version} · исходники Weather <a href="https://github.com/codeclew/clew-weather-demo/tree/{revision}">{revision[:8]}</a></p>
<a class="button" href="{entry}">Читать руководство →</a></div>
</section>
<section class="section" aria-labelledby="tasks"><h2 id="tasks">Найти ответ</h2>
<div class="grid">
<article class="card"><h3>Что происходит после выбора города?</h3><p>Проследить сохранение города от Dashboard до Places.</p><a href="{BASE}human/dashboard-save-place-route.html">Сохранение города →</a></article>
<article class="card"><h3>Как обновляется прогноз?</h3><p>Понять передачу событий через Kafka и обновление карточки Dashboard.</p><a href="{BASE}human/event-flow.html">Сквозной поток событий →</a></article>
<article class="card"><h3>Какие данные передаются?</h3><p>Посмотреть структуру событий и назначение полей.</p><a href="{BASE}human/events-data.html">Данные и поля →</a></article>
</div></section>
<section class="section" aria-labelledby="formats"><h2 id="formats">Другие форматы документации</h2>
<p>Это сохранённые сборки для сравнения. Они не пересобраны на {version} и могут отличаться составом и описаниями от актуального руководства.</p>
<div class="grid">
<article class="card"><span class="badge">Предыдущая сборка · {previous_version} · EN</span><h3>Pages · standalone HTML</h3><p>Готовый статический сайт: процессы, контракты, модель данных и дополнительный Data Flow использования полей в сценариях сохранения города и обновления карточки.</p><a href="{BASE}current/native/overview.html">Открыть HTML Pages →</a></article>
<article class="card"><span class="badge">Предыдущая сборка · {previous_version} · EN</span><h3>Pages · MDX / Docusaurus</h3><p>Документация в оболочке Docusaurus: страницы и боковая навигация, перекрёстные ссылки, модель данных и дополнительный Data Flow тех же сценариев.</p><a href="{BASE}current/docusaurus/">Открыть Docusaurus →</a></article>
<article class="card"><span class="badge">Архив · EN</span><h3>Классический docs render</h3><p>Прежний интерфейс с разделами сервисов, операциями и сохранёнными процессами. Точная версия производителя этого снимка не записана.</p><a href="{classic}">Открыть классический вид →</a></article>
</div>
<p class="meta">Data Flow использования полей есть в предыдущих Pages-сборках. В актуальном руководстве представлены таблицы полей и поток событий; отдельный Data Flow туда не перенесён.</p>
</section>
<section class="section" aria-labelledby="examples"><h2 id="examples">Возможности и история</h2>
<p><a href="{BASE}rendering/">Каталог рендеринга</a> — примеры страниц, блоков, диаграмм и способов их создания. Каталог объединяет материалы разных версий; это витрина возможностей, а не единая актуальная сборка.</p>
<details><summary>Архив и сведения о сборке</summary><ul>
<li><a href="{BASE}render-catalog/index.html">Исторический каталог блоков</a></li>
<li><a href="{BASE}history.html">История документации</a></li>
<li><a href="{BASE}retained-index.html">Прежняя стартовая страница</a></li>
<li><a href="{BASE}human/publication.json">Версия и состав актуального руководства</a></li>
</ul><p>«Актуальное» означает последнюю опубликованную сборку на этом сайте. Её привязки зафиксированы на указанной ревизии исходников; работа развёрнутой системы здесь не проверяется.</p></details>
</section></main>
<footer><div>Weather — публичный демо-проект Codeclew. <a href="https://github.com/codeclew/clew-weather-demo">Репозиторий</a></div></footer>
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
