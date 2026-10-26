"""Integration against the unmodified, pinned PocketBase binary; opt in explicitly."""

import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption

from obo_interop import PROFILE, digest_json, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "examples/integrations/pocketbase"
spec = importlib.util.spec_from_file_location("pocketbase_gateway", INTEGRATION / "gateway.py")
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@unittest.skipUnless(os.environ.get("POCKETBASE_BINARY"), "set POCKETBASE_BINARY to run real-service integration")
class PocketBaseLiveTests(unittest.TestCase):
    profile = PROFILE
    evidence_env = "OBO_POCKETBASE_RESULTS"
    verify_evidence = staticmethod(verify_bundle)

    @classmethod
    def configure_issuer(cls):
        """The base experiment issues its own grant; subclasses can replace it."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="obo-pocketbase-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        cls.pb_port, cls.gateway_port = free_port(), free_port()
        while cls.gateway_port == cls.pb_port:
            cls.gateway_port = free_port()
        cls.pb_url = f"http://127.0.0.1:{cls.pb_port}"
        cls.gateway_url = f"http://127.0.0.1:{cls.gateway_port}"
        cls.binary = str(Path(os.environ["POCKETBASE_BINARY"]).resolve())
        version = subprocess.run([cls.binary, "--version"], capture_output=True, text=True, check=True)
        if version.stdout.strip() != "pocketbase version 0.40.6":
            raise RuntimeError("Integration is pinned to PocketBase 0.40.6")
        cls.admin_password = secrets.token_urlsafe(32)
        subprocess.run([cls.binary, "superuser", "upsert", "admin@example.com", cls.admin_password,
                        "--dir", str(cls.work / "pb_data")], check=True, capture_output=True)
        cls.pb = cls.start_pb()
        cls.addClassCleanup(lambda: cls.stop(cls.pb))
        auth = gateway.http_json(cls.pb_url + "/api/collections/_superusers/auth-with-password", "POST",
                                 {"identity": "admin@example.com", "password": cls.admin_password})
        cls.admin = auth["token"]
        gateway.http_json(cls.pb_url + "/api/collections", "POST", {
            "name": "obo_services", "type": "auth", "authRule": "", "manageRule": None,
            "passwordAuth": {"enabled": True, "identityFields": ["email"]},
            "authAlert": {"enabled": False}}, cls.admin)
        password = secrets.token_urlsafe(32)
        gateway.http_json(cls.pb_url + "/api/collections/obo_services/records", "POST", {
            "email": "gateway@example.com", "password": password, "passwordConfirm": password}, cls.admin)
        native_auth = gateway.http_json(cls.pb_url + "/api/collections/obo_services/auth-with-password", "POST",
                                        {"identity": "gateway@example.com", "password": password})
        cls.backend_token = native_auth["token"]
        native_rule = '@request.auth.collectionName = "obo_services"'
        gateway.http_json(cls.pb_url + "/api/collections", "POST", {
            "name": "suppliers", "type": "base", "listRule": None, "viewRule": native_rule,
            "createRule": None, "deleteRule": None,
            "updateRule": native_rule + ' && @request.body.credit_limit:changed = false',
            "fields": [{"name": "contact_email", "type": "email", "required": True},
                       {"name": "credit_limit", "type": "number", "min": 0},
                       {"name": "updated", "type": "autodate", "onCreate": True, "onUpdate": True}]}, cls.admin)
        cls.record_id = "supplier0000001"
        cls.record_url = cls.pb_url + "/api/collections/suppliers/records/" + cls.record_id
        gateway.http_json(cls.pb_url + "/api/collections/suppliers/records", "POST", {
            "id": cls.record_id, "contact_email": "old@example.com", "credit_limit": 100}, cls.admin)

        cls.keys = {role: Ed25519PrivateKey.generate() for role in ("issuer", "policy_authority", "service")}
        cls.now = int(time.time())
        cls.trust = {"profile": cls.profile,
            **{role: {"iss": f"https://{role.replace('_', '-')}.example", "kid": role + "-live-test",
                      "public_key": base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode().rstrip("=")}
               for role, key in cls.keys.items()},
            "expected": {"principal_id": "urn:org:buyer.example", "agent_id": "urn:agent:procurement",
                         "operator_id": "urn:org:operator.example", "audience": cls.gateway_url,
                         "scope": "supplier:update"},
            "status": {"as_of": cls.now - 60, "valid_until": cls.now + 3600, "revoked_grant_ids": []}}
        cls.configure_issuer()
        cls.trust_path = cls.work / "trust.json"
        cls.trust_path.write_text(json.dumps(cls.trust))
        cls.service_key = cls.work / "service.pem"
        cls.service_key.write_bytes(cls.keys["service"].private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        cls.service_key.chmod(0o600)
        cls.config = {"trust_path": str(cls.trust_path), "service_key_path": str(cls.service_key),
                      "ledger_path": str(cls.work / "ledger.sqlite"), "backend_url": cls.pb_url,
                      "backend_token": cls.backend_token, "record_id": cls.record_id,
                      "policy_jwt": cls.sign("policy_authority", "obo-policy+jwt", {
                          "sub": cls.trust["expected"]["operator_id"], "profile": cls.profile,
                          "scope": "supplier:update", "action": "supplier.update",
                          "resource": "supplier:" + cls.record_id, "allowed_fields": ["contact_email"]})}
        cls.config_path = cls.work / "gateway.json"
        cls.config_path.write_text(json.dumps(cls.config))
        cls.config_path.chmod(0o600)
        cls.receiving = cls.start_gateway()
        cls.addClassCleanup(lambda: cls.stop(cls.receiving))

    @classmethod
    def sign(cls, role, typ, claims):
        expected = cls.trust["expected"]
        return jwt.encode({"iss": cls.trust[role]["iss"], "sub": expected["principal_id"],
                           "aud": expected["audience"], "iat": int(time.time()) - 1,
                           "exp": cls.now + 3600, "jti": str(uuid.uuid4()), **claims}, cls.keys[role],
                          algorithm="EdDSA", headers={"typ": typ, "kid": cls.trust[role]["kid"]})

    @classmethod
    def stop(cls, process):
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    @classmethod
    def start(cls, args, url, name):
        log = (cls.work / name).open("a")
        cls.addClassCleanup(log.close)
        process = subprocess.Popen(args, cwd=cls.work, stdout=log, stderr=log)
        cls.addClassCleanup(lambda: cls.stop(process))
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"{name} exited: " + (cls.work / name).read_text()[-4000:])
            try:
                gateway.http_json(url)
                return process
            except Exception:
                time.sleep(0.05)
        raise RuntimeError(f"{name} startup timeout")

    @classmethod
    def start_pb(cls):
        return cls.start([cls.binary, "serve", "--http", f"127.0.0.1:{cls.pb_port}",
                          "--dir", str(cls.work / "pb_data")], cls.pb_url + "/api/health", "pocketbase.log")

    @classmethod
    def start_gateway(cls):
        return cls.start([sys.executable, str(INTEGRATION / "gateway.py"), "--config", str(cls.config_path),
                          "--port", str(cls.gateway_port)], cls.gateway_url + "/health", "gateway.log")

    def setUp(self):
        gateway.http_json(self.record_url, "PATCH", {"contact_email": "old@example.com", "credit_limit": 100}, self.admin)

    def operation(self, parameters, request_id=None, grant_id=None):
        operation = {"request_id": request_id or str(uuid.uuid4()), "action": "supplier.update",
                     "resource": "supplier:" + self.record_id, "parameters": parameters}
        claims = {"client_id": self.trust["expected"]["agent_id"], "scope": "supplier:update",
                  "obo": {"profile": PROFILE, "operator_id": self.trust["expected"]["operator_id"],
                          "operation_digest": digest_json(operation)}}
        if grant_id:
            claims["jti"] = grant_id
        return {"operation": operation, "grant_jwt": self.sign("issuer", "at+jwt", claims)}

    def call(self, incoming):
        try:
            return 200, gateway.http_json(self.gateway_url + "/operations", "POST", incoming)
        except gateway.BackendError as exc:
            return exc.status, exc.body

    def assert_bundle(self, result, expected_outcome):
        bundle = result["bundle"]
        at = jwt.decode(bundle["decision_jwt"], options={"verify_signature": False})["iat"]
        report = self.verify_evidence(bundle, self.trust, at)
        self.assertEqual(report["outcome"], expected_outcome)
        self.assertEqual(report["result"], "verified")
        output = os.environ.get(self.evidence_env)
        if output:
            dest = Path(output)
            dest.mkdir(parents=True, exist_ok=True)
            (dest / (expected_outcome + ".json")).write_text(json.dumps(bundle, indent=2))
            (dest / "trust.json").write_text(json.dumps(self.trust, indent=2))
            (dest / (expected_outcome + "-report.json")).write_text(json.dumps(report, indent=2))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.json"
            path.write_text(json.dumps(bundle))
            checked = subprocess.run([sys.executable, str(ROOT / "obo"), "verify-bundle", str(path),
                                      "--trust", str(self.trust_path), "--at", str(at)], capture_output=True, text=True)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        return bundle

    def test_persisted_update_and_idempotent_retry_after_both_restarts(self):
        incoming = self.operation({"contact_email": "accounts@example.com"})
        code, result = self.call(incoming)
        self.assertEqual(code, 200, result)
        bundle = self.assert_bundle(result, "completed")
        before_restart = gateway.http_json(self.record_url, token=self.admin)
        self.assertEqual(before_restart["contact_email"], "accounts@example.com")
        self.stop(self.pb)
        type(self).pb = self.start_pb()
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before_restart)
        self.stop(self.receiving)
        type(self).receiving = self.start_gateway()
        code, replay = self.call(incoming)
        self.assertEqual(code, 200, replay)
        self.assertTrue(replay["cached"])
        self.assertEqual(replay["bundle"], bundle)
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before_restart)

    def test_policy_denial_leaves_record_unchanged(self):
        before = gateway.http_json(self.record_url, token=self.admin)
        code, result = self.call(self.operation({"credit_limit": 99999}))
        self.assertEqual(code, 403, result)
        self.assert_bundle(result, "denied")
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_backend_validation_failure_is_recorded_without_write(self):
        before = gateway.http_json(self.record_url, token=self.admin)
        code, result = self.call(self.operation({"contact_email": "not-an-email"}))
        self.assertEqual(code, 422, result)
        self.assert_bundle(result, "failed")
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_invalid_signature_or_changed_parameters_never_write(self):
        before = gateway.http_json(self.record_url, token=self.admin)
        incoming = self.operation({"contact_email": "authorized@example.com"})
        modified = copy.deepcopy(incoming)
        modified["operation"]["parameters"]["contact_email"] = "attacker@example.com"
        self.assertEqual(self.call(modified)[0], 401)
        incoming["grant_jwt"] = incoming["grant_jwt"].rsplit(".", 1)[0] + "." + "A" * 86
        self.assertEqual(self.call(incoming)[0], 401)
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_reused_grant_id_cannot_authorize_different_request(self):
        grant_id = str(uuid.uuid4())
        self.assertEqual(self.call(self.operation({"contact_email": "first@example.com"}, grant_id=grant_id))[0], 200)
        before = gateway.http_json(self.record_url, token=self.admin)
        code, _ = self.call(self.operation({"contact_email": "second@example.com"}, grant_id=grant_id))
        self.assertEqual(code, 409)
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_native_backend_rules_reject_unauthenticated_and_credit_changes(self):
        before = gateway.http_json(self.record_url, token=self.admin)
        for token, params in ((None, {"contact_email": "attacker@example.com"}),
                              (self.backend_token, {"credit_limit": 99999})):
            with self.assertRaises(gateway.BackendError):
                gateway.http_json(self.record_url, "PATCH", params, token)
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_unresolved_reservation_blocks_automatic_retry(self):
        incoming = self.operation({"contact_email": "new@example.com"})
        claims = jwt.decode(incoming["grant_jwt"], options={"verify_signature": False})
        with sqlite3.connect(self.config["ledger_path"]) as db:
            db.execute("INSERT INTO requests VALUES (?,?,?,?, 'reserved',NULL,NULL)",
                       (incoming["operation"]["request_id"], claims["iss"], claims["jti"], digest_json(incoming)))
        before = gateway.http_json(self.record_url, token=self.admin)
        self.assertEqual(self.call(incoming)[0], 409)
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_backend_outage_requires_reconciliation_instead_of_automatic_retry(self):
        incoming = self.operation({"contact_email": "outage@example.com"})
        before = gateway.http_json(self.record_url, token=self.admin)
        self.stop(self.pb)
        try:
            code, result = self.call(incoming)
            self.assertEqual(code, 503, result)
            self.assertEqual(result["error"], "backend_outcome_unknown")
            self.assertNotIn("bundle", result)
        finally:
            type(self).pb = self.start_pb()
        self.assertEqual(self.call(incoming)[0], 409)
        self.assertEqual(gateway.http_json(self.record_url, token=self.admin), before)

    def test_readback_failure_after_patch_is_not_reported_as_failed_execution(self):
        incoming = self.operation({"contact_email": "readback@example.com"})
        app = gateway.create_app(str(self.config_path))
        with patch.object(gateway, "http_json", side_effect=[{"id": self.record_id}, gateway.BackendError(404, {})]):
            response = app.test_client().post("/operations", json=incoming)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], "backend_outcome_unknown")
        self.assertNotIn("bundle", response.json)
        self.assertEqual(self.call(incoming)[0], 409)


if __name__ == "__main__":
    unittest.main()
