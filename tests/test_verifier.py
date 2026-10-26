"""Regression tests for credential integrity and explicit verification limits."""

import base64
import copy
import json
import io
from contextlib import redirect_stderr
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CLI = runpy.run_path(str(ROOT / "obo"))


class VerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "credential.json"
        self.key = Ed25519PrivateKey.generate()
        self.public = base64.urlsafe_b64encode(
            self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        ).decode().rstrip("=")
        self.credential = json.loads((ROOT / "examples/credentials/signed-demo.json").read_text())
        self.credential.update(issued_at=int(time.time()) - 10, expires_at=int(time.time()) + 600)

    def sign(self):
        self.credential["credential_digest"] = CLI["credential_digest"](self.credential)
        signature = self.key.sign(self.credential["credential_digest"].encode())
        self.credential["credential_sig"] = "Ed25519:" + base64.urlsafe_b64encode(signature).decode().rstrip("=")

    def verify(self, *extra, key=True, raw=None):
        self.path.write_text(raw if raw is not None else json.dumps(self.credential))
        command = [sys.executable, str(ROOT / "obo"), "verify", str(self.path)]
        if key:
            command += ["--public-key", self.public]
        return subprocess.run(command + list(extra), capture_output=True, text=True)

    def test_signed_credential_passes(self):
        self.sign()
        result = self.verify("--intent", "search flights from LHR to JFK on 2026-06-15")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("credential integrity verified", result.stdout)
        self.assertIn("authority, policy, replay, and binding proof not checked", result.stdout)

    def test_key_source_required(self):
        self.sign()
        self.assertNotEqual(self.verify(key=False).returncode, 0)

    def test_key_sources_mutually_exclusive(self):
        self.sign()
        self.assertNotEqual(self.verify("--dns").returncode, 0)

    def test_missing_fields_fail_even_with_recomputed_digest(self):
        for field in ("credential_sig", "expires_at", "principal_id", "issued_at"):
            with self.subTest(field=field):
                saved = copy.deepcopy(self.credential)
                self.credential.pop(field)
                self.sign()
                if field == "credential_sig":
                    self.credential.pop(field)
                self.assertNotEqual(self.verify().returncode, 0)
                self.credential = saved

    def test_invalid_expiry_types_and_zero_fail(self):
        for value in (0, -1, False, "4102444800"):
            with self.subTest(expiry=value):
                self.credential["expires_at"] = value
                self.sign()
                self.assertNotEqual(self.verify("--ignore-expiry").returncode, 0)

    def test_expired_and_future_issued_fail(self):
        now = int(time.time())
        for issued, expires in ((now - 30, now - 1), (now + 60, now + 600), (now - 1, now - 10)):
            with self.subTest(issued=issued, expires=expires):
                self.credential.update(issued_at=issued, expires_at=expires)
                self.sign()
                self.assertNotEqual(self.verify().returncode, 0)

    def test_expiry_boundary_is_exclusive(self):
        self.sign()
        self.path.write_text(json.dumps(self.credential))
        args = type("Args", (), dict(path=str(self.path), intent=None, ignore_expiry=False,
                                     public_key=self.public, dns=False))()
        with patch("time.time", return_value=self.credential["expires_at"]), redirect_stderr(io.StringIO()):
            self.assertEqual(CLI["verify_credential"](args), 1)

    def test_archived_override_keeps_signature_check(self):
        self.credential["expires_at"] = self.credential["issued_at"] + 1
        self.sign()
        result = self.verify("--ignore-expiry")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skipped (archived credential)", result.stdout)
        self.credential["credential_sig"] = "Ed25519:" + "A" * 86
        self.assertNotEqual(self.verify("--ignore-expiry").returncode, 0)

    def test_tampered_digest_and_wrong_key_fail(self):
        self.sign()
        self.credential["principal_id"] = "attacker"
        self.assertNotEqual(self.verify().returncode, 0)
        self.credential["credential_digest"] = CLI["credential_digest"](self.credential)
        self.assertNotEqual(self.verify().returncode, 0)

    def test_intent_mismatch_fails(self):
        self.sign()
        self.assertNotEqual(self.verify("--intent", "different request").returncode, 0)

    def test_unsupported_proofs_fail(self):
        for fields in ({"delegation_depth": {"current": 0, "max": 1}},
                       {"agent_instance_id": "instance:1"}):
            with self.subTest(fields=fields):
                saved = copy.deepcopy(self.credential)
                self.credential.update(fields)
                self.sign()
                result = self.verify()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("not implemented", result.stderr)
                self.credential = saved

    def test_malformed_json_fails_cleanly(self):
        self.sign()
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e400}', '[1,2]', '{broken'):
            with self.subTest(raw=raw):
                result = self.verify(raw=raw)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)

    def test_dns_key_source_and_issuer_mismatch(self):
        self.sign()
        self.path.write_text(json.dumps(self.credential))
        args = type("Args", (), dict(path=str(self.path), intent=None, ignore_expiry=False,
                                     public_key=None, dns=True))()
        verifier = CLI["verify_credential"]
        with patch.dict(verifier.__globals__, resolve_obo_key=lambda operator: self.public):
            self.assertEqual(verifier(args), 0)
            self.credential["issuer_id"] = "other.example"
            self.sign()
            self.path.write_text(json.dumps(self.credential))
            with redirect_stderr(io.StringIO()):
                self.assertEqual(verifier(args), 1)

    def test_validation_dependency_required(self):
        for script in ("obo", "scripts/validate_examples.py"):
            with self.subTest(script=script):
                command = [sys.executable, "-S", str(ROOT / script)]
                if script == "obo":
                    command += ["verify", str(self.path), "--public-key", self.public]
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("jsonschema is required", result.stderr)


class DelegationSchemaTests(unittest.TestCase):
    def test_draft_fields_representable_but_child_requires_parent(self):
        schema = json.loads((ROOT / "schemas/obo-credential.json").read_text())
        validator = Draft202012Validator(schema)
        credential = json.loads((ROOT / "examples/credentials/signed-demo.json").read_text())
        credential.update(delegation_depth={"current": 1, "max": 2},
                          parent_credential_ref="urn:obo:cred:parent",
                          delegation_chain_digest="sha256:" + "0" * 64)
        validator.validate(credential)
        del credential["parent_credential_ref"]
        self.assertTrue(list(validator.iter_errors(credential)))


if __name__ == "__main__":
    unittest.main()
