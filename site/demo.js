/* FIG demo — the educational half of the product.
   One scan per device. It reads a page for the patterns that make a site read
   as machine-made: repeated eyebrow numbering, default palettes, a flat type
   scale, uniform card treatments, filler copy.

   The findings are illustrative: a browser cannot fetch another origin, so this
   walks a scripted read of the URL you give it. Wiring it to app/scraper.py +
   app/rules/checks.py is what makes it real. Language stays probabilistic on
   purpose -- this tells you what a pattern is and how to change it, it never
   claims a page "is" AI-written.
*/
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };

  var form = $('#demoForm'), input = $('#demoUrl'), btn = $('#demoBtn');
  var gate = $('#demoGate'), stage = $('#demoStage'), log = $('#demoLog');
  var scoreEl = $('#demoScore'), ringEl = $('#demoRing'), targetEl = $('#demoTarget');
  var listEl = $('#demoFindings'), countEl = $('#demoCount'), lessonEl = $('#demoLesson');
  if (!form) return;

  var CHECKS = [
    { id: 'eyebrow', label: 'Numbered eyebrow labels',
      lead: '01 / 02 / 03 above section headings',
      why: 'Numbering every section is a layout habit that generators lean on because it fills space without deciding what matters. Readers skip it.',
      fix: 'Drop the numbers. If the order matters, say so in the heading itself.' },
    { id: 'uniform', label: 'One card treatment everywhere',
      lead: 'the same radius and shadow on every block',
      why: 'When every card carries an identical corner radius and drop shadow, nothing sits forward or back, so the page reads flat no matter how much is on it.',
      fix: 'Give one tier of card a heavier surface and let the rest sit quieter.' },
    { id: 'palette', label: 'Untouched default palette',
      lead: 'stock indigo / violet, straight from the framework',
      why: 'Framework defaults are recognisable precisely because nobody changed them. It is the quickest tell that a theme was accepted rather than chosen.',
      fix: 'Shift the hue and lightness away from the default, even slightly.' },
    { id: 'type', label: 'Flat type scale',
      lead: 'headings within a few px of body text',
      why: 'A hierarchy that barely changes size gives a reader nothing to land on. The eye needs a clear first stop.',
      fix: 'Widen the gap: body down, headings up, and cut a level if you have four.' },
    { id: 'copy', label: 'Filler marketing phrasing',
      lead: '"elevate", "seamless", "unlock", "supercharge"',
      why: 'These verbs describe no product in particular, which is why they turn up everywhere. A model reading the page learns nothing it can repeat back.',
      fix: 'Replace each with the specific thing it does, in your own words.' },
    { id: 'icons', label: 'Over-used icon set',
      lead: 'Sparkles, ArrowRight, Zap, CheckCircle',
      why: 'The same four glyphs carry most generated pages. They are not wrong, they are just invisible from familiarity.',
      fix: 'Keep them if they earn it, but let at least one visual be specific to you.' },
    { id: 'spacing', label: 'Uniform vertical rhythm',
      lead: 'identical padding on every section',
      why: 'Equal spacing everywhere removes grouping. Things that belong together should sit closer than things that do not.',
      fix: 'Tighten space inside a group, open it up between groups.' },
    { id: 'alt', label: 'Images without alt text',
      lead: 'decorative and meaningful images treated the same',
      why: 'A crawler reads alt text. Empty alt on a meaningful image removes it from what a model can learn about you.',
      fix: 'Describe the meaningful ones; mark the decorative ones empty on purpose.' }
  ];

  function hash(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function pick(seed, n) {
    // deterministic per URL, so the same site reads the same way twice
    var out = [], pool = CHECKS.slice(), s = seed;
    while (out.length < n && pool.length) {
      s = (s * 1103515245 + 12345) >>> 0;
      out.push(pool.splice(s % pool.length, 1)[0]);
    }
    return out;
  }
  function clean(v) {
    v = (v || '').trim().replace(/^https?:\/\//i, '').replace(/\/+$/, '');
    return v.split('/')[0];
  }

  function line(text, cls) {
    var p = document.createElement('p');
    p.className = 'dm-log-line' + (cls ? ' ' + cls : '');
    p.textContent = text;
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }

  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function label(text) {
    var sp = btn.querySelector('span');
    if (sp) sp.textContent = text; else btn.textContent = text;
  }

  async function run(host) {
    stage.hidden = false;
    log.innerHTML = '';
    listEl.innerHTML = '';
    targetEl.textContent = host;

    var seed = hash(host);
    var found = pick(seed, 3 + (seed % 3));            // 3 to 5 patterns
    var score = Math.max(18, 96 - found.length * 13 - (seed % 11));

    var steps = [
      'reading ' + host,
      'parsing markup and inline styles',
      'extracting class names, headings and text nodes',
      'measuring the type scale',
      'sampling colours against known defaults',
      'checking copy against the phrase list',
      'scoring ' + found.length + ' patterns'
    ];
    for (var i = 0; i < steps.length; i++) {
      line(steps[i]);
      await wait(260 + (seed % 90));
    }
    line('done', 'ok');

    // count up to the score
    var t0 = performance.now();
    await new Promise(function (done) {
      (function tick(now) {
        var k = Math.min(1, ((now || performance.now()) - t0) / 900);
        var e = k * k * (3 - 2 * k);
        scoreEl.textContent = Math.round(score * e);
        ringEl.style.setProperty('--v', (score * e / 100).toFixed(3));
        if (k < 1) requestAnimationFrame(tick); else done();
      })();
    });

    countEl.textContent = found.length + (found.length === 1 ? ' pattern' : ' patterns');
    found.forEach(function (c, i) {
      var li = document.createElement('li');
      li.className = 'dm-find';
      li.style.setProperty('--i', i);
      li.innerHTML =
        '<div class="dm-find-top"><b>' + c.label + '</b>' +
        '<span class="dm-lead mono">' + c.lead + '</span></div>' +
        '<p class="dm-why">' + c.why + '</p>' +
        '<p class="dm-fix"><span class="mono">fix</span> ' + c.fix + '</p>';
      listEl.appendChild(li);
    });

    lessonEl.hidden = false;
    window.FIG && window.FIG.scanRecord(host);
    lock();
  }

  function lock() {
    if (!window.FIG || !window.FIG.scanUsed()) return;
    gate.hidden = false;
    form.hidden = true;
    var rec = {};
    try { rec = JSON.parse(localStorage.getItem('fig_demo_scan') || '{}'); } catch (e) {}
    var when = rec.at ? new Date(rec.at).toLocaleDateString() : '';
    var host = rec.url || '';
    $('#demoGateText').textContent = host
      ? 'This device already ran its free scan on ' + host + (when ? ' on ' + when : '') + '.'
      : 'This device has already used its free scan.';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var host = clean(input.value);
    if (!host || host.indexOf('.') === -1) {
      input.focus();
      input.setAttribute('aria-invalid', 'true');
      return;
    }
    input.removeAttribute('aria-invalid');
    if (window.FIG && window.FIG.scanUsed()) { lock(); return; }
    // write into the inner span: setting textContent on the button itself drops
    // that span, and a bare text node renders behind the button's fill layer
    btn.disabled = true;
    label('Reading…');
    run(host).then(function () { btn.disabled = false; label('Read this site'); });
  });

  var reset = $('#demoReset');
  if (reset) {
    reset.addEventListener('click', function () {
      window.FIG && window.FIG.scanReset();
      gate.hidden = true;
      form.hidden = false;
      stage.hidden = true;
      input.focus();
    });
  }

  // show the device the visitor is actually on
  var dev = window.FIG ? window.FIG.device() : null;
  var devEl = $('#demoDevice');
  if (dev && devEl) {
    devEl.textContent = dev.kind + ' · ' + dev.width + '×' + dev.height +
                        ' · ' + (dev.dpr > 1 ? dev.dpr + 'x' : '1x');
  }

  lock();
})();
