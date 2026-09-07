/* Where the API and the dashboard live.

   The marketing site is static and the app is a persistent process, so in
   production they are different hosts. Everything that points at the app uses
   data-app="/path" and is rewritten below, so there is exactly one place to
   change when the backend gets a real domain.

   Local development assumes the backend on :8000 and the site on :8123. */
var FIG_API = (function () {
  var h = location.hostname;
  if (h === '127.0.0.1' || h === 'localhost') return 'http://127.0.0.1:8000';
  return 'https://api.fig.tools';
})();

var FIG_APP = FIG_API;          // the dashboard is served by the same process

(function () {
  function wire() {
    var links = document.querySelectorAll('[data-app]');
    for (var i = 0; i < links.length; i++) {
      links[i].setAttribute('href', FIG_APP + links[i].getAttribute('data-app'));
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
