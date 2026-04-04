# ADR-002: Ed25519 as the Sole Signing Algorithm (No Algorithm Agility)

**Status:** Accepted
**Date:** 2026-04-02
**Deciders:** OBO working group
**Spec ref:** §3.5

---

## Context

OBO requires cryptographic signatures in two places:

1. `credential_sig` — over the canonical OBO Credential fields, by the issuing
   operator.
2. `envelope_sig` — over `evidence_digest`, by the acting operator.

And optionally in two more (Class C/D):

3. `link_sig` / `delegation_issuer_sig` — over delegation chain links (§3.3).
4. `principal_sig` / `operator_sig` — over the Intent Artifact (§3.4).

A decision was required on which signing algorithm(s) to support.

---

## Decision

**OBO mandates Ed25519 (RFC 8032) as the sole signing algorithm. No algorithm
agility. No negotiation.**

All signatures in the OBO protocol are Ed25519 signatures over the SHA-256 hash
of the canonical pre-image. Public keys are the raw 32-byte Ed25519 public key,
base64url-encoded without padding.

The `alg` field is not present in OBO messages — there is nothing to negotiate.
A verifier that receives a message claiming a different algorithm MUST reject it.

---

## Rationale

### Algorithm agility is a security liability

"Algorithm agility" — the ability to negotiate or specify which signing
algorithm is used — sounds like a feature but has a consistent history of
producing vulnerabilities. The TLS 1.2 cipher suite negotiation attacks
(BEAST, POODLE, FREAK, Logjam), JWT algorithm confusion (`"alg": "none"`, RSA
vs HMAC confusion), and XML-DSig algorithm substitution attacks all share the
same root cause: a receiver that accepts algorithm selection from an untrusted
party can be induced to use a weaker algorithm.

For OBO's threat model — where a verifier must trust a presented credential
exactly as far as the cryptography warrants — any downgrade path is
unacceptable.

### Why Ed25519

**Performance.** Ed25519 signature verification is fast — typically 50–100 µs
on modern hardware. This matters for per-transaction verification at scale.
RSA-2048 verification is comparable but RSA-4096 is significantly slower and
ECDSA over P-256 requires careful implementation to avoid side channels.

**Small key and signature sizes.** Ed25519 public keys are 32 bytes (43 chars
base64url). Signatures are 64 bytes. Both fit comfortably in DNS TXT records,
JWT headers, and HTTP extension fields without size concerns. RSA-2048 keys are
294 bytes (base64) and signatures 256 bytes.

**No padding oracle attacks.** RSA signing is vulnerable to padding oracle
attacks when implemented incorrectly (Bleichenbacher, PKCS#1 v1.5). Ed25519
has no padding; the signing operation is deterministic.

**Deterministic signatures.** Ed25519 is deterministic — the same message and
key always produce the same signature. This eliminates the class of attacks
arising from poor random number generation that affects ECDSA (the Sony PS3
private key extraction attack is the canonical example of weak randomness in
ECDSA signing).

**Widely implemented.** Ed25519 is available in the standard library or a
well-audited package in every major programming language: Python
(`cryptography`), Go (`crypto/ed25519`), Rust (`ed25519-dalek`), Java
(`Bouncy Castle`), Node.js (`crypto` module). Implementers do not need to pull
in exotic dependencies.

**Modern standard with strong security analysis.** Ed25519 is specified in RFC
8032 (2017), used in TLS 1.3, SSH, and Signal. Its security properties are
well-understood and it has received extensive cryptanalytic attention without
material weakness.

### Why not P-256 / ECDSA

ECDSA over P-256 is widely deployed (TLS, JOSE, FIDO2) and a reasonable choice.
It was not chosen because:

- ECDSA requires a fresh random nonce per signature; poor randomness leads to
  private key recovery (as in the PS3 attack).
- P-256 curve arithmetic is more complex to implement correctly; constant-time
  implementations require care.
- Key and signature sizes are larger than Ed25519 (P-256 pubkeys are 65 bytes
  uncompressed, signatures are 64 bytes variable-length DER).

OBO may add P-256 support in a future profile for environments where Ed25519
is not available (e.g. certain HSM configurations). If added, it will be a
separate named profile, not a negotiated alternative.

### Why not RSA

RSA-2048 is the incumbent and is universally available. It was not chosen
because:

- Key sizes are large (294 bytes base64 for a 2048-bit key) and DNS TXT records
  have practical size limits.
- RSA signing is stateful in the sense that PKCS#1 v1.5 padding requires
  correct implementation to avoid oracle attacks.
- Performance at RSA-4096 (advisable for new deployments with long key lifetimes)
  is substantially worse than Ed25519.
- RSA is not the direction the field is moving for new protocol design.

---

## Consequences

**Positive:**
- Verifiers have exactly one code path for signature verification. No algorithm
  dispatch, no negotiation, no downgrade attacks.
- Implementations are simpler and easier to audit.
- DNS TXT records are compact.

**Negative / watch points:**
- Environments with HSMs that do not support Ed25519 (some FIPS 140-2 Level 3
  devices support only RSA and ECDSA P-256/P-384) cannot use OBO signing
  without a software shim or key wrapping approach. This is documented as a
  known limitation. The P-256 profile extension is the planned mitigation.
- Post-quantum: Ed25519 is not post-quantum secure. Neither is RSA or ECDSA.
  A post-quantum signing profile (e.g. ML-DSA / CRYSTALS-Dilithium) is a future
  consideration when NIST PQC standards mature and library support is
  widespread. OBO's deterministic canonical form makes adding a new algorithm
  profile tractable without breaking existing implementations.

---

## Rejected alternatives

| Alternative | Reason rejected |
|------------|----------------|
| Algorithm agility (negotiate alg in message) | Algorithm confusion attacks; downgrade risk |
| RSA-2048 / RSA-4096 | Large key/signature size; padding oracle risk; not forward-looking |
| ECDSA / P-256 | Non-deterministic; more implementation surface; larger than Ed25519 |
| HMAC | Symmetric — requires shared secret; does not support third-party verification |
