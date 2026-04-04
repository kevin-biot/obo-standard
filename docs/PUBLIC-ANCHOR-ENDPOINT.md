# Lane2 Public Evidence Anchor Endpoint

**For PoC development, integration testing, and OBO validation.**

---

## What This Is

Lane2 operates a public Evidence Anchor endpoint running the Lane2 commercial
Evidence Anchor implementation. It speaks the OBO Evidence Anchor API (§4.4)
and is available to anyone building against the OBO standard.

If you are implementing an OBO pipeline, testing an OBO integration, or
demonstrating OBO to a counterparty or regulator, you can use this endpoint
as your Evidence Anchor without standing up your own server. You get real
Merkle receipts, real inclusion proofs, and a real DNS-published public key —
everything you need to build and validate a complete OBO deployment.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `https://anchor.lane2.ai/v1/evidence/mint` | Submit Evidence Envelope leaves; receive signed receipt |
| `GET` | `https://anchor.lane2.ai/v1/evidence/{id}/proof` | Retrieve inclusion proof for a submitted envelope |
| `GET` | `https://anchor.lane2.ai/v1/status` | Anchor health, current checkpoint index, tree size |
| `GET` | `https://anchor.lane2.ai/.well-known/obo-anchor` | Public key, anchor domain, API version |

---

## Trust Material

The Lane2 Evidence Anchor signing key is published in DNS and in the
well-known document. Resolve it to verify any receipt independently:

```
DNS:  _anchor-key.lane2.ai IN TXT "v=anchor1 ed25519=<pubkey>"
HTTPS: GET https://anchor.lane2.ai/.well-known/obo-anchor
```

No trust in Lane2 is required to verify a receipt. The verification
algorithm (spec §7.2) works from the public key alone:

1. Resolve `_anchor-key.lane2.ai` → Ed25519 public key
2. Verify `envelope_sig` in the receipt against the public key
3. Recompute the Merkle root from the submitted `tag:value` leaves
   (sort lexicographically, SHA-256 each, build tree bottom-up)
4. Compare recomputed root against `merkle_root` in the receipt
5. Compare `checkpoint_index` against the current tree head
   (from `GET /v1/status` or a previously trusted checkpoint)

If all checks pass, the receipt is valid regardless of whether you trust
Lane2 as an organisation. That is the point. The evidence is
self-verifying.

---

## Submitting an Evidence Envelope

```bash
curl -X POST https://anchor.lane2.ai/v1/evidence/mint \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_bundle": "urn:obo:evidence:a1b2c3d4-...",
    "leaves": [
      "event_time:2026-04-04T12:00:00.000000+00:00",
      "obo_credential_id:urn:obo:cred:e5f6g7h8-...",
      "obo_intent_hash:b98d4238ecb978415a30d0a8657...",
      "obo_outcome:allow",
      "producer_id:your-operator.example.com",
      "reason_code:policy.allow"
    ]
  }'
```

**Response:**

```json
{
  "evidence_bundle": "urn:obo:evidence:a1b2c3d4-...",
  "merkle_root": "3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c183...",
  "checkpoint_index": 1042,
  "tree_size": 1043,
  "created_at": "2026-04-04T12:00:00.041Z",
  "anchor_id": "anchor.lane2.ai",
  "envelope_sig": "<Ed25519 signature over merkle_root || checkpoint_index || created_at>"
}
```

The receipt is sealed. Lane2 cannot alter it after issuance without
invalidating the signature and the DNS-published public key. Any party
with the spec can verify it.

---

## Retrieving an Inclusion Proof

```bash
curl https://anchor.lane2.ai/v1/evidence/urn:obo:evidence:a1b2c3d4-.../proof
```

**Response:**

