# OBO + A2A Composition — Docker Demo

**Illustrative reference — not a production implementation.**

Three containers. One DNS TXT record. Real Ed25519 signatures.
Full evidence chain from credential issuance through task execution to SAPP receipt.

---

## What runs

```
┌─────────────────────────────────────────────────────────────────────┐
│ travel-agent container                                              │
│   TravelAgent                                                       │
│   ① Issues OBO Credential (Ed25519-signed, operator key)           │
│   ② Attaches credential to A2A task in extensions.obo              │
│   ③ POST /tasks → flight-search                                     │
│   ④ On completion: seals OBO Evidence Envelope (Ed25519-signed)    │
│   ⑤ POST /v1/envelopes → sapp                                       │
└───────────────────┬─────────────────────────┬───────────────────────┘
                    │ A2A task (HTTP)          │ Evidence envelope (HTTP)
                    ▼                          ▼
┌───────────────────────────────┐  ┌──────────────────────────────────┐
│ flight-search container       │  │ sapp container                   │
│   FlightSearchAgent           │  │   SAPP stub                      │
│   Verifies OBO credential:    │  │   Verifies envelope_sig (Ed25519)│
│   · Ed25519 sig check         │  │   Stores envelope                │
│   · intent_hash consistency   │  │   Returns Merkle receipt         │
│   · expiry check              │  │   Writes /data/envelopes.jsonl   │
│   Executes task               │  │                                  │
└───────────────────────────────┘  └──────────────────────────────────┘
```

---

## Prerequisites

- Docker + docker-compose
- Python 3.11+ (for keygen only — runs locally)
- One DNS name you control

```bash
pip install cryptography   # for keygen.py only
```

---

## Setup

### Step 1 — Generate keys

```bash
cd examples/integrations/a2a
python keygen.py --operator-id your-domain.com
```

Output:
- `keys/private_key.pem` — keep secret
- `keys/public_key.b64` — base64url of raw 32-byte Ed25519 public key
- DNS TXT record value printed to stdout
- `.env` values printed to stdout

### Step 2 — Set DNS TXT record

```
_obo-key.your-domain.com  IN TXT  "v=obo1 ed25519=<value from keygen.py>"
```

Verify propagation (may take a few minutes):

```bash
dig TXT _obo-key.your-domain.com +short
```

### Step 3 — Configure .env

```bash
cp .env.example .env
# Paste TRAVEL_AGENT_OPERATOR_ID, TRAVEL_AGENT_PRIVATE_KEY_B64,
# TRAVEL_AGENT_PUBKEY from keygen.py output
```

### Step 4 — Run

```bash
docker-compose up --build
```

The `travel-agent` container waits for `flight-search` and `sapp` to be healthy,
then runs three scenarios and exits.

---

## Expected output

```
══════════════════════════════════════════════════════════════
  OBO + A2A DEMO — Cross-org task with real evidence chain
══════════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────────
  SCENARIO 1: Flight search: LHR → JFK
──────────────────────────────────────────────────────────────

  [1/4] Issuing OBO Credential
        operator_id:    your-domain.com
        principal_id:   did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2Q…
        intent_hash:    b98d4238ecb978415a30…
        credential_sig: Ed25519 ✓  (xK3mP9wQz…)

  [2/4] Sending A2A Task → FlightSearchAgent
        POST http://flight-search:8081/tasks
        task_id: task-969a89d4…

  [3/4] FlightSearchAgent response
        status: completed
        flights found: 2
          BA117  LHR→JFK  $487.0
          VS3    LHR→JFK  $512.0

  [4/4] Sealing OBO Evidence Envelope → SAPP
        evidence_digest: b76993bb1481565b31da…
        envelope_sig:    Ed25519 ✓  (of3jo69X…)
        POST http://sapp:8080/v1/envelopes

        ── SAPP Receipt ──────────────────────────────────
        receipt_id:    sapp-receipt-4e1fd6eb…
        merkle_leaf:   a3f421cc9d1b2e7f44ab…
        anchored_at:   2026-04-04T00:35:19.492591+00:00
        status:        accepted ✓

...

  SCENARIO 3: Tampered intent (should be rejected)
  [TAMPER] intent changed: '…LHR to JFK…' → '…LHR to CDG…'
  [3/4] FlightSearchAgent response
        status: failed
        ✗ rejected: OBO intent_hash mismatch — tampered or drifted intent
```

---

## Inspect evidence after the demo

SAPP writes all received envelopes to a Docker volume:

```bash
# List all envelopes received
curl http://localhost:8080/v1/envelopes | jq

# Get a specific envelope + its SAPP receipt
curl http://localhost:8080/v1/envelopes/<envelope_id> | jq

# Raw JSONL from the volume
docker-compose exec sapp cat /data/envelopes.jsonl | jq
```

---

## OBO → A2A field mapping

| OBO Credential field          | A2A Task location                   |
|-------------------------------|-------------------------------------|
| `credential_id`               | `extensions.obo.credential_id`      |
| `operator_id`                 | `extensions.obo.operator_id`        |
| `principal_id`                | `extensions.obo.principal_id`       |
| `intent_hash`                 | `extensions.obo.intent_hash`        |
| `issued_at` / `expires_at`    | `extensions.obo.issued_at/expires_at` |
| `credential_sig`              | `extensions.obo.credential_sig`     |

| A2A Task field  | OBO Evidence Envelope field         |
|-----------------|-------------------------------------|
| `task.id`       | `task_correlation_ref`              |
| `task.status`   | `outcome` (`completed` → `allow`)   |
| `task.result`   | included in `evidence_digest` pre-image |

---

## What is simplified vs production

| This demo | Production |
|---|---|
| Public key from env var | DNS TXT `_obo-key.<operator_id>` resolved live (Appendix E) or `did:web` DID Document (Appendix F) |
| Stub Merkle leaf (SHA-256) | Real Merkle tree with inclusion proof, epoch root anchored in DNS |
| HTTP POST (unsigned) | HTTP Message Signatures [RFC 9421] per §4.4 — same Ed25519 key, no new infrastructure |
| In-memory SAPP store | Immutable append-only audit log |

---

## Spec references

- [draft-obo-agentic-evidence-envelope-00](../../draft-obo-agentic-evidence-envelope-00.md)
- §3.1 OBO Credential
- §3.2 OBO Evidence Envelope
- §4.4 Submission Integrity (HTTP Message Signatures, RFC 9421)
- Appendix E — DNS Anchoring (`_obo-key` TXT)
- Appendix F — DID Profile (did:web, did:key, did:ebsi)
