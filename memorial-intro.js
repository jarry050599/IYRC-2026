/* 921 Digital Memorial Introduction. Homepage presentation only.
   Reset for another first visit: localStorage.removeItem('linkguard-921-intro'); then reload. */
(function () {
  'use strict';

  var dialog = document.getElementById('memorialIntro');
  var storageKey = 'linkguard-921-intro';
  if (!dialog || typeof dialog.showModal !== 'function') return;

  function wasDismissed() {
    try { return !!window.localStorage.getItem(storageKey); }
    catch (_) {
      try { return !!window.sessionStorage.getItem(storageKey); }
      catch (_) { return false; }
    }
  }
  function rememberDismissal() {
    try { window.localStorage.setItem(storageKey, 'seen'); return; }
    catch (_) {
      try { window.sessionStorage.setItem(storageKey, 'seen'); }
      catch (_) { /* The introduction remains dismissible when storage is unavailable. */ }
    }
  }
  if (wasDismissed()) return;

  var root = document.documentElement;
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var previousFocus = document.activeElement;
  var closing = false;
  var closeTimer = null;
  var elapsed = Math.max(0, new Date().getFullYear() - 1999);

  function chineseYears(number) {
    var digits = '零一二三四五六七八九';
    if (number < 10) return digits[number];
    if (number < 100) {
      return (number >= 20 ? digits[Math.floor(number / 10)] : '') + '十' +
        (number % 10 ? digits[number % 10] : '');
    }
    return String(number);
  }
  dialog.querySelectorAll('[data-memorial-years]').forEach(function (el) { el.textContent = String(elapsed); });
  dialog.querySelectorAll('[data-memorial-years-zh]').forEach(function (el) { el.textContent = chineseYears(elapsed); });

  function syncAccessibleLanguage() {
    var english = root.getAttribute('data-lang') === 'en';
    dialog.querySelector('.memorial-close').setAttribute('aria-label', english ? 'Close memorial introduction' : '關閉紀念視窗');
    dialog.querySelector('.memorial-language').setAttribute('aria-label', english ? 'Language' : '語言');
  }
  syncAccessibleLanguage();
  var languageObserver = new MutationObserver(syncAccessibleLanguage);
  languageObserver.observe(root, { attributes: true, attributeFilter: ['data-lang'] });

  function restorePage() {
    window.clearTimeout(closeTimer);
    root.classList.remove('memorial-open');
    dialog.classList.remove('is-leaving');
    languageObserver.disconnect();
    var destination = previousFocus && previousFocus !== document.body && previousFocus.isConnected
      ? previousFocus : document.getElementById('main-content');
    if (destination) destination.focus({ preventScroll: true });
  }
  function finishDismissal() {
    if (dialog.open) dialog.close();
  }
  function dismiss() {
    if (closing || !dialog.open) return;
    closing = true;
    rememberDismissal();
    if (motion.matches) { finishDismissal(); return; }
    dialog.classList.add('is-leaving');
    // A fallback also releases the page if a browser does not dispatch animationend.
    closeTimer = window.setTimeout(finishDismissal, 600);
  }
  dialog.addEventListener('close', restorePage);
  dialog.addEventListener('animationend', function (event) {
    if (event.target === dialog && event.animationName === 'memorial-exit') finishDismissal();
  });
  dialog.querySelectorAll('[data-memorial-close]').forEach(function (button) {
    button.addEventListener('click', dismiss);
  });
  dialog.addEventListener('cancel', function (event) { event.preventDefault(); dismiss(); });
  dialog.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      dismiss();
      return;
    }
    if (event.key !== 'Tab') return;
    // Keyboard users never have to wait for a staged control to become visible.
    dialog.classList.add('is-keyboard');
    var controls = Array.from(dialog.querySelectorAll('button,a[href],[tabindex="0"]')).filter(function (el) {
      return !el.disabled && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    });
    var first = controls[0], last = controls[controls.length - 1];
    if (!first) { event.preventDefault(); dialog.focus(); return; }
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog)) {
      event.preventDefault(); first.focus();
    }
  }, true);
  motion.addEventListener('change', function () { if (motion.matches && closing) finishDismissal(); });

  // Native modal semantics keep newly parsed/background controls inert without changing their handlers.
  dialog.showModal();
  root.classList.add('memorial-open');
  dialog.focus({ preventScroll: true });
})();
