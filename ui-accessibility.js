/* Presentation-only keyboard and focus support. Original application handlers stay intact. */
(function () {
  'use strict';
  var groups = Array.from(document.querySelectorAll('.nav-group'));
  groups.forEach(function (group) {
    group.addEventListener('toggle', function () {
      if (group.open) groups.forEach(function (other) { if (other !== group) other.open = false; });
    });
  });
  document.addEventListener('click', function (event) {
    groups.forEach(function (group) { if (!group.contains(event.target)) group.open = false; });
  });
  function focusables(scope) {
    return Array.from(scope.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex="0"]')).filter(function (el) {
      return !el.disabled && !el.closest('[inert]') && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    });
  }
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      var focusedGroup = groups.find(function (group) { return group.open && group.contains(document.activeElement); });
      groups.forEach(function (group) { group.open = false; });
      if (focusedGroup) focusedGroup.querySelector('summary').focus();
      var menu = document.getElementById('navLinks');
      var toggle = document.getElementById('navToggle');
      if (menu && menu.classList.contains('open') && toggle) { toggle.click(); toggle.focus(); }
    }
    if (event.key !== 'Tab') return;
    var dialog = document.querySelector('.modal.open,.photo-lightbox.open');
    if (!dialog) return;
    var items = focusables(dialog);
    if (!items.length) return;
    var first = items[0], last = items[items.length - 1];
    if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
      event.preventDefault(); first.focus();
    }
  });
  document.querySelectorAll('.card,.member,.acc-item').forEach(function (group) {
    var panel = group.querySelector('.unit-body,.member-body,.acc-body');
    if (!panel) return;
    function sync() { panel.inert = !group.classList.contains('open'); }
    sync();
    new MutationObserver(sync).observe(group, { attributes: true, attributeFilter: ['class'] });
  });
})();
