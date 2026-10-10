// The dashboard service worker (f12-01): shows notifications and, on a tap,
// opens the dashboard. No fetch handler, no cache, no push.
self.addEventListener("notificationclick", (event) => {
  event.waitUntil(
    (async () => {
      const clients = await self.clients.matchAll({ includeUncontrolled: true });
      for (const client of clients) {
        client.focus();
        return;
      }
      await self.clients.openWindow("/");
    })(),
  );
});
