import ast
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class CaptureExitStatusTest(unittest.TestCase):
    def test_launcher_contract_survives_thread_contract_iteration(self):
        tree = ast.parse(Path(__file__).with_name('capture.py').read_text())
        stores = [node for node in ast.walk(tree) if isinstance(node, ast.Name)
                  and node.id == 'launcher_contract' and isinstance(node.ctx, ast.Store)]
        self.assertEqual(len(stores), 1)
        receipt = next(node for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == 'receipt' for target in node.targets))
        authority = next(value for key, value in zip(receipt.value.keys, receipt.value.values)
                         if isinstance(key, ast.Constant) and key.value == 'launcherAuthority')
        self.assertIsInstance(authority, ast.Subscript)
        self.assertEqual(authority.value.id, 'launcher_contract')

    def invoke(self, arguments, code, response):
        source = Path(__file__).with_name('capture.py')
        tree = ast.parse(source.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'invoke')
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            namespace = {'sequence': 0, 'receipts': directory, 'launcher': 'clew',
                         'repository': directory, 'environment': {}, 'json': json,
                         'subprocess': subprocess}
            exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), 'exec'), namespace)
            result = subprocess.CompletedProcess([], code, json.dumps(response).encode(), b'')
            with patch.object(subprocess, 'run', return_value=result):
                return namespace['invoke'](arguments)

    def test_checked_snapshot_status_is_accepted_for_check_and_recompose(self):
        response = {'status': 'CHECKED', 'unresolved': {}, 'snapshot': 'saved'}
        for command in ['check', 'recompose']:
            for code in [0, 3, 4]:
                with self.subTest(command=command, code=code):
                    self.assertEqual(self.invoke(['docs', command], code, response), response)

    def test_failure_or_unresolved_capture_is_not_hidden(self):
        cases = [(['docs', 'recompose'], 2, {'status': 'CHECKED', 'unresolved': {}}),
                 (['docs', 'recompose'], 3, {'status': 'CHECKED', 'unresolved': {'places': 'missing'}}),
                 (['docs', 'recompose'], 3, {'status': 'FAILED', 'unresolved': {}}),
                 (['docs', 'process', 'put'], 3, {'status': 'CHECKED', 'unresolved': {}})]
        for arguments, code, response in cases:
            with self.subTest(arguments=arguments, code=code, response=response):
                with self.assertRaises(SystemExit):
                    self.invoke(arguments, code, response)


if __name__ == '__main__':
    unittest.main()
