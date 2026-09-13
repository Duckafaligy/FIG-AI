/* FIG — device identity and the demo quota.
   First-party only. One cookie holds a random id so the same browser is
   recognised across visits, plus a coarse device read used to size the demo
   and, later, to remember preferences. Nothing leaves this origin. */
(function () {
  'use strict';

  var NS = 'fig';
  var ID_KEY = NS + '_did';
  var CONSENT_KEY = NS + '_consent';
  var SCAN_KEY = NS + '_demo_scan';
  var YEAR = 365 * 24 * 60 * 60;

  function setCookie(name, value, maxAge) {
    var bits = [name + '=' + encodeURIComponent(value), 'path=/', 'SameSite=Lax',
                'max-age=' + (maxAge || YEAR)];
    if (location.protocol === 'https:') bits.push('Secure');
    document.cookie = bits.join('; ');
  }
  function getCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : null;
  }
  function del(name) { document.cookie = name + '=; path=/; max-age=0'; }

  function uid() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'x' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  }

  // Coarse, non-identifying: enough to size the demo and remember a device,
  // not enough to fingerprint anyone across sites.
  function device() {
    var w = window.innerWidth || 0;
    var touch = ('ontouchstart' in window) || (navigator.maxTouchPoints || 0) > 0;
    var kind = w < 700 ? 'phone' : (w < 1100 ? 'tablet' : 'desktop');
    if (kind !== 'phone' && touch && w < 1400) kind = 'tablet';
    return {
      kind: kind,
      width: w,
      height: window.innerHeight || 0,
      dpr: window.devicePixelRatio || 1,
      touch: touch,
      reducedMotion: !!(window.matchMedia &&
        matchMedia('(prefers-reduced-motion: reduce)').matches),
      lang: (navigator.language || '').slice(0, 5),
      tz: (Intl.DateTimeFormat().resolvedOptions() || {}).timeZone || ''
    };
  }

  var FIG = {
    consent: function () { return getCookie(CONSENT_KEY); },
    grant: function () {
      setCookie(CONSENT_KEY, 'granted');
      FIG.id();                       // mint the id now that it is allowed
      document.documentElement.classList.add('fig-consented');
    },
    decline: function () {
      setCookie(CONSENT_KEY, 'declined');
      del(ID_KEY);
      try { localStorage.removeItem(SCAN_KEY); } catch (e) {}
    },
    /* The device id is strictly functional: it is what stops the free demo
       being run over and over from one browser. It is minted regardless of the
       analytics choice, and it is never sent anywhere. */
    id: function () {
      var v = getCookie(ID_KEY);
      if (!v) { v = uid(); setCookie(ID_KEY, v); }
      return v;
    },
    device: device,
    /* the demo allows a single scan per device */
    scanUsed: function () {
      try { return !!localStorage.getItem(SCAN_KEY); }
      catch (e) { return !!getCookie(SCAN_KEY); }
    },
    scanRecord: function (url) {
      var rec = JSON.stringify({ url: url, at: Date.now(), device: FIG.id() });
      try { localStorage.setItem(SCAN_KEY, rec); }
      catch (e) { setCookie(SCAN_KEY, rec); }
    },
    scanReset: function () {
      try { localStorage.removeItem(SCAN_KEY); } catch (e) {}
      del(SCAN_KEY);
    }
  };

  /* ---- theme ----
     Applied before paint from an inline snippet in the page head; this part
     just handles the switch and remembering the choice. */
  var THEME_KEY = NS + '_theme';
  FIG.theme = {
    get: function () {
      try { return localStorage.getItem(THEME_KEY); } catch (e) { return getCookie(THEME_KEY); }
    },
    set: function (name) {
      var root = document.documentElement;
      root.classList.add('theme-anim');
      if (name === 'light') root.setAttribute('data-theme', 'light');
      else root.removeAttribute('data-theme');
      try { localStorage.setItem(THEME_KEY, name); } catch (e) { setCookie(THEME_KEY, name); }
      document.querySelectorAll('[data-theme-set]').forEach(function (b) {
        b.setAttribute('aria-pressed', b.dataset.themeSet === name ? 'true' : 'false');
      });
      clearTimeout(FIG.theme._t);
      FIG.theme._t = setTimeout(function () { root.classList.remove('theme-anim'); }, 400);
      // Scroll-driven sections compute some values from the active theme, so
      // they need a nudge to recompute rather than waiting for the next scroll.
      try { window.dispatchEvent(new Event('scroll')); } catch (e) {}
    },
    current: function () {
      return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
    }
  };

  function wireTheme() {
    var cur = FIG.theme.current();
    document.querySelectorAll('[data-theme-set]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.dataset.themeSet === cur ? 'true' : 'false');
      b.addEventListener('click', function () { FIG.theme.set(b.dataset.themeSet); });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireTheme);
  } else {
    wireTheme();
  }

  FIG.id();
  var d = device();
  document.documentElement.setAttribute('data-device', d.kind);
  window.FIG = FIG;

  /* ---- the notice ----
     A centred dialog, held back a beat so it arrives after the page rather
     than on top of it. Neither button is a default: nothing is stored until
     one of them is pressed. */
  function banner() {
    if (FIG.consent()) return;
    var wrap = document.createElement('div');
    wrap.className = 'ckwrap';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.setAttribute('aria-labelledby', 'ckTitle');
    wrap.innerHTML =
      '<div class="ck-back"></div>' +
      '<div class="ck-card">' +
        '<div class="ck-ico" aria-hidden="true">' +
          '<svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9 4 4 0 0 1-5-5 4 4 0 0 1-4-4Z"/>' +
          '<circle cx="9.5" cy="13.5" r=".9"/><circle cx="14" cy="16" r=".9"/>' +
          '<circle cx="8.5" cy="9" r=".9"/></svg>' +
        '</div>' +
        '<h2 class="ck-title" id="ckTitle">Two cookies, both doing a job</h2>' +
        '<p class="ck-body">FIG keeps a couple of first-party cookies so this browser is ' +
          'recognised between visits. Nothing is shared with anyone else, and there is ' +
          'no advertising or cross-site tracking on this site.</p>' +
        '<ul class="ck-list">' +
          '<li><b>fig_did</b><span>Recognises this browser, which is what keeps the ' +
            'free demo to one scan per device.</span></li>' +
          '<li><b>fig_theme</b><span>Remembers whether you chose the light or dark ' +
            'theme.</span></li>' +
        '</ul>' +
        '<div class="ck-act">' +
          '<button class="ck-btn" type="button" data-ck="decline">Essential only</button>' +
          '<button class="ck-btn ck-yes" type="button" data-ck="grant">Allow</button>' +
        '</div>' +
        '<a class="ck-link" href="#">Read the cookie notice</a>' +
      '</div>';
    document.body.appendChild(wrap);
    document.documentElement.classList.add('ck-open');
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { wrap.classList.add('on'); });
    });
    var yes = wrap.querySelector('.ck-yes');
    if (yes) yes.focus({ preventScroll: true });

    function close() {
      wrap.classList.remove('on');
      document.documentElement.classList.remove('ck-open');
      setTimeout(function () { wrap.remove(); }, 340);
      document.removeEventListener('keydown', onKey);
    }
    // Esc is the conservative choice, not a dismissal
    function onKey(e) {
      if (e.key === 'Escape') { FIG.decline(); close(); return; }
      if (e.key !== 'Tab') return;
      var f = wrap.querySelectorAll('button, a[href]');
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    document.addEventListener('keydown', onKey);

    wrap.addEventListener('click', function (e) {
      var b = e.target.closest('[data-ck]');
      if (!b) return;
      if (b.dataset.ck === 'grant') FIG.grant(); else FIG.decline();
      close();
    });
  }
  function showBanner() { setTimeout(banner, 700); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', showBanner);
  } else {
    showBanner();
  }
})();
