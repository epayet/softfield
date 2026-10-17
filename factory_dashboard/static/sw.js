// The dashboard service worker (f12-01): shows notifications and, on a tap,
// opens the dashboard. No fetch handler, no cache, no push.
self.addEventListener("notificationclick", (event) => {
  event.notification.close(); // Android keeps a tapped notification otherwise
  const link = event.notification.data && event.notification.data.link;
  event.waitUntil(
    (async () => {
      const clients = await self.clients.matchAll({ includeUncontrolled: true });
      for (const client of clients) {
        await client.focus();
        client.postMessage({ link: link || "/" });
        return;
      }
      const target = link || "/";
      await self.clients.openWindow(target);
    })(),
  );
});
