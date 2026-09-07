/* ==========================================================
   FIG — landing page interactions
   ========================================================== */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var LOCKED_DOMAIN = 'launchvault.ca';
  var docked = false;   // set by the URL-bar dock, read by the typewriter
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  /* ---------- reveal on scroll (defaults to visible) ---------- */
  document.documentElement.classList.add('js-on');
  (function reveals() {
    var els = $$('.reveal');
    var root = document.documentElement;
    var off = false;
    function showAll() {
      if (off) return;
      off = true;
      root.classList.add('reveal-off');
    }

    if (!('IntersectionObserver' in window) || reduced) { showAll(); return; }

    // Every element gets its own guard: once it is told to reveal, it has
    // one transition-length to actually paint. If it has not, the whole
    // effect is dropped. A single page-load timer would not cover elements
    // that enter view later, on a slow or throttled device.
    function guard(el) {
      setTimeout(function () {
        if (off) return;
        if (parseFloat(getComputedStyle(el).opacity) < 0.9) showAll();
      }, 1400);
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add('in');
        io.unobserve(e.target);
        guard(e.target);
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -6% 0px' });

    els.forEach(function (el, i) {
      el.style.transitionDelay = (Math.min(i % 5, 4) * 70) + 'ms';
      io.observe(el);
    });

    // Backstop: if the observer itself never fires (its callbacks depend on
    // the rendering pipeline), nothing above ever runs.
    setTimeout(function () {
      if (off) return;
      var stuck = els.some(function (el) {
        var r = el.getBoundingClientRect();
        return r.top < window.innerHeight && r.bottom > 0 &&
               parseFloat(getComputedStyle(el).opacity) < 0.9;
      });
      if (stuck) showAll();
    }, 4000);
  })();

  /* ---------- nav: closes on scroll down, opens on scroll up or tap ---------- */
  (function nav() {
    var n = $('#nav'); if (!n) return;
    var pill = $('#navPill');
    var TOP = 90;      // always open this close to the top
    var DELTA = 10;    // net px of travel before the state flips (kills jitter)
    var lastY = window.scrollY;

    function open()  { n.classList.remove('shrunk'); }
    function close() { n.classList.add('shrunk'); }

    function tick() {
      var y = window.scrollY;
      if (y <= TOP) { open(); lastY = y; return; }
      var d = y - lastY;
      if (Math.abs(d) < DELTA) return;   // too small to count; hold current state
      if (d > 0) close(); else open();
      lastY = y;
    }

    if (pill) {
      pill.addEventListener('click', function (e) {
        if (!n.classList.contains('shrunk')) return;   // already open, act normally
        if (e.target.closest('.btn')) return;          // never swallow the CTA
        e.preventDefault();                            // tap opens instead of jumping
        open();
        lastY = window.scrollY;                        // re-baseline so it stays open
      });
    }

    tick();
    window.addEventListener('scroll', tick, { passive: true });
  })();

  /* ---------- marquee speeds ---------- */
  $$('.marquee').forEach(function (m) {
    var track = $('.marquee-track', m);
    if (!track) return;
    track.innerHTML += track.innerHTML;            // duplicate for seamless loop
    track.style.setProperty('--dur', (m.dataset.speed || 40) + 's');
  });

  /* Palette is fixed (grey/white) now that the switcher is gone. This
     registry is kept so the canvas and 3D core still read their colours
     from the CSS custom properties in one place. */
  var themeListeners = [];
  function onTheme(fn) { themeListeners.push(fn); }

  /* ---------- ember particles ---------- */
  (function embers() {
    var cv = $('#embers'); if (!cv || reduced) return;
    var ctx = cv.getContext('2d');
    var w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    var parts = [], SPRITE = 64, sprites = [];
    var TRAIL_GAP = 7;   // px of tail per trail step, scaled by velocity

    function hexToRgb(hex, fb) {
      hex = (hex || '').replace('#', '');
      if (hex.length === 3) hex = hex.split('').map(function (c) { return c + c; }).join('');
      var n = parseInt(hex, 16);
      return isNaN(n) ? fb : [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }
    function mix(a, b, t) {
      return [Math.round(a[0] + (b[0] - a[0]) * t),
              Math.round(a[1] + (b[1] - a[1]) * t),
              Math.round(a[2] + (b[2] - a[2]) * t)];
    }

    /* Pre-render one glow sprite per temperature step. Drawing a cached
       bitmap is far cheaper than building a radial gradient per particle
       per frame, which is what buys us the higher particle count. */
    function buildSprites(accent, accent2) {
      var hot = [255, 247, 235];
      var c2 = hexToRgb(accent2, [255, 179, 71]);
      var c1 = hexToRgb(accent, [242, 107, 42]);
      var cold = mix(c1, [74, 12, 6], 0.7);
      sprites = [];
      for (var i = 0; i < 8; i++) {
        var t = i / 7;
        var c = t < 0.34 ? mix(hot, c2, t / 0.34)
              : t < 0.70 ? mix(c2, c1, (t - 0.34) / 0.36)
                         : mix(c1, cold, (t - 0.70) / 0.30);
        var sp = document.createElement('canvas');
        sp.width = sp.height = SPRITE;
        var g = sp.getContext('2d'), r = SPRITE / 2;
        var grd = g.createRadialGradient(r, r, 0, r, r, r);
        var rgb = c[0] + ',' + c[1] + ',' + c[2];
        grd.addColorStop(0.00, 'rgba(255,255,255,' + (0.92 - t * 0.55) + ')');
        grd.addColorStop(0.16, 'rgba(' + rgb + ',0.88)');
        grd.addColorStop(0.42, 'rgba(' + rgb + ',0.26)');
        grd.addColorStop(1.00, 'rgba(' + rgb + ',0)');
        g.fillStyle = grd;
        g.fillRect(0, 0, SPRITE, SPRITE);
        sprites.push(sp);
      }
    }
    buildSprites(cssVar('--accent') || '#F26B2A', cssVar('--accent-2') || '#FFB347');
    onTheme(function (a, b) { buildSprites(a, b); });

    function spawn(anywhere) {
      var spark = Math.random() > 0.93;   // rare bright one, for variety
      var span = 340 + Math.random() * 460;
      return {
        x: Math.random() * w,
        y: anywhere ? Math.random() * h : h + Math.random() * 80,
        size: spark ? 10 + Math.random() * 8 : 3.5 + Math.random() * 5.5,
        vx: (Math.random() - 0.5) * 0.22,
        vy: -(0.26 + Math.random() * 0.72) * (spark ? 1.5 : 1),
        // seed the initial field mid-life so it does not all fade in together
        life: anywhere ? Math.random() * span * 0.75 : 0,
        span: span,
        wob: Math.random() * Math.PI * 2,
        wobSpd: 0.007 + Math.random() * 0.018,
        wobAmp: 0.10 + Math.random() * 0.34,
        flick: Math.random() * Math.PI * 2,
        base: spark ? 0.55 + Math.random() * 0.35 : 0.24 + Math.random() * 0.4,
        // long cinematic tail only on the bright sparks that show it off;
        // the dim majority get a shorter one, which halves the draw calls
        trail: spark ? 7 : 4
      };
    }

    function resize() {
      w = cv.clientWidth; h = cv.clientHeight;
      cv.width = w * dpr; cv.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var cap = w < 700 ? 55 : 140;
      var target = Math.max(24, Math.round(Math.min(cap, (w * h) / 9000)));
      while (parts.length < target) parts.push(spawn(true));
      parts.length = target;
    }

    var running = true;
    document.addEventListener('visibilitychange', function () { running = !document.hidden; });

    function frame() {
      requestAnimationFrame(frame);
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      ctx.globalCompositeOperation = 'lighter';

      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.life++;
        var lt = p.life / p.span;
        if (lt >= 1 || p.y < -70) { parts[i] = spawn(false); continue; }

        p.wob += p.wobSpd;
        p.vx += Math.sin(p.wob) * 0.005;   // turbulence
        p.vx *= 0.99;
        p.vy -= 0.0005;                    // buoyancy: rises faster as it lifts
        p.x += p.vx + Math.sin(p.wob) * p.wobAmp * 0.3;
        p.y += p.vy;

        p.flick += 0.17;
        var flick = 0.7 + 0.3 * Math.sin(p.flick) * Math.sin(p.flick * 2.3);
        var env = lt < 0.10 ? lt / 0.10 : (lt > 0.5 ? 1 - (lt - 0.5) / 0.5 : 1);
        var alpha = p.base * env * flick;
        if (alpha <= 0.004) continue;
        var size = p.size * (1 - lt * 0.42);
        var sprite = sprites[Math.min(7, Math.floor(lt * 8))];  // cools with age

        for (var k = p.trail - 1; k >= 0; k--) {
          var f = k / p.trail;
          var ta = alpha * (1 - f) * (1 - f) * (k === 0 ? 1 : 0.5);
          if (ta <= 0.004) continue;
          var ts = size * (1 - f * 0.55);
          ctx.globalAlpha = ta;
          ctx.drawImage(sprite,
            p.x - p.vx * k * TRAIL_GAP - ts / 2,
            p.y - p.vy * k * TRAIL_GAP - ts / 2, ts, ts);
        }
      }
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';
    }

    resize();
    window.addEventListener('resize', resize);
    frame();
  })();

  /* ---------- hero: typing loop in the URL field ---------- */
  (function typer() {
    var input = $('#urlInput'), bar = $('#urlForm'), btn = $('#scanBtn');
    if (!input || reduced) return;
    var domains = ['northwind.io', 'acmedental.com', 'lumenworks.co', 'kestrel.studio'];
    var idx = 0, userTouched = false;

    ['focus', 'input'].forEach(function (ev) {
      input.addEventListener(ev, function () { userTouched = true; });
    });

    function type(text) {
      return new Promise(function (done) {
        var i = 0;
        (function step() {
          if (userTouched || docked) return done();
          input.value = text.slice(0, ++i);
          if (i < text.length) setTimeout(step, 62 + Math.random() * 55);
          else done();
        })();
      });
    }
    function erase() {
      return new Promise(function (done) {
        (function step() {
          if (userTouched || docked) return done();
          var v = input.value;
          input.value = v.slice(0, -1);
          if (input.value.length) setTimeout(step, 26);
          else done();
        })();
      });
    }
    async function loop() {
      while (!userTouched) {
        // while the bar is docked it shows the one locked domain for the
        // session; the hero resumes cycling when you scroll back up
        if (docked) {
          if (input.value !== LOCKED_DOMAIN) input.value = LOCKED_DOMAIN;
          await sleep(300);
          continue;
        }
        await type(domains[idx % domains.length]);
        if (userTouched) break;
        await sleep(950);
        bar.classList.add('sending');
        if (btn) btn.textContent = 'Scanning...';
        await sleep(1150);
        bar.classList.remove('sending');
        if (btn) btn.textContent = 'Scan free';
        await sleep(320);
        await erase();
        await sleep(420);
        idx++;
      }
      if (btn) btn.textContent = 'Scan free';
      bar.classList.remove('sending');
    }
    setTimeout(loop, 1100);
  })();


  /* ---------- URL bar pins, then flies into the dashboard ---------- */
  (function urlDock() {
    var wrap = $('#urlWrap'), bar = $('#urlForm'), input = $('#urlInput');
    var slot = $('#dockSlot'), sticky = $('.stage-sticky'), stageEl = $('#stage');
    if (!wrap || !bar) return;

    var homeDocTop = 0, homeLeft = 0, homeW = 0, barH = 0, enabled = false;

    function measure() {
      enabled = window.innerWidth > 900;
      bar.classList.remove('pinned');
      bar.style.cssText = '';
      wrap.style.height = '';
      if (!enabled) { bar.classList.remove('docked'); return; }
      // measure the BAR itself, not its wrapper -- the bar is centred inside
      // the wrapper by auto margins, which stop applying once it is fixed
      var r = bar.getBoundingClientRect();
      homeDocTop = r.top + window.scrollY;
      homeLeft = r.left;
      homeW = r.width;
      barH = r.height;
      wrap.style.height = barH + 'px';
      bar.classList.add('pinned');
      update();
    }

    // Where the slot sits once the stage is pinned to the top of the viewport.
    // Measured relative to the sticky container so it is correct even while
    // the stage is still below the fold.
    function target() {
      if (!slot || !sticky) return null;
      var sr = sticky.getBoundingClientRect(), qr = slot.getBoundingClientRect();
      if (!qr.width) return null;
      return { top: qr.top - sr.top, left: qr.left - sr.left, w: qr.width };
    }

    function update() {
      if (!enabled) return;
      var heroH = document.querySelector('.hero').getBoundingClientRect().height || window.innerHeight;
      var p = Math.min(1, Math.max(0, window.scrollY / (heroH * 0.9)));
      var eased = p * p * (3 - 2 * p);

      var t = target();
      var scale = t ? (1 + (t.w / homeW - 1) * eased) : 1 - 0.26 * eased;
      var tgtLeft = t ? t.left : 30;
      var tgtTop = t ? t.top : window.innerHeight - 30 - barH * scale;

      // Derive the home slot from the placeholder every frame. A one-off
      // measurement goes stale the moment the hero text reflows (fonts,
      // resize, wrapping), which is what kept dropping the bar onto the
      // subhead.
      var wr = wrap.getBoundingClientRect();
      if (wr.width) {
        homeW = Math.min(560, wr.width);
        homeLeft = wr.left + (wr.width - homeW) / 2;
        homeDocTop = wr.top + window.scrollY;
      }

      var homeTopV = homeDocTop - window.scrollY;
      bar.style.width = homeW + 'px';
      bar.style.left = (homeLeft + (tgtLeft - homeLeft) * eased) + 'px';
      bar.style.top = (homeTopV + (tgtTop - homeTopV) * eased) + 'px';
      bar.style.transformOrigin = 'left top';
      bar.style.transform = 'scale(' + scale.toFixed(4) + ')';
      document.documentElement.style.setProperty('--sp', eased.toFixed(4));

      // the bar only lives between the hero and the dashboard: it fades out
      // with the stage and stops accepting clicks once it is gone. Computed
      // here rather than read from the stage module, so it can never lag a
      // frame behind depending on listener order.
      var vis = 1;
      if (stageEl) {
        var sTotal = stageEl.offsetHeight - window.innerHeight;
        if (sTotal > 0) {
          var sp = Math.min(1, Math.max(0, -stageEl.getBoundingClientRect().top / sTotal));
          if (sp > 0.78) { var v = Math.max(0, 1 - (sp - 0.78) / 0.22); vis = v * v * (3 - 2 * v); }
        }
      }
      bar.style.setProperty('--bar-o', vis.toFixed(3));
      bar.setAttribute('data-gone', vis < 0.02 ? '1' : '0');

      var nowDocked = p > 0.6;
      if (nowDocked !== docked) {
        docked = nowDocked;
        bar.classList.toggle('docked', docked);
        if (docked) {
          if (input) input.value = LOCKED_DOMAIN;
        } else if (input) {
          // hand back to the typewriter from empty so it does not jump
          input.value = '';
        }
      }
    }

    // A resize reflows the hero text, and reading the slot mid-reflow gives
    // a stale position -- settle on the next frame (and once more after).
    function settle() {
      measure();
      requestAnimationFrame(update);
      setTimeout(update, 120);
    }

    measure();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', settle);

    // The hero text also reflows when the web fonts land.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(settle);
    window.addEventListener('load', settle);
    setTimeout(settle, 1200);
  })();

  /* ---------- hero: parallax on floating cards ---------- */
  (function parallax() {
    var host = $('#heroCards'); if (!host || reduced) return;
    var cards = $$('.fcard', host);
    cards.forEach(function (c, i) {
      c.style.setProperty('--dur', (11 + (i % 5) * 1.8) + 's');
      c.style.setProperty('--dly', (i * 0.55) + 's');
    });
    var tx = 0, ty = 0, cx = 0, cy = 0, active = false;
    window.addEventListener('mousemove', function (e) {
      tx = (e.clientX / window.innerWidth - 0.5) * 2;
      ty = (e.clientY / window.innerHeight - 0.5) * 2;
      if (!active) { active = true; raf(); }
    }, { passive: true });
    function raf() {
      cx += (tx - cx) * 0.055; cy += (ty - cy) * 0.055;
      cards.forEach(function (c) {
        var d = parseFloat(c.dataset.depth || 20) / 10;
        c.style.setProperty('--px', (-cx * d * 6).toFixed(2) + 'px');
        c.style.setProperty('--py', (-cy * d * 6).toFixed(2) + 'px');
      });
      requestAnimationFrame(raf);
    }
  })();


  /* ---------- curved brand arc ---------- */
  (function arcBand() {
    var band = $('#arcBand'); if (!band) return;
    var track = $('#arcTrack', band);
    var items = $$('.arc-item', track);
    if (!items.length || !track) return;

    var LIMIT = 18;                 // shallower arc: same per-item spacing
                                    // (that is set by band width) but ~90px less rise,
                                    // so it stays inside its band and clear of the widgets
    var SPAN = LIMIT * 2;
    var SPEED = 2.1;                // degrees per second (slow drift)
    var R = 0, cx = 0, cy = 0, W = 0, H = 0;
    var active = items.slice();   // items CSS has not hidden at this width
    var step = SPAN / active.length;

    function refreshActive() {
      active = items.filter(function (el) { return el.offsetParent !== null; });
      if (!active.length) active = items.slice();
      step = SPAN / active.length;
    }

    function measure() {
      refreshActive();
      W = band.clientWidth; H = band.clientHeight;
      if (!W || !H) return false;
      R = (W / 2) / Math.sin(LIMIT * Math.PI / 180);  // ends land at the band edges
      cx = W / 2;
      cy = H - 44 - R;                                // low point, clear of the label
      return true;
    }

    function layout(t) {
      if (!R) return;
      for (var i = 0; i < active.length; i++) {
        var a = -LIMIT + (((i * step + t) % SPAN) + SPAN) % SPAN;
        var rad = a * Math.PI / 180;
        var edge = 1 - Math.min(1, Math.abs(a) / LIMIT);
        var el = active[i];
        el.style.left = (cx + R * Math.sin(rad)).toFixed(1) + 'px';
        el.style.top = (cy + R * Math.cos(rad)).toFixed(1) + 'px';
        el.style.transform = 'translate(-50%,-50%) rotate(' + (-a).toFixed(2) + 'deg)';
        el.style.opacity = (Math.min(1, edge / 0.26)).toFixed(3);
      }
    }

    // Lay the arc out synchronously BEFORE switching the items to absolute
    // positioning, so a tab that never gets a rAF frame still shows a
    // correct (static) arc rather than a pile at the origin.
    var t = 0;
    if (!measure()) return;
    layout(0);
    band.classList.add('arc-on');

    window.addEventListener('resize', function () { if (measure()) layout(t); });

    if (reduced) return;            // static arc is the whole story

    var visible = true;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) { visible = e.isIntersecting; });
      }, { threshold: 0 }).observe(band);
    }

    // Hovering anywhere over the strip's band holds it still. Done by
    // hit-testing the cursor against the band's box rather than giving the
    // band pointer-events, so it can never swallow a click meant for the
    // URL field sitting behind it. The links themselves keep their own
    // pointer-events so they stay clickable.
    var paused = false, rect = null;
    function refreshRect() {
      var r = band.getBoundingClientRect();
      // items sit ON the curve, so their boxes extend above the band's own
      // top edge at the arc ends -- pad the hit region so hovering those
      // still holds the strip
      rect = { left: r.left, right: r.right, top: r.top - 34, bottom: r.bottom };
    }
    refreshRect();
    window.addEventListener('resize', refreshRect);
    window.addEventListener('scroll', refreshRect, { passive: true });

    function setPaused(v) {
      if (v === paused) return;
      paused = v;
      band.classList.toggle('paused', v);
    }
    window.addEventListener('mousemove', function (e) {
      if (!rect) return;
      setPaused(e.clientX >= rect.left && e.clientX <= rect.right &&
                e.clientY >= rect.top && e.clientY <= rect.bottom);
    }, { passive: true });
    document.addEventListener('mouseleave', function () { setPaused(false); });
    // keyboard users tabbing through the links get the same hold
    items.forEach(function (el) {
      el.addEventListener('focus', function () { setPaused(true); });
      el.addEventListener('blur', function () { setPaused(false); });
    });

    var last = performance.now();
    function frame(now) {
      requestAnimationFrame(frame);
      var dt = Math.min(0.05, (now - last) / 1000); last = now;
      if (!visible || document.hidden || !R) return;
      if (!paused) { t += dt * SPEED; layout(t); }
    }
    requestAnimationFrame(frame);
  })();


  /* ---------- hero live-checks ticker ---------- */
  (function ticker() {
    var box = $('#ticker'); if (!box || reduced) return;
    var FEED = [
      ['#4285F4','G','pricing','wrong','bad'],
      ['#D97757','C','hours','correct','ok'],
      ['#10A37F','G','refunds','vague','warn'],
      ['#20808D','P','shipping','correct','ok'],
      ['#10A37F','G','HIPAA','wrong','bad'],
      ['#4285F4','G','founders','vague','warn'],
      ['#D97757','C','insurance','correct','ok'],
      ['#20808D','P','pricing','wrong','bad']
    ];
    var i = 3;
    setInterval(function () {
      if (document.hidden) return;
      var rows = $$('.tk', box);
      if (!rows.length) return;
      var first = rows[0];
      first.classList.add('out');
      setTimeout(function () {
        first.remove();
        var f = FEED[i++ % FEED.length];
        var d = document.createElement('div');
        d.className = 'tk';
        d.innerHTML = '<span class="mono-sq xs" style="--m:' + f[0] + '">' + f[1] + '</span>' +
                      '<span class="tk-t mono">' + f[2] + '</span>' +
                      '<span class="tk-v ' + f[4] + '">' + f[3] + '</span>';
        box.appendChild(d);
      }, 340);
    }, 2600);
  })();

  /* ---------- form submit (demo) ---------- */
  $$('#urlForm, #urlForm2').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var b = $('.urlbar-btn', f);
      if (!b) return;
      var old = b.textContent;
      b.textContent = 'Queued';
      setTimeout(function () { b.textContent = old; }, 1700);
    });
  });

  /* ---------- count-up stats ---------- */
  (function stats() {
    var band = $('#stats'); if (!band) return;
    var nums = $$('.stat-num', band), done = false;
    function run() {
      if (done) return; done = true;
      nums.forEach(function (el) {
        var to = parseFloat(el.dataset.to || '0');
        var pre = el.dataset.prefix || '', suf = el.dataset.suffix || '';
        if (reduced) { el.textContent = pre + to + suf; return; }
        var t0 = performance.now(), dur = 1500;
        (function step(now) {
          var p = Math.min(1, (now - t0) / dur);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = pre + Math.round(to * eased) + suf;
          if (p < 1) requestAnimationFrame(step);
        })(t0);
      });
    }
    if (!('IntersectionObserver' in window)) return run();
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { run(); io.disconnect(); } });
    }, { threshold: 0.35 });
    io.observe(band);
  })();

  /* ---------- steps advance while the section is pinned ---------- */
  (function steps() {
    var list = $('#steps'), sec = list && list.closest('.why-sec');
    if (!list || !sec) return;
    var items = $$('.step', list);
    if (!items.length) return;

    function update() {
      var total = sec.offsetHeight - window.innerHeight;
      var p = total > 0
        ? Math.min(1, Math.max(0, -sec.getBoundingClientRect().top / total))
        : 0;
      // hold on the last step for the tail of the section
      var i = Math.min(items.length - 1, Math.floor(p / 0.88 * items.length));
      items.forEach(function (el, n) { el.classList.toggle('on', n === i); });
    }
    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
  })();

  /* ==========================================================
     LIVE AUDIT
     ========================================================== */
  var LAYERS = [
    { name: 'Craft',     sub: 'how it reads',    key: 'C' },
    { name: 'Structure', sub: 'section order',   key: 'S' },
    { name: 'Search',    sub: 'what crawlers get', key: 'E' },
    { name: 'Answers',   sub: 'what models say',  key: 'A' }
  ];

  // NOTE: placeholder audit content for launchvault.ca -- swap these
  // questions, truths and findings for the real ones before shipping.
  var LV = { domain: 'launchvault.ca', org: 'LaunchVault', questions: [] };
  var SITES = [LV];

  LV.questions.push({
    q: '/ &mdash; home',
    truth: 'read for 4 layers',
    answers: [
      { t: '01 / 02 / 03 eyebrows on 6 sections; h2 30px against 28px body', v: 'wrong', finding: {
        sev: 'critical', src: 'Craft &middot; home',
        exp: 'Two of the strongest generated-layout tells on one page. Numbering every section fills space without deciding what matters, and a type scale this flat gives a reader nothing to land on first.',
        fix: 'Drop the numbers. Take body to 15px and h2 to 30px so the hierarchy actually steps.' } },
      { t: 'CTA at 2, pricing at 3, what-we-do at 4', v: 'wrong', finding: {
        sev: 'critical', src: 'Structure &middot; home',
        exp: 'You ask for the sale before you say what the product is. A visitor hits a price with nothing to weigh it against, so the number reads as expensive by default.',
        fix: 'Move <span class="mono">What we do</span> above <span class="mono">Pricing</span> and push the CTA below proof.' } },
      { t: 'No meta description; h1 repeated in the hero and the nav', v: 'vague', finding: {
        sev: 'warning', src: 'Search &middot; home',
        exp: 'Google writes its own snippet when you leave the description empty, and two h1s means neither is the page subject.',
        fix: 'One h1. Write a 150-character description that names the product and the outcome.' } },
      { t: 'ChatGPT quotes $39/mo against an actual $20/mo', v: 'wrong', finding: {
        sev: 'critical', src: 'Answers &middot; home',
        exp: 'The price only exists inside a widget, so there is nothing quotable on the page. The model fills the gap with a category average and is wrong by nearly double.',
        fix: 'State the figure once in plain body text, above the fold.' } }
    ],
    report: { score: 41, critical: 3, warning: 1, correct: 0, cats: [22, 34, 58, 40] },
    sources: [['6 slop tells',57,'bad'],['section order',41,'warn'],['no description',15,'dim']],
    fixes: ['Drop the eyebrow numbers', 'Reorder home sections', 'Write a meta description']
  });

  LV.questions.push({
    q: '/pricing',
    truth: 'read for 4 layers',
    answers: [
      { t: 'Palette and spacing are chosen, not framework defaults', v: 'correct' },
      { t: 'Plans, then comparison, then FAQ &mdash; reads in order', v: 'correct' },
      { t: 'Plan table renders client-side; a crawler sees an empty shell', v: 'wrong', finding: {
        sev: 'critical', src: 'Search &middot; /pricing',
        exp: 'The whole table is built in JavaScript after load. Googlebot and every AI crawler fetch the HTML and find an empty container, so the page indexes as though it has no prices on it at all.',
        fix: 'Server-render the plan table and add Product + Offer schema with <span class="mono">price: 20.00</span>.' } },
      { t: 'Both engines guess the price rather than cite it', v: 'wrong', finding: {
        sev: 'critical', src: 'Answers &middot; /pricing',
        exp: 'A direct consequence of the line above. Nothing on the page is citable, so both models infer from competitors.',
        fix: 'Once the table is server-rendered, re-run and the answers correct themselves.' } }
    ],
    report: { score: 58, critical: 2, warning: 0, correct: 2, cats: [78, 74, 24, 30] },
    sources: [['/pricing (JS)',62,'bad'],['no Offer schema',34,'warn'],['g2 listing',18,'dim']],
    fixes: ['Server-render the plan table', 'Add Offer schema', 'Re-run the answers']
  });

  LV.questions.push({
    q: '/about',
    truth: 'read for 4 layers',
    answers: [
      { t: '&ldquo;elevate&rdquo;, &ldquo;seamless&rdquo;, &ldquo;unlock&rdquo; in three of five paragraphs', v: 'vague', finding: {
        sev: 'warning', src: 'Craft &middot; /about',
        exp: 'Filler verbs describe no company in particular, which is exactly why they turn up everywhere. A model reading this page learns nothing it can repeat back about you.',
        fix: 'Replace each with the specific thing you do, in your own words.' } },
      { t: 'Story, then team, then contact &mdash; reads in order', v: 'correct' },
      { t: 'Founding year appears here only, and not in schema', v: 'vague', finding: {
        sev: 'warning', src: 'Search &middot; /about',
        exp: 'One mention in prose on one page is a thin signal. Anything contradicting it elsewhere on the web will outweigh it.',
        fix: 'Add Organization schema with <span class="mono">foundingDate</span> so the fact is machine-readable.' } },
      { t: 'ChatGPT reports the founding year as 2016, actual 2019', v: 'wrong', finding: {
        sev: 'critical', src: 'Answers &middot; /about',
        exp: 'Traced to a 2022 press release that misprinted the year. It outranks your own about page because it is on a higher-authority domain.',
        fix: 'Publish the correct year in schema, then ask the outlet for a correction.' } }
    ],
    report: { score: 63, critical: 1, warning: 2, correct: 1, cats: [52, 80, 46, 44] },
    sources: [['2022 press release',48,'bad'],['filler phrasing',30,'warn'],['/about',12,'dim']],
    fixes: ['Rewrite the filler paragraphs', 'Add Organization schema', 'Request a correction']
  });

  (function audit() {
    var win = $('#auditWindow'); if (!win) return;
    var elDomain = $('#auditDomain'), elQ = $('#qText'), elTruth = $('#truthText');
    var elModels = $('#models'), elFeed = $('#feed'), elCount = $('#findCount');
    var elStatus = $('#statusText'), pill = $('#statusPill');
    var elSb = $('#sbProgress'), elOrg = $('#orgName'), elBadge = $('#snBadge');
    var elCrumb = $('#crumbDomain');
    var elQq = $('#qqList'), elQqN = $('#qqN'), elSrc = $('#srcList');
    var elFix = $('#fixList'), elFixN = $('#fixCount');
    var elCost = $('#costNum'), elCostQ = $('#costQ'), elCostE = $('#costE');
    var nQ = 0, nE = 0;   // model queries / explanations this run
    var elDial = $('#dialFg'), elNum = $('#dialNum');
    var elC = $('#tCritical'), elW = $('#tWarning'), elOk = $('#tCorrect');
    var bars = $$('#cats .cat-bar i');
    var CIRC = 2 * Math.PI * 52;

    var gen = 0, running = false;

    function status(text, done) {
      if (elStatus) elStatus.textContent = text;
      if (pill) pill.classList.toggle('done', !!done);
    }

    function buildRows() {
      elModels.innerHTML = '';
      LAYERS.forEach(function (m, i) {
        var row = document.createElement('div');
        row.className = 'model-row pending';
        row.dataset.idx = i;
        row.innerHTML =
          '<span class="tell-i mono" aria-hidden="true">' + m.key + '</span>' +
          '<div class="m-main"><div class="m-name">' + m.name +
          ' <span class="m-sub mono">' + m.sub + '</span></div>' +
          '<div class="m-answer mono"></div></div>' +
          '<span class="verdict hidden"></span>';
        elModels.appendChild(row);
      });
    }

    function rowAt(i) { return elModels.children[i]; }

    function think(i) {
      var row = rowAt(i); if (!row) return;
      row.classList.remove('pending'); row.classList.add('active');
      $('.m-answer', row).innerHTML = '<span class="spinner"></span> thinking';
      $('.m-answer', row).classList.add('thinking');
    }

    function answer(i, a) {
      var row = rowAt(i); if (!row) return;
      row.classList.remove('active');
      row.classList.add('v-' + a.v);
      var ans = $('.m-answer', row);
      ans.classList.remove('thinking');
      ans.textContent = a.t;
      var v = $('.verdict', row);
      v.className = 'verdict v-' + a.v;
      v.textContent = a.v === 'correct' ? 'Clean' : (a.v === 'vague' ? 'Check' : 'Fix');
    }

    function addFinding(f) {
      var art = document.createElement('article');
      art.className = 'finding sev-' + f.sev;
      art.innerHTML =
        '<header class="f-head"><span class="sev">' + (f.sev === 'critical' ? 'Critical' : 'Warning') +
        '</span><span class="f-src mono">' + f.src + '</span></header>' +
        '<p class="f-exp">' + f.exp + '</p>' +
        '<p class="f-fix"><span class="fix-label">Fix</span>' + f.fix + '</p>';
      elFeed.insertBefore(art, elFeed.firstChild);
      if (elCount) elCount.textContent = elFeed.children.length;
      if (elBadge) elBadge.textContent = elFeed.children.length;
      while (elFeed.children.length > 7) elFeed.removeChild(elFeed.lastChild);
    }

    function countTo(el, to, ms) {
      if (!el) return;
      var from = parseInt(el.textContent, 10) || 0;
      if (reduced || from === to) { el.textContent = to; return; }
      // token guards against two count-ups racing on the same element
      var token = (el.__ct = (el.__ct || 0) + 1);
      var t0 = performance.now();
      (function step(now) {
        if (el.__ct !== token) return;
        var p = Math.min(1, (now - t0) / ms);
        el.textContent = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      })(t0);
    }

    function report(r) {
      if (elDial) elDial.style.strokeDashoffset = CIRC * (1 - r.score / 100);
      countTo(elNum, r.score, 1000);
      countTo(elC, r.critical, 600);
      countTo(elW, r.warning, 600);
      countTo(elOk, r.correct, 600);
      bars.forEach(function (b, i) {
        if (r.cats[i] != null) b.style.width = r.cats[i] + '%';
      });
    }

    function renderQueue(site, cur) {
      if (!elQq) return;
      elQq.innerHTML = '';
      site.questions.forEach(function (q, i) {
        var d = document.createElement('div');
        d.className = 'qq' + (i === cur ? ' on' : (i < cur ? ' done' : ''));
        d.innerHTML = '<span class="qq-dot"></span><span class="qq-t"></span>';
        // page paths carry real entities (&mdash;), so decode rather than
        // blanket-replace them with an apostrophe
        var tmp = document.createElement('span');
        tmp.innerHTML = q.q;
        $('.qq-t', d).textContent = tmp.textContent;
        elQq.appendChild(d);
      });
      if (elQqN) elQqN.textContent = (cur + 1) + ' / ' + site.questions.length;
    }

    function renderSources(q) {
      if (!elSrc || !q.sources) return;
      elSrc.innerHTML = q.sources.map(function (s) {
        return '<div class="src"><span class="src-n mono">' + s[0] +
               '</span><span class="src-b"><i class="' + s[2] + '" style="width:' + s[1] +
               '%"></i></span><span class="src-v mono">' + s[1] + '</span></div>';
      }).join('');
    }

    function renderFixes(q, done) {
      if (!elFix || !q.fixes) return;
      elFix.innerHTML = q.fixes.map(function (f) {
        return '<div class="fq' + (done ? ' done' : '') + '"><span class="fq-box"></span>' +
               '<span class="fq-t">' + f + '</span></div>';
      }).join('');
      if (elFixN) elFixN.textContent = done ? 'all cleared' : q.fixes.length + ' open';
    }

    function bumpCost() {
      if (elCostQ) elCostQ.textContent = nQ;
      if (elCostE) elCostE.textContent = nE;
      if (elCost) elCost.textContent = '$' + (nQ * 0.0009 + nE * 0.0006).toFixed(3);
    }

    function resetReport() {
      if (elDial) elDial.style.strokeDashoffset = CIRC;
      [elNum, elC, elW, elOk].forEach(function (e) { if (e) e.textContent = '0'; });
      bars.forEach(function (b) { b.style.width = '0%'; });
    }

    async function run() {
      var mine = ++gen;
      var alive = function () { return mine === gen; };
      buildRows();

      while (alive()) {
        for (var s = 0; s < SITES.length; s++) {
          var site = SITES[s];
          if (elDomain) elDomain.textContent = site.domain;
          if (elOrg) elOrg.textContent = site.org;
          if (elCrumb) elCrumb.textContent = site.domain;
          nQ = 0; nE = 0; bumpCost();
          elFeed.innerHTML = '';
          if (elCount) elCount.textContent = '0';
          if (elBadge) elBadge.textContent = '0';
          resetReport();
          await sleep(500); if (!alive()) return;

          for (var qi = 0; qi < site.questions.length; qi++) {
            var q = site.questions[qi];
            status('Reading the page');
            if (elSb) elSb.textContent = 'question ' + (qi + 1) + ' of ' + site.questions.length;
            renderQueue(site, qi);
            renderSources(q);
            renderFixes(q, false);
            if (elQ) elQ.innerHTML = q.q;
            if (elTruth) elTruth.innerHTML = q.truth;
            buildRows();
            await sleep(650); if (!alive()) return;

            for (var i = 0; i < LAYERS.length; i++) {
              think(i);
              await sleep(560 + Math.random() * 420); if (!alive()) return;
              answer(i, q.answers[i]);
              nQ++; bumpCost();
              if (q.answers[i].finding) {
                status('Writing finding');
                await sleep(300); if (!alive()) return;
                addFinding(q.answers[i].finding);
                nE++; bumpCost();
              }
              await sleep(230); if (!alive()) return;
            }

            status('Diffing against source of truth');
            await sleep(520); if (!alive()) return;
            report(q.report);
            renderFixes(q, true);
            status('Report updated', true);
            await sleep(2900); if (!alive()) return;
          }
          await sleep(700); if (!alive()) return;
        }
      }
    }

    function start() { if (running) return; running = true; run(); }
    function stop() { gen++; running = false; }

    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) { e.isIntersecting ? start() : stop(); });
      }, { threshold: 0.12 }).observe(win);
    } else {
      start();
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop();
      else if (win.getBoundingClientRect().top < window.innerHeight) start();
    });
  })();

    /* ---------- "what it catches": horizontal rail driven by scroll ---------- */
  (function rail() {
    var sec = $('#catches'), track = $('#railTrack');
    var dot = $('#railDot'), core = $('#railCore');
    var path = $('#railPath'), svg = $('#railSvg'), count = $('#railCount');
    var view = track && track.parentElement;
    if (!sec || !track || !view) return;

    var cards = $$('.bcard', track);
    if (!cards.length) return;

    var travel = 0, pathLen = 0, step = 0, pad = 0, cardW = 0, lastW = -1;
    var FOCUS = 0.28;            // cards are judged against this fixed point

    function measure() {
      pathLen = path && path.getTotalLength ? path.getTotalLength() : 0;
      if (cards.length > 1) {
        // offsetLeft ignores the track's transform, so these stay correct
        // wherever the rail currently sits
        pad = cards[0].offsetLeft;
        step = cards[1].offsetLeft - cards[0].offsetLeft;
        cardW = cards[0].offsetWidth;
      }
      // Travel is set so the LAST card lands exactly on the focus point at the
      // end of the scroll. Deriving it from scrollWidth instead stopped as soon
      // as the track's right edge met the viewport, which is why the counter
      // used to cap out around 14 / 16.
      var last = pad + (cards.length - 1) * step + cardW / 2;
      travel = Math.max(0, last - view.clientWidth * FOCUS);
    }

    // exact inverse of the focus test below, so a click lands on that card
    function pFor(i) {
      if (!travel) return 0;
      var want = pad + i * step + cardW / 2 - view.clientWidth * FOCUS;
      return Math.min(1, Math.max(0, want / travel));
    }

    function update() {
      if (window.innerWidth <= 900) {
        track.style.transform = '';
        cards.forEach(function (c) {
          c.style.removeProperty('--card-o'); c.style.removeProperty('--card-s');
          c.classList.remove('on');
        });
        return;
      }
      // re-measure when the view resizes; measure() can run before layout
      // settles, which used to leave travel short
      if (view.clientWidth !== lastW) { lastW = view.clientWidth; measure(); }

      var r = sec.getBoundingClientRect();
      var total = sec.offsetHeight - window.innerHeight;
      var p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0;

      track.style.transform = 'translate3d(' + (-p * travel).toFixed(1) + 'px,0,0)';

      if (dot && pathLen && svg) {
        var pt = path.getPointAtLength(p * pathLen);
        var box = svg.getBoundingClientRect();
        dot.style.transform = 'translate(' + (pt.x / 1000 * box.width).toFixed(1) +
                              'px,' + (pt.y / 40 * box.height).toFixed(1) + 'px)';
      }

      var vr = view.getBoundingClientRect();
      var focusX = vr.left + vr.width * FOCUS;
      var best = 0, bestD = Infinity;
      for (var i = 0; i < cards.length; i++) {
        var cr = cards[i].getBoundingClientRect();
        var d = Math.abs((cr.left + cr.width / 2) - focusX);
        if (d < bestD) { bestD = d; best = i; }
      }
      for (var j = 0; j < cards.length; j++) {
        var near = Math.abs(j - best);
        cards[j].style.setProperty('--card-o', j === best ? 1 : (near === 1 ? 0.5 : 0.28));
        cards[j].style.setProperty('--card-s', j === best ? 1 : 0.965);
        cards[j].classList.toggle('on', j === best);
      }
      if (count) count.textContent = (best + 1) + ' / ' + cards.length;
    }

    // ---- the dot: grab it and slide, exactly like a scrollbar thumb
    var dragging = false;

    function railFromX(clientX) {
      var box = svg.getBoundingClientRect();
      if (!box.width) return 0;
      return Math.min(1, Math.max(0, (clientX - box.left) / box.width));
    }
    // html has scroll-behavior:smooth, so a plain scrollTo animates and the
    // rail lags the cursor; force it instant while scrubbing
    function scrubTo(clientX) {
      var total = sec.offsetHeight - window.innerHeight;
      if (total <= 0) return;
      var y = sec.offsetTop + railFromX(clientX) * total;
      try { window.scrollTo({ top: y, left: 0, behavior: 'instant' }); }
      catch (e) { window.scrollTo(0, y); }
    }

    function grab(e) {
      if (window.innerWidth <= 900) return;
      dragging = true;
      dot.classList.add('dragging');
      document.documentElement.classList.add('scrubbing');
      try { dot.setPointerCapture(e.pointerId); } catch (err) {}
      scrubTo(e.clientX);
      e.preventDefault();
    }
    if (dot) dot.addEventListener('pointerdown', grab);
    if (svg) svg.addEventListener('pointerdown', grab);   // grab the track too

    window.addEventListener('pointermove', function (e) {
      if (dragging) { scrubTo(e.clientX); return; }
      if (window.innerWidth <= 900 || !dot || !core) return;
      var b = dot.getBoundingClientRect();
      var near = Math.hypot(e.clientX - b.left, e.clientY - b.top) <= 5.5 * 1.3 + 16;
      core.style.setProperty('--dot-s', near ? 1.3 : 1);
      dot.classList.toggle('near', near);
    }, { passive: true });

    function release() {
      if (!dragging) return;
      dragging = false;
      dot.classList.remove('dragging');
      document.documentElement.classList.remove('scrubbing');
    }
    window.addEventListener('pointerup', release);
    window.addEventListener('pointercancel', release);
    window.addEventListener('blur', release);

    // click a card -- usually the one either side -- to bring it to focus
    var swiped = false;
    cards.forEach(function (card, i) {
      card.style.cursor = 'pointer';
      card.addEventListener('click', function () {
        if (window.innerWidth <= 900 || swiped) return;
        var total = sec.offsetHeight - window.innerHeight;
        if (total <= 0) return;
        measure();
        window.scrollTo({ top: sec.offsetTop + pFor(i) * total, behavior: 'smooth' });
      });
    });

    // and drag the cards themselves, the way you would flick a carousel
    (function () {
      var down = false, startX = 0, startTop = 0;
      view.addEventListener('pointerdown', function (e) {
        if (window.innerWidth <= 900 || e.button) return;
        down = true; swiped = false;
        startX = e.clientX; startTop = window.scrollY;
        try { view.setPointerCapture(e.pointerId); } catch (err) {}
      });
      view.addEventListener('pointermove', function (e) {
        if (!down) return;
        var dx = e.clientX - startX;
        if (!swiped && Math.abs(dx) < 4) return;   // let a real click stay a click
        if (!swiped) { swiped = true; document.documentElement.classList.add('scrubbing'); }
        var total = sec.offsetHeight - window.innerHeight;
        if (total <= 0 || !travel) return;
        var y = startTop - (dx / travel) * total;
        y = Math.max(sec.offsetTop, Math.min(sec.offsetTop + total, y));
        try { window.scrollTo({ top: y, left: 0, behavior: 'instant' }); }
        catch (err) { window.scrollTo(0, y); }
      });
      function end() {
        if (!down) return;
        down = false;
        document.documentElement.classList.remove('scrubbing');
        setTimeout(function () { swiped = false; }, 0);
      }
      view.addEventListener('pointerup', end);
      view.addEventListener('pointercancel', end);
      view.addEventListener('pointerleave', end);
      view.style.cursor = 'grab';
    })();

    measure(); update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', function () { measure(); update(); });
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { measure(); update(); });
    }
    setTimeout(function () { measure(); update(); }, 400);
  })();

  /* ---------- pricing: tiers arrive, branch out, then the table ---------- */
  /* every digit is a 0-9 strip that slides to the one it should show,
     so a value change reads as an odometer rolling rather than a swap */
  function roll(el, str, quick) {
    if (!el) return;
    str = String(str);
    el.classList.add('roll');
    el.classList.toggle('quick', !!quick);
    // the visible digits are ten-deep strips, so the value goes on the label
    el.setAttribute('role', 'img');
    el.setAttribute('aria-label', str);

    // rebuild only when the shape of the value changes ("+82%" vs "+217%")
    var shape = str.replace(/\d/g, '#');
    if (el.__shape !== shape) {
      el.__shape = shape;
      var html = '';
      for (var i = 0; i < str.length; i++) {
        if (str[i] >= '0' && str[i] <= '9') {
          html += '<span class="roll-dig" aria-hidden="true"><span class="roll-strip">' +
                  '<b>0</b><b>1</b><b>2</b><b>3</b><b>4</b>' +
                  '<b>5</b><b>6</b><b>7</b><b>8</b><b>9</b></span></span>';
        } else {
          html += '<span class="roll-ch" aria-hidden="true">' + str[i] + '</span>';
        }
      }
      el.innerHTML = html;
      el.__strips = el.querySelectorAll('.roll-strip');
      // start every strip at 0 so the first render actually travels
      el.__strips.forEach(function (s) { s.style.transform = 'translateY(0)'; });
      void el.offsetWidth;
    }

    var strips = el.__strips || el.querySelectorAll('.roll-strip');
    var d = 0;
    for (var j = 0; j < str.length; j++) {
      var ch = str[j];
      if (ch < '0' || ch > '9') continue;
      var strip = strips[d];
      if (strip) {
        strip.style.transitionDelay = quick ? '0ms' : (d * 55) + 'ms';
        strip.style.transform = 'translateY(-' + (+ch) + 'em)';
      }
      d++;
    }
  }


  /* ---------- dashboard: the sidebar actually switches views ---------- */
  (function dashViews() {
    var nav = $('.side-nav');
    if (!nav) return;
    var items = $$('.sn', nav);
    var views = $$('.dv');
    var crumb = $('.crumb.cur');
    if (!items.length || !views.length) return;

    function show(view, label) {
      views.forEach(function (v) { v.classList.toggle('dv-on', v.dataset.view === view); });
      items.forEach(function (a) { a.classList.toggle('on', a.dataset.view === view); });
      if (crumb) crumb.textContent = label.toLowerCase();
    }

    items.forEach(function (a) {
      var view = a.dataset.view;
      var label = (a.textContent || '').replace(/\d+$/, '').trim();
      if (!view) return;
      a.addEventListener('click', function (e) { e.preventDefault(); show(view, label); });
      a.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(view, label); }
      });
    });
  })();

  /* ---------- pricing: values pop in, then the card rolls to the next tier ---------- */
  (function plans() {
    var sec = $('#pricing');
    var card = $('#tierCard'), field = $('#wgField');
    if (!sec || !card || !field) return;

    var items = $$('.wg', field);
    if (!items.length) return;

    var rolls = $$('.tier-roll', card);
    var num   = $('#tierNum');
    var dots  = $$('#tierDots i');
    var PRICES = ['20', '79', '199'];
    var TIERS = 3;

    // group the widgets by the tier that introduces them
    var byTier = [[], [], []];
    items.forEach(function (el, i) {
      var t = +(el.dataset.tier || 0);
      byTier[t].push(el);
      el.style.setProperty('--i', i);
    });

    // Each tier gets a window: its widgets pop in one by one across the first
    // part, then a short beat where the card rolls over to the next tier.
    var SHOW = 0.74;                 // share of a tier's window spent popping in

    function tierWindow(p) {
      var raw = p * TIERS;
      var t = Math.min(TIERS - 1, Math.floor(raw));
      return { t: t, k: raw - t };   // which tier, and how far through it
    }

    var shownTier = -1;

    function update() {
      if (window.innerWidth <= 900) {
        items.forEach(function (el) {
          el.style.removeProperty('--o'); el.style.removeProperty('--s'); el.style.removeProperty('--dy');
        });
        return;
      }

      var total = sec.offsetHeight - window.innerHeight;
      if (total <= 0) return;
      var r = sec.getBoundingClientRect();
      var p = Math.min(1, Math.max(0, -r.top / total));

      var w = tierWindow(p);
      var t = w.t, k = w.k;

      // --- the card rolls once per tier boundary
      if (t !== shownTier) {
        shownTier = t;
        rolls.forEach(function (el) {
          el.style.transform = 'translateY(' + (-t * 100 / TIERS) + '%)';
        });
        if (num && typeof roll === 'function') roll(num, PRICES[t]);
        else if (num) num.textContent = PRICES[t];
        dots.forEach(function (d, i) { d.classList.toggle('on', i === t); });
      }

      // --- widgets: everything from earlier tiers stays, but recedes
      for (var ti = 0; ti < TIERS; ti++) {
        var group = byTier[ti];
        for (var j = 0; j < group.length; j++) {
          var el = group[j], o, s, dy;

          if (ti > t) {                       // not introduced yet
            o = 0; s = 0.86; dy = 8;
          } else if (ti === t) {              // popping in, one after another
            var slot = (j / group.length) * SHOW;
            var span = SHOW / group.length;
            var f = Math.min(1, Math.max(0, (k - slot) / span));
            f = f * f * (3 - 2 * f);
            o = f; s = 0.86 + f * 0.14; dy = (1 - f) * 8;
          } else {                            // already shown: sit back
            var depth = t - ti;
            o = depth === 1 ? 0.46 : 0.26;
            s = depth === 1 ? 0.84 : 0.74;
            dy = 0;
          }
          el.style.setProperty('--o', o.toFixed(3));
          el.style.setProperty('--s', s.toFixed(3));
          el.style.setProperty('--dy', dy.toFixed(1) + 'px');
        }
      }
    }

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    setTimeout(update, 300);
  })();

  /* ---------- scroll stage: the dashboard assembles itself ---------- */
  (function stage() {
    var stage = $('#stage'), inner = $('.stage-inner', stage || document);
    if (!stage || !inner) return;

    // Ordered list of the pieces, in the order they should appear. Containers
    // are used for anything the audit engine re-renders, so a rebuild cannot
    // strip the animation state off a child.
    var order = [];
    function add(sel, root) { $$(sel, root || inner).forEach(function (e) { order.push(e); }); }
    add('.titlebar'); add('.side-org'); add('.sn'); add('.side-foot');
    add('.tb-left'); add('.tb-right'); add('.qqueue'); add('.qcard');
    add('.models'); add('.findings .panel-head'); add('.feed');
    add('.dial-wrap'); add('.tallies'); add('.cats'); add('.rhist');
    add('.pnl'); add('.statusbar');
    if (!order.length) return;
    order.forEach(function (e) { e.classList.add('bit'); });

    var BUILD_END = 0.18;      // snap together early, then hold while it runs
    var FADE_START = 0.78;     // long, soft fade out rather than a snap
    var stepSpan = BUILD_END / order.length;

    function update() {
      // width is re-checked on every update so widening the window revives it
      if (window.innerWidth <= 900) {
        inner.style.removeProperty('--frame-o');
        inner.style.removeProperty('--stage-op');
        order.forEach(function (e) { e.style.removeProperty('--bit-o'); e.style.removeProperty('--bit-y'); });
        return;
      }
      var r = stage.getBoundingClientRect();
      var total = stage.offsetHeight - window.innerHeight;
      var p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0;

      for (var i = 0; i < order.length; i++) {
        var start = i * stepSpan;
        var local = Math.min(1, Math.max(0, (p - start) / (stepSpan * 3.2)));
        var eased = local * local * (3 - 2 * local);
        order[i].style.setProperty('--bit-o', eased.toFixed(3));
        order[i].style.setProperty('--bit-y', ((1 - eased) * 14).toFixed(2) + 'px');
      }

      // the window frame itself appears first, so an empty shell never
      // slides into view while the hero is still on screen
      var frame = Math.min(1, Math.max(0, p / 0.12));
      inner.style.setProperty('--frame-o', (frame * frame * (3 - 2 * frame)).toFixed(3));

      var out = p <= FADE_START ? 1 : 1 - (p - FADE_START) / (1 - FADE_START);
      out = Math.max(0, Math.min(1, out));
      out = out * out * (3 - 2 * out);      // ease the fade at both ends
      inner.style.setProperty('--stage-op', out.toFixed(3));
    }

    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
  })();

  /* ==========================================================
     3D FACETED CORE
     ========================================================== */
  (function core3d() {
    var stage = $('#coreStage');
    if (!stage || typeof THREE === 'undefined') return;

    var w = stage.clientWidth, h = stage.clientHeight;
    if (!w || !h) return;

    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch (e) { return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h);
    stage.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(42, w / h, 0.1, 100);
    camera.position.set(0, 0, 5.4);

    var geo = new THREE.IcosahedronGeometry(1.65, 1);
    var mat = new THREE.MeshStandardMaterial({
      color: 0xB4B4BE, metalness: 1, roughness: 0.26, flatShading: true
    });
    var mesh = new THREE.Mesh(geo, mat);
    scene.add(mesh);

    var wire = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.68, 1),
      new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.07 })
    );
    scene.add(wire);

    function hex(v, fb) { var n = parseInt((v || '').replace('#', ''), 16); return isNaN(n) ? fb : n; }
    scene.add(new THREE.AmbientLight(0x404048, 1.1));
    var key  = new THREE.PointLight(hex(cssVar('--accent'), 0xE8E8EA), 90, 26);
    var fill = new THREE.PointLight(hex(cssVar('--accent-2'), 0x9CA3AF), 55, 26);
    var rim  = new THREE.PointLight(0x6f7dff, 40, 26);
    key.position.set(3.6, 2.8, 3.4);
    fill.position.set(-3.8, -1.6, 2.6);
    rim.position.set(-1.2, 3.4, -3.6);
    scene.add(key, fill, rim);

    onTheme(function (a, b) {
      key.color.setHex(hex(a, 0xE8E8EA));
      fill.color.setHex(hex(b, 0x9CA3AF));
    });

    /* drag to rotate */
    var drag = false, px = 0, py = 0, vx = 0.0016, vy = 0.0026;
    function down(e) {
      drag = true; stage.classList.add('dragging');
      var p = e.touches ? e.touches[0] : e;
      px = p.clientX; py = p.clientY;
    }
    function move(e) {
      if (!drag) return;
      var p = e.touches ? e.touches[0] : e;
      var dx = p.clientX - px, dy = p.clientY - py;
      px = p.clientX; py = p.clientY;
      mesh.rotation.y += dx * 0.008; mesh.rotation.x += dy * 0.008;
      vx = dx * 0.0006; vy = dy * 0.0006;
    }
    function up() { drag = false; stage.classList.remove('dragging'); }
    stage.addEventListener('mousedown', down);
    window.addEventListener('mousemove', move, { passive: true });
    window.addEventListener('mouseup', up);
    stage.addEventListener('touchstart', down, { passive: true });
    stage.addEventListener('touchmove', move, { passive: true });
    stage.addEventListener('touchend', up);

    var visible = true;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) { visible = e.isIntersecting; });
      }, { threshold: 0.05 }).observe(stage);
    }

    var t = 0;
    function loop() {
      requestAnimationFrame(loop);
      if (!visible || document.hidden) return;
      t += 0.01;
      if (!drag) {
        vx += (0.0016 - vx) * 0.02; vy += (0.0026 - vy) * 0.02;
        mesh.rotation.y += vy; mesh.rotation.x += vx;
      }
      wire.rotation.copy(mesh.rotation);
      mesh.position.y = Math.sin(t * 0.8) * 0.06;
      wire.position.copy(mesh.position);
      key.position.x = Math.cos(t * 0.35) * 4.2;
      key.position.z = Math.sin(t * 0.35) * 4.2;
      renderer.render(scene, camera);
    }
    loop();

    window.addEventListener('resize', function () {
      w = stage.clientWidth; h = stage.clientHeight;
      if (!w || !h) return;
      camera.aspect = w / h; camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
  })();

  /* ---------- closer: pick a business type, the report redraws ---------- */
  (function () {
    var box = document.querySelector('.cbox');
    if (!box) return;

    var W = 640, H = 260;

    // Modelled trajectories. y values are percentages, mapped onto the 25-65% grid.
    var CASES = [
      { who: 'Dental Clinic', days: 90, from: 18, to: 57, delta: '+217%',
        note: 'Modelled from closing directory, schema, and review-response gaps.',
        pts: [18, 17, 19, 24, 27, 26, 33, 41, 47, 52, 57],
        marks: [
          { i: 3, text: 'claimed 4 directories' },
          { i: 6, text: 'FAQ schema on 8 pages' },
          { i: 9, text: 'answered 140 reviews' }
        ] },
      { who: 'Law Firm', days: 60, from: 22, to: 40, delta: '+82%',
        note: 'Modelled from practice-area pages and unblocking AI crawlers.',
        pts: [22, 21, 23, 22, 26, 29, 31, 30, 34, 37, 40],
        marks: [
          { i: 2, text: 'unblocked GPTBot' },
          { i: 5, text: 'per-practice pages' },
          { i: 8, text: 'named the partners' }
        ] },
      { who: 'Local Services', days: 120, from: 14, to: 36, delta: '+156%',
        note: 'Modelled from service-area copy, pricing in text, and hours markup.',
        pts: [14, 15, 14, 18, 21, 20, 25, 28, 27, 32, 36],
        marks: [
          { i: 3, text: 'pricing written in text' },
          { i: 6, text: 'service areas listed' },
          { i: 9, text: 'hours in schema' }
        ] }
    ];

    var opts   = [].slice.call(box.querySelectorAll('.copt'));
    var line   = document.getElementById('cpLine');
    var marksG = document.getElementById('cpMarks');
    var notes  = document.getElementById('cpNotes');
    var elWho  = document.getElementById('cbWho');
    var elFrom = document.getElementById('cbFrom');
    var elTo   = document.getElementById('cbTo');
    var elEnd  = document.getElementById('cbEnd');
    var elBig  = document.getElementById('csBig');
    var elNote = document.getElementById('csNote');
    if (!line) return;



    // the axis follows each case, so every trajectory fills the plot
    var lo = 0, hi = 100;
    function fitAxis(c) {
      var min = Math.min.apply(null, c.pts), max = Math.max.apply(null, c.pts);
      lo = Math.max(0, Math.floor((min - 5) / 5) * 5);
      hi = Math.ceil((max + 6) / 5) * 5;
    }
    function yOf(v) {
      var t = (v - lo) / (hi - lo);
      return 205 - t * (205 - 40);
    }
    function xOf(i, n) { return (i / (n - 1)) * W; }

    var current = -1;
    var lastXY = null;

    // The stroke is vector-effect:non-scaling-stroke, so the dash pattern is
    // measured in SCREEN pixels -- but getTotalLength() reports user units, and
    // the viewBox is stretched (preserveAspectRatio="none"). Feeding it the user
    // length made the dash run out before the path did, which is the break in
    // the line. Measure the polyline in rendered pixels instead.
    function setDash() {
      if (!lastXY || lastXY.length < 2) return;
      var svg = line.ownerSVGElement;
      var r = svg ? svg.getBoundingClientRect() : null;
      var sx = r && r.width ? r.width / W : 1;
      var sy = r && r.height ? r.height / H : 1;
      var len = 0;
      for (var i = 1; i < lastXY.length; i++) {
        len += Math.hypot((lastXY[i][0] - lastXY[i - 1][0]) * sx,
                          (lastXY[i][1] - lastXY[i - 1][1]) * sy);
      }
      // a whisker of slack so rounding can never reopen the gap
      box.style.setProperty('--cp-len', (len + 2).toFixed(1));
    }

    function render(k) {
      if (k === current) return;
      current = k;
      var c = CASES[k];
      var n = c.pts.length;
      fitAxis(c);

      // the four y labels sit on the four gridlines, so they must match the axis
      var yl = document.querySelector('.cp-ylab');
      if (yl) {
        var span = yl.querySelectorAll('span');
        [40, 95, 150, 205].forEach(function (gy, gi) {
          if (!span[gi]) return;
          var v = lo + (205 - gy) / (205 - 40) * (hi - lo);
          span[gi].textContent = Math.round(v) + '%';
        });
      }

      var xy = c.pts.map(function (v, i) { return [xOf(i, n), yOf(v)]; });
      var coords = xy.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); });
      line.setAttribute('points', coords.join(' '));
      lastXY = xy;

      // the same shape closed down to the baseline, for the gradient fill
      var area = document.getElementById('cpArea');
      if (area) {
        area.setAttribute('d', 'M' + coords.join(' L') + ' L' + W + ',' + H + ' L0,' + H + ' Z');
      }

      // restart the draw-in: length changes with the shape
      setDash();
      // rewind, flush the style, then set the target: the transition replays
      // every time a case is picked rather than only on the first draw
      var plot = box.querySelector('.cbox-plot');
      if (plot) {
        plot.classList.remove('drawn');
        void plot.offsetWidth;      // flush, so re-adding replays every animation
        plot.classList.add('drawn');
      }

      // milestone dots + their dashed drop lines
      var g = '';
      c.marks.forEach(function (m) {
        var x = xOf(m.i, n), y = yOf(c.pts[m.i]);
        g += '<line x1="' + x.toFixed(1) + '" y1="' + y.toFixed(1) +
             '" x2="' + x.toFixed(1) + '" y2="' + H + '"/>';
        g += '<circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="4"/>';
      });
      var ey = yOf(c.pts[n - 1]).toFixed(1);
      marksG.innerHTML = g;

      // The dots are drawn in the SAME coordinate space as the line, so they
      // cannot drift off it. A separate overlay was sized by CSS inset while the
      // plot was sized by its own min-height, and the two boxes did not match.
      // preserveAspectRatio="none" would squash a circle, so each is an ellipse
      // whose radii are pre-divided by the axis scale -- round on screen, and
      // exactly on the curve.
      var svgEl = line.ownerSVGElement;
      var vb = svgEl ? svgEl.getBoundingClientRect() : null;
      var kx = vb && vb.width ? W / vb.width : 1;
      var ky = vb && vb.height ? H / vb.height : 1;
      function dot(cx, cy, r, cls) {
        return '<ellipse' + (cls ? ' class="' + cls + '"' : '') +
               ' cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) +
               '" rx="' + (r * kx).toFixed(2) + '" ry="' + (r * ky).toFixed(2) + '"/>';
      }
      var dg = '';
      c.marks.forEach(function (m) {
        dg += dot(xOf(m.i, n), yOf(c.pts[m.i]), 4.5);
      });
      dg += dot(W, +ey, 5.5, 'end');
      dg += dot(W, +ey, 5.5, 'halo');
      marksG.insertAdjacentHTML('beforeend', dg);

      // the labels live in HTML so they stay crisp and never stretch with the viewBox
      notes.innerHTML = c.marks.map(function (m) {
        var xp = (m.i / (n - 1)) * 100;
        var yp = (yOf(c.pts[m.i]) / H) * 100;
        var edge = xp > 72 ? ' right' : '';
        return '<span class="cp-note' + edge + '" style="left:' + xp.toFixed(1) +
               '%;top:' + Math.min(88, yp + 14).toFixed(1) + '%">' + m.text + '</span>';
      }).join('');
      var els = notes.querySelectorAll('.cp-note');
      els.forEach(function (el, i) {
        setTimeout(function () { el.classList.add('show'); }, 260 + i * 190);
      });

      elWho.textContent  = c.who;
      elEnd.textContent  = 'day ' + c.days;
      elNote.textContent = c.note;
      roll(elFrom, c.from + '%');
      roll(elTo,   c.to + '%');
      roll(elBig,  c.delta);

      opts.forEach(function (o, i) {
        o.classList.toggle('is-on', i === k);
        o.setAttribute('aria-pressed', i === k ? 'true' : 'false');
      });

      var hit = document.getElementById('cpHit');
      if (hit && hit.__reset) hit.__reset();
    }


    /* ---------- hover the plot to read any day on the curve ---------- */
    (function () {
      var layer = document.getElementById('cpHit');
      var cross = document.getElementById('cpCross');
      var dot   = document.getElementById('cpDot');
      var tip   = document.getElementById('cpTip');
      var tDay  = document.getElementById('tipDay');
      var tVal  = document.getElementById('tipVal');
      if (!layer || !cross || !dot || !tip) return;

      // the line is straight between points, so a linear read matches what is drawn
      function sample(c, t) {
        var n = c.pts.length;
        var x = t * (n - 1);
        var i = Math.max(0, Math.min(n - 2, Math.floor(x)));
        var f = x - i;
        return c.pts[i] + (c.pts[i + 1] - c.pts[i]) * f;
      }

      function place(t) {
        var c = CASES[current] || CASES[0];
        var v = sample(c, t);
        var xp = t * 100;
        var yp = (yOf(v) / H) * 100;

        cross.style.left = xp + '%';
        dot.style.left = xp + '%';
        dot.style.top = yp + '%';
        tip.style.left = xp + '%';
        tip.style.top = yp + '%';
        tip.classList.toggle('edge-l', xp < 12);
        tip.classList.toggle('edge-r', xp > 88);

        tDay.textContent = 'day ' + Math.round(t * c.days);
        roll(tVal, Math.round(v) + '%', true);
      }

      // pointermove is already frame-throttled by the browser, and these are five
      // style writes, so placing straight away keeps the readout under the cursor
      function move(e) {
        var b = layer.getBoundingClientRect();
        if (!b.width) return;
        place(Math.max(0, Math.min(1, (e.clientX - b.left) / b.width)));
      }

      layer.addEventListener('pointerenter', function (e) {
        layer.classList.add('on');
        move(e);
      });
      layer.addEventListener('pointermove', move);
      layer.addEventListener('pointerdown', move);
      layer.addEventListener('pointerleave', function () {
        layer.classList.remove('on');
      });

      // keyboard: arrow along the curve once the chart has focus
      var kt = 0;
      layer.tabIndex = 0;
      layer.addEventListener('keydown', function (e) {
        var step = e.shiftKey ? 0.1 : 0.02;
        if (e.key === 'ArrowRight') kt = Math.min(1, kt + step);
        else if (e.key === 'ArrowLeft') kt = Math.max(0, kt - step);
        else return;
        e.preventDefault();
        layer.classList.add('on');
        place(kt);
      });
      layer.addEventListener('blur', function () { layer.classList.remove('on'); });

      // a new case means the old readout is stale
      layer.__reset = function () { layer.classList.remove('on'); };
    })();

    // a click always wins: it also cancels the pending first draw below,
    // so a late intersection callback can never overwrite the chosen case
    var seen = false;
    opts.forEach(function (o, i) {
      o.addEventListener('click', function () { seen = true; render(i); });
    });

    window.addEventListener('resize', function () {
      setDash();
      var k = current; current = -1; if (k >= 0) render(k);
    });

    function first() { if (seen) return; seen = true; render(0); }

    // draw the first one once the box is actually on screen
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es, obs) {
        if (es[0].isIntersecting) { obs.disconnect(); first(); }
      }, { threshold: 0.2 });
      io.observe(box);
      // already on screen at load? don't wait for a scroll that may never come
      var b = box.getBoundingClientRect();
      if (b.top < window.innerHeight && b.bottom > 0) { io.disconnect(); first(); }
    } else {
      first();
    }
    setTimeout(first, 2500);
  })();

})();
