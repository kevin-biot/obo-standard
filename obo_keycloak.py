"""Narrow experimental Keycloak client-credentials adapter, not generic OIDC."""

from obo_interop import (VerificationError, digest_json, digest_token, exact_claims, parse_jwt,
                         require, validate_schema, verify_jwt, verify_policy, verify_receipts)

PROFILE = "obo-keycloak/0.5-alpha.3"
LIMITATIONS = [
    "Keycloak authenticates a service account, not the legal principal's decision to delegate.",
    "The separate mandate authority and policy are configured by the operator; their lawful authority is not adjudicated.",
    "Pinned keys and the supplied local status snapshot are not live Keycloak introspection or revocation checks.",
    "Only the tested RS256 client-credentials configuration is supported; no token exchange, multi-hop delegation or proof of possession.",
]


def verify_workload(token, trust, at):
    """Retain and verify the issuer's original token, including its machine subject."""
    import jwt
    try:
        header, claims = parse_jwt(token)
        anchor, expected = trust["workload_issuer"], trust["expected"]
        require(header == {"alg": "RS256", "typ": "JWT", "kid": anchor["jwk"]["kid"]}, "workload JOSE mismatch")
        core = {"iss", "sub", "aud", "iat", "exp", "jti", "typ", "azp", "scope", "client_id"}
        require(core <= set(claims) <= core | {"clientHost", "clientAddress"}, "unsupported workload claims")
        key = jwt.PyJWK.from_dict(anchor["jwk"], algorithm="RS256").key
        require(key.key_size >= 2048, "weak workload RSA key")
        verified = jwt.decode(token, key, algorithms=["RS256"], issuer=anchor["iss"], audience=expected["audience"],
                              options={"verify_exp": False, "verify_iat": False, "verify_nbf": False,
                                       "require": sorted(core)})
        require(verified == claims, "inconsistent workload decoding")
        for name in core - {"iat", "exp"}:
            require(type(claims[name]) is str and bool(claims[name]), f"invalid workload {name}")
        for name in ("iat", "exp"):
            require(type(claims[name]) is int and 0 <= claims[name] <= 2**53 - 1, f"invalid workload {name}")
        require(claims["iat"] <= at < claims["exp"], "workload token not valid at evaluation time")
        require(claims["typ"] == "Bearer", "unsupported workload token type")
        require(claims["aud"] == expected["audience"], "workload audience mismatch")
        require(claims["sub"] == expected["workload_subject"], "workload subject mismatch")
        require(claims["azp"] == claims["client_id"] == expected["agent_id"], "workload client mismatch")
        require(claims["scope"] == expected["scope"], "unsupported workload scope")
        return claims
    except VerificationError:
        raise
    except Exception as exc:
        raise VerificationError(f"workload JWT verification: {type(exc).__name__}: {exc}") from exc


def verify_request(operation, grant_jwt, policy_jwt, trust, at, delegation_jwt):
    validate_schema({"profile": PROFILE, "operation": operation, "grant_jwt": grant_jwt,
                     "delegation_jwt": delegation_jwt, "policy_jwt": policy_jwt,
                     "decision_jwt": "not-yet-issued"}, "keycloak-bundle-v0.5.json")
    validate_schema(trust, "keycloak-trust-v0.5.json")
    require(type(at) is int and 0 <= at <= 2**53 - 1, "invalid independently supplied evaluation time")
    expected = trust["expected"]
    workload = verify_workload(grant_jwt, trust, at)
    mandate = verify_jwt(delegation_jwt, trust["issuer"], "obo-delegation+jwt", expected["audience"])
    exact_claims(mandate, ["profile", "grant_digest", "operation_digest", "workload_subject", "client_id", "operator_id", "scope"])
    require(mandate["profile"] == PROFILE, "mandate profile mismatch")
    require(mandate["sub"] == expected["principal_id"], "mandate principal mismatch")
    require(mandate["client_id"] == workload["client_id"] and mandate["workload_subject"] == workload["sub"],
            "mandate workload mismatch")
    require(mandate["operator_id"] == expected["operator_id"] and mandate["scope"] == workload["scope"],
            "mandate operator/scope mismatch")
    require(mandate["grant_digest"] == digest_token(grant_jwt), "mandate grant mismatch")
    operation_hash = digest_json(operation)
    require(mandate["operation_digest"] == operation_hash, "mandate operation mismatch")
    require(workload["iat"] <= mandate["iat"] <= at < mandate["exp"] <= workload["exp"], "mandate validity exceeds workload grant")
    policy, allowed = verify_policy(operation, workload["scope"], policy_jwt, trust, at, PROFILE)
    # Internal authority view only: never rewrite or reissue the external JWT.
    authority = {**workload, "sub": mandate["sub"], "exp": min(workload["exp"], mandate["exp"])}
    return authority, policy, allowed, operation_hash


def verify_bundle(bundle, trust, at):
    validate_schema(bundle, "keycloak-bundle-v0.5.json")
    grant, policy, allowed, operation_hash = verify_request(
        bundle["operation"], bundle["grant_jwt"], bundle["policy_jwt"], trust, at, bundle["delegation_jwt"])
    report = verify_receipts(bundle, trust, at, grant, policy, allowed, operation_hash, PROFILE,
                             {"delegation_digest": digest_token(bundle["delegation_jwt"])})
    report["checks"].update(workload_grant="verified", explicit_mandate="verified")
    report["limitations"] = [*report["limitations"], *LIMITATIONS]
    return report
