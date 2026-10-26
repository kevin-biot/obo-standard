#!/usr/bin/env python3
"""Generate public TEST-ONLY cross-language inputs with explicit expected results."""

import argparse
import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from obo_interop import digest_json, digest_token
from test_keycloak import AT, KeycloakAdapterTests

DEST = ROOT / "tests/vectors/keycloak/corpus.json"


def json_text(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def build():
    KeycloakAdapterTests.setUpClass()
    cases = []

    def add(name, mutate=None, result="failed", outcome=None, raw_bundle=None):
        fixture = KeycloakAdapterTests()
        fixture.setUp()
        if mutate:
            mutate(fixture)
        bundle = raw_bundle(fixture) if raw_bundle else json_text(fixture.bundle)
        cases.append({"name": name, "at": AT, "bundle_json": bundle, "trust_json": json_text(fixture.trust),
                      "expected": {"result": result, **({"outcome": outcome} if outcome else {})}})

    def resign(field, changes, delete=()):
        return lambda f: f.resign(field, changes, delete)

    def remove_status(f):
        del f.trust["status"]

    def deny(f):
        f.resign("policy_jwt", {"allowed_fields": ["credit_limit"]})
        f.resign("decision_jwt", {"policy_digest": digest_token(f.bundle["policy_jwt"]), "outcome": "deny", "reason_code": "policy.deny"})
        del f.bundle["execution_jwt"], f.bundle["response"]

    add("completed", result="verified", outcome="completed")
    add("failed-execution", resign("execution_jwt", {"outcome": "failed"}), "verified", "failed")
    add("policy-denial", deny, "verified", "denied")
    add("missing-status", remove_status, "incomplete", "completed")
    for field in ("delegation_jwt", "decision_jwt", "execution_jwt", "response"):
        add("missing-" + field, lambda f, field=field: f.bundle.pop(field))
    add("unknown-profile", lambda f: f.bundle.update(profile="obo-keycloak/unknown"))
    add("extra-bundle-member", lambda f: f.bundle.update(unrecognized_constraint=True))
    add("extra-trust-member", lambda f: f.trust.update(unrecognized_constraint=True))
    add("changed-parameters", lambda f: f.operation["parameters"].update(contact_email="attacker@example.com"))
    add("changed-resource", lambda f: f.operation.update(resource="supplier:other"))
    for name, value in (("sub", "another-account"), ("iss", "https://attacker.example"), ("aud", "other-service"),
                        ("aud", ["https://gateway.example", "other"]), ("client_id", "other"), ("azp", "other"),
                        ("scope", "supplier:update supplier:delete"), ("typ", "ID"), ("iat", False),
                        ("iat", AT + 1), ("exp", AT), ("jti", "swapped-grant")):
        add("workload-" + name + "-" + str(len(cases)), resign("grant_jwt", {name: value}))
    for name, value in (("act", {"sub": "parent"}), ("cnf", {"jkt": "holder"}), ("nbf", AT - 1),
                        ("authorization_details", []), ("realm_access", {"roles": ["admin"]})):
        add("unsupported-" + name, resign("grant_jwt", {name: value}))
    for name, value in (("sub", "another-principal"), ("client_id", "other"), ("workload_subject", "other"),
                        ("operator_id", "other"), ("scope", "supplier:delete"), ("exp", AT + 301), ("iat", AT - 11)):
        add("mandate-" + name, resign("delegation_jwt", {name: value}))
    for name in ("grant_digest", "delegation_digest", "operation_digest", "policy_digest", "request_id", "sub"):
        add("decision-" + name, resign("decision_jwt", {name: "wrong"}))
    add("decision-contradicts-policy", resign("decision_jwt", {"outcome": "deny", "reason_code": "policy.deny"}))
    for name in ("decision_digest", "operation_digest", "response_digest", "request_id", "sub"):
        add("execution-" + name, resign("execution_jwt", {name: "wrong"}))
    add("execution-expired-authority", resign("execution_jwt", {"iat": AT + 100, "exp": AT + 200}))
    add("execution-after-status", resign("execution_jwt", {"iat": AT + 50}))
    add("changed-response", lambda f: f.bundle["response"].update(unexpected="change"))
    add("revoked-grant", lambda f: f.trust["status"].update(revoked_grant_ids=["keycloak-grant"]))
    add("stale-status", lambda f: f.trust["status"].update(valid_until=AT))
    add("future-status", lambda f: f.trust["status"].update(as_of=AT + 1))
    add("wrong-pinned-subject", lambda f: f.trust["expected"].update(workload_subject="other"))
    add("wrong-pinned-key-id", lambda f: f.trust["workload_issuer"]["jwk"].update(kid="other"))
    add("forged-signature", lambda f: f.bundle.update(grant_jwt=f.bundle["grant_jwt"].rsplit(".", 1)[0] + "." + "A" * 342))
    add("noncanonical-base64url", lambda f: f.bundle.update(grant_jwt=f.bundle["grant_jwt"] + "="))

    def change_header(f, changes):
        parts = f.bundle["grant_jwt"].split(".")
        header = jwt.get_unverified_header(f.bundle["grant_jwt"])
        header.update(changes)
        parts[0] = base64.urlsafe_b64encode(json_text(header).encode()).decode().rstrip("=")
        f.bundle["grant_jwt"] = ".".join(parts)

    add("algorithm-confusion", lambda f: change_header(f, {"alg": "HS256"}))
    add("unsupported-critical-header", lambda f: change_header(f, {"crit": ["extra"], "extra": True}))
    add("embedded-key-url", lambda f: change_header(f, {"jku": "https://attacker.example/keys"}))
    add("wrong-workload-token-type", lambda f: change_header(f, {"typ": "at+jwt"}))
    add("role-key-substitution", lambda f: f.bundle.update(delegation_jwt=f.sign("service", "obo-delegation+jwt", f.mandate)))
    add("legacy-profile-not-translated", lambda f: f.bundle.update(profile="obo-interop/0.5-alpha.1"))

    def raw_grant(f, transform):
        token = f.bundle["grant_jwt"]
        header, payload, _ = token.split(".")
        raw = transform(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode())
        encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
        message = (header + "." + encoded).encode()
        signature = f.rsa_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        f.bundle["grant_jwt"] = message.decode() + "." + base64.urlsafe_b64encode(signature).decode().rstrip("=")
        # Rebind the downstream evidence, so rejection must concern this grant.
        f.resign("delegation_jwt", {"grant_digest": digest_token(f.bundle["grant_jwt"])})
        f.resign("decision_jwt", {"grant_digest": digest_token(f.bundle["grant_jwt"]),
                                  "delegation_digest": digest_token(f.bundle["delegation_jwt"])})
        f.resign("execution_jwt", {"decision_digest": digest_token(f.bundle["decision_jwt"])})

    add("signed-duplicate-member", lambda f: raw_grant(f, lambda raw: raw[:-1] + ',"sub":"account-uuid"}'))
    add("signed-fractional-time", lambda f: raw_grant(f, lambda raw: raw.replace('"iat":' + str(AT - 10), '"iat":' + str(AT - 10) + '.0')))
    add("signed-exponent-time", lambda f: raw_grant(f, lambda raw: raw.replace('"iat":' + str(AT - 10), '"iat":' + str(AT - 10) + 'e0')))
    add("outer-duplicate-member", raw_bundle=lambda f: json_text(f.bundle)[:-1] + ',"profile":"obo-keycloak/0.5-alpha.3"}')
    add("outer-trailing-comma", raw_bundle=lambda f: json_text(f.bundle)[:-1] + ',}')

    def structured(f):
        f.operation["parameters"]["contact_email"] = {"\ue000": "bmp", "\U0001f600": "astral", "a": [-0.0, 1e-7, 1e20, 333333333.3333333],
                                                      "__proto__": {"polluted": False}, "text": "\u00e9\n\t"}
        op_hash = digest_json(f.operation)
        f.resign("delegation_jwt", {"operation_digest": op_hash})
        f.resign("decision_jwt", {"operation_digest": op_hash, "delegation_digest": digest_token(f.bundle["delegation_jwt"])})
        f.bundle["response"] = {"structured_test_only": f.operation["parameters"]}
        f.resign("execution_jwt", {"operation_digest": op_hash, "decision_digest": digest_token(f.bundle["decision_jwt"]),
                                   "response_digest": digest_json(f.bundle["response"])})

    add("jcs-unicode-numeric-prototype-keys", structured, "verified", "completed")
    return {"suite": "obo-keycloak-vectors/0.5-alpha.4", "profile": "obo-keycloak/0.5-alpha.3",
            "notice": "PUBLIC TEST KEYS AND SYNTHETIC TOKENS ONLY. Not real Keycloak runtime evidence or legal authority.", "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    serialized = json.dumps(build(), indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if args.check:
        if not DEST.exists() or DEST.read_text() != serialized:
            raise SystemExit("shared Keycloak vectors differ; regenerate with scripts/keycloak_vectors.py")
        print("shared Keycloak vectors reproduce exactly")
    else:
        DEST.write_text(serialized)
        print(f"generated {len(json.loads(serialized)['cases'])} public cases at {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
