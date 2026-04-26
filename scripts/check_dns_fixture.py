#!/usr/bin/env python3
"""Verify the live public OBO DNS fixture used by the A2A demo."""

from __future__ import annotations

import subprocess
import sys

EXPECTED_NAME = "_obo-key.lane2.ai"
EXPECTED_VALUE = "v=obo1 ed25519=vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"


def resolve_with_dnspython() -> list[str]:
    import dns.resolver

    answers = dns.resolver.resolve(EXPECTED_NAME, "TXT", lifetime=10)
    values: list[str] = []
    for answer in answers:
        values.append("".join(part.decode() for part in answer.strings))
    return values


def resolve_with_dig() -> list[str]:
    proc = subprocess.run(
        ["dig", "+short", "TXT", EXPECTED_NAME, "@8.8.8.8"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [line.strip().strip('"') for line in proc.stdout.splitlines() if line.strip()]


def main() -> int:
    try:
        try:
            values = resolve_with_dnspython()
        except ImportError:
            values = resolve_with_dig()
    except Exception as exc:
        print(f"DNS fixture lookup failed: {exc}", file=sys.stderr)
        return 1

    if EXPECTED_VALUE not in values:
        print(f"DNS fixture mismatch for {EXPECTED_NAME}", file=sys.stderr)
        print(f"expected: {EXPECTED_VALUE}", file=sys.stderr)
        print(f"actual:   {values}", file=sys.stderr)
        return 1

    print(f"{EXPECTED_NAME} OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
