"""
OBO Demo — Ed25519 Key Generation
===================================
Generates an Ed25519 keypair for the demo TravelAgent operator.
Outputs the DNS TXT record value to set on your domain.

Usage:
    python keygen.py --operator-id your-domain.com

Output:
    keys/private_key.pem    — keep secret, mount into travel-agent container
    keys/public_key.b64     — raw base64url pubkey (for DNS TXT and env vars)

DNS TXT record to create:
    _obo-key.your-domain.com  IN TXT  "v=obo1 ed25519=<value from keys/public_key.b64>"

Environment variables for docker-compose:
    TRAVEL_AGENT_PRIVATE_KEY_B64  — base64 of PEM (travel-agent container)
    TRAVEL_AGENT_PUBKEY           — base64url of raw 32 bytes (flight-search container)
"""

import argparse
import base64
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption,
)


def generate(operator_id: str, keys_dir: Path):
    keys_dir.mkdir(exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # PEM private key
    pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    pem_path = keys_dir / "private_key.pem"
    pem_path.write_bytes(pem)
    pem_path.chmod(0o600)

    # Raw 32-byte public key → base64url (no padding)
    raw_pub = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    pub_b64 = base64.urlsafe_b64encode(raw_pub).decode().rstrip("=")
    pub_path = keys_dir / "public_key.b64"
    pub_path.write_text(pub_b64)

    # PEM → base64 (for env var injection)
    pem_b64 = base64.b64encode(pem).decode()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  OBO Demo Keys Generated                                     ║
╚══════════════════════════════════════════════════════════════╝

Files written:
  {pem_path}   (private key — keep secret)
  {pub_path}   (public key base64url)

─── DNS TXT record ───────────────────────────────────────────

Create this record in your DNS zone and wait for propagation:

  _obo-key.{operator_id}  IN TXT  "v=obo1 ed25519={pub_b64}"

─── .env for docker-compose ──────────────────────────────────

Copy these into .env (or export to shell):

TRAVEL_AGENT_OPERATOR_ID={operator_id}
TRAVEL_AGENT_PRIVATE_KEY_B64={pem_b64}
TRAVEL_AGENT_PUBKEY={pub_b64}

─── Verify DNS propagation ───────────────────────────────────

  dig TXT _obo-key.{operator_id} +short
  # should return: "v=obo1 ed25519={pub_b64}"

""")


def main():
    parser = argparse.ArgumentParser(description="Generate OBO demo Ed25519 keypair")
    parser.add_argument(
        "--operator-id",
        default="travel-agent.example.com",
        help="DNS name of the issuing operator (default: travel-agent.example.com)",
    )
    parser.add_argument(
        "--keys-dir",
        default="keys",
        help="Directory to write key files (default: keys/)",
    )
    args = parser.parse_args()
    generate(args.operator_id, Path(args.keys_dir))


if __name__ == "__main__":
    main()
