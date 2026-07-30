const CACHE_NAME = "linkguard-site-v1";
const OFFLINE_ASSETS = [
  "./LinkGuard-%E7%B6%B2%E7%AB%99%E5%82%99%E4%BB%BD.html",
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
          cached || caches.match("./LinkGuard-%E7%B6%B2%E7%AB%99%E5%82%99%E4%BB%BD.html")
        )
      )
  );
});
