#!/usr/bin/env python3
"""Human-export guards use neutral technical fixtures, not authored Weather data."""
import importlib.util
import copy
import json
from pathlib import Path
import shutil
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

    def history(self):
        archive = self.folder / 'history/previous'
        archive.mkdir(parents=True)
        shutil.copy2(self.site / 'index.html', archive / 'index.html')
        shutil.copy2(self.folder / 'publication.json', archive / 'publication.json')
        old_root = C.ROOT; C.ROOT = self.root
        self.addCleanup(setattr, C, 'ROOT', old_root)
        return archive

    def test_history_staging_preserves_all_bytes_without_touching_frozen_native_docs(self):
        archive = self.history()
        native = self.root / 'docs'; native.mkdir()
        (native / 'index.html').write_bytes(b'Native export')
        output = self.root / 'output'; output.mkdir()
        C.stage_human(output)
        C.verify_human_history(output)
        exported = output / 'human-history/previous'
        self.assertEqual(V.verify(self.root, exported=exported, publication=archive / 'publication.json'), self.policy)
        for name in ['index.html', 'publication.json']:
            self.assertEqual((exported / name).read_bytes(), (archive / name).read_bytes())
        self.assertEqual(list(native.iterdir()), [native / 'index.html'])
        self.assertEqual((native / 'index.html').read_bytes(), b'Native export')
        (exported / 'index.html').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Changed human export'): C.verify_human_history(output)
        shutil.copy2(archive / 'index.html', exported / 'index.html')
        (exported / 'publication.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'record changed'): C.verify_human_history(output)

    def test_history_source_rejects_mutation_extra_files_symlinks_and_missing_policy(self):
        archive = self.history()
        original = (archive / 'index.html').read_bytes()
        (archive / 'index.html').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Changed human export'): C.human_history()
        (archive / 'index.html').write_bytes(original)
        extra = archive / 'unexpected.html'; extra.write_text('extra')
        with self.assertRaisesRegex(ValueError, 'unlisted'): C.human_history()
        extra.unlink(); extra.symlink_to('index.html')
        with self.assertRaisesRegex(ValueError, 'Symlink'): C.human_history()
        extra.unlink(); (archive / 'publication.json').unlink()
        with self.assertRaisesRegex(ValueError, 'no publication record'): C.human_history()

    def test_history_destination_refuses_overwrite_extra_entries_and_symlink_root(self):
        archive = self.history()
        output = self.root / 'output'; output.mkdir()
        destination = output / 'human-history'; destination.mkdir()
        with self.assertRaisesRegex(ValueError, 'already exists'): C.stage_human(output)
        destination.rmdir(); C.stage_human(output)
        (destination / 'unlisted').mkdir()
        with self.assertRaisesRegex(ValueError, 'unlisted'): C.verify_human_history(output)
        shutil.rmtree(destination); destination.symlink_to(archive.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Unsafe staged'): C.verify_human_history(output)

    def test_broken_history_symlink_is_not_treated_as_absent(self):
        old_root = C.ROOT; C.ROOT = self.root
        self.addCleanup(setattr, C, 'ROOT', old_root)
        (self.folder / 'history').symlink_to('missing-history', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Unsafe human history'): C.human_history()

    def use_treatment(self):
        runtime = dict(self.policy.pop('renderer'))
        runtime.pop('skillDigest')
        self.policy.update(schema='weather-human-publication/1.1',
            capture={'kind': 'retained-snapshot', 'snapshot': 'sha256:' + '9' * 64 + '/123',
                     'producerVersion': '0.0.9', 'recaptured': False},
            acquisition={'kind': 'official-release', **runtime},
            treatment={'kind': 'accepted-unreleased-skill', 'repository': V.PRODUCT,
                       'commit': '1' * 40, 'tree': '2' * 40, 'skillDigest': 'sha256:' + '3' * 64,
                       'runtimeVersion': runtime['version']},
            export={'kind': 'frozen-export', 'digest': V.export_digest(self.policy['filesSha256']), 'fileCount': 1})
        self.save()

    def official_responses(self):
        runtime = V.acquisition(self.policy)
        return {'repos/codeclew/codeclew/releases/tags/v' + runtime['version']:
                {'draft': False, 'prerelease': False, 'assets': [{'name': runtime['package'], 'digest': 'sha256:' + runtime['packageSha256']}]},
                'repos/codeclew/codeclew/commits/v' + runtime['version']: {'sha': runtime['sourceRevision']},
                'repos/codeclew/clew-weather-demo/commits/' + 'd' * 40: {'sha': 'd' * 40}}

    def test_treatment_keeps_historical_capture_official_runtime_and_frozen_export_separate(self):
        self.use_treatment()
        responses = self.official_responses()
        with patch.object(V.subprocess, 'check_output', side_effect=lambda argv, **kw: json.dumps(responses[argv[2]])) as calls:
            self.assertEqual(V.verify(self.root, official=True), self.policy)
        self.assertEqual(len(calls.call_args_list), 3)
        self.assertEqual(self.policy['capture']['producerVersion'], '0.0.9')
        self.assertEqual(self.policy['acquisition']['version'], '0.1.0')
        old_root = C.ROOT; C.ROOT = self.root
        self.addCleanup(setattr, C, 'ROOT', old_root)
        output = self.root / 'treatment-output'; output.mkdir()
        C.stage_human(output)
        self.assertEqual(V.verify(self.root, exported=output / 'human'), self.policy)

    def test_missing_treatment_hashes_and_runtime_identity_conflation_refuse(self):
        self.use_treatment()
        before = copy.deepcopy(self.policy)
        for field in ['commit', 'tree', 'skillDigest', 'runtimeVersion']:
            with self.subTest(field=field):
                self.policy = copy.deepcopy(before); self.policy['treatment'].pop(field); self.save()
                with self.assertRaises(ValueError): V.verify(self.root)
        changes = [('acquisition', 'kind', 'accepted-unreleased-skill'),
                   ('treatment', 'kind', 'official-release'),
                   ('treatment', 'repository', 'https://example.invalid/unrelated-renderer'),
                   ('treatment', 'commit', before['acquisition']['sourceRevision']),
                   ('treatment', 'runtimeVersion', '0.1.1'),
                   ('capture', 'recaptured', True)]
        for section, key, value in changes:
            with self.subTest(section=section, key=key):
                self.policy = copy.deepcopy(before); self.policy[section][key] = value; self.save()
                with self.assertRaises(ValueError): V.verify(self.root)

    def test_frozen_export_hash_is_required_and_survives_reader_rehash_attempt(self):
        self.use_treatment(); before = copy.deepcopy(self.policy)
        self.policy['export'].pop('digest'); self.save()
        with self.assertRaisesRegex(ValueError, 'frozen export identity'): V.verify(self.root)
        self.policy = before
        (self.site / 'index.html').write_text('<main>Changed fixture</main>')
        self.policy['filesSha256']['index.html'] = V.digest(self.site / 'index.html'); self.save()
        with self.assertRaisesRegex(ValueError, 'Frozen export identity differs'): V.verify(self.root)

    def test_treatment_cannot_bypass_official_tag_package_and_public_source_checks(self):
        self.use_treatment()
        pristine = self.official_responses()
        for key, change in [
            ('repos/codeclew/codeclew/releases/tags/v0.1.0', lambda row: row.update(draft=True)),
            ('repos/codeclew/codeclew/releases/tags/v0.1.0', lambda row: row['assets'][0].update(digest='sha256:' + 'e' * 64)),
            ('repos/codeclew/codeclew/commits/v0.1.0', lambda row: row.update(sha='e' * 40)),
            ('repos/codeclew/clew-weather-demo/commits/' + 'd' * 40, lambda row: row.update(sha='e' * 40))]:
            responses = copy.deepcopy(pristine); change(responses[key])
            with self.subTest(key=key), patch.object(V.subprocess, 'check_output', side_effect=lambda argv, **kw: json.dumps(responses[argv[2]])):
                with self.assertRaises(ValueError): V.verify(self.root, official=True)

    def test_treatment_never_allows_private_paths_or_reports_in_identity(self):
        self.use_treatment()
        self.policy['treatment']['localRoot'] = '/fixture/workspace'; self.save()
        with self.assertRaisesRegex(ValueError, 'explicit accepted unreleased'): V.verify(self.root)

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
