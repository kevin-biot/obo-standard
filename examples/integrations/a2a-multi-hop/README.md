# A2A multi-hop agents — Sentinel monitor negative control

This directory builds on the sibling `../a2a/` reference impl to host a
multi-hop agent-agent-agent topology used as a **negative control** for a
Sentinel-framework experiment in the DOP repo.

The DOP-side experiment lives at:
**`github.com/kevin-biot/DOP` @ `main`, `research/agent-topology-comparison/`**

## Why this exists

The DOP repo's 5-run replication of Gagné's Sentinel monitor on a
typed-intent topology (16-service banking MVP) read **S1 = S4 = CPL = 0**
across 300 monitor windows × 5 RNG seeds. The interpretation we want to
defend is "the metrics correctly detect that DOP's architecture has no
NL-coupling substrate." But that interpretation is asymmetric — it needs
a **positive measurement on a topology where the substrate is present**.

This dir provides that positive-measurement substrate: a deliberate
agent-agent-agent chain where each agent embeds an LM Studio call and
passes natural-language `narrative_text` forward. The same Go monitor
implementation (parity-tested 1e-6 against Gagné's Python reference)
will be pointed at this stack via DOP-side wire-tap proxy + scraper.

If S1/S4 fire on this topology and stay zero on DOP, the asymmetric
claim is empirically grounded.

## What this is NOT

- **Not a security-best-practice example.** This is the architecture DOP
  was designed to reject. It's here to be measured, not emulated.
- **Not a faithful OBO ceremony reproduction.** OBO credentials, DNS
  trust anchors, and Anchor evidence are deliberately stripped — the
  experiment measures Sentinel signals on the agent-agent-agent
  substrate, and the OBO ceremony is orthogonal to that.
- **Not production code.** Demo-grade. Will rebuild containers each run.

## Topology variants

```
T1 (linear, smallest signal-bearing case):

  client ──► TravelAgent  ──► FlightAgent  ──► SeatAgent
              :8082            :8081            :8083

T2 (interim fan-out, exercises CPL specifically):

                                   ┌──► SeatAgent  :8083
  client ──► TravelAgent  ──► FlightAgent
              :8082            :8081       └──► MealAgent  :8084
```

Each arrow carries a JSON A2A task with a `narrative_text` field. Each
agent reads that field, calls LM Studio with a per-agent "voice" prompt
(see `AGENT_VOICES` in `agents.py`), produces its own `narrative_text`
contribution, forwards to downstream agents.

## Running

Prerequisites:
- Docker + Compose v2
- LM Studio running locally with `mistralai/ministral-3-3b` on `:1234`

```bash
# T1 (linear chain)
docker compose --profile t1 up --build

# T2 (interim fan-out)
docker compose --profile t2 up --build

# Smoke-test a single request
curl -s -X POST http://localhost:8082/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "intent": "travel.search.flight",
    "narrative_text": "Book me LHR to JFK on June 15, business class.",
    "session_id": "smoke-001",
    "persona": "business-traveller"
  }' | jq .
```

Expected response: nested JSON with `narrative_text` from TravelAgent,
plus `downstream[]` containing FlightAgent's response, which in turn
contains its own `downstream[]` with SeatAgent (T1) or both
SeatAgent + MealAgent (T2).

## Sentinel measurement

The DOP-side wire-tap proxy + scraper in
`github.com/kevin-biot/DOP/research/agent-topology-comparison/code/`
sits in front of each agent's `/tasks` endpoint, captures
`narrative_text` in/out, and feeds the existing Go monitor.

Per-agent ports:
- TravelAgent  :8082
- FlightAgent  :8081
- SeatAgent    :8083
- MealAgent    :8084

The wire-tap proxies bind to one port higher (8092 / 8091 / 8093 /
8094) and forward to the agent's actual port. Driver script points at
the proxy ports.

## Files

```
agents.py              All agent role implementations + LM Studio client
docker-compose.yml     T1 + T2 profiles
Dockerfile             Shared (one image, role + port via env)
requirements.txt       Flask + requests
README.md              This file
```

## Cross-references

- DOP-side experiment plan: `research/agent-topology-comparison/PLAN.md`
- DOP-230 §14.9 5-run replication (the positive case being contrasted):
  `research/dop-230-soak-v2/feedback/report.md`
- Sibling A2A reference impl (production-shaped): `../a2a/README.md`
