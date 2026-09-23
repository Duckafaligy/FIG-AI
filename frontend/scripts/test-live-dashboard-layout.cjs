const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
function load(file, imports = {}) {
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'), {
    compilerOptions: { jsx: ts.JsxEmit.ReactJSX, module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  }).outputText;
  const exports = {};
  vm.runInNewContext(code, { exports, require: name => imports[name] ?? require(name) });
  return exports;
}
const { dashboardPages } = load('lib/dashboard-pages.ts');
const { LiveDashboardPage } = load('components/live-dashboard-page.tsx', {
  '@/lib/dashboard-pages': { dashboardPages },
  '@/lib/live': { applyOverlay: page => ({ ...page, metrics: [], sections: page.sections.map(section => ({ ...section, rows: [], stats: [], score: undefined })) }) },
  './dashboard-shell': { useDashboardSearch: () => '', MetricCard: () => null, LiveTrendChart: () => null },
  './service-unavailable': { ServiceUnavailable: () => null },
});
const css = fs.readFileSync(path.join(__dirname, '../app/dashboard-redesign.css'), 'utf8');
let count = 0;
for (const [page, data] of Object.entries(dashboardPages)) {
  const html = renderToStaticMarkup(React.createElement(LiveDashboardPage, { page, overlay: { projectName: 'Layout test' } }));
  assert.ok(html.includes(`dashboard-grid--${data.layout}`));
  for (const section of data.sections) {
    assert.ok(section.area, `${page}: missing area for ${section.title}`);
    assert.ok(html.includes(`dashboard-panel--${section.area}`), `${page}: renderer lost ${section.area}`);
    assert.ok(css.includes(`.dashboard-panel--${section.area}`), `${page}: missing CSS area`);
    if (section.span) assert.ok(html.includes(section.span === 'wide' ? 'dashboard-panel--wide' : `dashboard-panel--span-${section.span}`));
    count++;
  }
}
console.log(`PASS: ${count} panel layout assignments across ${Object.keys(dashboardPages).length} dashboard pages.`);
