"""Experimental offline evidence verification; no live authorization service."""

import base64
import hashlib
import json
from pathlib import Path

PROFILE = "obo-interop/0.5-alpha.1"
ROOT = Path(__file__).resolve().parent
LIMITATIONS = [
    "Trust configuration and historical evaluation time are supplied independently by the verifier.",
    "Signed decisions and execution receipts are service assertions, not proof of physical execution.",
    "No proof of possession, live replay prevention, timestamp authority, or complete log coverage.",
    "Legal identity, lawful delegation and duty of care are not adjudicated by this verifier.",
]


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def unique_members(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON member: {key}")
        result[key] = value
    return result


def strict_json(data):
    def reject(value):
        raise VerificationError(f"invalid JSON constant: {value}")
    return json.loads(data, object_pairs_hook=unique_members, parse_constant=reject)


def read_json(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def digest_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_json(value):
    import rfc8785
    return digest_bytes(rfc8785.dumps(value))


def digest_token(token):
    return digest_bytes(token.encode("ascii"))


def validate_schema(value, name):
    from jsonschema import Draft202012Validator
    schema = read_json(ROOT / "schemas" / name)
    errors = list(Draft202012Validator(schema).iter_errors(value))
    require(not errors, "schema: " + "; ".join(error.message for error in errors))


def parse_jwt(token):
    """Reject ambiguous JSON and noncanonical encodings before signature checks."""
    parts = token.split(".")
    require(len(parts) == 3, "expected compact signed JWT")
    decoded = []
    for part in parts:
        require(part and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-" for c in part),
                "non-base64url JWT segment")
        raw = base64.b64decode(part + "=" * (-len(part) % 4), altchars=b"-_", validate=True)
        require(base64.urlsafe_b64encode(raw).decode().rstrip("=") == part, "noncanonical base64url JWT segment")
        decoded.append(raw)
    header, claims = strict_json(decoded[0]), strict_json(decoded[1])
    require(isinstance(header, dict) and set(header) == {"alg", "typ", "kid"}, "unsupported JOSE header")
    require(isinstance(claims, dict), "JWT claims must be an object")
    return header, claims


def verify_jwt(token, anchor, typ, audience):
    """Verify original compact JWS bytes with a pinned role key and fixed algorithm."""
    import jwt
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        header, claims = parse_jwt(token)
        require(header == {"alg": "EdDSA", "typ": typ, "kid": anchor["kid"]}, "JWT algorithm/type/key mismatch")
        key = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(anchor["public_key"] + "="))
        verified = jwt.decode(token, key, algorithms=["EdDSA"], issuer=anchor["iss"], audience=audience,
                              options={"verify_exp": False, "verify_iat": False, "verify_nbf": False,
                                       "require": ["iss", "sub", "aud", "iat", "exp", "jti"]})
        require(verified == claims, "inconsistent JWT decoding")
        for name in ("iss", "sub", "aud", "jti"):
            require(type(claims[name]) is str and bool(claims[name]), f"invalid {name}")
        for name in ("iat", "exp"):
            require(type(claims[name]) is int and 0 <= claims[name] <= 2**53 - 1, f"invalid {name}")
        require(claims["iat"] < claims["exp"], "invalid JWT validity window")
        return claims
    except VerificationError:
        raise
    except Exception as exc:
        raise VerificationError(f"JWT verification: {type(exc).__name__}: {exc}") from exc


def exact_claims(claims, extra):
    require(set(claims) == {"iss", "sub", "aud", "iat", "exp", "jti"} | set(extra),
            "unsupported or missing JWT claims (delegation, cnf and critical constraints are not ignored)")


def verify_request(operation, grant_jwt, policy_jwt, trust, at):
    """Verify the authority and policy before dispatching an operation."""
    validate_schema({"profile": PROFILE, "operation": operation, "grant_jwt": grant_jwt,
                     "policy_jwt": policy_jwt, "decision_jwt": "not-yet-issued"}, "interop-bundle-v0.5.json")
    validate_schema(trust, "interop-trust-v0.5.json")
    require(type(at) is int and 0 <= at <= 2**53 - 1, "invalid independently supplied evaluation time")
    expected = trust["expected"]
    audience = expected["audience"]
    operation_hash = digest_json(operation)

    grant = verify_jwt(grant_jwt, trust["issuer"], "at+jwt", audience)
    exact_claims(grant, ["client_id", "scope", "obo"])
    require(grant["sub"] == expected["principal_id"], "principal mismatch")
    require(grant["client_id"] == expected["agent_id"], "agent mismatch")
    require(grant["scope"] == expected["scope"], "unsupported or mismatched scope")
    require(grant["obo"] == {"profile": PROFILE, "operator_id": expected["operator_id"],
                             "operation_digest": operation_hash}, "grant operation/operator binding mismatch")
    require(grant["iat"] <= at < grant["exp"], "grant not valid at evaluation time")

    policy, allowed = verify_policy(operation, grant["scope"], policy_jwt, trust, at, PROFILE)
    return grant, policy, allowed, operation_hash


def verify_policy(operation, scope, policy_jwt, trust, at, profile):
    expected = trust["expected"]
    policy = verify_jwt(policy_jwt, trust["policy_authority"], "obo-policy+jwt", expected["audience"])
    exact_claims(policy, ["profile", "action", "resource", "allowed_fields", "scope"])
    require(policy["profile"] == profile and policy["sub"] == expected["operator_id"], "policy operator/profile mismatch")
    require(policy["iat"] <= at < policy["exp"], "policy not valid at evaluation time")
    for name in ("action", "resource", "scope"):
        require(type(policy[name]) is str and bool(policy[name]), f"invalid policy {name}")
    fields = policy["allowed_fields"]
    require(isinstance(fields, list) and fields and all(type(f) is str and f for f in fields), "invalid policy fields")
    require(len(fields) == len(set(fields)), "duplicate policy fields")
    allowed = (policy["scope"] == scope and policy["action"] == operation["action"]
               and policy["resource"] == operation["resource"]
               and set(operation["parameters"]) <= set(fields))
    return policy, allowed


def verify_bundle(bundle, trust, at):
    """Return supported evidence checks, preserving unknown status as incomplete."""
    validate_schema(bundle, "interop-bundle-v0.5.json")
    operation = bundle["operation"]
    grant, policy, allowed, operation_hash = verify_request(
        operation, bundle["grant_jwt"], bundle["policy_jwt"], trust, at)
    return verify_receipts(bundle, trust, at, grant, policy, allowed, operation_hash, PROFILE)


def verify_receipts(bundle, trust, at, grant, policy, allowed, operation_hash, profile, bindings=None):
    """Common receipt checks after a profile has verified its authority inputs."""
    bindings = bindings or {}
    operation = bundle["operation"]
    expected = trust["expected"]
    audience = expected["audience"]

    decision = verify_jwt(bundle["decision_jwt"], trust["service"], "obo-decision+jwt", audience)
    exact_claims(decision, ["profile", "grant_digest", "policy_digest", "operation_digest",
                            "request_id", "client_id", "operator_id", "outcome", "reason_code", *bindings])
    require(decision["profile"] == profile, "decision profile mismatch")
    for name, value in bindings.items():
        require(decision[name] == value, f"decision {name} mismatch")
    require(decision["sub"] == grant["sub"] and decision["client_id"] == grant["client_id"]
            and decision["operator_id"] == expected["operator_id"], "decision identity mismatch")
    require(decision["iat"] == at, "decision time must equal independently supplied evaluation time")
    require(decision["grant_digest"] == digest_token(bundle["grant_jwt"]), "decision grant binding mismatch")
    require(decision["policy_digest"] == digest_token(bundle["policy_jwt"]), "decision policy binding mismatch")
    require(decision["operation_digest"] == operation_hash, "decision operation mismatch")
    require(decision["request_id"] == operation["request_id"], "decision request mismatch")
    require(decision["outcome"] == ("allow" if allowed else "deny"), "decision disagrees with evaluated policy")
    require(decision["reason_code"] == ("policy.allow" if allowed else "policy.deny"), "decision reason mismatch")

    if allowed:
        require("execution_jwt" in bundle and "response" in bundle, "accepted operation lacks execution evidence")
        execution = verify_jwt(bundle["execution_jwt"], trust["service"], "obo-execution+jwt", audience)
        exact_claims(execution, ["profile", "decision_digest", "operation_digest", "response_digest", "request_id", "outcome"])
        require(execution["profile"] == profile and execution["sub"] == grant["sub"], "execution identity/profile mismatch")
        require(execution["decision_digest"] == digest_token(bundle["decision_jwt"]), "execution decision mismatch")
        require(execution["operation_digest"] == operation_hash and execution["request_id"] == operation["request_id"],
                "execution operation mismatch")
        require(execution["response_digest"] == digest_json(bundle["response"]), "execution response mismatch")
        require(at <= execution["iat"] < min(grant["exp"], policy["exp"], decision["exp"]), "execution outside authorization window")
        require(execution["outcome"] in ("completed", "failed"), "unsupported execution outcome")
        outcome = execution["outcome"]
    else:
        require("execution_jwt" not in bundle and "response" not in bundle, "denied operation contains execution evidence")
        outcome = "denied"

    status = trust.get("status")
    status_result = "unknown"
    if status is not None:
        last_event = execution["iat"] if allowed else at
        require(status["as_of"] <= at <= last_event < status["valid_until"], "stale or future status snapshot")
        require(grant["jti"] not in status["revoked_grant_ids"], "grant revoked in supplied status snapshot")
        status_result = "verified"
    return {"profile": profile, "result": "verified" if status else "incomplete", "outcome": outcome,
            "checks": {"signatures": "verified", "identity_bindings": "verified", "operation_binding": "verified",
                       "policy_decision": "verified", "receipts": "verified", "archived_status": status_result},
            "evaluation_time": at, "limitations": LIMITATIONS}


def verify_bundle_cli(args):
    profile = None
    try:
        trust = read_json(args.trust)
        reports = []
        seen = set()
        for path in args.path:
            bundle = read_json(path)
            profile = bundle.get("profile")
            if bundle.get("profile") == PROFILE:
                report = verify_bundle(bundle, trust, args.at)
            else:
                from obo_keycloak import PROFILE as KEYCLOAK_PROFILE, verify_bundle as verify_keycloak_bundle
                require(profile == KEYCLOAK_PROFILE, "unsupported bundle profile")
                report = verify_keycloak_bundle(bundle, trust, args.at)
            # The selected verifier already authenticated these exact bytes.
            _, grant = parse_jwt(bundle["grant_jwt"])
            identifiers = {("request", bundle["operation"]["request_id"]), ("grant", grant["iss"], grant["jti"])}
            require(not (identifiers & seen), "duplicate request or grant in supplied bundle set")
            seen.update(identifiers)
            reports.append(report)
    except Exception as exc:
        print(json.dumps({"profile": profile, "result": "failed", "error": str(exc)}))
        return 1
    print(json.dumps(reports[0] if len(reports) == 1 else reports, indent=2))
    return 0 if all(report["result"] == "verified" for report in reports) else 2
