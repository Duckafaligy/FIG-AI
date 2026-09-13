/* Where the API and the dashboard live.

   The marketing site is static (Vercel); the app is a persistent process
   (Railway/Render), so in production they are different hosts. Everything that
   points at the app uses data-app="/path" and is rewritten below, so this is
   the only file to change when the backend gets a domain.

   FIG_API is deliberately left empty until that domain exists: an empty base
   makes the demo fail visibly with "could not reach the FIG API" rather than
   silently calling a host nobody owns. */
var FIG_API = (function () {
  var h = location.hostname;
  if (h === '127.0.0.1' || h === 'localhost') return 'http://127.0.0.1:8000';
  return '';                      // <- set to https://your-backend-host once deployed
})();

var FIG_APP = FIG_API;            // the dashboard is served by the same process

(function () {
  function wire() {
    var links = document.querySelectorAll('[data-app]');
    for (var i = 0; i < links.length; i++) {
      var path = links[i].getAttribute('data-app');
      if (FIG_APP) {
        links[i].setAttribute('href', FIG_APP + path);
      } else {
        // Nothing to point at yet -- say so rather than sending people to a 404.
        links[i].setAttribute('href', 'demo.html');
        links[i].setAttribute('title', 'Accounts open when the backend is deployed');
      }
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
