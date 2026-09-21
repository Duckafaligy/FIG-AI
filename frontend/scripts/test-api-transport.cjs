const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

async function main() {
  const source = fs.readFileSync(path.join(__dirname, '../lib/api.ts'), 'utf8');
  const code = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
  let captured;
  let response = new Response('{"ok":true}');
  const exports = {};
  vm.runInNewContext(code, {
    exports, require, AbortSignal, console,
    process: { env: { NODE_ENV: 'production', NEXT_PUBLIC_API_URL: 'https://wrong-origin.example' } },
    fetch: async (url, init) => { captured = { url, init }; return response; },
  });
  assert.equal(exports.apiUrl('/api/me'), '/api/me');
  assert.equal((await exports.apiClient('/api/me', { cache: 'force-cache' })).ok, true);
  assert.equal(captured.init.cache, 'no-store');
  assert.equal(captured.init.credentials, 'include');
  response = new Response('{"detail":"sign in required"}', { status: 401 });
  const denied = await exports.apiClient('/api/content');
  assert.equal(denied.status, 401);
  assert.equal(denied.error, 'sign in required');
  response = new Response('<html>gateway error</html>');
  assert.equal((await exports.apiClient('/api/me')).ok, false);

  const config = (await import('../next.config.mjs')).default;
  process.env.VERCEL = '1';
  delete process.env.FIG_BACKEND_URL;
  delete process.env.NEXT_PUBLIC_DEMO_MODE;
  await assert.rejects(config.rewrites(), /required/);
  process.env.FIG_BACKEND_URL = 'https://backend.example/';
  const rules = await config.rewrites();
  assert.equal(rules[0].destination, 'https://backend.example/api/:path*');
  assert.equal(rules.length, 4);
  process.env.FIG_BACKEND_URL = 'https://backend.example/wrong-path';
  await assert.rejects(config.rewrites(), /origin/);
  console.log('API transport checks passed: same-origin auth, no cache, error handling, deployment configuration.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
