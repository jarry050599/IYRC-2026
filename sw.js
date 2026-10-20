const CACHE_NAME = "linkguard-site-v33";
const OFFLINE_ASSETS = [
  "./index.html", "./overview.html", "./background.html", "./functionality.html",
  "./data.html", "./experiments.html", "./comparison.html", "./deployment.html",
  "./site-pages.js", "./system.html", "./research.html", "./field.html",
  "./technical.html", "./team.html", "./awards.html", "./wayfinder-ui.css",
  "./multipage.css", "./site-foundation.css", "./site-layout.css",
  "./site-technical.css", "./design-system.css", "./ui-accessibility.js",
  "./reading-experience.css?v=31", "./reading-experience.js",
  "./premium.css?v=3", "./premium.js",
  "./assets/fonts/inter-latin-wght-normal.woff2", "./assets/fonts/jetbrains-mono-latin-wght-normal.woff2",
  "./manifest.webmanifest", "./assets/linkguard-logo.jpg", "./assets/hero-topo.svg",
  "./assets/linkguard-proposal.pdf"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(fetch(event.request).then((response) => {
    if (!response || response.status !== 200 || response.type === "opaque") return response;
    const copy = response.clone();
    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request).then((cached) => cached || caches.match("./index.html"))));
});
