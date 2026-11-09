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
                      'entrypoint': 'start.html'}

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
