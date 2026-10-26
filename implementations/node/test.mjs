import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, rmSync, writeFileSync, readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {digestJson, readJson, strictJson, verifyBundle} from './verify.mjs';

const corpus = readJson(new URL('../../tests/vectors/keycloak/corpus.json', import.meta.url));
const cli = fileURLToPath(new URL('./verify.mjs', import.meta.url));

for (const vector of corpus.cases) {
  test('shared vector: ' + vector.name, async () => {
    const verify = async () => verifyBundle(strictJson(vector.bundle_json), strictJson(vector.trust_json), vector.at);
    if (vector.expected.result === 'failed') {
      await assert.rejects(verify);
    } else {
      const report = await verify();
      assert.equal(report.result, vector.expected.result);
      assert.equal(report.outcome, vector.expected.outcome);
      assert.ok(report.limitations.length);
    }
  });
}

test('strict parser rejects ambiguous, nonfinite and unsafe input', () => {
  for (const text of ['{"a":1,"\\u0061":2}', '{/*comment*/"a":1}', '{"a":1,}', '{"n":NaN}',
    '{"n":1e999}', '{"n":9007199254740993}', '\ufeff{}', 'true false']) assert.throws(() => strictJson(text));
});

test('strict parser preserves own prototype-like members', () => {
  const parsed = strictJson('{"__proto__":{"polluted":true},"constructor":1}');
  assert.equal(Object.hasOwn(parsed, '__proto__'), true);
  assert.equal({}.polluted, undefined);
  assert.equal(digestJson(parsed), digestJson(JSON.parse('{"constructor":1,"__proto__":{"polluted":true}}')));
});

test('JCS rejects lone Unicode surrogates', () => {
  assert.throws(() => digestJson({text: '\ud800'}));
  assert.throws(() => digestJson({'\ud800': 1}));
});

test('CLI exit codes, duplicate sets and argument validation', () => {
  const directory = mkdtempSync(join(tmpdir(), 'obo-node-test-'));
  try {
    const bundle = join(directory, 'bundle.json');
    const trust = join(directory, 'trust.json');
    for (const [name, code] of [['completed', 0], ['missing-status', 2], ['signed-duplicate-member', 1]]) {
      const vector = corpus.cases.find(v => v.name === name);
      writeFileSync(bundle, vector.bundle_json);
      writeFileSync(trust, vector.trust_json);
      const args = [bundle, '--trust', trust, '--at', String(vector.at)];
      const result = spawnSync(process.execPath, [cli, ...args], {encoding: 'utf8'});
      assert.equal(result.status, code, result.stdout + result.stderr);
      assert.equal(JSON.parse(result.stdout).result, vector.expected.result);
      if (code === 0) {
        const duplicate = spawnSync(process.execPath, [cli, bundle, ...args], {encoding: 'utf8'});
        assert.equal(duplicate.status, 1);
        assert.match(duplicate.stdout, /duplicate request or grant/);
      }
    }
    for (const args of [[], ['--unknown'], [bundle], [bundle, '--trust'], [bundle, '--trust', trust, '--at', '1.0'],
      [bundle, '--trust', trust, '--at', '9007199254740993']]) {
      const result = spawnSync(process.execPath, [cli, ...args], {encoding: 'utf8'});
      assert.equal(result.status, 1);
      assert.equal(JSON.parse(result.stdout).result, 'failed');
    }
  } finally {
    rmSync(directory, {recursive: true, force: true});
  }
});

test('Node package and lock follow the repository version', () => {
  const version = readFileSync(new URL('../../VERSION', import.meta.url), 'utf8').trim();
  assert.equal(readJson(new URL('./package.json', import.meta.url)).version, version);
  const lock = readJson(new URL('./package-lock.json', import.meta.url));
  assert.equal(lock.version, version);
  assert.equal(lock.packages[''].version, version);
  const result = spawnSync(process.execPath, [cli, '--version'], {encoding: 'utf8'});
  assert.equal(result.status, 0);
  assert.equal(result.stdout.trim(), 'obo-node ' + version);
});
