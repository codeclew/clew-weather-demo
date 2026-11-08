#!/usr/bin/env python3
"""Human-export guards use neutral technical fixtures, not authored Weather data."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


V = module('human_verify', HERE / 'verify.py')
C = module('showcase_compose', HERE.parent / 'rendering/build.py')


class HumanPublicationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'documentation/human'
        self.site = self.folder / 'site'
        self.site.mkdir(parents=True)
        (self.site / 'index.html').write_text('<!doctype html><main id="content">Fixture</main>')
        self.policy = {
            'schema': 'weather-human-publication/1.0',
            'renderer': {'version': '0.1.0', 'sourceRevision': 'a' * 40,
                         'skillDigest': 'sha256:' + 'b' * 64,
                         'package': 'codeclew-linux-x86_64.tar.gz', 'packageSha256': 'c' * 64},
            'source': {'repository': V.REPOSITORY, 'revision': 'd' * 40},
            'services': ['dashboard', 'places', 'forecasts'], 'language': 'en',
            'entrypoint': 'index.html', 'filesSha256': {'index.html': V.digest(self.site / 'index.html')}}
        self.save()

    def save(self):
        (self.folder / 'publication.json').write_text(json.dumps(self.policy))

    def test_no_human_inputs_leave_existing_site_optional_but_orphan_fails(self):
        self.assertIsNone(V.verify(self.root / 'absent'))
        (self.folder / 'publication.json').unlink()
        with self.assertRaisesRegex(ValueError, 'no publication record'):
            V.verify(self.root)

    def test_exact_files_pass_and_mutation_or_extra_files_fail(self):
        self.assertEqual(V.verify(self.root), self.policy)
        (self.site / 'extra.html').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'unlisted'):
            V.verify(self.root)
        (self.site / 'extra.html').unlink()
        (self.site / 'index.html').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Changed human export'):
            V.verify(self.root)

    def test_source_identity_scope_and_extra_metadata_fail_closed(self):
        for change in [{'services': ['dashboard']}, {'language': 'bilingual'},
                       {'source': {'repository': 'https://example.invalid', 'revision': 'd' * 40}},
                       {'privateRuntimeConfiguration': {}}]:
            with self.subTest(change=change):
                before = dict(self.policy)
                self.policy.update(change); self.save()
                with self.assertRaises(ValueError):
                    V.verify(self.root)
                self.policy = before; self.save()

    def test_local_path_is_rejected_even_with_matching_digest(self):
        (self.site / 'index.html').write_text('<a href="file://fixture/input">Local</a>')
        self.policy['filesSha256']['index.html'] = V.digest(self.site / 'index.html'); self.save()
        with self.assertRaisesRegex(ValueError, 'Local workspace'):
            V.verify(self.root)

    def test_symlink_and_non_reader_file_are_rejected(self):
        (self.site / 'alias.html').symlink_to('index.html')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            V.verify(self.root)
        (self.site / 'alias.html').unlink()
        (self.site / 'runtime.json').write_text('{}')
        self.policy['filesSha256']['runtime.json'] = V.digest(self.site / 'runtime.json'); self.save()
        with self.assertRaisesRegex(ValueError, 'Unsafe export path'):
            V.verify(self.root)

    def test_staging_preserves_bytes_and_refuses_overwrite_or_changed_policy(self):
        old_root = C.ROOT; C.ROOT = self.root
        self.addCleanup(setattr, C, 'ROOT', old_root)
        output = self.root / 'output'; output.mkdir()
        self.assertEqual(C.stage_human(output), self.policy)
        self.assertEqual(V.verify(self.root, exported=output / 'human'), self.policy)
        self.assertEqual((output / 'human/index.html').read_bytes(), (self.site / 'index.html').read_bytes())
        self.assertIn('/clew-weather-demo/human/index.html', C.page('Test', 'Fixture'))
        with self.assertRaisesRegex(ValueError, 'already exists'):
            C.stage_human(output)
        (output / 'human/publication.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'record changed'):
            V.verify(self.root, exported=output / 'human')

    def test_official_check_binds_tag_package_and_public_source(self):
        r = self.policy['renderer']
        release = {'draft': False, 'prerelease': False,
                   'assets': [{'name': r['package'], 'digest': 'sha256:' + r['packageSha256']}]}
        responses = {'repos/codeclew/codeclew/releases/tags/v0.1.0': release,
                     'repos/codeclew/codeclew/commits/v0.1.0': {'sha': r['sourceRevision']},
                     'repos/codeclew/clew-weather-demo/commits/' + 'd' * 40: {'sha': 'd' * 40}}
        with patch.object(V.subprocess, 'check_output', side_effect=lambda argv, **kw: json.dumps(responses[argv[2]])):
            self.assertEqual(V.verify(self.root, official=True), self.policy)
            release['assets'][0]['digest'] = 'sha256:' + 'e' * 64
            with self.assertRaisesRegex(ValueError, 'package digest differs'):
                V.verify(self.root, official=True)


if __name__ == '__main__':
    unittest.main()
