#!/usr/bin/env python3
"""Regression checks for actual field markup, not JavaScript template counts."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('verify_reference', Path(__file__).with_name('verify.py'))
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class FieldMarkupTests(unittest.TestCase):
    def parse(self, html):
        parser = VERIFY.FieldTables()
        parser.feed(html)
        return parser

    def test_script_templates_and_pipe_prose_are_not_rendered_field_tables(self):
        html = '<script>const template = `<table class="dm-fields"><th scope="col">Field</th><a href="#field-value">value</a></table>`;</script><p>| value | description |</p>'
        parsed = self.parse(html)
        self.assertEqual((parsed.tables, parsed.headers, parsed.fields), (0, 0, []))

    def test_real_field_table_retains_field_order_and_column_headers(self):
        html = '<table class="dm-fields"><thead><tr>' + '<th scope="col">Heading</th>' * 2 + '</tr></thead><tbody>'
        html += ''.join('<tr><th scope="row"><a href="#field-' + field + '">' + field + '</a></th><td>Purpose</td></tr>' for field in ['id', 'name'])
        parsed = self.parse(html + '</tbody></table>')
        self.assertEqual((parsed.tables, parsed.headers, parsed.fields), (1, 2, ['id', 'name']))

    def test_unrelated_tables_do_not_count_as_entity_field_rows(self):
        parsed = self.parse('<table class="dm-records"><th scope="col">Field</th><a href="#field-other">Other</a></table>')
        self.assertEqual((parsed.tables, parsed.fields), (0, []))

    def test_builder_preserves_native_launcher_failure_code_and_diagnostic(self):
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            launcher = root / 'clew'
            launcher.write_text('#!/bin/sh\nprintf \'{"schema":"fixture-error","error":"blocked"}\\n\' >&2\nexit 7\n')
            launcher.chmod(0o700)
            result = subprocess.run(['python3', '-I', '-S', str(Path(__file__).with_name('build.py')),
                                     '--root', str(root), '--clew', str(launcher), '--output', str(root / 'out'),
                                     '--generator-commit', 'a' * 40], capture_output=True, text=True)
            self.assertEqual(result.returncode, 7)
            self.assertIn('"schema":"fixture-error"', result.stderr)
            self.assertFalse((root / 'out').exists())


class PublicationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.site, self.inputs = self.base / 'site', self.base / 'inputs'
        self.site.mkdir()
        self.inputs.mkdir()
        self.write(self.inputs / 'accepted.json', {'original': 'unchanged'})
        config = {'publication': 'pub', 'snapshot': 'snap', 'language': 'en',
                  'inputSha256': {'accepted.json': VERIFY.sha(self.inputs / 'accepted.json')},
                  'expectedModels': {'thing': ['value']}, 'expectedDataFlow': ['save'],
                  'serviceModelLinks': 'services.json'}
        self.write(self.inputs / 'inputs.json', config)
        self.write(self.inputs / 'services.json', {'sample': ['thing']})
        self.write(self.site / 'data-model.json', {'models': [{'id': 'thing', 'fields': [{'id': 'value'}]}]})
        path = self.site / 'data-model/thing.html'
        path.parent.mkdir()
        path.write_text('<table class="dm-fields"><th scope="col">Field</th><th scope="col">Purpose</th><th scope="row"><a href="#field-value">value</a></th></table>')
        self.write(self.site / 'scenarios/save.json', {'questionReader': {'presentation': 'SEQUENTIAL'},
                   'processDataFlow': {'request': {'enabled': True, 'stages': ['Store']}, 'models': [{}]}})
        (self.site / 'scenarios/save.html').write_text('<script>CodeclewDataModel; processDataFlow;</script>')
        self.write(self.site / 'services/sample.json', {'serviceModelLinks': [{'id': 'thing'}]})
        manifest = {'publication': 'pub', 'snapshot': 'snap', 'documentationLanguage': 'en',
                    'files': [{'path': str(p.relative_to(self.site)), 'digest': 'sha256:' + VERIFY.sha(p)}
                              for p in self.site.rglob('*') if p.is_file()]}
        self.write(self.site / 'pages-manifest.json', manifest)
        identity = {'generator': {'version': '0.1.0', 'sourceRevision': 'a' * 40, 'selection': 'SOURCE_CANDIDATE'},
                    'publication': 'pub', 'snapshot': 'snap', 'language': 'en', 'inputSha256': config['inputSha256']}
        self.write(self.site / 'reference-render.json', identity)
        self.write(self.site / 'reference-checks.json', {'status': 'PASS'})
        for name in ['inputs.json', 'accepted.json']:
            (self.site / 'reference-inputs').mkdir(exist_ok=True)
            (self.site / 'reference-inputs' / name).write_bytes((self.inputs / name).read_bytes())
        self.write(self.site / 'reference-inputs/rendered-data-model-plan.json', {})
        self.pins = {str(p.relative_to(self.site)): VERIFY.sha(p) for p in self.site.rglob('*') if p.is_file()}
        self.write(self.inputs / 'pins.json', self.pins)
        self.policy = {'schema': 'weather-reference-publication/1.0', 'mode': 'accepted-source',
                       'renderer': {'version': '0.1.0', 'sourceRevision': 'a' * 40},
                       'acceptedFiles': 'pins.json', 'acceptedFilesSha256': VERIFY.sha(self.inputs / 'pins.json')}
        self.policy_path = self.inputs / 'publication.json'
        self.sync_policy()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + '\n')

    def sync_policy(self):
        self.write(self.policy_path, self.policy)
        (self.site / 'reference-publication.json').write_bytes(self.policy_path.read_bytes())

    def check(self, **kwargs):
        return VERIFY.verify_publication(self.site, self.policy_path, inputs=self.inputs, **kwargs)

    def test_exact_accepted_source_does_not_require_or_claim_a_public_release(self):
        self.assertEqual(self.check()['publicationMode'], 'accepted-source')

    def test_changed_manifest_bytes_fail_even_when_coverage_still_matches(self):
        path = self.site / 'pages-manifest.json'
        value = json.loads(path.read_text())
        value['output'] = 'changed'
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, 'accepted artifact changed'):
            self.check()

    def test_required_artifact_cannot_be_removed_from_the_pin_index(self):
        del self.pins['reference-render.json']
        self.write(self.inputs / 'pins.json', self.pins)
        self.policy['acceptedFilesSha256'] = VERIFY.sha(self.inputs / 'pins.json')
        self.sync_policy()
        with self.assertRaisesRegex(ValueError, 'omits required'):
            self.check()

    def test_another_source_commit_is_rejected(self):
        path = self.site / 'reference-render.json'
        value = json.loads(path.read_text())
        value['generator']['sourceRevision'] = 'b' * 40
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, 'different generator commit'):
            self.check()

    def test_latest_release_mode_requires_latest_identity_and_installed_release(self):
        self.policy['mode'] = 'latest-release'
        self.sync_policy()
        with self.assertRaisesRegex(ValueError, 'latest release identity'):
            self.check()
        with self.assertRaisesRegex(ValueError, 'selection mode'):
            self.check(latest_version='v0.1.0', latest_commit='a' * 40)
        path = self.site / 'reference-render.json'
        value = json.loads(path.read_text())
        value['generator']['selection'] = 'INSTALLED_RELEASE'
        self.write(path, value)
        self.assertEqual(self.check(latest_version='v0.1.0', latest_commit='a' * 40)['publicationMode'], 'latest-release')

    def test_visible_publication_policy_must_match_the_checked_policy(self):
        self.write(self.site / 'reference-publication.json', {'mode': 'different'})
        with self.assertRaisesRegex(ValueError, 'published policy differs'):
            self.check()


if __name__ == '__main__':
    unittest.main()