```json
{
  "evidence_bundle": "urn:obo:evidence:a1b2c3d4-...",
  "leaf_hash": "sha256:<hash of this envelope's Merkle leaf>",
  "merkle_root": "3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c183...",
  "audit_path": [
    "sha256:<sibling hash at depth 0>",
    "sha256:<sibling hash at depth 1>",
    "sha256:<sibling hash at depth 2>"
  ],
  "tree_size": 1043,
  "checkpoint_index": 1042
}
```

The audit path allows any party to independently verify inclusion
without trusting the Evidence Anchor. Walk the path bottom-up, hashing
at each step, and confirm the resulting root matches `merkle_root`.

---

## Terms of Use

| Term | Value |
|------|-------|
| Availability | Best-effort. No SLA. |
| Data retention | 90 days from submission, then purged. |
| Rate limit | 100 requests/minute per IP. |
| Max leaves per submission | 50 |
| Production use | Not permitted. For development and testing only. |
| Personal data | Do not submit real personal data. Use synthetic or test values. |
| Cost | Free for PoC and open-source projects. |

**Enterprise PoC:** If you need higher rate limits, extended retention,
dedicated capacity, or a private endpoint for internal testing, open a
discussion at [github.com/kevin-biot/obo-standard/discussions](https://github.com/kevin-biot/obo-standard/discussions)
or contact Lane2 directly. Enterprise PoC environments are available
at no cost for organisations evaluating OBO for production deployment.

---

## Performance Note

The Lane2 Evidence Anchor is a purpose-built, high-performance implementation
optimised for the OBO Evidence Anchor workload. It is not a Trillian wrapper.

Typical minting latency from submission to signed receipt, measured from the
AWS endpoint with clients in the same region: **under 5 ms at p99** for
standard OBO evidence submissions (14–30 leaves). Inclusion proof retrieval:
under 2 ms. Both operations are synchronous and blocking — the agent waits
for the receipt before considering the transaction complete.

This matters because evidence minting sits on the critical path of every
agentic transaction. An Evidence Anchor that adds 50–100 ms per transaction
creates measurable friction at scale. The Lane2 implementation was built with
this constraint as a first-class requirement — an agent pipeline that submits
hundreds of transactions per minute should not be bottlenecked by evidence
anchoring.

Detailed benchmark methodology is available on request.

---

## Integration Examples

### Python (requests)

```python
import requests

anchor_url = "https://anchor.lane2.ai"

def mint_evidence(evidence_bundle_id: str, leaves: list[str]) -> dict:
    resp = requests.post(
        f"{anchor_url}/v1/evidence/mint",
        json={"evidence_bundle": evidence_bundle_id, "leaves": leaves},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()

receipt = mint_evidence(
    "urn:obo:evidence:test-001",
    [
        "event_time:2026-04-04T12:00:00.000000+00:00",
        "obo_credential_id:urn:obo:cred:test-001",
        "obo_intent_hash:b98d4238ecb978415a30...",
        "obo_outcome:allow",
        "producer_id:test.example.com",
    ]
)
print(f"Merkle root: {receipt['merkle_root']}")
print(f"Checkpoint: {receipt['checkpoint_index']}")
```

### Go

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type MintRequest struct {
    EvidenceBundle string   `json:"evidence_bundle"`
    Leaves         []string `json:"leaves"`
}

type MintReceipt struct {
    MerkleRoot      string `json:"merkle_root"`
    CheckpointIndex int    `json:"checkpoint_index"`
    EnvelopeSig     string `json:"envelope_sig"`
    CreatedAt       string `json:"created_at"`
}

func mintEvidence(bundleID string, leaves []string) (*MintReceipt, error) {
    body, _ := json.Marshal(MintRequest{EvidenceBundle: bundleID, Leaves: leaves})
    resp, err := http.Post(
        "https://anchor.lane2.ai/v1/evidence/mint",
        "application/json",
        bytes.NewReader(body),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    var receipt MintReceipt
    json.NewDecoder(resp.Body).Decode(&receipt)
    return &receipt, nil
}

func main() {
    receipt, err := mintEvidence("urn:obo:evidence:test-001", []string{
        "event_time:2026-04-04T12:00:00.000000+00:00",
        "obo_outcome:allow",
        "producer_id:test.example.com",
    })
    if err != nil {
        panic(err)
    }
    fmt.Printf("Root: %s  Checkpoint: %d\n", receipt.MerkleRoot, receipt.CheckpointIndex)
}
```

### Using the A2A reference implementation

The A2A integration example (`examples/integrations/a2a/`) is pre-configured
to use `anchor_stub/` for local development. To point it at the public
endpoint instead, set the environment variable:

```bash
ANCHOR_URL=https://anchor.lane2.ai docker compose up
```

All agents in the reference implementation will submit to the public endpoint.
Receipts will be real, independently verifiable OBO Evidence Anchor receipts.

---

## Verifying a Receipt Without Trusting Lane2

The following Python snippet verifies a mint receipt from scratch using
only the OBO spec and the DNS-published public key:

```python
import hashlib
import dns.resolver
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_der_public_key
import base64

def resolve_anchor_pubkey(anchor_domain: str) -> Ed25519PublicKey:
    """Resolve Ed25519 public key from DNS TXT record."""
    answers = dns.resolver.resolve(f"_anchor-key.{anchor_domain}", "TXT")
    for rdata in answers:
        txt = rdata.to_text().strip('"')
        for part in txt.split():
            if part.startswith("ed25519="):
                raw = base64.b64decode(part[8:])
                return Ed25519PublicKey.from_public_bytes(raw)
    raise ValueError(f"No anchor key found for {anchor_domain}")

def verify_receipt(receipt: dict, leaves: list[str]) -> bool:
    """
    Verify an Evidence Anchor receipt against the submitted leaves
    and the DNS-published public key.
    Returns True if receipt is valid; raises on any failure.
    """
    # 1. Sort leaves lexicographically (Evidence Anchor sorts them)
    sorted_leaves = sorted(leaves)

    # 2. Hash each leaf: SHA-256(UTF-8 bytes)
    leaf_hashes = [hashlib.sha256(leaf.encode()).digest() for leaf in sorted_leaves]

    # 3. Build Merkle tree bottom-up
    layer = leaf_hashes
    while len(layer) > 1:
        next_layer = []
        for i in range(0, len(layer) - 1, 2):
            combined = layer[i] + layer[i + 1]
            next_layer.append(hashlib.sha256(combined).digest())
        if len(layer) % 2 == 1:
            next_layer.append(layer[-1])
        layer = next_layer
    computed_root = layer[0].hex()

    # 4. Compare with receipt's merkle_root
    assert computed_root == receipt["merkle_root"], \
        f"Merkle root mismatch: computed {computed_root}, got {receipt['merkle_root']}"

    # 5. Resolve public key from DNS
    pubkey = resolve_anchor_pubkey(receipt["anchor_id"])

    # 6. Verify envelope_sig over canonical fields
    msg = (receipt["merkle_root"] + receipt["created_at"]).encode()
    sig = base64.b64decode(receipt["envelope_sig"])
    pubkey.verify(sig, msg)  # raises InvalidSignature on failure

    return True
```

If this verification passes, the receipt is valid — independently of any
trust in Lane2. The DNS-published key is the trust anchor.

---

## See Also

- [OBO Spec §4.4 — Evidence Anchor Submission](../draft-obo-agentic-evidence-envelope-01.md)
- [docs/EVIDENCE-INFRASTRUCTURE.md — Why this infrastructure matters](EVIDENCE-INFRASTRUCTURE.md)
- [docs/adr/ADR-008-merkle-log-over-blockchain.md — Architecture decision](adr/ADR-008-merkle-log-over-blockchain.md)
- [examples/integrations/a2a/ — A2A reference implementation](../examples/integrations/a2a/)
