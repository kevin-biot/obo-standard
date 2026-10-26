"""Real Keycloak -> explicit mandate -> OBO gateway -> real PocketBase."""

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import uuid

import jwt

from keycloak_support import Keycloak
import test_pocketbase_live as pocketbase
from obo_interop import digest_json, digest_token
import obo_keycloak


@unittest.skipUnless(os.environ.get("OBO_KEYCLOAK_LIVE") == "1" and os.environ.get("POCKETBASE_BINARY"),
                     "set OBO_KEYCLOAK_LIVE=1 and POCKETBASE_BINARY for the independent issuer test")
class KeycloakLiveTests(pocketbase.PocketBaseLiveTests):
    profile = obo_keycloak.PROFILE
    evidence_env = "OBO_KEYCLOAK_RESULTS"
    verify_evidence = staticmethod(obo_keycloak.verify_bundle)

    def node_check(self, bundle, trust, at, expected_code):
        with tempfile.TemporaryDirectory(prefix="obo-node-live-") as directory:
            bundle_path, trust_path = (Path(directory) / name for name in ("bundle.json", "trust.json"))
            bundle_path.write_text(json.dumps(bundle))
            trust_path.write_text(json.dumps(trust))
            checked = subprocess.run(["node", str(pocketbase.ROOT / "implementations/node/verify.mjs"), str(bundle_path),
                                      "--trust", str(trust_path), "--at", str(at)],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(checked.returncode, expected_code, checked.stdout + checked.stderr)
            return json.loads(checked.stdout)

    def assert_bundle(self, result, expected_outcome):
        bundle = super().assert_bundle(result, expected_outcome)
        if os.environ.get("OBO_NODE_VERIFY") == "1":
            at = jwt.decode(bundle["decision_jwt"], options={"verify_signature": False})["iat"]
            report = self.node_check(bundle, self.trust, at, 0)
            primary = self.verify_evidence(bundle, self.trust, at)
            for field in ("profile", "result", "outcome", "evaluation_time", "checks"):
                self.assertEqual(report[field], primary[field])
            output = os.environ.get(self.evidence_env)
            if output:
                (Path(output) / (expected_outcome + "-node-report.json")).write_text(json.dumps(report, indent=2))
        return bundle

    @classmethod
    def configure_issuer(cls):
        port = pocketbase.free_port()
        while port in (cls.pb_port, cls.gateway_port):
            port = pocketbase.free_port()
        cls.keycloak = Keycloak(port, cls.gateway_url, cls.addClassCleanup)
        cls.trust["workload_issuer"] = {"iss": cls.keycloak.issuer, "jwk": cls.keycloak.jwk}
        cls.trust["expected"].update(agent_id="procurement-agent", workload_subject=cls.keycloak.subject)
        cls.grants = {}

    def operation(self, parameters, request_id=None, grant_id=None):
        operation = {"request_id": request_id or str(uuid.uuid4()), "action": "supplier.update",
                     "resource": "supplier:" + self.record_id, "parameters": parameters}
        if grant_id and grant_id in self.grants:
            token = self.grants[grant_id]
        else:
            token = self.keycloak.token()
            if grant_id:
                self.grants[grant_id] = token
        # Claims are used only to construct a request, then authenticated at admission.
        workload = jwt.decode(token, options={"verify_signature": False})
        delegation = self.sign("issuer", "obo-delegation+jwt", {
            "profile": self.profile, "grant_digest": digest_token(token), "operation_digest": digest_json(operation),
            "workload_subject": self.keycloak.subject, "client_id": "procurement-agent",
            "operator_id": self.trust["expected"]["operator_id"], "scope": "supplier:update",
            "iat": max(int(time.time()), workload["iat"]), "exp": workload["exp"]})
        return {"operation": operation, "grant_jwt": token, "delegation_jwt": delegation}

    def test_native_service_account_is_not_the_legal_principal(self):
        incoming = self.operation({"contact_email": "keycloak@example.com"})
        native = obo_keycloak.verify_workload(incoming["grant_jwt"], self.trust, int(time.time()))
        self.assertEqual(native["sub"], self.keycloak.subject)
        self.assertNotEqual(native["sub"], self.trust["expected"]["principal_id"])
        code, result = self.call(incoming)
        self.assertEqual(code, 200, result)
        bundle = self.assert_bundle(result, "completed")
        self.assertEqual(bundle["grant_jwt"], incoming["grant_jwt"])
        self.assertEqual(bundle["delegation_jwt"], incoming["delegation_jwt"])

    def test_valid_native_token_without_mandate_cannot_write(self):
        before = pocketbase.gateway.http_json(self.record_url, token=self.admin)
        incoming = self.operation({"contact_email": "not-authorized@example.com"})
        del incoming["delegation_jwt"]
        self.assertEqual(self.call(incoming)[0], 401)
        self.assertEqual(pocketbase.gateway.http_json(self.record_url, token=self.admin), before)

    def test_token_swapping_does_not_transfer_the_mandate(self):
        incoming = self.operation({"contact_email": "not-authorized@example.com"})
        other = self.operation({"contact_email": "not-authorized@example.com"})
        self.assertNotEqual(incoming["grant_jwt"], other["grant_jwt"])
        incoming["grant_jwt"] = other["grant_jwt"]
        self.assertEqual(self.call(incoming)[0], 401)

    def test_offline_verification_rejects_wrong_pinned_workload_subject(self):
        code, result = self.call(self.operation({"contact_email": "pinned@example.com"}))
        self.assertEqual(code, 200, result)
        bundle = result["bundle"]
        at = jwt.decode(bundle["decision_jwt"], options={"verify_signature": False})["iat"]
        trust = copy.deepcopy(self.trust)
        trust["expected"]["workload_subject"] = "another-service-account"
        with self.assertRaisesRegex(ValueError, "workload subject mismatch"):
            self.verify_evidence(bundle, trust, at)
        if os.environ.get("OBO_NODE_VERIFY") == "1":
            self.assertEqual(self.node_check(bundle, trust, at, 1)["result"], "failed")
