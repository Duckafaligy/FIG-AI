/* Where the API lives.
   Same-origin in local development; set FIG_API to the deployed backend
   before the site goes anywhere public. The marketing site is static and the
   API is a persistent process, so in production these are different hosts. */
var FIG_API = (function () {
  var h = location.hostname;
  if (h === '127.0.0.1' || h === 'localhost') return 'http://127.0.0.1:8000';
  return 'https://api.fig.tools';
})();
