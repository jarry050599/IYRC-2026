/* LinkGuard — Japanese / Korean reading modes.
   Additive layer on top of the site's existing zh/en switch:
   - existing .l-zh / .l-en markup and the inline zh/en logic are left untouched;
   - in ja/ko mode each .l-en element gets a sibling clone (.l-ja / .l-ko) whose
     content comes from i18n/<lang>.json; untranslated items fall back to English;
   - the choice is stored separately (lg-lang-x) so zh/en behaviour is unchanged. */
(function () {
  'use strict';
  var KEY = 'lg-lang-x';
  var LANGS = {
    ja: { label: '日本語', htmlLang: 'ja', home: 'LinkGuard — 災害捜索救助システム', toastOk: 'メールアドレスをコピーしました：', toastFail: 'メールアドレスをコピーできませんでした' },
    ko: { label: '한국어', htmlLang: 'ko', home: 'LinkGuard — 재난 수색 구조 시스템', toastOk: '이메일 주소를 복사했습니다: ', toastFail: '이메일 주소를 복사하지 못했습니다' }
  };
  var VERSION = '2';
  var root = document.documentElement;
  var dicts = {};
  var current = null;          // 'ja' | 'ko' | null
  var done = new WeakSet();    // .l-en elements already given clones
  var observer = null;

  function stored() {
    try { var v = localStorage.getItem(KEY); return LANGS[v] ? v : null; } catch (e) { return null; }
  }
  function store(v) {
    try { if (v) localStorage.setItem(KEY, v); else localStorage.removeItem(KEY); } catch (e) {}
  }

  // Hide text briefly while a saved ja/ko dictionary loads, to avoid a flash of zh/en.
  var initial = stored();
  if (initial) {
    root.classList.add('lg-xl-pending');
    setTimeout(function () { root.classList.remove('lg-xl-pending'); }, 2500);
  }

  function norm(s) { return (s || '').replace(/\s+/g, ' ').trim(); }

  function load(lang) {
    if (dicts[lang]) return Promise.resolve(dicts[lang]);
    return fetch('i18n/' + lang + '.json?v=' + VERSION, { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { dicts[lang] = d; return d; });
  }

  function cloneFor(el, lang, dict) {
    var c = el.cloneNode(false);
    var cls = (c.getAttribute('class') || '').replace(/\bl-en\b/, 'l-' + lang);
    c.setAttribute('class', cls);
    c.removeAttribute('id');
    // Entrance-animation classes are driven by observers that never see clones.
    if (c.classList.contains('reveal')) c.classList.add('in');
    if (c.classList.contains('lg-r')) c.classList.add('lg-in');
    c.setAttribute('lang', LANGS[lang].htmlLang);
    var t = dict[norm(el.textContent)];
    if (typeof t === 'string') c.innerHTML = t;
    else { c.innerHTML = el.innerHTML; c.setAttribute('lang', 'en'); c.setAttribute('data-lg-fallback', ''); }
    return c;
  }

  function process(scope) {
    var d = dicts[current];
    if (!d) return;
    var list = [];
    if (scope.nodeType === 1 && scope.classList && scope.classList.contains('l-en')) list.push(scope);
    if (scope.querySelectorAll) list = list.concat(Array.prototype.slice.call(scope.querySelectorAll('.l-en')));
    list.forEach(function (el) {
      if (done.has(el)) return;
      if (el.parentElement && el.parentElement.closest('.l-en')) return;
      done.add(el);
      var anchor = el;
      ['ja', 'ko'].forEach(function (lang) {
        var dict = dicts[lang];
        if (!dict) return;
        var next = anchor.nextElementSibling;
        if (next && next.classList.contains('l-' + lang)) { anchor = next; return; }
        var c = cloneFor(el, lang, dict);
        anchor.insertAdjacentElement('afterend', c);
        anchor = c;
      });
    });
  }

  // Both dictionaries are only needed for the language being shown; clones for the
  // other language are added lazily the first time it is chosen.
  function reprocessAll() {
    Array.prototype.forEach.call(document.querySelectorAll('.l-en'), function (el) {
      var lang = current;
      if (el.parentElement && el.parentElement.closest('.l-en')) return;
      var sib = el.nextElementSibling, has = false;
      while (sib && (sib.classList.contains('l-ja') || sib.classList.contains('l-ko'))) {
        if (sib.classList.contains('l-' + lang)) { has = true; break; }
        sib = sib.nextElementSibling;
      }
      if (!has) done.delete(el);
    });
    process(document.body);
  }

  function setTitle() {
    if (!current) return;
    var active = document.querySelector('.nav-links a[aria-current="page"] .l-' + current);
    var page = document.body && document.body.getAttribute('data-route');
    if (active && page !== 'index') document.title = norm(active.textContent) + ' — LinkGuard';
    else document.title = LANGS[current].home;
  }

  function translateToast(node) {
    if (!current || !node || !node.classList || !node.classList.contains('copy-toast')) return;
    var t = node.textContent || '';
    if (t.indexOf('已複製電子郵件：') === 0) node.textContent = LANGS[current].toastOk + t.slice('已複製電子郵件：'.length);
    else if (t === '無法複製電子郵件') node.textContent = LANGS[current].toastFail;
  }

  function observe() {
    if (observer) return;
    observer = new MutationObserver(function (records) {
      if (!current) return;
      records.forEach(function (r) {
        if (r.type === 'childList') {
          Array.prototype.forEach.call(r.addedNodes, function (n) {
            if (n.nodeType === 1) process(n);
          });
          translateToast(r.target);
        }
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function syncButtons() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-lg-lang]'), function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-lg-lang') === current));
    });
    if (current) {
      Array.prototype.forEach.call(document.querySelectorAll('[data-set-lang]'), function (b) {
        b.setAttribute('aria-pressed', 'false');
      });
    }
    var label = current ? LANGS[current].label : (root.getAttribute('data-lang') === 'en' ? 'EN' : '中文');
    Array.prototype.forEach.call(document.querySelectorAll('.lg-lang-current'), function (s) { s.textContent = label; });
  }

  function apply(lang) {
    current = lang;
    store(lang);
    root.setAttribute('data-lang', lang);
    root.setAttribute('lang', LANGS[lang].htmlLang);
    reprocessAll();
    observe();
    setTitle();
    syncButtons();
    root.classList.remove('lg-xl-pending');
  }

  function choose(lang) {
    root.classList.add('lg-xl-loading');
    load(lang).then(function () { apply(lang); }, function () {
      // Dictionary unavailable (offline, blocked): stay in the current language.
      root.classList.remove('lg-xl-pending');
    }).then(function () { root.classList.remove('lg-xl-loading'); });
  }

  function leave() {
    // Called after the site's own zh/en handler has run.
    current = null;
    store(null);
    syncButtons();
  }

  /* ---------- Language menu (wraps the existing .lang group) ---------- */
  function buildMenu(group, index) {
    if (group.closest('.lg-langmenu')) return;
    var wrap = document.createElement('div');
    wrap.className = 'lg-langmenu';
    group.parentNode.insertBefore(wrap, group);
    var trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'lg-lang-trigger';
    var id = 'lgLangList' + index;
    group.id = group.id || id;
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-controls', group.id);
    trigger.setAttribute('aria-label', 'Language / 語言 / 言語 / 언어');
    trigger.innerHTML = '<svg aria-hidden="true" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="8" cy="8" r="6.2"/><path d="M1.8 8h12.4M8 1.8c1.9 2 2.8 4 2.8 6.2S9.9 12.2 8 14.2C6.1 12.2 5.2 10.2 5.2 8S6.1 3.8 8 1.8z"/></svg><span class="lg-lang-current"></span><svg class="lg-lang-chev" aria-hidden="true" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="m4 6 4 4 4-4"/></svg>';
    wrap.appendChild(trigger);
    wrap.appendChild(group);
    group.classList.add('lg-lang-list');
    ['ja', 'ko'].forEach(function (lang) {
      if (group.querySelector('[data-lg-lang="' + lang + '"]')) return;
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('data-lg-lang', lang);
      b.setAttribute('lang', LANGS[lang].htmlLang);
      b.setAttribute('aria-pressed', 'false');
      b.textContent = LANGS[lang].label;
      b.addEventListener('click', function () { choose(lang); close(); });
      group.appendChild(b);
    });
    Array.prototype.forEach.call(group.querySelectorAll('[data-set-lang]'), function (b) {
      // Runs after the site's own handler (registered earlier), which sets zh/en.
      b.addEventListener('click', function () { leave(); close(); });
    });
    function open() { wrap.classList.add('open'); trigger.setAttribute('aria-expanded', 'true'); }
    function close() { wrap.classList.remove('open'); trigger.setAttribute('aria-expanded', 'false'); }
    trigger.addEventListener('click', function (e) {
      e.stopPropagation();
      if (wrap.classList.contains('open')) close();
      else {
        open();
        var sel = group.querySelector('[aria-pressed="true"]') || group.querySelector('button');
        if (sel && e.detail === 0) sel.focus();
      }
    });
    document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) close(); });
    wrap.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && wrap.classList.contains('open')) { close(); trigger.focus(); }
      if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && wrap.classList.contains('open')) {
        var items = Array.prototype.slice.call(group.querySelectorAll('button'));
        var i = items.indexOf(document.activeElement);
        var n = e.key === 'ArrowDown' ? (i + 1) % items.length : (i - 1 + items.length) % items.length;
        items[n].focus(); e.preventDefault();
      }
    });
    wrap.addEventListener('focusout', function (e) { if (!wrap.contains(e.relatedTarget)) close(); });
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll('.lang'), buildMenu);
    syncButtons();
    if (initial) choose(initial);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
