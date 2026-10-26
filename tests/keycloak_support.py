"""Disposable, pinned Keycloak issuer for local interoperability tests only."""

import json
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

IMAGE = "quay.io/keycloak/keycloak:26.8.1@sha256:a78d6b79572168cb25886b80a8b5b8d4ed4390743e3eecb810538683e209dd6b"


def request(url, body=None, token=None, form=False, method=None):
    headers = {"Content-Type": "application/x-www-form-urlencoded" if form else "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = (urllib.parse.urlencode(body).encode() if form else json.dumps(body).encode()) if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        code = exc.code
        exc.close()
        raise RuntimeError(f"Keycloak HTTP {code}") from None


class Keycloak:
    def __init__(self, port, audience, cleanup):
        self.url = f"http://127.0.0.1:{port}"
        self.issuer = self.url + "/realms/obo"
        self.name = "obo-keycloak-test-" + uuid.uuid4().hex
        self.secret = secrets.token_urlsafe(32)
        password = secrets.token_urlsafe(32)
        cleanup(self.close)
        started = subprocess.run(["docker", "run", "--rm", "-d", "--name", self.name,
                        "-p", f"127.0.0.1:{port}:8080", "-e", "KC_BOOTSTRAP_ADMIN_USERNAME=admin",
                        "-e", "KC_BOOTSTRAP_ADMIN_PASSWORD=" + password, IMAGE,
                        "start-dev", "--hostname-strict=false", "--log-level=warn"],
                       check=False, capture_output=True)
        if started.returncode:
            raise RuntimeError("Keycloak container startup failed (credentials withheld)")
        for _ in range(120):
            try:
                admin = request(self.url + "/realms/master/protocol/openid-connect/token", {
                    "grant_type": "password", "client_id": "admin-cli", "username": "admin", "password": password}, form=True)["access_token"]
                break
            except (OSError, RuntimeError):
                time.sleep(1)
        else:
            raise RuntimeError("Keycloak startup timeout (credentials withheld)")
        request(self.url + "/admin/realms", {"realm": "obo", "enabled": True,
                "sslRequired": "none", "accessTokenLifespan": 300}, admin)
        api = self.url + "/admin/realms/obo"
        request(api + "/client-scopes", {"name": "supplier:update", "protocol": "openid-connect",
                "attributes": {"include.in.token.scope": "true"}}, admin)
        request(api + "/clients", {"clientId": "procurement-agent", "secret": self.secret,
                "publicClient": False, "serviceAccountsEnabled": True, "standardFlowEnabled": False,
                "directAccessGrantsEnabled": False, "defaultClientScopes": ["supplier:update"],
                "protocolMappers": [{"name": "obo-audience", "protocol": "openid-connect",
                    "protocolMapper": "oidc-audience-mapper", "config": {
                        "included.custom.audience": audience, "access.token.claim": "true",
                        "id.token.claim": "false"}}]}, admin)
        client = request(api + "/clients?clientId=procurement-agent", token=admin)[0]
        account = request(api + "/clients/" + client["id"] + "/service-account-user", token=admin)
        self.subject = account["id"]
        discovery = request(self.issuer + "/.well-known/openid-configuration")
        if discovery["issuer"] != self.issuer:
            raise RuntimeError("Keycloak discovery issuer mismatch")
        keys = request(discovery["jwks_uri"])["keys"]
        key = next(key for key in keys if key.get("alg") == "RS256" and key.get("use") == "sig")
        # Pin the RSA key directly, not an unrelated X.509 certificate chain.
        self.jwk = {name: key[name] for name in ("kty", "kid", "alg", "use", "n", "e")}

    def token(self):
        return request(self.issuer + "/protocol/openid-connect/token", {
            "grant_type": "client_credentials", "client_id": "procurement-agent", "client_secret": self.secret,
            "scope": "supplier:update"}, form=True)["access_token"]

    def close(self):
        subprocess.run(["docker", "rm", "-f", self.name], capture_output=True, check=False)
