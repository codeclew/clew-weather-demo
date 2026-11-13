"""Reader entry and archive preservation regression checks."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

HUB = runpy.run_path(str(Path(__file__).resolve().with_name('hub.py')))


class HubTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'output'
        self.output.mkdir()
        self.original = b'<!doctype html><h1>Retained entry</h1>\n'
        (self.output / 'index.html').write_bytes(self.original)
        policy = self.root / 'documentation/current/publication.json'
        policy.parent.mkdir(parents=True)
        policy.write_text(json.dumps({'renderer': {'version': '0.2.0'}, 'publication': 'a' * 64}))
        self.human = {'renderer': {'version': '0.3.0'}, 'source': {'revision': 'b' * 40},
                      'entrypoint': 'start.html', 'language': 'ru', 'filesSha256': {
                          name: 'c' * 64 for name in ['start.html', 'dashboard-save-place-route.html',
                                                    'event-flow.html', 'events-data.html']}}

    def separate_treatment(self):
        return {'schema': 'weather-human-publication/1.1', 'language': 'en',
                'capture': {'producerVersion': '0.1.0', 'snapshot': 'sha256:' + 'c' * 64 + '/100',
                            'recaptured': False},
                'acquisition': {'version': '0.4.0'},
                'treatment': {'commit': 'd' * 40, 'tree': 'e' * 40, 'skillDigest': 'sha256:' + 'f' * 64},
                'export': {'fileCount': 4, 'digest': 'sha256:' + 'a' * 64},
                'source': self.human['source'], 'entrypoint': 'index.html',
                'filesSha256': {name: 'c' * 64 for name in ['index.html', 'process-add-place.html',
                                                          'process-refresh-place.html', 'forecast-data.html']}}

    def test_entry_is_static_manifest_driven_and_original_is_verbatim(self):
        record = HUB['stage'](self.output, self.root, self.human)
        HUB['verify'](self.output, record)
        self.assertEqual((self.output / 'retained-index.html').read_bytes(), self.original)
        page = (self.output / 'index.html').read_text()
        self.assertNotIn('<script', page)
        for target in ['human/start.html', 'current/native/overview.html', 'current/docusaurus/',
                       'generated/' + 'a' * 64 + '/overview.html', 'rendering/']:
            self.assertIn('/clew-weather-demo/' + target, page)
        self.assertIn('0.3.0', page)
        self.assertIn('0.2.0', page)
        self.assertIn('/clew-weather-demo/human-history/0.14.8-186544d2/index.html', page)
        self.assertIn('<html lang="ru">', page)
        for name in ['dashboard-save-place-route.html', 'event-flow.html', 'events-data.html']:
            self.assertIn('/clew-weather-demo/human/' + name, page)

    def test_separate_treatment_has_english_navigation_and_no_official_renderer_claim(self):
        human = self.separate_treatment()
        record = HUB['stage'](self.output, self.root, human)
        HUB['verify'](self.output, record)
        page = (self.output / 'index.html').read_text()
        self.assertIn('<html lang="en">', page)
        self.assertIn('Written in English', page)
        self.assertNotRegex(page, '[\u0400-\u04ff]')
        primary, details = page.split('<details>', 1)
        self.assertNotIn('Generated with Codeclew', primary)
        self.assertNotIn(human['treatment']['commit'], primary)
        self.assertIn('Capture producer version: 0.1.0', details)
        self.assertIn('Official acquisition runtime: Codeclew 0.4.0', details)
        self.assertIn('Accepted unreleased skill treatment: ' + 'd' * 40, details)
        self.assertIn('Treatment tree: ' + 'e' * 40, details)
        self.assertIn(human['export']['digest'], details)
        self.assertEqual((self.output / 'retained-index.html').read_bytes(), self.original)

    def test_task_destinations_follow_reader_map_with_current_and_legacy_names(self):
        human = self.separate_treatment()
        page = HUB['render'](self.root, human)
        for name in ['process-add-place.html', 'process-refresh-place.html', 'forecast-data.html']:
            self.assertIn('/clew-weather-demo/human/' + name, page)
        self.assertNotIn('human/event-flow.html', page)
        del human['filesSha256']['process-refresh-place.html']
        page = HUB['render'](self.root, human)
        self.assertNotIn('How does a forecast refresh?', page)
        self.assertNotIn('human/event-flow.html', page)
        self.assertNotIn('human/process-refresh-place.html', page)

    def test_unknown_producer_stays_unknown_and_metadata_is_escaped(self):
        human = self.separate_treatment()
        human['capture']['producerVersion'] = None
        human['treatment']['commit'] = '<script>example</script>'
        page = HUB['render'](self.root, human)
        self.assertIn('Capture producer version: unrecorded', page)
        self.assertNotIn('Capture producer version: 0.4.0', page)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;example&lt;/script&gt;', page)

    def test_optional_export_keeps_previous_entry_behavior(self):
        self.assertIsNone(HUB['stage'](self.output, self.root, None))
        self.assertEqual((self.output / 'index.html').read_bytes(), self.original)

    def test_both_changed_entry_and_changed_archive_fail_verification(self):
        record = HUB['stage'](self.output, self.root, self.human)
        for path in ['index.html', 'retained-index.html']:
            file = self.output / path
            before = file.read_bytes()
            file.write_bytes(before + b'changed')
            with self.assertRaises(AssertionError):
                HUB['verify'](self.output, record)
            file.write_bytes(before)

    def test_existing_archive_is_never_overwritten(self):
        (self.output / 'retained-index.html').write_bytes(b'existing')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            HUB['stage'](self.output, self.root, self.human)
        self.assertEqual((self.output / 'index.html').read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
