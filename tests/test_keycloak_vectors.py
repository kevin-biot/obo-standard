"""Public corpus expectations checked by Python; Node consumes the same bytes."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from obo_interop import strict_json
from obo_keycloak import verify_bundle

ROOT = Path(__file__).resolve().parents[1]


class SharedVectorTests(unittest.TestCase):
    def test_python_matches_every_declared_result(self):
        corpus = json.loads((ROOT / "tests/vectors/keycloak/corpus.json").read_text())
        names = [case["name"] for case in corpus["cases"]]
        self.assertEqual(len(names), len(set(names)))
        for case in corpus["cases"]:
            with self.subTest(case=case["name"]):
                def verify():
                    return verify_bundle(strict_json(case["bundle_json"]), strict_json(case["trust_json"]), case["at"])
                if case["expected"]["result"] == "failed":
                    with self.assertRaises(ValueError):
                        verify()
                else:
                    report = verify()
                    self.assertEqual(report["result"], case["expected"]["result"])
                    self.assertEqual(report["outcome"], case["expected"]["outcome"])

    def test_corpus_is_reproducible(self):
        generated = subprocess.run([sys.executable, str(ROOT / "scripts/keycloak_vectors.py"), "--check"],
                                   capture_output=True, text=True)
        self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
