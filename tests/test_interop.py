"""Adversarial cases for the pinned external-grant profile (not a certification suite)."""

import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from obo_interop import digest_json, digest_token, read_json, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/integrations/external-grant"
AT = 1793016000


class InteropTests(unittest.TestCase):
    def setUp(self):
        self.bundle = read_json(EXAMPLE / "accepted.json")
        self.denied = read_json(EXAMPLE / "denied.json")
        self.trust = read_json(EXAMPLE / "trust.json")

    def resign(self, field, changes, role=None):
        role = role or {"grant_jwt": "issuer", "policy_jwt": "policy_authority",
                        "decision_jwt": "service", "execution_jwt": "service"}[field]
        claims = jwt.decode(self.bundle[field], options={"verify_signature": False})
        claims.update(changes)
        header = jwt.get_unverified_header(self.bundle[field])
        seed = {"issuer": 1, "policy_authority": 2, "service": 3}[role]
        self.bundle[field] = jwt.encode(claims, Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32),
                                       algorithm="EdDSA", headers={"typ": header["typ"], "kid": header["kid"]})

    def fails(self, pattern=None):
        with self.assertRaisesRegex(ValueError, pattern or ".+"):
            verify_bundle(self.bundle, self.trust, AT)

    def test_acceptance_and_denial(self):
        for bundle, outcome in ((self.bundle, "completed"), (self.denied, "denied")):
            report = verify_bundle(bundle, self.trust, AT)
            self.assertEqual(report["result"], "verified")
            self.assertEqual(report["outcome"], outcome)
            self.assertTrue(report["limitations"])

    def test_unknown_status_is_incomplete(self):
        del self.trust["status"]
        report = verify_bundle(self.bundle, self.trust, AT)
        self.assertEqual(report["result"], "incomplete")
        self.assertEqual(report["checks"]["archived_status"], "unknown")

    def test_stale_future_or_revoked_status(self):
        for status in ({"as_of": AT - 10, "valid_until": AT, "revoked_grant_ids": []},
                       {"as_of": AT + 1, "valid_until": AT + 10, "revoked_grant_ids": []},
                       {"as_of": AT - 1, "valid_until": AT + 1, "revoked_grant_ids": ["grant-test-accepted"]}):
            with self.subTest(status=status):
                self.trust["status"] = status
                self.fails()

    def test_changed_operation_parameters_or_target(self):
        for key, value in (("resource", "supplier:99"), ("parameters", {"contact_email": "attacker@example.com"}),
                           ("request_id", "replay:2")):
            saved = copy.deepcopy(self.bundle)
            self.bundle["operation"][key] = value
            self.fails("binding mismatch")
            self.bundle = saved

    def test_principal_agent_operator_and_audience_substitution(self):
        cases = ({"sub": "urn:org:attacker"}, {"client_id": "attacker"}, {"aud": "wrong-service"},
                 {"obo": {"operator_id": "attacker"}})
        for changes in cases:
            with self.subTest(changes=changes):
                saved = copy.deepcopy(self.bundle)
                self.resign("grant_jwt", changes)
                self.fails()
                self.bundle = saved

    def test_unknown_constraints_and_delegation_fail_closed(self):
        for changes in ({"cnf": {"jkt": "key"}}, {"act": {"sub": "parent"}},
                        {"authorization_details": [{"type": "unknown"}]}, {"nbf": AT - 10}):
            with self.subTest(changes=changes):
                saved = copy.deepcopy(self.bundle)
                self.resign("grant_jwt", changes)
                self.fails("unsupported or missing")
                self.bundle = saved

    def test_wider_scope_rejected(self):
        self.resign("grant_jwt", {"scope": "supplier:update supplier:delete"})
        self.fails("scope")

    def test_grant_expiry_future_issue_or_boolean_time_rejected(self):
        for changes in ({"exp": AT}, {"iat": AT + 1}, {"iat": False}):
            saved = copy.deepcopy(self.bundle)
            self.resign("grant_jwt", changes)
            self.fails()
            self.bundle = saved

    def test_role_key_substitution(self):
        self.resign("grant_jwt", {}, role="service")
        self.fails("JWT verification")

    def test_unsigned_or_forged_jwt(self):
        self.bundle["grant_jwt"] = self.bundle["grant_jwt"].rsplit(".", 1)[0] + "." + "A" * 86
        self.fails("JWT verification")

    def test_unsupported_jose_critical_header(self):
        parts = self.bundle["grant_jwt"].split(".")
        header = jwt.get_unverified_header(self.bundle["grant_jwt"])
        header.update(crit=["unknown"], unknown=True)
        parts[0] = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        self.bundle["grant_jwt"] = ".".join(parts)
        self.fails("unsupported JOSE header")

    def test_duplicate_members_in_signed_payload(self):
        parts = self.bundle["grant_jwt"].split(".")
        raw = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)).decode()
        parts[1] = base64.urlsafe_b64encode((raw[:-1] + ',"sub":"other"}').encode()).decode().rstrip("=")
        self.bundle["grant_jwt"] = ".".join(parts)
        self.fails("duplicate JSON member")

    def test_changed_policy_rebound_by_service_still_rejects_wrong_decision(self):
        self.resign("policy_jwt", {"allowed_fields": ["credit_limit"]})
        self.resign("decision_jwt", {"policy_digest": digest_token(self.bundle["policy_jwt"])})
        self.fails("disagrees with evaluated policy")

    def test_policy_validity_and_unknown_policy_constraints(self):
        for changes in ({"exp": AT}, {"max_amount": 100}, {"allowed_fields": ["contact_email", "contact_email"]}):
            saved = copy.deepcopy(self.bundle)
            self.resign("policy_jwt", changes)
            self.fails()
            self.bundle = saved

    def test_missing_or_spliced_receipts(self):
        for field in ("decision_jwt", "execution_jwt", "response"):
            saved = copy.deepcopy(self.bundle)
            del self.bundle[field]
            self.fails()
            self.bundle = saved
        self.bundle["decision_jwt"] = self.denied["decision_jwt"]
        self.fails("grant binding mismatch")

    def test_service_signed_identity_and_request_changes_rejected(self):
        for changes in ({"sub": "other"}, {"request_id": "other"}, {"reason_code": "unknown"}, {"iat": AT + 1}):
            saved = copy.deepcopy(self.bundle)
            self.resign("decision_jwt", changes)
            self.fails()
            self.bundle = saved

    def test_altered_response_and_execution_binding(self):
        self.bundle["response"]["record_version"] = 99
        self.fails("response mismatch")
        self.bundle = read_json(EXAMPLE / "accepted.json")
        self.resign("execution_jwt", {"decision_digest": "sha256:" + "0" * 64})
        self.fails("decision mismatch")

    def test_execution_after_grant_expiry(self):
        self.resign("execution_jwt", {"iat": AT + 300, "exp": AT + 600})
        self.fails("outside authorization window")

    def test_status_must_cover_execution_as_well_as_admission(self):
        self.resign("execution_jwt", {"iat": AT + 60})
        self.fails("status snapshot")

    def test_denial_cannot_claim_execution(self):
        self.denied["execution_jwt"] = self.bundle["execution_jwt"]
        self.denied["response"] = self.bundle["response"]
        self.bundle = self.denied
        self.fails("denied operation")

    def test_unsupported_profile_version_and_non_ijson_numbers(self):
        self.bundle["profile"] = "obo-interop/999"
        self.fails("schema")
        with self.assertRaises(ValueError):
            digest_json({"amount": float("inf")})

    def test_cross_process_cli_and_replay_set(self):
        cmd = [sys.executable, str(ROOT / "obo"), "verify-bundle", str(EXAMPLE / "accepted.json"),
               "--trust", str(EXAMPLE / "trust.json"), "--at", str(AT)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        replay = subprocess.run(cmd[:4] + [str(EXAMPLE / "accepted.json")] + cmd[4:], capture_output=True, text=True)
        self.assertEqual(replay.returncode, 1)
        self.assertIn("duplicate request or grant", replay.stdout)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trust.json"
            del self.trust["status"]
            path.write_text(json.dumps(self.trust))
            result = subprocess.run(cmd[:5] + [str(path)] + cmd[6:], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["result"], "incomplete")

    def test_fixtures_are_reproducible(self):
        result = subprocess.run([sys.executable, str(EXAMPLE / "demo.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_release_identity_is_explicit(self):
        version = (ROOT / "VERSION").read_text().strip()
        self.assertEqual(version, "0.5.0-alpha.4")
        result = subprocess.run([sys.executable, str(ROOT / "obo"), "--version"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "obo " + version)
        self.assertIn("v" + version, (ROOT / "CHANGELOG.md").read_text())


if __name__ == "__main__":
    unittest.main()
