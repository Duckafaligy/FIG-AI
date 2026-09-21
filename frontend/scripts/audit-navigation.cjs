const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const root = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '..');
function files(dir) { return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? files(path.join(dir, e.name)) : [path.join(dir, e.name)]); }
const sources = [...files(path.join(root, 'app')), ...files(path.join(root, 'components'))].filter(f => f.endsWith('.tsx'));
const routes = new Set(sources.filter(f => /[\\/]page.tsx$/.test(f)).map(f => '/' + path.relative(path.join(root, 'app'), path.dirname(f)).split(path.sep).join('/')));
let issues = 0;
for (const file of sources) {
  const source = ts.createSourceFile(file, fs.readFileSync(file, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  function report(node, text) { issues++; console.log(`${path.relative(root, file)}:${source.getLineAndCharacterOfPosition(node.pos).line + 1}: ${text}`); }
  function visit(node) {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const tag = node.tagName.getText(source);
      const attrs = Object.fromEntries(node.attributes.properties.filter(ts.isJsxAttribute).map(a => [a.name.getText(source), a.initializer]));
      if (attrs.href && ts.isStringLiteral(attrs.href)) {
        const href = attrs.href.text;
        if (!href || href === '#') report(node, 'Empty link destination');
        const route = href.split(/[?#]/)[0];
        if (route.startsWith('/') && !routes.has(route)) report(node, `Unknown route: ${route}`);
      }
      if (tag === 'button' && !('onClick' in attrs) && !('onPointerDown' in attrs) && !('disabled' in attrs) && !(attrs.type && ts.isStringLiteral(attrs.type) && attrs.type.text === 'submit')) report(node, 'Button needs review: no click handler or explicit submit');
      if (tag === 'select' && !('onChange' in attrs) && !('name' in attrs) && !('disabled' in attrs)) report(node, 'Select needs review: no change handler or form field name');
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
}
console.log(`Audited ${sources.length} source files and ${routes.size} page routes; ${issues} findings.`);
process.exitCode = issues ? 1 : 0;
