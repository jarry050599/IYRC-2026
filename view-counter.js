/* LinkGuard — site-wide page-view counter shown in the footer.
   Counts with the free Abacus counting service (abacus.jasoncameron.dev):
   - one count per page per browser session (reloads are not re-counted);
   - local previews and automated browsers only read the number, never add to it;
   - no cookies, no referrer and no personal data are sent;
   - if the service is unreachable the counter simply stays hidden. */
(function () {
  'use strict';
  var API = 'https://abacus.jasoncameron.dev';
  var NS = 'linkguard-tw';
  var KEY = 'views';
  var TIMEOUT = 5000;

  function locale() {
    var l = document.documentElement.getAttribute('data-lang');
    return { en: 'en-US', ja: 'ja-JP', ko: 'ko-KR' }[l] || 'zh-TW';
  }

  function build(foot) {
    var el = document.createElement('p');
    el.className = 'lg-views';
    el.hidden = true;
    el.setAttribute('aria-live', 'polite');
    el.innerHTML = '<span class="lg-views-dot" aria-hidden="true"></span>' +
      '<span class="lg-views-label"><span class="l-zh">總點閱數</span><span class="l-en">Total views</span></span>' +
      '<strong class="lg-views-n"></strong>';
    var slogan = foot.querySelector('.slogan');
    if (slogan) foot.insertBefore(el, slogan); else foot.appendChild(el);
    return el;
  }

  function show(el, n) {
    var out = el.querySelector('.lg-views-n');
    var render = function () {
      try { out.textContent = Number(n).toLocaleString(locale()); } catch (e) { out.textContent = String(n); }
    };
    render();
    el.hidden = false;
    // Keep digit grouping in step with language changes.
    new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ['data-lang'] });
  }

  function shouldCount() {
    var host = location.hostname;
    if (!/^https?:$/.test(location.protocol)) return false;
    if (host === 'localhost' || host === '127.0.0.1' || host === '' || /\.local$/.test(host)) return false;
    if (navigator.webdriver) return false;
    var mark = 'lg-viewed:' + location.pathname;
    try {
      if (sessionStorage.getItem(mark)) return false;
      sessionStorage.setItem(mark, '1');
    } catch (e) { /* storage blocked: count this load */ }
    return true;
  }

  function init() {
    var foot = document.querySelector('footer .foot');
    if (!foot || foot.querySelector('.lg-views') || !window.fetch) return;
    var el = build(foot);
    var op = shouldCount() ? 'hit' : 'get';
    var ctrl = window.AbortController ? new AbortController() : null;
    var timer = setTimeout(function () { if (ctrl) ctrl.abort(); }, TIMEOUT);
    fetch(API + '/' + op + '/' + NS + '/' + KEY, {
      method: 'GET', mode: 'cors', credentials: 'omit', cache: 'no-store',
      referrerPolicy: 'no-referrer', signal: ctrl ? ctrl.signal : undefined
    }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        clearTimeout(timer);
        if (d && typeof d.value === 'number' && d.value >= 0) show(el, d.value);
      })
      .catch(function () { clearTimeout(timer); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
