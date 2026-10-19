#!/usr/bin/env python3
"""Regression checks for actual field markup, not JavaScript template counts."""

import importlib.util
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


if __name__ == '__main__':
    unittest.main()
