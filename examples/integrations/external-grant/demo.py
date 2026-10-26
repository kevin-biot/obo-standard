#!/usr/bin/env python3
"""Reproduce public TEST-ONLY evidence fixtures. Never use these keys in deployment."""

import argparse
import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from obo_interop import PROFILE, digest_json, digest_token

AT = 1793016000


def fixtures():
    # Public, deterministic TEST keys. These do not identify a real organization.
    keys = {role: Ed25519PrivateKey.from_private_bytes(bytes([seed]) * 32)
            for role, seed in (("issuer", 1), ("policy_authority", 2), ("service", 3))}
    anchors = {
        role: {"iss": f"https://{role.replace('_', '-')}.example", "kid": role + "-test-1",
               "public_key": base64.urlsafe_b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode().rstrip("=")}
        for role, key in keys.items()
    }
    expected = {"principal_id": "urn:org:buyer.example", "agent_id": "urn:agent:buyer:procurement",
                "operator_id": "urn:org:operator.example", "audience": "https://supplier.example/api",
                "scope": "supplier:update"}
    trust = {"profile": PROFILE, **anchors, "expected": expected,
             "status": {"as_of": AT - 60, "valid_until": AT + 60, "revoked_grant_ids": []}}

    def sign(role, typ, claims, issued=AT):
        payload = {"iss": anchors[role]["iss"], "sub": expected["principal_id"],
                   "aud": expected["audience"], "iat": issued, "exp": AT + 300,
                   "jti": typ + "-test", **claims}
        return jwt.encode(payload, keys[role], algorithm="EdDSA",
                          headers={"typ": typ, "kid": anchors[role]["kid"]})

    policy_claims = {
        "profile": PROFILE, "sub": expected["operator_id"], "action": "supplier.update",
        "resource": "supplier:42", "allowed_fields": ["contact_email"], "scope": "supplier:update"}
    policy = sign("policy_authority", "obo-policy+jwt", policy_claims, AT - 30)
    bundles = {}
    for name, parameters in (("accepted", {"contact_email": "accounts@example.com"}),
                             ("denied", {"credit_limit": 100000})):
        operation = {"request_id": "request-test-" + name, "action": "supplier.update", "resource": "supplier:42",
                     "parameters": parameters}
        allowed = (operation["action"] == policy_claims["action"]
                   and operation["resource"] == policy_claims["resource"]
                   and set(parameters) <= set(policy_claims["allowed_fields"]))
        operation_hash = digest_json(operation)
        grant = sign("issuer", "at+jwt", {"jti": "grant-test-" + name, "client_id": expected["agent_id"],
                     "scope": "supplier:update", "obo": {"profile": PROFILE, "operator_id": expected["operator_id"],
                     "operation_digest": operation_hash}}, AT - 10)
        decision = sign("service", "obo-decision+jwt", {"jti": "decision-test-" + name,
                        "profile": PROFILE, "grant_digest": digest_token(grant), "policy_digest": digest_token(policy),
                        "operation_digest": operation_hash, "request_id": operation["request_id"],
                        "client_id": expected["agent_id"], "operator_id": expected["operator_id"],
                        "outcome": "allow" if allowed else "deny", "reason_code": "policy.allow" if allowed else "policy.deny"})
        bundle = {"profile": PROFILE, "operation": operation, "grant_jwt": grant,
                  "policy_jwt": policy, "decision_jwt": decision}
        if allowed:
            # In-memory service simulation; no live supplier system is changed.
            record = {"contact_email": "old@example.com", "record_version": 7}
            record.update(parameters)
            record["record_version"] += 1
            response = {"supplier_id": operation["resource"], "record_version": record["record_version"],
                        "updated": sorted(parameters)}
            execution = sign("service", "obo-execution+jwt", {"profile": PROFILE,
                             "decision_digest": digest_token(decision), "operation_digest": operation_hash,
                             "response_digest": digest_json(response), "request_id": operation["request_id"],
                             "outcome": "completed"}, AT + 1)
            bundle.update(execution_jwt=execution, response=response)
        bundles[name + ".json"] = bundle
    return {"trust.json": trust, **bundles}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare generated fixtures without writing")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    for name, data in fixtures().items():
        path = args.output_dir / name
        serialized = json.dumps(data, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text() != serialized:
                raise SystemExit(f"fixture drift: {path}")
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(serialized)
    print("public test fixtures match" if args.check else "wrote public TEST-ONLY fixtures")


if __name__ == "__main__":
    main()
