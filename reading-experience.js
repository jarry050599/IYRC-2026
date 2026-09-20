/* Reading and navigation presentation only. Existing application handlers own all system interactions. */
(function () {
  'use strict';
  var menu = document.getElementById('navLinks');
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('nav');
  var scrim = document.querySelector('.nav-scrim');
  var compact = window.matchMedia('(max-width: 1000px)');
  var background = [document.querySelector('main'), document.querySelector('footer'), document.getElementById('toTop')].filter(Boolean);
  var isDrawerOpen = false;
  function syncDrawer() {
    var open = compact.matches && menu.classList.contains('open');
    document.body.classList.toggle('drawer-open', open);
    background.forEach(function (el) { el.inert = open; });
    toggle.setAttribute('aria-label', open ? '關閉導覽 / Close navigation' : '開啟導覽 / Open navigation');
    if (open && !isDrawerOpen) menu.querySelector('summary').focus();
    isDrawerOpen = open;
  }
  new MutationObserver(syncDrawer).observe(menu, { attributes: true, attributeFilter: ['class'] });
  compact.addEventListener('change', function () {
    if (!compact.matches && menu.classList.contains('open')) toggle.click();
    syncDrawer();
  });
  scrim.addEventListener('click', function () { if (isDrawerOpen) { toggle.click(); toggle.focus(); } });
  nav.addEventListener('click', function (event) {
    if (isDrawerOpen && event.target.closest('[data-modal-open]')) toggle.click();
  }, true);
  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Tab' || !isDrawerOpen || document.querySelector('.modal.open,.photo-lightbox.open')) return;
    var items = Array.from(nav.querySelectorAll('a,button,summary')).filter(function (el) { return el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden'; });
    var first = items[0], last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  syncDrawer();

  function expose(target) {
    for (var ancestor = target; ancestor && ancestor !== document.body; ancestor = ancestor.parentElement) {
      if (ancestor.tagName === 'DETAILS') ancestor.open = true;
      if (ancestor.matches('.acc-item,.card,.member') && !ancestor.classList.contains('open')) {
        var control = ancestor.querySelector('.acc-head,.unit,.member-toggle');
        if (control) control.click();
      }
    }
  }
  function followReadingTarget(id, scroll) {
    var target = document.getElementById(id);
    if (!target) return;
    expose(target);
    if (scroll) requestAnimationFrame(function () {
      var destination = target.closest('.acc-item,.card') || target;
      destination.scrollIntoView({ block: 'start', behavior: 'auto' });
    });
  }
  document.querySelectorAll('[data-reading-target]').forEach(function (link) {
    link.addEventListener('click', function () { followReadingTarget(link.getAttribute('data-reading-target'), true); });
  });
  function revealHash() {
    try { if (location.hash) followReadingTarget(decodeURIComponent(location.hash.slice(1)), true); } catch (_) {}
  }
  window.addEventListener('hashchange', revealHash);
  revealHash();

  var phases = Array.from(document.querySelectorAll('[data-flow-phase]'));
  var flowDiagram = document.getElementById('diagram');
  var selectedPhase = null;
  var phasePaths = {
    sense: { nodes: ['sbn', 'sen'], segments: [] },
    send: { nodes: ['sbn', 'sen', 'cmd'], segments: ['1'] },
    search: { nodes: ['fw', 'qr', 'ugv'], segments: ['2'] },
    decide: { nodes: ['cmd'], segments: [] },
    dispatch: { nodes: ['cmd', 'rr', 'victim'], segments: ['3'] }
  };
  function highlightPhase(phase) {
    if (!flowDiagram) return;
    if (!phase) { flowDiagram.removeAttribute('data-reading-phase'); return; }
    flowDiagram.setAttribute('data-reading-phase', phase);
    var path = phasePaths[phase];
    flowDiagram.querySelectorAll('.dg-node,.dg-seg').forEach(function (part) {
      part.classList.toggle('phase-highlight', path.nodes.indexOf(part.getAttribute('data-node')) !== -1 || path.segments.indexOf(part.getAttribute('data-seg')) !== -1);
    });
  }
  phases.forEach(function (button) {
    ['mouseenter', 'focus'].forEach(function (type) { button.addEventListener(type, function () { highlightPhase(button.getAttribute('data-flow-phase')); }); });
    ['mouseleave', 'blur'].forEach(function (type) { button.addEventListener(type, function () { highlightPhase(selectedPhase); }); });
    button.addEventListener('click', function () {
      var original = document.querySelector('#steps .step[data-step="' + button.getAttribute('data-original-step') + '"]');
      if (original && original.getAttribute('aria-pressed') !== 'true') original.click();
      phases.forEach(function (other) { other.setAttribute('aria-pressed', String(other === button)); });
      selectedPhase = button.getAttribute('data-flow-phase');
      highlightPhase(selectedPhase);
    });
  });
  document.querySelectorAll('#steps .step').forEach(function (button) {
    ['mouseenter', 'focus'].forEach(function (type) { button.addEventListener(type, function () { highlightPhase(null); }); });
    button.addEventListener('click', function () {
      selectedPhase = null;
      highlightPhase(null);
      var group = button.getAttribute('data-step');
      phases.forEach(function (phase) { phase.setAttribute('aria-pressed', String(button.getAttribute('aria-pressed') === 'true' && phase.getAttribute('data-original-step') === group)); });
    });
  });

  // Expand native disclosures for printing, then restore the reader's choices.
  var printDetails = [];
  window.addEventListener('beforeprint', function () {
    printDetails = Array.from(document.querySelectorAll('main details')).filter(function (details) { return !details.open; });
    printDetails.forEach(function (details) { details.open = true; });
  });
  window.addEventListener('afterprint', function () { printDetails.forEach(function (details) { details.open = false; }); });
})();
