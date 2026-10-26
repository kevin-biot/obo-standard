#!/usr/bin/env python3
"""Local OBO admission gateway for the pinned PocketBase integration."""

import argparse
import base64
import json
from pathlib import Path
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from flask import Flask, jsonify, request
from obo_interop import PROFILE, digest_json, digest_token, read_json, require, strict_json, verify_bundle, verify_request


class BackendError(Exception):
    def __init__(self, status, body):
        self.status = status
        self.body = body


def http_json(url, method="GET", body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return strict_json(response.read())
    except urllib.error.HTTPError as exc:
        # Do not retain backend tokens or raw exception headers in evidence.
        try:
            body = strict_json(exc.read())
        except ValueError:
            body = {"message": "unparseable backend error"}
        finally:
            exc.close()
        raise BackendError(exc.code, body) from exc


def create_app(config_path):
    config = read_json(config_path)
    trust = read_json(config["trust_path"])
    policy_jwt = config["policy_jwt"]
    key = load_pem_private_key(Path(config["service_key_path"]).read_bytes(), password=None)
    public_key = base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode().rstrip("=")
    require(public_key == trust["service"]["public_key"], "service signing key does not match trust configuration")
    db_path = config["ledger_path"]
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 65536
    with sqlite3.connect(db_path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS requests (
            request_id TEXT PRIMARY KEY, issuer TEXT NOT NULL, grant_id TEXT NOT NULL,
            request_digest TEXT NOT NULL, state TEXT NOT NULL, bundle TEXT, http_status INTEGER,
            UNIQUE(issuer, grant_id))""")

    def sign(typ, claims, issued, expires):
        payload = {"iss": trust["service"]["iss"], "aud": trust["expected"]["audience"],
                   "sub": trust["expected"]["principal_id"], "iat": issued, "exp": expires,
                   "jti": str(uuid.uuid4()), "profile": PROFILE, **claims}
        return jwt.encode(payload, key, algorithm="EdDSA",
                          headers={"typ": typ, "kid": trust["service"]["kid"]})

    def store(request_id, state, bundle, status):
        with sqlite3.connect(db_path) as db:
            db.execute("UPDATE requests SET state=?,bundle=?,http_status=? WHERE request_id=?",
                       (state, json.dumps(bundle), status, request_id))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/operations")
    def operate():
        try:
            incoming = strict_json(request.get_data())
            require(isinstance(incoming, dict) and set(incoming) == {"operation", "grant_jwt"}, "invalid request shape")
            operation, token = incoming["operation"], incoming["grant_jwt"]
            now = int(time.time())
            grant, policy, allowed, op_hash = verify_request(operation, token, policy_jwt, trust, now)
            status = trust.get("status")
            require(status is not None and status["as_of"] <= now < status["valid_until"], "live admission needs fresh status")
            require(grant["jti"] not in status["revoked_grant_ids"], "grant revoked")
            require(operation["resource"] == "supplier:" + config["record_id"], "unsupported backend resource")
            fingerprint = digest_json(incoming)
        except Exception as exc:
            return jsonify({"error": "admission_failed", "detail": str(exc)}), 401

        with sqlite3.connect(db_path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT request_id,request_digest,state,bundle,http_status FROM requests "
                                  "WHERE request_id=? OR (issuer=? AND grant_id=?)",
                                  (operation["request_id"], grant["iss"], grant["jti"])).fetchall()
            if previous:
                if len(previous) == 1:
                    rid, old_digest, state, encoded, code = previous[0]
                    if rid == operation["request_id"] and old_digest == fingerprint and state == "finished":
                        response = jsonify({"cached": True, "bundle": json.loads(encoded)})
                        return response, code
                return jsonify({"error": "replay_or_unresolved_request"}), 409
            db.execute("INSERT INTO requests VALUES (?,?,?,?, 'reserved',NULL,NULL)",
                       (operation["request_id"], grant["iss"], grant["jti"], fingerprint))

        expiry = min(grant["exp"], policy["exp"], status["valid_until"])
        decision = sign("obo-decision+jwt", {
            "grant_digest": digest_token(token), "policy_digest": digest_token(policy_jwt),
            "operation_digest": op_hash, "request_id": operation["request_id"],
            "client_id": grant["client_id"], "operator_id": trust["expected"]["operator_id"],
            "outcome": "allow" if allowed else "deny", "reason_code": "policy.allow" if allowed else "policy.deny"
        }, now, expiry)
        bundle = {"profile": PROFILE, "operation": operation, "grant_jwt": token,
                  "policy_jwt": policy_jwt, "decision_jwt": decision}
        if not allowed:
            store(operation["request_id"], "finished", bundle, 403)
            return jsonify({"cached": False, "bundle": bundle}), 403

        endpoint = config["backend_url"] + "/api/collections/suppliers/records/" + config["record_id"]
        patched = False
        try:
            result = http_json(endpoint, "PATCH", operation["parameters"], config["backend_token"])
            patched = True
            observed = http_json(endpoint, token=config["backend_token"])
            require(all(observed.get(k) == v for k, v in operation["parameters"].items()), "backend readback mismatch")
            response_body = {"backend": "pocketbase", "http_status": 200, "record": result, "readback": observed}
            outcome, response_status = "completed", 200
        except BackendError as exc:
            if patched or exc.status not in (400, 403, 404):
                store(operation["request_id"], "indeterminate", bundle, 503)
                return jsonify({"error": "backend_outcome_unknown", "request_id": operation["request_id"]}), 503
            response_body = {"backend": "pocketbase", "http_status": exc.status, "error": exc.body}
            outcome, response_status = "failed", 422
        except Exception:
            store(operation["request_id"], "indeterminate", bundle, 503)
            return jsonify({"error": "backend_outcome_unknown", "request_id": operation["request_id"]}), 503

        ended = int(time.time())
        if ended >= expiry:
            store(operation["request_id"], "indeterminate", bundle, 503)
            return jsonify({"error": "execution_exceeded_evidence_window"}), 503
        bundle.update(response=response_body, execution_jwt=sign("obo-execution+jwt", {
            "decision_digest": digest_token(decision), "operation_digest": op_hash,
            "response_digest": digest_json(response_body), "request_id": operation["request_id"], "outcome": outcome
        }, ended, expiry))
        verify_bundle(bundle, trust, now)
        store(operation["request_id"], "finished", bundle, response_status)
        return jsonify({"cached": False, "bundle": bundle}), response_status

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=8091)
    args = parser.parse_args()
    create_app(args.config).run(host="127.0.0.1", port=args.port, threaded=True)


if __name__ == "__main__":
    main()
