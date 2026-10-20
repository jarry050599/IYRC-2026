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
  function refineSharedChrome() {
    document.querySelectorAll('.sec-head .eyebrow').forEach(function (label) {
      label.innerHTML = label.innerHTML.replace(/^\s*\d+[A-Z]?\s*[—–-]\s*/, '');
    });
    if (menu && !menu.querySelector('.mobile-nav-flat')) {
      var flat = document.createElement('div');
      flat.className = 'mobile-nav-flat';
      menu.querySelectorAll('.nav-group').forEach(function (group) {
        var heading = document.createElement('div');
        heading.className = 'mobile-nav-heading';
        heading.innerHTML = group.querySelector('summary').innerHTML;
        flat.appendChild(heading);
        group.querySelectorAll('.nav-group-links a').forEach(function (link) { flat.appendChild(link.cloneNode(true)); });
      });
      var contact = document.createElement('button');
      contact.className = 'btn btn-primary mobile-nav-contact';
      contact.setAttribute('data-modal-open', 'contactModal');
      contact.innerHTML = '<span class="l-zh">聯絡我們</span><span class="l-en">Contact us</span>';
      contact.addEventListener('click', function () {
        var original = document.querySelector('.nav-right [data-modal-open]');
        if (original) original.click();
      });
      flat.appendChild(contact);
      menu.appendChild(flat);
    }
    var WF = 'https://wayfinder.linkguard.tw';
    var arrow = '<svg aria-hidden="true" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 11l6-6M6 5h5v5"/></svg>';
    var navRight = document.querySelector('.nav-right');
    if (navRight && !navRight.querySelector('.wf-nav-link')) {
      var wl = document.createElement('a');
      wl.className = 'wf-nav-link';
      wl.href = WF; wl.target = '_blank'; wl.rel = 'noopener';
      wl.innerHTML = '<span class="wf-dot" aria-hidden="true"></span><span>WAYFINDER</span>' + arrow;
      wl.setAttribute('aria-label', 'WAYFINDER 官方網站 / WAYFINDER website');
      navRight.insertBefore(wl, navRight.firstChild);
    }
    if (menu && !menu.querySelector('.wf-drawer-link')) {
      var dl = document.createElement('a');
      dl.className = 'wf-drawer-link';
      dl.href = WF; dl.target = '_blank'; dl.rel = 'noopener';
      dl.innerHTML = '<span><b>WAYFINDER</b><small>wayfinder.linkguard.tw</small></span>' + arrow;
      menu.appendChild(dl);
    }
    var homeProblem = document.getElementById('home-problem');
    if (homeProblem && !document.querySelector('.wf-entry')) {
      var band = document.createElement('div');
      band.className = 'wf-entry';
      band.setAttribute('role', 'region'); band.setAttribute('aria-label', 'WAYFINDER');
      band.innerHTML = '<div class="wrap"><div class="wf-entry-copy"><p class="wf-entry-kicker">WAYFINDER</p><h2><span class="l-zh">前往 WAYFINDER 尋途官方網站</span><span class="l-en">Visit the WAYFINDER website</span></h2><p class="wf-entry-url">wayfinder.linkguard.tw</p></div><a class="wf-entry-btn" href="' + WF + '" target="_blank" rel="noopener"><span class="l-zh">前往網站</span><span class="l-en">Go to website</span>' + arrow + '</a></div>';
      homeProblem.parentNode.insertBefore(band, homeProblem);
    }
    document.querySelectorAll('footer .credits').forEach(function (credits) {
      var groups = credits.querySelectorAll('.credit-group');
      if (!groups.length || credits.querySelector('.footer-contact')) return;
      if (groups[0]) groups[0].remove();
      if (groups[2]) groups[2].remove();
      var schools = credits.querySelector('.credit-group');
      if (schools) {
        var zh = schools.querySelector('.credit-label .l-zh');
        var en = schools.querySelector('.credit-label .l-en');
        if (zh) zh.textContent = '團隊所屬學校';
        if (en) en.textContent = 'Team Schools';
      }
      var contact = document.createElement('div');
      contact.className = 'credit-group footer-contact';
      contact.innerHTML = '<div class="credit-label"><span class="l-zh">聯絡 LinkGuard</span><span class="l-en">Contact LinkGuard</span></div><ul class="credit-list"><li><span class="b">→</span><span><a href="mailto:jouyun@alinkguard.com">jouyun@alinkguard.com</a></span></li><li><span class="b">→</span><span><a href="https://www.instagram.com/linkguard_dev_team/" target="_blank" rel="noopener noreferrer">@linkguard_dev_team</a></span></li></ul>';
      credits.appendChild(contact);
      var company = document.createElement('div');
      company.className = 'credit-group footer-company';
      company.innerHTML = '<div class="credit-label"><span class="l-zh">公司資訊</span><span class="l-en">Company</span></div><ul class="credit-list"><li><span class="b">→</span><span><span class="l-zh">固碩實業有限公司</span><span class="l-en">GOOD SO INDUSTRIAL CO., LTD.</span></span></li><li><span class="b">→</span><span><span class="l-zh">統一編號 27617680</span><span class="l-en">Tax ID 27617680</span></span></li><li><span class="b">→</span><span><span class="l-zh">新竹縣竹東鎮北興路一段571號</span><span class="l-en">No. 571, Sec. 1, Beixing Rd., Zhudong Township, Hsinchu County</span></span></li></ul>';
      credits.appendChild(company);
    });
  }
  function syncDrawer() {
    var open = compact.matches && menu.classList.contains('open');
    if (open) menu.querySelectorAll('details').forEach(function (group) { group.open = true; });
    document.body.classList.toggle('drawer-open', open);
    background.forEach(function (el) { el.inert = open; });
    toggle.setAttribute('aria-label', open ? '關閉導覽 / Close navigation' : '開啟導覽 / Open navigation');
    if (open && !isDrawerOpen) menu.querySelector('summary').focus();
    isDrawerOpen = open;
  }
  refineSharedChrome();
  new MutationObserver(syncDrawer).observe(menu, { attributes: true, attributeFilter: ['class'] });
  toggle.addEventListener('click', function () {
    requestAnimationFrame(function () {
      if (compact.matches && menu.classList.contains('open')) {
        menu.querySelectorAll('details').forEach(function (group) { group.open = true; });
      }
    });
  });
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
