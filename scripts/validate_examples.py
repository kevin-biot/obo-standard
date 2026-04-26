#!/usr/bin/env python3
"""Validate every JSON example in the repository.

Credential and envelope examples are validated against the public JSON Schemas.
A2A capture files are checked as capture artifacts so no JSON under examples/
quietly drifts into an unrecognised shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SCHEMAS = ROOT / "schemas"

try:
    import jsonschema
except ImportError:  # pragma: no cover - CI installs jsonschema.
    jsonschema = None


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc


def validate_with_schema(instance: dict[str, Any], schema: dict[str, Any], path: Path) -> None:
    if jsonschema is not None:
        jsonschema.Draft202012Validator(schema).validate(instance)
        return

    required = set(schema.get("required", []))
    properties = set(schema.get("properties", {}))
    missing = sorted(required - set(instance))
    extra = sorted(set(instance) - properties)
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"extra={extra}")
        raise AssertionError(f"{path}: schema mismatch ({', '.join(detail)})")


def validate_capture(instance: dict[str, Any], path: Path) -> None:
    if not {"_capture", "request", "receipt"} <= set(instance):
        raise AssertionError(f"{path}: unrecognised JSON example shape")
    request = instance["request"]
    receipt = instance["receipt"]
    leaves = request.get("leaves")
    if not isinstance(leaves, list) or not leaves:
        raise AssertionError(f"{path}: capture request.leaves must be a non-empty list")
    if not all(isinstance(leaf, str) and ":" in leaf for leaf in leaves):
        raise AssertionError(f"{path}: capture leaves must be tag:value strings")
    if not isinstance(receipt.get("merkle_root"), str):
        raise AssertionError(f"{path}: capture receipt.merkle_root missing")


def assert_no_draft_00(path: Path) -> None:
    text = path.read_text()
    if "draft-obo-agentic-evidence-envelope-00" in text:
        raise AssertionError(f"{path}: stale draft-00 reference")


def main() -> int:
    credential_schema = load_json(SCHEMAS / "obo-credential.json")
    envelope_schema = load_json(SCHEMAS / "obo-evidence-envelope.json")

    checked = 0
    failures: list[str] = []
    for path in sorted(EXAMPLES.rglob("*.json")):
        try:
            instance = load_json(path)
            assert_no_draft_00(path)

            if "obo_credential_id" in instance and "evidence_id" not in instance:
                validate_with_schema(instance, credential_schema, path)
            elif "evidence_id" in instance and "obo_credential_ref" in instance:
                validate_with_schema(instance, envelope_schema, path)
            else:
                validate_capture(instance, path)
            checked += 1
        except Exception as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(f"validated {checked} JSON examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
