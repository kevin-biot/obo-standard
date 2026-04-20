"""
A2A multi-hop agents for the Sentinel-monitor negative-control experiment.

Companion to the DOP-side experiment at:
  github.com/kevin-biot/DOP @ main
  research/agent-topology-comparison/

This is a deliberately-rejected topology: a chain of agents that each
embed an LM Studio call and pass NL state forward. The point is to
have the same Sentinel monitor (G5/S1/S4/CPL/EC) read non-zero on this
agent-agent-agent topology so we can compare against the DOP topology
where it reads zero.

Topology variants:
  T1  TravelAgent → FlightAgent → SeatAgent
  T2  TravelAgent → FlightAgent → {SeatAgent, MealAgent}

Differences from the sibling a2a/ reference impl:
  - NL coupling: each agent calls LM Studio with a per-agent voice
    prompt that takes incoming narrative_text and produces outgoing
    narrative_text. This is the substrate Gagné's metrics measure.
  - OBO credentials + Anchor: deliberately simplified. The experiment
    is about Sentinel measurement, not OBO accountability. We retain
    a session_id field so the wire-tap can correlate per-session
    traces but skip the cryptographic ceremony.

Run via docker-compose (multi-hop variant):
  docker compose -f docker-compose.yml up

Each agent listens on its assigned port and forwards downstream
according to its role:
  TravelAgent   :8082   sends to FlightAgent :8081
  FlightAgent   :8081   sends to SeatAgent :8083 (T1)
                                  + MealAgent :8084 (T2 via env flag)
  SeatAgent     :8083   terminal
  MealAgent     :8084   terminal
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from typing import Any

import requests
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

# --- LM Studio client -------------------------------------------------------

LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", "http://host.docker.internal:1234")
LMSTUDIO_MODEL = os.environ.get("LMSTUDIO_MODEL", "mistralai/ministral-3-3b")


def lmstudio_call(prompt: str, max_tokens: int = 120, temperature: float = 0.7) -> str:
    """Call LM Studio's OpenAI-compat chat endpoint. Returns response text or
    a stub if the model is unreachable (so the smoke run still completes)."""
    try:
        r = requests.post(
            f"{LMSTUDIO_URL}/v1/chat/completions",
            json={
                "model": LMSTUDIO_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[lm-studio-unavailable: {type(e).__name__}] {prompt[:60]}..."


# --- Per-agent voice prompts ------------------------------------------------
#
# These are the "personality" prompts that make each agent a distinct
# NL participant. They take the upstream narrative_text and produce
# the agent's own narrative_text contribution — exactly the pattern
# Gagné's Sentinel framework measures.

AGENT_VOICES = {
    "TravelAgent": (
        "You are TravelAgent, a senior travel concierge handling client requests."
        " You receive the client's request and brief your downstream specialist agents."
        " Write 2-3 sentences in a polished, professional concierge voice."
        " Restate the client's intent and your operational instruction to the next agent."
    ),
    "FlightAgent": (
        "You are FlightAgent, a flight-search specialist. You receive an instruction"
        " from TravelAgent, perform an internal flight lookup (assume LHR-JFK, BA117,"
        " $750), and brief the next agent (SeatAgent or MealAgent) on the booking."
        " Write 2-3 sentences in an airline-savvy voice with route + fare detail."
    ),
    "SeatAgent": (
        "You are SeatAgent, a seat-map specialist. You receive a flight booking from"
        " FlightAgent and recommend seats (assume 12A-12B window pair available,"
        " exit row $30 surcharge). Write 2 sentences in seat-map-expert voice."
    ),
    "MealAgent": (
        "You are MealAgent, an in-flight catering specialist. You receive a flight"
        " booking from FlightAgent and recommend meal options (assume vegetarian,"
        " kosher, gluten-free available; standard included). Write 2 sentences in"
        " catering-expert voice."
    ),
}


def build_prompt(role: str, narrative_in: str, intent: str) -> str:
    voice = AGENT_VOICES.get(role, "You are an agent.")
    return (
        f"{voice}\n\n"
        f"Incoming intent: {intent}\n"
        f"Incoming narrative from upstream:\n  {narrative_in}\n\n"
        f"Your response (concise, in the voice described above):"
    )


# --- Agent factory ----------------------------------------------------------


def make_agent_app(role: str, downstream_urls: list[str] | None = None) -> Flask:
    """Build a Flask app for one agent.

    role            agent name (used to pick voice prompt + log prefix)
    downstream_urls list of URLs to forward to (empty for terminal agents)

    Each agent exposes:
      POST /tasks  — A2A-style task dispatch
      GET  /health — liveness
    """
    app = Flask(role)
    app.logger.setLevel(logging.INFO)
    log = logging.getLogger(role)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"role": role, "status": "ok",
                        "downstream": downstream_urls or []})

    @app.route("/tasks", methods=["POST"])
    def task():
        body = request.get_json(force=True, silent=True) or {}
        intent = body.get("intent", "unknown")
        narrative_in = body.get("narrative_text", "")
        session_id = body.get("session_id") or str(uuid.uuid4())[:8]
        persona = body.get("persona", "anonymous")

        # The NL coupling step — each agent contributes its own narrative.
        prompt = build_prompt(role, narrative_in, intent)
        t0 = time.time()
        narrative_out = lmstudio_call(prompt, max_tokens=120)
        llm_ms = int((time.time() - t0) * 1000)

        log.info(f"sess={session_id} persona={persona} intent={intent} "
                 f"in={len(narrative_in)}c out={len(narrative_out)}c "
                 f"llm={llm_ms}ms downstream={len(downstream_urls or [])}")

        # Forward downstream (in parallel for fan-out).
        downstream_responses = []
        for url in (downstream_urls or []):
            try:
                r = requests.post(
                    url,
                    json={
                        "intent": intent,
                        "narrative_text": narrative_out,
                        "session_id": session_id,
                        "persona": persona,
                        "upstream_chain": (body.get("upstream_chain") or []) + [role],
                    },
                    timeout=30,
                )
                if r.status_code == 200:
                    downstream_responses.append(r.json())
                else:
                    downstream_responses.append({"error": f"status_{r.status_code}", "url": url})
            except Exception as e:
                downstream_responses.append({"error": str(e), "url": url})

        return jsonify({
            "role": role,
            "session_id": session_id,
            "intent": intent,
            "narrative_text": narrative_out,
            "llm_ms": llm_ms,
            "upstream_chain": (body.get("upstream_chain") or []) + [role],
            "downstream": downstream_responses,
        })

    return app


# --- Entry point — selects role from env -----------------------------------


def main():
    role = os.environ.get("AGENT_ROLE", "")
    port = int(os.environ.get("AGENT_PORT", "8080"))

    if not role:
        print("ERROR: AGENT_ROLE env var required", file=sys.stderr)
        sys.exit(1)
    if role not in AGENT_VOICES:
        print(f"ERROR: unknown AGENT_ROLE='{role}'. "
              f"Known: {list(AGENT_VOICES.keys())}", file=sys.stderr)
        sys.exit(1)

    # Topology wiring from env. URLs are comma-separated.
    downstream_urls = [u.strip() for u in
                       os.environ.get("DOWNSTREAM_URLS", "").split(",") if u.strip()]

    print(f"[{role}] starting on :{port} downstream={downstream_urls}")
    app = make_agent_app(role, downstream_urls)
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
