// Service worker mínimo -- só existe para satisfazer o critério de "instalável"
// dos navegadores. Não guarda cache: o app depende de dados sempre atualizados
// do banco, então cache agressivo faria mais mal do que bem aqui.
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
