#!/usr/bin/env python3
"""Meaningful deploy guards: native deltas, frozen bytes and path-based hosting."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('variant', Path(__file__).with_name('variant.py'))
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


class VariantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_native_pin_requires_complete_byte_identical_tree_and_policy(self):
        r = self.root
        subprocess.run(['git', 'init', '-q', str(r)], check=True)
        (r / 'docs').mkdir(); (r / 'docs/index.html').write_text('original')
        (r / 'documentation/reference').mkdir(parents=True)
        (r / 'documentation/reference/publication.json').write_text('policy')
        subprocess.run(['git', 'add', '.'], cwd=r, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                        'commit', '-qm', 'baseline'], cwd=r, check=True)
        baseline = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r, text=True).strip()
        self.assertTrue(V.native_unchanged(r, baseline))
        (r / 'docs/index.html').write_text('changed')
        self.assertFalse(V.native_unchanged(r, baseline))
        (r / 'docs/index.html').write_text('original')
        (r / 'docs/extra.html').write_text('untracked')
        self.assertFalse(V.native_unchanged(r, baseline))
        (r / 'docs/extra.html').unlink()
        (r / 'documentation/reference/publication.json').write_text('changed policy')
        self.assertFalse(V.native_unchanged(r, baseline))

    def project(self):
        p = self.root / 'project'; p.mkdir()
        (p / 'entry.mdx').write_text('original retained content')
        V.write(p / 'export-manifest.json', {'publication': 'pub', 'snapshot': 'snap',
            'documentationLanguage': 'en', 'format': 'docusaurus',
            'resolvedPayloadParity': {'status': 'VERIFIED'},
            'files': [{'path': 'entry.mdx', 'digest': 'sha256:' + V.digest(p / 'entry.mdx')}]})
        return p

    def test_export_manifest_rejects_changed_bytes_and_snapshot(self):
        p = self.project(); config = {'publication': 'pub', 'snapshot': 'snap', 'language': 'en'}
        V.verify_export(p, config)
        with self.assertRaisesRegex(ValueError, 'different retained snapshot'):
            V.verify_export(p, {**config, 'snapshot': 'other'})
        (p / 'entry.mdx').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'changed exported file'):
            V.verify_export(p, config)

    def test_project_index_catches_extra_source_but_ignores_only_derived_builds(self):
        p = self.project(); before = V.project_files(p)
        (p / 'build').mkdir(); (p / 'build/derived.html').write_text('derived')
        self.assertEqual(before, V.project_files(p))
        (p / 'unindexed.mdx').write_text('extra')
        self.assertNotEqual(before, V.project_files(p))

    def test_deep_base_url_rejects_root_assets_and_unprefixed_routes(self):
        p = self.root / 'build'; p.mkdir()
        (p / 'variant-identity.json').write_text('{}')
        (p / 'review.html').write_text('<a href="/clew-weather-demo/docusaurus/services/places#section-ingress">Place</a><script src="/clew-weather-demo/docusaurus/assets/main.js"></script>')
        self.assertEqual(V.verify_build(p)['status'], 'PASS')
        for url in ['/assets/main.js', '/services/places']:
            (p / 'review.html').write_text('<a href="' + url + '">Wrong</a>')
            with self.assertRaisesRegex(ValueError, 'escaped deployment base'):
                V.verify_build(p)

    def test_source_version_accepts_reported_semver_and_rejects_slashes(self):
        self.assertEqual(V.validate_version('0.13.46'), '0.13.46')
        with self.assertRaisesRegex(ValueError, 'invalid source version'):
            V.validate_version(r'0\x13\x46')

    def test_showcase_overlay_allows_only_the_explicit_entry_with_opt_in(self):
        p = self.root / 'build'; p.mkdir()
        (p / 'variant-identity.json').write_text('{}')
        (p / 'review.html').write_text('<a href="/clew-weather-demo/rendering/">Showcase</a>')
        with self.assertRaisesRegex(ValueError, 'escaped deployment base'):
            V.verify_build(p)
        self.assertEqual(V.verify_build(p, showcase_navigation=True)['status'], 'PASS')
        for url in ['/clew-weather-demo/rendering/unknown', '/other-site/', '/assets/other.js']:
            (p / 'review.html').write_text('<a href="' + url + '">Wrong</a>')
            with self.assertRaisesRegex(ValueError, 'escaped deployment base'):
                V.verify_build(p, showcase_navigation=True)


if __name__ == '__main__':
    unittest.main()
