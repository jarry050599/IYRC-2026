/* LinkGuard independent topic pages and compatibility for existing bookmarks. */
(function () {
  'use strict';
  var ownerForId = {
  "a-firmware-flow": "technical.html",
  "a-fw": "technical.html",
  "a-packet": "technical.html",
  "a-radio": "technical.html",
  "a-schedule": "technical.html",
  "acc": "technical.html",
  "archSimulate": "system.html",
  "architecture": "system.html",
  "arrow": "functionality.html",
  "background": "background.html",
  "compare": "comparison.html",
  "composition": "system.html",
  "data": "data.html",
  "deepdive": "technical.html",
  "diagram": "functionality.html",
  "field": "field.html",
  "functionality": "functionality.html",
  "m-1": "team.html",
  "m-2": "team.html",
  "m-3": "team.html",
  "m-4": "team.html",
  "p-seg1a": "functionality.html",
  "p-seg1b": "functionality.html",
  "p-seg2": "functionality.html",
  "p-seg3": "functionality.html",
  "photoCarouselCount": "field.html",
  "photoCarouselNext": "field.html",
  "photoCarouselPrev": "field.html",
  "photoLightbox": "field.html",
  "photoLightboxImage": "field.html",
  "roadmap": "deployment.html",
  "safe-access": "technical.html",
  "safe-battery": "technical.html",
  "safe-compliance": "technical.html",
  "safe-enclosure": "technical.html",
  "safe-offline": "technical.html",
  "safe-priority": "technical.html",
  "safe-tolerance": "technical.html",
  "safety": "technical.html",
  "safetyAcc": "technical.html",
  "steps": "functionality.html",
  "story": "research.html",
  "summary": "overview.html",
  "team": "team.html",
  "team-grid": "team.html",
  "top": "index.html",
  "u-cmd": "system.html",
  "u-rr": "system.html",
  "u-sbn": "system.html",
  "u-sen": "system.html",
  "u-uav": "system.html",
  "u-ugv": "system.html",
  "units": "system.html",
  "video": "field.html",
  "videoPlay": "field.html"
};
  function followExistingBookmark() {
    if (!window.location.hash) return false;
    var id;
    try { id = decodeURIComponent(window.location.hash.slice(1)); } catch (error) { return false; }
    if (document.getElementById(id)) return false;
    var owner = ownerForId[id];
    var currentFile = window.location.pathname.split('/').pop() || 'index.html';
    if (typeof owner !== 'string' || owner === currentFile) return false;
    window.location.replace(owner + window.location.search + window.location.hash);
    return true;
  }
  if (followExistingBookmark()) return;
  window.addEventListener('hashchange', followExistingBookmark);

  function updatePageTitle() {
    var active = document.querySelector('.nav-links a[aria-current="page"]');
    if (!active) return;
    var language = document.documentElement.getAttribute('data-lang') === 'en' ? 'en' : 'zh';
    var label = active.querySelector('.l-' + language);
    if (label) document.title = label.textContent.trim() + ' — LinkGuard';
  }
  updatePageTitle();
  document.querySelectorAll('[data-set-lang]').forEach(function (button) {
    button.addEventListener('click', updatePageTitle);
  });
})();
