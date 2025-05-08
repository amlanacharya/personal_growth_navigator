// service-worker.js
self.addEventListener('push', function(event) {
    const data = event.data.json();
    
    const options = {
        body: data.message,
        icon: '/static/img/logo.png',
        badge: '/static/img/badge.png',
        data: {
            url: data.url || '/'
        },
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action) {
        // Handle action button clicks
        const actionUrl = event.notification.data.actionUrls[event.action];
        if (actionUrl) {
            clients.openWindow(actionUrl);
        }
    } else {
        // Handle notification click
        const url = event.notification.data.url;
        event.waitUntil(
            clients.matchAll({type: 'window'}).then(function(clientList) {
                // Check if there's already a window open
                for (let i = 0; i < clientList.length; i++) {
                    const client = clientList[i];
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                // If no window is open, open a new one
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
        );
    }
});
