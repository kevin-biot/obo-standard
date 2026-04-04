# OBO + A2A Reference Implementation

End-to-end demonstration of the OBO accountability layer composed with the
[A2A protocol](https://google.github.io/A2A/). Two autonomous agents, real
Ed25519 keys, a live DNS trust anchor, and SAPP Merkle evidence — three Docker
containers, no pre-shared config, no mocks for the cryptography.

---

## What this demonstrates

| Layer | What runs here |
|-------|---------------|
| **OBO** | Pre-transaction credential issued by TravelAgent, verified by FlightSearchAgent; post-transaction evidence envelope sealed and Merkle-anchored |
| **A2A** | Agent Card discovery (`GET /.well-known/agent.json`), task dispatch (`POST /tasks`), structured result |
| **DNS trust anchor** | `_obo-key.lane2.ai IN TXT "v=obo1 ed25519=…"` — key resolved live from public DNS per transaction; independently verifiable with `dig` |
| **SAPP** | Evidence minted via `POST /v1/evidence/mint` (ADR-153); Merkle proof returned via `GET /evidence/{id}/proof` (ADR-181 E7) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker network                          │
│                                                                 │
│  ┌─────────────────┐   A2A task (+ OBO cred)  ┌─────────────┐  │
│  │  TravelAgent    │ ───────────────────────► │FlightSearch │  │
│  │  (--demo)       │ ◄─────────────────────── │Agent        │  │
│  │                 │       result              │(--server)   │  │
│  │  issues OBO     │                           │             │  │
│  │  credential     │  ┌──────────────────┐     │ resolves    │  │
│  │  seals evidence │  │  DNS (public)    │     │ OBO key     │  │
│  │  mints to SAPP  │  │ _obo-key.lane2.ai│◄────│ via DNS TXT │  │
│  └────────┬────────┘  └──────────────────┘     └─────────────┘  │
│           │                                                     │
│           │  POST /v1/evidence/mint                             │
│           │  GET  /evidence/{id}/proof                          │
│           ▼                                                     │
│  ┌─────────────────┐                                            │
│  │   SAPP stub     │  merkle_root + evidence_bundle             │
│  │   :8080         │  checkpoint_index + JWS proof              │
│  │   /data/*.jsonl │  (stub JWS; production: SAPP operator key) │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Python 3.11+ (for `keygen.py` only — not needed inside containers)
- A DNS zone you control (for the trust anchor)
- AWS CLI (if using Route 53)

---

## Setup

### 1. Generate keys

```bash
pip install cryptography   # one-time, for keygen.py only
python3 keygen.py --operator-id your-domain.com
```

Output:
```
TRAVEL_AGENT_OPERATOR_ID=your-domain.com
TRAVEL_AGENT_PRIVATE_KEY_B64=<base64 PEM PKCS8 — keep secret>
TRAVEL_AGENT_PUBKEY=<base64url raw 32 bytes — goes in DNS>

DNS TXT record to set:
  _obo-key.your-domain.com  IN TXT  "v=obo1 ed25519=<TRAVEL_AGENT_PUBKEY>"
```

Keys are also written to `keys/private_key.pem` and `keys/public_key.b64`
(both gitignored).

### 2. Set the DNS trust anchor

**Route 53:**
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id YOUR_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "_obo-key.your-domain.com.",
        "Type": "TXT",
        "TTL": 60,
        "ResourceRecords": [{"Value": "\"v=obo1 ed25519=YOUR_PUBKEY\""}]
      }
    }]
  }'
```

**Verify propagation** (usually < 60 s on Route 53):
```bash
dig +short TXT _obo-key.your-domain.com @8.8.8.8
# → "v=obo1 ed25519=<your pubkey>"
```

Once this resolves, FlightSearchAgent will resolve it live — no env var needed
for the public key.

### 3. Configure `.env`

```bash
cp .env.example .env
# Fill TRAVEL_AGENT_OPERATOR_ID, TRAVEL_AGENT_PRIVATE_KEY_B64,
# TRAVEL_AGENT_PUBKEY (fallback if DNS unreachable), SAPP_PROFILE_ID
```

`.env` is gitignored. The private key lives here and nowhere else.

### 4. Run

```bash
docker compose up --build
```

`travel-agent` waits for `sapp` and `flight-search` to pass health checks,
runs all 7 scenarios, then exits cleanly.

---

## Live run — captured output, 2026-04-04

The following is unedited output from a run against `lane2.ai`.
The DNS record is still live — verify it yourself at any time:

```bash
dig +short TXT _obo-key.lane2.ai @8.8.8.8
# → "v=obo1 ed25519=vqiddGZ0skvsek13nUksdu9NfLq7fDN3BmtCsKkEysU"
```

```
[FlightSearchAgent] OBO key ready  source=dns-txt  key=vqiddGZ0skvsek13nUks…
[FlightSearchAgent] listening on :8081

══════════════════════════════════════════════════════════════
  OBO + A2A DEMO — Cross-org task with real evidence chain
══════════════════════════════════════════════════════════════

  [discovery] GET http://flight-search:8081/.well-known/agent.json
  agent:       FlightSearchAgent  v1.0.0
  skills:      flight-search, hotel-search
  auth.obo:    ✓ required

──────────────────────────────────────────────────────────────
  SCENARIO 1: Flight search: LHR → JFK  [expect: allow]
──────────────────────────────────────────────────────────────

  [1/5] Issuing OBO Credential
        operator_id:    lane2.ai
        principal_id:   did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta…
        intent_hash:    b98d4238ecb978415a30…
        credential_sig: Ed25519 ✓  (DGEpg-oqT-_lHY2Qfgrk…)

  [2/5] Sending A2A Task → FlightSearchAgent
        POST http://flight-search:8081/tasks
        task_id: task-0fe230c3-1a…

  [3/5] FlightSearchAgent response
        status: completed
        flights found: 2
          BA117  LHR→JFK  $487.0
          VS3    LHR→JFK  $512.0

  [4/5] Sealing OBO Evidence Envelope
        envelope_id:     urn:obo:env:523068f5-8f09-4969-b7e6-ed61…
        outcome:         allow
        evidence_digest: f07160c23ddd9b9f111e…
        envelope_sig:    Ed25519 ✓  (nvrois4PEAUNY-3MFX82…)
        task_ref:        task-0fe230c3-1a81-4…

  [5/5] Minting Evidence → SAPP  POST /v1/evidence/mint

        ── SAPP Mint Response ────────────────────────────
        evidence_bundle: yBEdJg9rcnI-xyZfigUc9CbU5U3TTI…
        merkle_root:     4f29251a3d5a565c53a1…
        checkpoint_idx:  0
        tree_size:       1
        created_at:      2026-04-04T11:55:07.039747+00:00

        ── Fetching Signed Proof  GET /evidence/…/proof ──
        ⚠  stub JWS — production is SAPP operator Ed25519 over inclusion proof

──────────────────────────────────────────────────────────────
  SCENARIO 2: Hotel search: New York  [expect: allow]
──────────────────────────────────────────────────────────────

  [1/5] Issuing OBO Credential
        operator_id:    lane2.ai
        intent_hash:    e2b7c2bfeaeb1d0e7084…
        credential_sig: Ed25519 ✓  (5qPTgCqdoyR74RzF1vr0…)

  [5/5] Minting Evidence → SAPP
        merkle_root:     116234800d9a56a49a8f…
        checkpoint_idx:  1
        tree_size:       2

──────────────────────────────────────────────────────────────
  SCENARIO 3: Tampered intent  [expect: OBO-ERR-005]
──────────────────────────────────────────────────────────────

  ⚠ INJECT tamper_intent: intent changed to 'search flights from LHR to CDG'
  ✗ request failed: HTTP Error 422  reason_code: OBO-ERR-005

──────────────────────────────────────────────────────────────
  SCENARIO 4: Missing OBO extension  [expect: OBO-ERR-001]
──────────────────────────────────────────────────────────────

  ⚠ INJECT drop_obo: extensions.obo omitted entirely
  ✗ request failed: HTTP Error 422  reason_code: OBO-ERR-001

──────────────────────────────────────────────────────────────
  SCENARIO 5: Expired credential  [expect: OBO-ERR-003]
──────────────────────────────────────────────────────────────

  ⚠ INJECT expire: credential expired at 2026-04-04T11:54:07…
  ✗ request failed: HTTP Error 422  reason_code: OBO-ERR-003

──────────────────────────────────────────────────────────────
  SCENARIO 6: Forged signature  [expect: OBO-ERR-004]
──────────────────────────────────────────────────────────────

  ⚠ INJECT forge_sig: credential_sig corrupted
  ✗ request failed: HTTP Error 422  reason_code: OBO-ERR-004

──────────────────────────────────────────────────────────────
  SCENARIO 7: Replayed credential  [expect: OBO-ERR-008]
──────────────────────────────────────────────────────────────

  ⚠ INJECT replay: reusing credential_id urn:obo:cred:1d8d3842…
  ✗ request failed: HTTP Error 422  reason_code: OBO-ERR-008

══════════════════════════════════════════════════════════════
  DEMO COMPLETE
══════════════════════════════════════════════════════════════
```

**All 7 scenarios produced the expected result.** Scenarios 1–2 produced SAPP
Merkle receipts with monotonically increasing `checkpoint_index` values.
Scenarios 3–7 were rejected at the gate with typed OBO error codes — no task
executed, no evidence minted for the rejected cases.

---

## Evidence chain — what gets committed to SAPP

For each allowed transaction, 14 leaves are minted under the `regulated`
profile. SAPP sorts them lexicographically, hashes each as
`SHA-256(tag:value)`, and builds a Merkle tree. The `merkle_root` commits
to all 14 leaves at once:

```
event_time:2026-04-04T11:55:07+00:00
obo_credential_id:urn:obo:cred:…
obo_envelope_id:urn:obo:env:523068f5…
obo_envelope_sig:nvrois4PEAUNY-3MFX82…
obo_evidence_digest:f07160c23ddd9b9f111e…
obo_governance_ref:https://example.com/obo/v1/policy
obo_intent_hash:b98d4238ecb978415a30…
obo_operator_id:lane2.ai
obo_outcome:allow
obo_principal_id:did:key:z6MkhaXgBZ…
obo_reason_code:none
obo_task_ref:task-0fe230c3…
producer_id:lane2.ai
schema_ref:draft-obo-agentic-evidence-envelope-00
```

The `evidence_bundle` handle is the stable reference for proof retrieval.

---

## DNS key resolution

FlightSearchAgent calls `resolve_obo_key_from_dns(operator_id)` on **every
incoming request** — no stale cached key material (spec §3.4):

```python
# _obo-key.<operator_id>  IN TXT  "v=obo1 ed25519=<base64url>"
answers = dns.resolver.resolve(f"_obo-key.{operator_id}", "TXT", lifetime=5.0)
```

Startup confirms key source:
```
[FlightSearchAgent] OBO key ready  source=dns-txt  key=vqiddGZ0skvsek13nUks…
```

Falls back to `TRAVEL_AGENT_PUBKEY` env var if DNS is unreachable (`source=env`).
Acceptable for local development; not for production Class C/D actions.

---

## Agent Card

FlightSearchAgent publishes a standard A2A Agent Card at
`GET /.well-known/agent.json`. The `authentication.schemes: ["obo"]` entry is
the machine-readable signal that an OBO credential is required:

```json
{
  "name": "FlightSearchAgent",
  "version": "1.0.0",
  "authentication": {
    "schemes": ["obo"],
    "obo": {
      "required": true,
      "key_resolution": "dns-txt",
      "dns_record_format": "_obo-key.{operator_id}  IN TXT  \"v=obo1 ed25519=<pubkey>\""
    }
  },
  "skills": [
    {"id": "flight-search", "name": "Flight Search"},
    {"id": "hotel-search",  "name": "Hotel Search"}
  ]
}
```

TravelAgent fetches this card before sending any task — discovers the OBO
requirement, confirms the endpoint, proceeds. No out-of-band configuration.

---

## OBO field mapping to A2A

| OBO Credential field | A2A location |
|---------------------|-------------|
| `credential_id` | `extensions.obo.credential_id` |
| `operator_id` | `extensions.obo.operator_id` |
| `principal_id` | `extensions.obo.principal_id` |
| `intent_hash` | `extensions.obo.intent_hash` |
| `issued_at` / `expires_at` | `extensions.obo.issued_at` / `expires_at` |
| `credential_sig` | `extensions.obo.credential_sig` |

| A2A Task field | OBO Evidence Envelope field |
|---------------|----------------------------|
| `task.id` | `task_correlation_ref` |
| `task.status` | `outcome` (`completed` → `allow`) |
| `task.result` | included in `evidence_digest` pre-image |

---

## Inspect evidence after the run

```bash
# List all minted evidence records
curl -s http://localhost:8080/v1/envelopes | jq

# Fetch Merkle proof for a specific envelope
curl -s http://localhost:8080/evidence/<envelope_id>/proof | jq

# Copy the full JSONL log off the volume
docker compose cp sapp:/data/envelopes.jsonl ./evidence-capture.jsonl
cat evidence-capture.jsonl | jq .
```

---

## Error codes exercised

| Scenario | Code | Meaning |
|----------|------|---------|
| 3 — Tampered intent | `OBO-ERR-005` | `SHA-256(task.intent)` ≠ `credential.intent_hash` |
| 4 — Missing extension | `OBO-ERR-001` | `extensions.obo` absent entirely |
| 5 — Expired credential | `OBO-ERR-003` | `expires_at` in the past |
| 6 — Forged signature | `OBO-ERR-004` | Ed25519 verification failed |
| 7 — Replayed credential | `OBO-ERR-008` | `credential_id` already seen |

Full taxonomy: [§5 of the spec](../../draft-obo-agentic-evidence-envelope-01.md).

---

## Files

| File | Purpose |
|------|---------|
| `agents.py` | TravelAgent + FlightSearchAgent (both modes in one file) |
| `keygen.py` | Ed25519 keypair generation, DNS TXT output, `.env` template |
| `sapp_stub/server.py` | SAPP stub — ADR-153 mint + ADR-181 E7 proof routes |
| `docker-compose.yml` | Three-container orchestration with health checks |
| `requirements.txt` | `cryptography`, `dnspython`, `flask` |
| `.env.example` | Template — copy to `.env`, fill from `keygen.py` output |
| `.env` | **gitignored** — private key lives here, never commit |
| `keys/` | **gitignored** — key files written by `keygen.py`, never commit |

---

## Production gaps

| Capability | This demo | Production |
|-----------|-----------|------------|
| Ed25519 signing / verification | ✅ Real | ✅ Real |
| DNS trust anchor | ✅ Real (Route 53, live) | ✅ Real |
| SAPP `POST /v1/evidence/mint` | Stub | Real SAPP instance |
| Merkle tree | SHA-256 over sorted leaves (real commitment) | Full binary Merkle tree with sibling path |
| SAPP operator key | No key — stub JWS is `SHA-256(header.payload)` | Ed25519 keypair; pubkey at `_sapp-key.<domain> IN TXT "v=sapp1 ed25519=…"` |
| JWS proof (`GET /evidence/{id}/proof`) | Structurally valid, not cryptographically signed | Real Ed25519 over `{merkle_root, checkpoint_index, tree_size, iss}` |
| Inclusion proof | Not returned | `inclusion_proof` sibling array lets verifier recompute root independently |
| Epoch root anchoring | Not implemented | `_sapp-epoch-N.<domain> IN TXT` or CT log — prevents retroactive rewrite |
| HTTP Message Signatures (RFC 9421) | Not implemented | Required for §4.4 |
| Curated operator registry | Not implemented | Required for Class C/D |
| Key rotation | Not implemented | Required for long-lived operators |

> **The unsigned Merkle gap explained:** `obo_envelope_sig` proves the *issuer*
> committed to the record. It does not prove SAPP *received* it. A SAPP operator
> Ed25519 signature over the checkpoint is a second independent party attesting
> receipt — closing the accountability chain. See
> [`captures/README.md`](captures/README.md#sapp-merkle-signing--what-the-demo-omits-and-best-practice)
> for the full best-practice description, production JWS payload format, and
> epoch root anchoring pattern.

---

## Spec references

- [draft-obo-agentic-evidence-envelope-01](../../draft-obo-agentic-evidence-envelope-01.md)
- §3.1 OBO Credential
- §3.2 OBO Evidence Envelope
- §4.4 Submission Integrity (HTTP Message Signatures, RFC 9421)
- §5 Error Taxonomy (`OBO-ERR-001` through `OBO-ERR-022`)
- Appendix E — DNS Anchoring (`_obo-key` TXT record format)
