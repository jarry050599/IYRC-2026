/* LinkGuard Premium Light — scroll reveal.
   Progressive enhancement only: adds presentation classes, never changes content,
   links, IDs or the behaviour of existing scripts. Does nothing when the visitor
   prefers reduced motion or the browser has no IntersectionObserver. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !('IntersectionObserver' in window)) return;

  var SELECTOR = [
    '.reading-section-head', '.sec-head', '.system-flow > li', '.large-metric', '.evidence-caveat',
    '#home-system .chip', '.system-home-photo', '.home-team-grid > a', '.home-intro-copy',
    '.kpi', '.exp-card', '.place-card', '.road-card', '.award-card', '.member', '.chart-card',
    '.table-scroll', '.facts', '.fact', '.quote', '.report-block > .sec-head'
  ].join(',');

  function setup() {
    var targets = Array.prototype.slice.call(document.querySelectorAll(SELECTOR)).filter(function (el) {
      return !el.closest('.modal, .photo-lightbox, [hidden], nav, footer');
    });
    if (!targets.length) return;

    root.classList.add('lg-motion');

    // Stagger siblings that enter together.
    var groups = new Map();
    targets.forEach(function (el) {
      var parent = el.parentElement;
      var n = groups.get(parent) || 0;
      el.style.setProperty('--lg-i', Math.min(n, 5));
      groups.set(parent, n + 1);
      el.classList.add('lg-r');
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('lg-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    targets.forEach(function (el) { io.observe(el); });

    // Existing .reveal elements are driven by the page's own observer; mirror it so
    // nothing can stay hidden if that script is delayed.
    document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

    // Failsafe: never leave content hidden.
    window.setTimeout(function () {
      document.querySelectorAll('.lg-r:not(.lg-in)').forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.top < window.innerHeight * 1.1) el.classList.add('lg-in');
      });
    }, 2500);
    window.addEventListener('beforeprint', function () {
      document.querySelectorAll('.lg-r').forEach(function (el) { el.classList.add('lg-in'); });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
  else setup();
})();
