/* FIG demo — the free read.

   This calls the real API. It queues a crawl of the URL you give it, polls
   until it lands, and renders what the rules engine actually found: four
   layer scores and every finding with its why and its fix.

   Language stays probabilistic on purpose. This tells you what a pattern is
   and how to change it; it never claims a page "is" AI-written.
*/
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };

  var form = $('#demoForm'), input = $('#demoUrl'), btn = $('#demoBtn');
  var share = $('#demoShare');
  var gate = $('#demoGate'), stage = $('#demoStage'), log = $('#demoLog');
  var scoreEl = $('#demoScore'), ringEl = $('#demoRing'), targetEl = $('#demoTarget');
  var listEl = $('#demoFindings'), countEl = $('#demoCount'), lessonEl = $('#demoLesson');
  var layersEl = $('#demoLayers');
  if (!form) return;

  var LAYERS = [
    ['craft', 'Craft', 'how it reads'],
    ['structure', 'Structure', 'what sits where'],
    ['search', 'Search', 'what a crawler reaches'],
    ['answers', 'Answers', 'what a model can quote']
  ];

  var POLL_MS = 1800;
  var POLL_LIMIT = 90;          // ~2.7 minutes before we give up on a read

  function line(text, cls) {
    var p = document.createElement('p');
    p.className = 'dm-log-line' + (cls ? ' ' + cls : '');
    p.textContent = text;
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }

  function label(text) {
    var sp = btn.querySelector('span');
    if (sp) sp.textContent = text; else btn.textContent = text;
  }

  function clean(v) {
    v = (v || '').trim().replace(/^https?:\/\//i, '').replace(/\/+$/, '');
    return v.split('/')[0];
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  /* count the ring up to the real score rather than snapping to it */
  function countUp(target) {
    return new Promise(function (done) {
      var t0 = performance.now();
      (function tick(now) {
        var k = Math.min(1, ((now || performance.now()) - t0) / 900);
        var e = k * k * (3 - 2 * k);
        scoreEl.textContent = Math.round(target * e);
        ringEl.style.setProperty('--v', (target * e / 100).toFixed(3));
        if (k < 1) requestAnimationFrame(tick); else done();
      })();
    });
  }

  function renderLayers(layers) {
    if (!layersEl) return;
    layersEl.innerHTML = LAYERS.map(function (l) {
      var v = layers && layers[l[0]] != null ? layers[l[0]] : 0;
      return '<div class="dm-bar">' +
        '<div class="dm-bar-t"><span>' + l[1] + '</span><b>' + v + '</b></div>' +
        '<div class="dm-bar-track"><div class="dm-bar-fill" style="width:' + v + '%"></div></div>' +
        '<div class="dm-bar-s">' + l[2] + '</div>' +
      '</div>';
    }).join('');
  }

  function renderFindings(findings) {
    listEl.innerHTML = '';
    var order = { high: 0, medium: 1, low: 2, info: 3 };
    findings.slice().sort(function (a, b) {
      return (order[a.severity] || 9) - (order[b.severity] || 9);
    }).forEach(function (f, i) {
      var li = document.createElement('li');
      li.className = 'dm-find';
      li.style.setProperty('--i', Math.min(i, 12));
      var ev = (f.evidence || []).slice(0, 5).map(function (e) {
        return '<li>' + esc(e) + '</li>';
      }).join('');
      li.innerHTML =
        '<div class="dm-find-top">' +
          '<b>' + esc((f.check || '').replace(/_/g, ' ')) + '</b>' +
          '<span class="dm-lead mono">' + esc(f.layer_label || f.layer) +
            ' &middot; ' + esc(f.severity) + '</span>' +
        '</div>' +
        '<p class="dm-why">' + esc(f.summary) + '</p>' +
        (f.why ? '<p class="dm-why">' + esc(f.why) + '</p>' : '') +
        (ev ? '<ul class="dm-ev">' + ev + '</ul>' : '') +
        (f.page ? '<p class="dm-where mono">' + esc(f.page) + '</p>' : '') +
        (f.fix ? '<p class="dm-fix"><span class="mono">fix</span> ' + esc(f.fix) + '</p>' : '');
      listEl.appendChild(li);
    });
  }

  function fail(message) {
    line(message, 'bad');
    countEl.textContent = 'could not read this site';
    listEl.innerHTML = '<li class="dm-find"><p class="dm-why">' + esc(message) + '</p>' +
      '<p class="dm-fix"><span class="mono">why</span> Common causes: the site ' +
      'asks crawlers not to read it in robots.txt, it was unreachable, or it ' +
      'renders entirely in the browser with no HTML for a crawler to see.</p></li>';
  }

  async function run(host) {
    stage.hidden = false;
    log.innerHTML = '';
    listEl.innerHTML = '';
    lessonEl.hidden = true;
    targetEl.textContent = host;
    countEl.textContent = 'reading…';
    scoreEl.textContent = '0';
    ringEl.style.setProperty('--v', 0);
    renderLayers(null);

    line('queueing a read of ' + host);

    var start;
    try {
      var res = await fetch(FIG_API + '/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: host,
          device_id: window.FIG ? window.FIG.id() : null,
          share: !!(share && share.checked)
        })
      });
      start = await res.json().catch(function () { return {}; });
      if (res.status === 429) { gateOut(start.detail || 'Free read limit reached.'); return; }
      if (!res.ok) { fail(start.detail || 'The read could not be started.'); return; }
    } catch (e) {
      fail('Could not reach the FIG API. If you are running this locally, ' +
           'start the backend with: uvicorn app.main:app');
      return;
    }

    line('queued · ' + start.scan_id.slice(0, 8));
    line('fetching robots.txt and looking for a sitemap');

    var said = {};
    var result = null;
    for (var i = 0; i < POLL_LIMIT; i++) {
      await wait(POLL_MS);
      var r;
      try {
        r = await (await fetch(FIG_API + '/scan/' + start.scan_id)).json();
      } catch (e) { continue; }

      if (r.status === 'running' && !said.running) {
        said.running = true;
        line('reading pages, one request at a time');
      }
      if (r.status === 'failed') { fail(r.error || 'The read failed.'); return; }
      if (r.status === 'done') { result = r; break; }
    }

    if (!result) { fail('The read is taking longer than expected. Try again shortly.'); return; }

    line('read ' + result.pages + ' page' + (result.pages === 1 ? '' : 's'));
    line('scoring across four layers');
    line('done', 'ok');

    await countUp(result.score || 0);
    renderLayers(result.layers);

    var n = (result.findings || []).length;
    countEl.textContent = n + (n === 1 ? ' finding' : ' findings') +
                          ' · ' + (result.verdict || '');
    renderFindings(result.findings || []);
    lessonEl.hidden = false;
  }

  function gateOut(message) {
    gate.hidden = false;
    form.hidden = true;
    var t = $('#demoGateText');
    if (t) t.textContent = message;
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
    // write into the inner span: setting textContent on the button itself drops
    // that span, and a bare text node renders behind the button's fill layer
    btn.disabled = true;
    label('Reading…');
    run(host).then(function () {
      btn.disabled = false;
      label('Read this site');
    });
  });

  var reset = $('#demoReset');
  if (reset) {
    reset.addEventListener('click', function () {
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
})();
