const CACHE_NAME = "linkguard-site-v38";
const OFFLINE_ASSETS = [
  "./index.html",
  "./overview.html",
  "./background.html",
  "./functionality.html",
  "./data.html",
  "./experiments.html",
  "./comparison.html",
  "./deployment.html",
  "./site-pages.js",
  "./system.html",
  "./research.html",
  "./field.html",
  "./technical.html",
  "./team.html",
  "./awards.html",
  "./wayfinder-ui.css",
  "./multipage.css",
  "./site-foundation.css",
  "./site-layout.css",
  "./site-technical.css",
  "./design-system.css",
  "./ui-accessibility.js",
  "./reading-experience.css?v=26",
  "./reading-experience.js",
  "./archive-theme.css?v=921-2",
  "./home-hero.css?v=921-6",
  "./assets/archive/taiwan-921-locator.svg",
  "./memorial-intro.css?v=921-5",
  "./memorial-intro.js?v=921-6",
  "./memorial-voice.js?v=921-3",
  "./manifest.webmanifest",
  "./assets/linkguard-logo.jpg",
  "./assets/linkguard-proposal.pdf"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(OFFLINE_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (!response || response.status !== 200 || response.type === "opaque") {
          return response;
        }
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() =>
        caches.match(event.request).then((cached) =>
          cached || caches.match("./index.html")
        )
      )
  );
});
