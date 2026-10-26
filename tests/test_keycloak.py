"""Deterministic-time adversarial checks for the explicitly bounded adapter."""

import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_private_key

from obo_interop import digest_json, digest_token
from obo_keycloak import PROFILE, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
AT = 1793016000


class KeycloakAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rsa_key = load_pem_private_key((ROOT / "tests/vectors/keycloak/TEST-ONLY-RSA.pem").read_bytes(), password=None)
        cls.keys = {role: ed25519.Ed25519PrivateKey.from_private_bytes(bytes([i]) * 32)
                    for i, role in enumerate(("issuer", "policy_authority", "service"), 1)}

    def sign(self, role, typ, claims):
        if role == "workload_issuer":
            key, algorithm, kid = self.rsa_key, "RS256", "rsa-test"
        else:
            key, algorithm, kid = self.keys[role], "EdDSA", role
        return jwt.encode(claims, key, algorithm=algorithm, headers={"typ": typ, "kid": kid})

    def setUp(self):
        jwk = jwt.algorithms.RSAAlgorithm.to_jwk(self.rsa_key.public_key(), as_dict=True)
        jwk = {name: jwk[name] for name in ("kty", "n", "e")}
        self.trust = {"profile": PROFILE, "workload_issuer": {
            "iss": "https://keycloak.example/realms/obo", "jwk": {**jwk, "kid": "rsa-test", "alg": "RS256", "use": "sig"}},
            **{role: {"iss": "https://" + role + ".example", "kid": role,
                      "public_key": base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode().rstrip("=")}
               for role, key in self.keys.items()},
            "expected": {"principal_id": "urn:org:buyer", "agent_id": "procurement-agent", "workload_subject": "account-uuid",
                         "operator_id": "urn:org:operator", "audience": "https://gateway.example", "scope": "supplier:update"},
            "status": {"as_of": AT - 1, "valid_until": AT + 50, "revoked_grant_ids": []}}
        self.operation = {"request_id": "request-1", "action": "supplier.update", "resource": "supplier:1",
                          "parameters": {"contact_email": "new@example.com"}}
        self.workload = {"iss": self.trust["workload_issuer"]["iss"], "sub": "account-uuid", "aud": "https://gateway.example",
                         "iat": AT - 10, "exp": AT + 300, "jti": "keycloak-grant", "typ": "Bearer",
                         "azp": "procurement-agent", "client_id": "procurement-agent", "scope": "supplier:update",
                         "clientHost": "127.0.0.1", "clientAddress": "127.0.0.1"}
        self.bundle = {"profile": PROFILE, "operation": self.operation,
                       "grant_jwt": self.sign("workload_issuer", "JWT", self.workload)}
        common = {"aud": "https://gateway.example", "sub": "urn:org:buyer", "iat": AT, "exp": AT + 100}
        self.mandate = {**common, "iss": self.trust["issuer"]["iss"], "jti": "mandate-1", "profile": PROFILE,
                        "grant_digest": digest_token(self.bundle["grant_jwt"]), "operation_digest": digest_json(self.operation),
                        "workload_subject": "account-uuid", "client_id": "procurement-agent", "operator_id": "urn:org:operator",
                        "scope": "supplier:update"}
        self.bundle["delegation_jwt"] = self.sign("issuer", "obo-delegation+jwt", self.mandate)
        self.policy = {**common, "iss": self.trust["policy_authority"]["iss"], "sub": "urn:org:operator", "jti": "policy-1",
                       "profile": PROFILE, "action": "supplier.update", "resource": "supplier:1",
                       "scope": "supplier:update", "allowed_fields": ["contact_email"]}
        self.bundle["policy_jwt"] = self.sign("policy_authority", "obo-policy+jwt", self.policy)
        self.decision = {**common, "iss": self.trust["service"]["iss"], "jti": "decision-1", "profile": PROFILE,
                         "grant_digest": digest_token(self.bundle["grant_jwt"]), "delegation_digest": digest_token(self.bundle["delegation_jwt"]),
                         "policy_digest": digest_token(self.bundle["policy_jwt"]), "operation_digest": digest_json(self.operation),
                         "request_id": "request-1", "client_id": "procurement-agent", "operator_id": "urn:org:operator",
                         "outcome": "allow", "reason_code": "policy.allow"}
        self.bundle["decision_jwt"] = self.sign("service", "obo-decision+jwt", self.decision)
        self.bundle["response"] = {"record": {"contact_email": "new@example.com"}}
        self.execution = {**common, "iss": self.trust["service"]["iss"], "jti": "execution-1", "profile": PROFILE,
                          "decision_digest": digest_token(self.bundle["decision_jwt"]), "operation_digest": digest_json(self.operation),
                          "response_digest": digest_json(self.bundle["response"]), "request_id": "request-1", "outcome": "completed"}
        self.bundle["execution_jwt"] = self.sign("service", "obo-execution+jwt", self.execution)

    def resign(self, field, changes, delete=()):
        role, typ = {"grant_jwt": ("workload_issuer", "JWT"), "delegation_jwt": ("issuer", "obo-delegation+jwt"),
                     "policy_jwt": ("policy_authority", "obo-policy+jwt"), "decision_jwt": ("service", "obo-decision+jwt"),
                     "execution_jwt": ("service", "obo-execution+jwt")}[field]
        claims = jwt.decode(self.bundle[field], options={"verify_signature": False})
        claims.update(changes)
        for name in delete:
            del claims[name]
        self.bundle[field] = self.sign(role, typ, claims)

    def fails(self, pattern=".+"):
        with self.assertRaisesRegex(ValueError, pattern):
            verify_bundle(self.bundle, self.trust, AT)

    def test_valid_native_grant_and_explicit_mandate(self):
        report = verify_bundle(self.bundle, self.trust, AT)
        self.assertEqual(report["result"], "verified")
        self.assertEqual(report["checks"]["explicit_mandate"], "verified")
        self.assertNotEqual(self.workload["sub"], self.mandate["sub"])

    def test_missing_mandate_and_wrong_profile(self):
        del self.bundle["delegation_jwt"]
        self.fails("schema")
        self.setUp()
        self.bundle["profile"] = "obo-interop/0.5-alpha.1"
        self.fails("schema")

    def test_changed_operation(self):
        self.operation["parameters"]["contact_email"] = "attacker@example.com"
        self.fails("mandate operation")

    def test_valid_token_swapping(self):
        self.resign("grant_jwt", {"jti": "other-grant"})
        self.fails("mandate grant")

    def test_workload_identity_and_audience_are_independently_pinned(self):
        for changes in ({"iss": "https://attacker.example"}, {"sub": "other"}, {"aud": "wrong"},
                        {"aud": ["https://gateway.example", "extra"]}, {"azp": "other"}, {"client_id": "other"}):
            with self.subTest(changes=changes):
                self.setUp()
                self.resign("grant_jwt", changes)
                self.fails()

    def test_unknown_native_constraints_are_not_dropped(self):
        for changes in ({"act": {"sub": "parent"}}, {"cnf": {"jkt": "key"}}, {"nbf": AT - 10},
                        {"authorization_details": []}, {"realm_access": {"roles": ["admin"]}}):
            with self.subTest(changes=changes):
                self.setUp()
                self.resign("grant_jwt", changes)
                self.fails("unsupported workload claims")

    def test_workload_time_scope_and_token_type(self):
        for changes in ({"exp": AT}, {"iat": AT + 1}, {"iat": False}, {"exp": 2**53},
                        {"scope": "supplier:update supplier:delete"}, {"typ": "ID"}):
            with self.subTest(changes=changes):
                self.setUp()
                self.resign("grant_jwt", changes)
                self.fails()

    def test_mandate_identity_operator_scope_and_profile(self):
        for changes in ({"sub": "other"}, {"client_id": "other"}, {"workload_subject": "other"},
                        {"operator_id": "other"}, {"scope": "supplier:delete"}, {"profile": "other"}, {"act": {}}):
            with self.subTest(changes=changes):
                self.setUp()
                self.resign("delegation_jwt", changes)
                self.fails()

    def test_mandate_cannot_outlive_or_predate_grant(self):
        for changes in ({"exp": AT + 301}, {"iat": AT - 11}, {"iat": AT + 1}, {"exp": AT}):
            with self.subTest(changes=changes):
                self.setUp()
                self.resign("delegation_jwt", changes)
                self.fails("validity")

    def test_decision_must_bind_exact_mandate(self):
        self.resign("decision_jwt", {"delegation_digest": "sha256:" + "0" * 64})
        self.fails("delegation_digest mismatch")
        self.setUp()
        self.resign("decision_jwt", {}, delete=["delegation_digest"])
        self.fails("unsupported or missing")

    def test_forged_signature_and_untrusted_role_key(self):
        self.bundle["grant_jwt"] = self.bundle["grant_jwt"].rsplit(".", 1)[0] + "." + "A" * 342
        self.fails()
        self.setUp()
        self.bundle["delegation_jwt"] = self.sign("service", "obo-delegation+jwt", self.mandate)
        self.fails()

    def test_duplicate_json_and_unsupported_header(self):
        for part, raw in ((0, '{"alg":"RS256","typ":"JWT","kid":"rsa-test","jku":"https://attacker.example"}'),
                          (1, '{"sub":"one","sub":"two"}')):
            with self.subTest(part=part):
                self.setUp()
                parts = self.bundle["grant_jwt"].split(".")
                parts[part] = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
                self.bundle["grant_jwt"] = ".".join(parts)
                self.fails()

    def test_changed_policy_response_and_receipt(self):
        self.resign("policy_jwt", {"allowed_fields": ["credit_limit"]})
        self.resign("decision_jwt", {"policy_digest": digest_token(self.bundle["policy_jwt"])})
        self.fails("disagrees")
        self.setUp()
        self.bundle["response"]["record"]["contact_email"] = "other@example.com"
        self.fails("response mismatch")

    def test_status_is_not_assumed(self):
        del self.trust["status"]
        self.assertEqual(verify_bundle(self.bundle, self.trust, AT)["result"], "incomplete")
        self.setUp()
        self.trust["status"]["revoked_grant_ids"] = ["keycloak-grant"]
        self.fails("revoked")
        self.setUp()
        self.trust["status"]["valid_until"] = AT
        self.fails("status snapshot")

    def test_policy_denial_is_evidence_not_permission(self):
        self.resign("policy_jwt", {"allowed_fields": ["credit_limit"]})
        self.resign("decision_jwt", {"policy_digest": digest_token(self.bundle["policy_jwt"]),
                                    "outcome": "deny", "reason_code": "policy.deny"})
        self.fails("denied operation")
        del self.bundle["response"], self.bundle["execution_jwt"]
        report = verify_bundle(self.bundle, self.trust, AT)
        self.assertEqual((report["result"], report["outcome"]), ("verified", "denied"))

    def test_execution_must_fit_the_shorter_mandate_window(self):
        self.resign("delegation_jwt", {"exp": AT + 2})
        self.resign("decision_jwt", {"delegation_digest": digest_token(self.bundle["delegation_jwt"])})
        self.resign("execution_jwt", {"decision_digest": digest_token(self.bundle["decision_jwt"]), "iat": AT + 2})
        self.fails("outside authorization window")

    def test_algorithm_confusion_and_noncanonical_encoding(self):
        for header in ({"alg": "HS256", "typ": "JWT", "kid": "rsa-test"},
                       {"alg": "RS256", "typ": "at+jwt", "kid": "rsa-test"}):
            with self.subTest(header=header):
                self.setUp()
                parts = self.bundle["grant_jwt"].split(".")
                parts[0] = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
                self.bundle["grant_jwt"] = ".".join(parts)
                self.fails("JOSE mismatch")
        self.setUp()
        self.bundle["grant_jwt"] += "="
        self.fails("non-base64url")

    def test_cli_profile_dispatch_exit_codes_and_duplicate_set(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle_path, trust_path = (Path(directory) / name for name in ("bundle.json", "trust.json"))
            bundle_path.write_text(json.dumps(self.bundle))
            trust_path.write_text(json.dumps(self.trust))
            cmd = [sys.executable, str(ROOT / "obo"), "verify-bundle", str(bundle_path), "--trust", str(trust_path), "--at", str(AT)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run(cmd[:4] + [str(bundle_path)] + cmd[4:], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("duplicate request or grant", result.stdout)
            del self.trust["status"]
            trust_path.write_text(json.dumps(self.trust))
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
            self.bundle["profile"] = "unknown-profile"
            bundle_path.write_text(json.dumps(self.bundle))
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 1)
