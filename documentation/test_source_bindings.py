import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("source_bindings", Path(__file__).with_name("source_bindings.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SourceBindingsTest(unittest.TestCase):
    def fixture(self):
        text = "async function save() {\n return value;\n}"
        record = {"id": "dashboard-source", "service": "dashboard", "file": "main.ts",
                  "startLine": 10, "endLine": 12, "text": text,
                  "textDigest": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
                  "authority": "EXACT_SNAPSHOT_TEXT", "revision": "b" * 40}
        expected = {record["id"]: {k: record[k] for k in
                    ("id", "service", "file", "startLine", "endLine", "textDigest")}}
        method = {"id": "save", "service": "dashboard", "sourceId": record["id"],
                  "entrypoint": "dashboard-save", "textDigest": record["textDigest"]}
        evidence = {"service": "dashboard", "sourceId": record["id"],
                    "textDigest": record["textDigest"], "revision": "a" * 40,
                    "startLine": 11, "endLine": 11}
        process = {"process": {"thread": {"methods": [method], "steps": [{"id": "save"}],
                   "boundaryContracts": [{"evidence": {"send": evidence}}]}}}
        return process, expected, {("dashboard", record["id"]): record}

    def test_only_revision_changes_and_original_is_preserved(self):
        process, expected, sources = self.fixture()
        result, updates = module.rebind_thread(process, expected, sources)
        original = process["process"]["thread"]["boundaryContracts"][0]["evidence"]["send"]
        rebound = result["process"]["thread"]["boundaryContracts"][0]["evidence"]["send"]
        self.assertEqual(original["revision"], "a" * 40)
        self.assertEqual(rebound, {**original, "revision": "b" * 40})
        self.assertEqual(result["process"]["thread"]["methods"], process["process"]["thread"]["methods"])
        self.assertEqual(result["process"]["thread"]["steps"], process["process"]["thread"]["steps"])
        self.assertEqual(updates[0]["previousRevision"], "a" * 40)

    def test_changed_file_span_or_text_is_refused(self):
        for field, value in [("file", "other.ts"), ("startLine", 11), ("endLine", 13),
                             ("textDigest", "sha256:" + "c" * 64), ("text", "altered")]:
            with self.subTest(field=field):
                process, expected, sources = self.fixture()
                sources[("dashboard", "dashboard-source")][field] = value
                with self.assertRaises(ValueError):
                    module.rebind_thread(process, expected, sources)

    def test_missing_or_foreign_source_is_refused(self):
        process, expected, sources = self.fixture()
        for records in [{}, {("other", "dashboard-source"): next(iter(sources.values()))}]:
            with self.assertRaises(ValueError):
                module.rebind_thread(process, expected, records)

    def test_citation_outside_source_is_refused(self):
        process, expected, sources = self.fixture()
        process["process"]["thread"]["boundaryContracts"][0]["evidence"]["send"]["endLine"] = 13
        with self.assertRaises(ValueError):
            module.rebind_thread(process, expected, sources)

    def test_unverified_source_or_invalid_revision_is_refused(self):
        for field, value in [("authority", "IMPORTED"), ("revision", "main")]:
            process, expected, sources = self.fixture()
            sources[("dashboard", "dashboard-source")][field] = value
            with self.assertRaises(ValueError):
                module.rebind_thread(process, expected, sources)

    def test_process_without_thread_remains_unchanged(self):
        process = {"id": "publisher", "process": {"linkedSubviews": ["consumer"]}}
        result, updates = module.rebind_thread(process, {}, {})
        self.assertEqual(result, process)
        self.assertIsNot(result, process)
        self.assertEqual(updates, [])


if __name__ == "__main__":
    unittest.main()
