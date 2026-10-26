#!/usr/bin/env node
// Separate implementation: no calls to the Python verifier or its helpers.
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import Ajv2020 from 'ajv/dist/2020.js';
import canonicalize from 'canonicalize';
import {compactVerify, importJWK} from 'jose';
import {parseTree} from 'jsonc-parser';

export const PROFILE = 'obo-keycloak/0.5-alpha.3';
const commonNames = ['iss', 'sub', 'aud', 'iat', 'exp', 'jti'];
const decimalMembers = new WeakMap();
const utf8 = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true});
const limitations = [
  'Second implementation maintained in the same repository, not independent third-party validation.',
  'Pinned trust and historical time are verifier inputs; no live issuer introspection or mandate revocation.',
  'Receipts are service assertions, not independently attested execution or complete log coverage.',
  'No holder binding, multi-hop delegation, trusted timestamp or determination of lawful delegation and duty of care.'
];

function check(ok, message) {
  if (!ok) throw new Error(message);
}

function object(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function exact(value, names) {
  check(object(value) && Object.keys(value).length === names.length && names.every(n => Object.hasOwn(value, n)),
    'unsupported or missing members');
}

export function strictJson(source) {
  const errors = [];
  const tree = parseTree(source, errors, {disallowComments: true, allowTrailingComma: false, allowEmptyContent: false});
  check(tree && errors.length === 0, 'invalid JSON');
  const result = JSON.parse(source);
  function visit(node, value) {
    if (node.type === 'object') {
      const seen = new Set();
      const decimals = new Set();
      for (const property of node.children || []) {
        const [name, child] = property.children;
        check(!seen.has(name.value), 'duplicate JSON member');
        seen.add(name.value);
        if (child.type === 'number' && /[.eE]/.test(source.slice(child.offset, child.offset + child.length))) decimals.add(name.value);
        visit(child, value[name.value]);
      }
      decimalMembers.set(value, decimals);
    } else if (node.type === 'array') {
      node.children.forEach((child, i) => visit(child, value[i]));
    } else if (node.type === 'number') {
      const raw = source.slice(node.offset, node.offset + node.length);
      check(Number.isFinite(value), 'nonfinite JSON number');
      if (!/[.eE]/.test(raw)) check(Number.isSafeInteger(value), 'unsafe JSON integer');
    }
  }
  visit(tree, result);
  return result;
}

export function readJson(path) {
  return strictJson(utf8.decode(readFileSync(path)));
}

function hash(bytes) {
  return 'sha256:' + createHash('sha256').update(bytes).digest('hex');
}

export function digestJson(value) {
  return hash(Buffer.from(canonicalize(value), 'utf8'));
}

function tokenHash(token) {
  check(typeof token === 'string' && /^[\x00-\x7f]*$/.test(token), 'token is not ASCII');
  return hash(Buffer.from(token, 'ascii'));
}

function segment(value) {
  check(/^[A-Za-z0-9_-]+$/.test(value), 'invalid base64url segment');
  const bytes = Buffer.from(value, 'base64url');
  check(bytes.toString('base64url') === value, 'noncanonical base64url segment');
  return bytes;
}

function common(claims) {
  for (const name of ['iss', 'sub', 'aud', 'jti']) check(typeof claims[name] === 'string' && claims[name].length > 0, 'invalid ' + name);
  for (const name of ['iat', 'exp']) {
    check(Number.isSafeInteger(claims[name]) && claims[name] >= 0 && !decimalMembers.get(claims)?.has(name), 'invalid ' + name);
  }
  check(claims.iat < claims.exp, 'invalid JWT window');
}

async function signed(token, anchor, typ, algorithm, audience) {
  check(typeof token === 'string', 'expected compact JWS');
  const parts = token.split('.');
  check(parts.length === 3, 'expected compact JWS');
  const bytes = parts.map(segment);
  const header = strictJson(utf8.decode(bytes[0]));
  const claims = strictJson(utf8.decode(bytes[1]));
  exact(header, ['alg', 'typ', 'kid']);
  const jwk = algorithm === 'RS256' ? anchor.jwk : {kty: 'OKP', crv: 'Ed25519', x: anchor.public_key};
  check(header.alg === algorithm && header.typ === typ && header.kid === (anchor.jwk?.kid ?? anchor.kid), 'JOSE mismatch');
  const key = await importJWK(jwk, algorithm);
  if (algorithm === 'RS256') check(key.algorithm.modulusLength >= 2048, 'weak RSA key');
  // Verify JWS bytes with jose; apply the profile's historical claim rules below.
  await compactVerify(token, key, {algorithms: [algorithm]});
  check(object(claims), 'claims must be an object');
  common(claims);
  check(claims.iss === anchor.iss && claims.aud === audience, 'issuer/audience mismatch');
  return claims;
}

const ajv = new Ajv2020({strict: true, allErrors: false, ownProperties: true});
const bundleSchema = ajv.compile(readJson(new URL('../../schemas/keycloak-bundle-v0.5.json', import.meta.url)));
const trustSchema = ajv.compile(readJson(new URL('../../schemas/keycloak-trust-v0.5.json', import.meta.url)));

export async function verifyBundle(bundle, trust, at) {
  check(bundleSchema(bundle), 'bundle schema rejected');
  check(trustSchema(trust), 'trust schema rejected');
  check(Number.isSafeInteger(at) && at >= 0, 'invalid evaluation time');
  const e = trust.expected;
  const op = bundle.operation;
  const opHash = digestJson(op);
  const workload = await signed(bundle.grant_jwt, trust.workload_issuer, 'JWT', 'RS256', e.audience);
  const workloadNames = [...commonNames, 'typ', 'azp', 'scope', 'client_id'];
  check(workloadNames.every(n => Object.hasOwn(workload, n)) &&
    Object.keys(workload).every(n => [...workloadNames, 'clientHost', 'clientAddress'].includes(n)), 'unsupported workload claims');
  check(workload.typ === 'Bearer' && workload.sub === e.workload_subject && workload.azp === e.agent_id &&
    workload.client_id === e.agent_id && workload.scope === e.scope, 'workload identity/scope mismatch');
  check(workload.iat <= at && at < workload.exp, 'workload expired or future');

  const mandate = await signed(bundle.delegation_jwt, trust.issuer, 'obo-delegation+jwt', 'EdDSA', e.audience);
  exact(mandate, [...commonNames, 'profile', 'grant_digest', 'operation_digest', 'workload_subject', 'client_id', 'operator_id', 'scope']);
  check(mandate.profile === PROFILE && mandate.sub === e.principal_id && mandate.workload_subject === workload.sub &&
    mandate.client_id === workload.client_id && mandate.operator_id === e.operator_id && mandate.scope === workload.scope, 'mandate identity mismatch');
  check(mandate.grant_digest === tokenHash(bundle.grant_jwt) && mandate.operation_digest === opHash, 'mandate binding mismatch');
  check(workload.iat <= mandate.iat && mandate.iat <= at && at < mandate.exp && mandate.exp <= workload.exp, 'mandate window mismatch');

  const policy = await signed(bundle.policy_jwt, trust.policy_authority, 'obo-policy+jwt', 'EdDSA', e.audience);
  exact(policy, [...commonNames, 'profile', 'action', 'resource', 'allowed_fields', 'scope']);
  check(policy.profile === PROFILE && policy.sub === e.operator_id, 'policy identity/profile mismatch');
  check(policy.iat <= at && at < policy.exp, 'policy expired or future');
  for (const name of ['action', 'resource', 'scope']) check(typeof policy[name] === 'string' && policy[name].length > 0, 'invalid policy value');
  const fields = policy.allowed_fields;
  check(Array.isArray(fields) && fields.length > 0 && fields.every(f => typeof f === 'string' && f.length > 0) &&
    new Set(fields).size === fields.length, 'invalid policy fields');
  const allowed = policy.scope === workload.scope && policy.action === op.action && policy.resource === op.resource &&
    Object.keys(op.parameters).every(f => fields.includes(f));

  const decision = await signed(bundle.decision_jwt, trust.service, 'obo-decision+jwt', 'EdDSA', e.audience);
  exact(decision, [...commonNames, 'profile', 'grant_digest', 'delegation_digest', 'policy_digest', 'operation_digest',
    'request_id', 'client_id', 'operator_id', 'outcome', 'reason_code']);
  check(decision.profile === PROFILE && decision.sub === mandate.sub && decision.client_id === workload.client_id &&
    decision.operator_id === e.operator_id, 'decision identity/profile mismatch');
  check(decision.iat === at, 'decision reference time mismatch');
  check(decision.grant_digest === tokenHash(bundle.grant_jwt) && decision.delegation_digest === tokenHash(bundle.delegation_jwt) &&
    decision.policy_digest === tokenHash(bundle.policy_jwt) && decision.operation_digest === opHash && decision.request_id === op.request_id,
  'decision binding mismatch');
  check(decision.outcome === (allowed ? 'allow' : 'deny') && decision.reason_code === (allowed ? 'policy.allow' : 'policy.deny'), 'decision contradicts policy');

  let outcome = 'denied';
  let lastEvent = at;
  if (allowed) {
    check(Object.hasOwn(bundle, 'execution_jwt') && Object.hasOwn(bundle, 'response'), 'missing execution');
    const execution = await signed(bundle.execution_jwt, trust.service, 'obo-execution+jwt', 'EdDSA', e.audience);
    exact(execution, [...commonNames, 'profile', 'decision_digest', 'operation_digest', 'response_digest', 'request_id', 'outcome']);
    check(execution.profile === PROFILE && execution.sub === mandate.sub, 'execution identity/profile mismatch');
    check(execution.decision_digest === tokenHash(bundle.decision_jwt) && execution.operation_digest === opHash &&
      execution.response_digest === digestJson(bundle.response) && execution.request_id === op.request_id, 'execution binding mismatch');
    check(at <= execution.iat && execution.iat < Math.min(workload.exp, mandate.exp, policy.exp, decision.exp), 'execution outside authorization');
    check(['completed', 'failed'].includes(execution.outcome), 'unsupported execution outcome');
    outcome = execution.outcome;
    lastEvent = execution.iat;
  } else {
    check(!Object.hasOwn(bundle, 'execution_jwt') && !Object.hasOwn(bundle, 'response'), 'denial contains execution');
  }

  const status = trust.status;
  if (status !== undefined) {
    check(status.as_of <= at && at <= lastEvent && lastEvent < status.valid_until, 'status snapshot does not cover events');
    check(!status.revoked_grant_ids.includes(workload.jti), 'grant revoked');
  }
  return {profile: PROFILE, result: status ? 'verified' : 'incomplete', outcome, evaluation_time: at,
    checks: {signatures: 'verified', identity_bindings: 'verified', operation_binding: 'verified', policy_decision: 'verified',
      receipts: 'verified', archived_status: status ? 'verified' : 'unknown', workload_grant: 'verified', explicit_mandate: 'verified'},
    limitations};
}

export async function verifyFiles(paths, trustPath, at) {
  const trust = readJson(trustPath);
  const seen = new Set();
  const reports = [];
  for (const path of paths) {
    const bundle = readJson(path);
    const report = await verifyBundle(bundle, trust, at);
    const workload = strictJson(utf8.decode(segment(bundle.grant_jwt.split('.')[1])));
    for (const id of [JSON.stringify(['request', bundle.operation.request_id]), JSON.stringify(['grant', workload.iss, workload.jti])]) {
      check(!seen.has(id), 'duplicate request or grant in supplied bundle set');
      seen.add(id);
    }
    reports.push(report);
  }
  return reports;
}

async function main(args) {
  try {
    if (args.length === 1 && args[0] === '--version') {
      console.log('obo-node ' + readJson(new URL('./package.json', import.meta.url)).version);
      return;
    }
    const paths = [];
    let trustPath, at;
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--trust' && trustPath === undefined) trustPath = args[++i];
      else if (args[i] === '--at' && at === undefined) {
        check(/^\d+$/.test(args[++i] ?? ''), 'invalid --at');
        at = Number(args[i]);
      } else {
        check(!args[i].startsWith('-'), 'unknown or repeated option');
        paths.push(args[i]);
      }
    }
    check(paths.length && trustPath && at !== undefined, 'usage: node verify.mjs BUNDLE... --trust TRUST --at SECONDS');
    const reports = await verifyFiles(paths, trustPath, at);
    console.log(JSON.stringify(reports.length === 1 ? reports[0] : reports, null, 2));
    process.exitCode = reports.every(r => r.result === 'verified') ? 0 : 2;
  } catch (error) {
    console.log(JSON.stringify({profile: PROFILE, result: 'failed', error: error.message}));
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main(process.argv.slice(2));
