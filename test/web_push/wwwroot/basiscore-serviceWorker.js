self.addEventListener("push", function (e) {
  const message = e.data ? e.data.json() : { message: "Standard Message" };
  clients.matchAll({ includeUncontrolled: true }).then(function (allClients) {
    if (allClients.length > 0) {
      for (const client of allClients) {
        client.postMessage(message);
      }
    } else {
      const options = {
        body: message.offlineMessage ?? e.data.text(),
        vibrate: [100, 50, 100],
        data: message,
        actions: [
          {
            action: "close",
            title: "Ignore",
          },
        ],
      };
      if (message.url) {
        options.actions.push({
          action: "explore",
          title: "Visit",
        });
      }
      e.waitUntil(
        self.registration.showNotification("Push Notification", options)
      );
    }
  });
});
self.addEventListener("notificationclick", function (e) {
  const notification = e.notification;
  const action = e.action;
  console.log(e.data);
  if (action === "explore") {
    clients.openWindow(e.data.url).then((x) => notification.close());
  } else {
    notification.close();
  }
});
