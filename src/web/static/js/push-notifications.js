// push-notifications.js
document.addEventListener('DOMContentLoaded', function() {
    // Check if push notifications are supported
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        console.log('Push notifications are not supported in this browser');
        disablePushNotifications();
        return;
    }
    
    // Initialize push notifications
    initPushNotifications();
});

function initPushNotifications() {
    // Register service worker
    navigator.serviceWorker.register('/static/js/service-worker.js')
        .then(function(registration) {
            console.log('Service Worker registered with scope:', registration.scope);
            
            // Check if push notifications are enabled
            const pushNotificationsCheckbox = document.getElementById('push_notifications');
            if (pushNotificationsCheckbox && pushNotificationsCheckbox.checked) {
                subscribeToPushNotifications(registration);
            }
            
            // Add event listener to checkbox
            if (pushNotificationsCheckbox) {
                pushNotificationsCheckbox.addEventListener('change', function() {
                    if (this.checked) {
                        subscribeToPushNotifications(registration);
                    } else {
                        unsubscribeFromPushNotifications(registration);
                    }
                });
            }
        })
        .catch(function(error) {
            console.error('Service Worker registration failed:', error);
            disablePushNotifications();
        });
}

function subscribeToPushNotifications(registration) {
    // Check permission
    if (Notification.permission === 'denied') {
        console.log('Push notifications permission denied');
        disablePushNotifications();
        return;
    }
    
    // Request permission if not granted
    if (Notification.permission !== 'granted') {
        Notification.requestPermission().then(function(permission) {
            if (permission !== 'granted') {
                console.log('Push notifications permission not granted');
                disablePushNotifications();
                return;
            }
            
            // Subscribe to push notifications
            subscribeUserToPush(registration);
        });
    } else {
        // Subscribe to push notifications
        subscribeUserToPush(registration);
    }
}

function subscribeUserToPush(registration) {
    // Get server's public key
    fetch('/api/push-public-key')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            const publicKey = data.publicKey;
            
            // Subscribe to push notifications
            return registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(publicKey)
            });
        })
        .then(function(subscription) {
            // Send subscription to server
            return sendSubscriptionToServer(subscription);
        })
        .catch(function(error) {
            console.error('Error subscribing to push notifications:', error);
            disablePushNotifications();
        });
}

function unsubscribeFromPushNotifications(registration) {
    registration.pushManager.getSubscription()
        .then(function(subscription) {
            if (subscription) {
                // Send unsubscription to server
                sendUnsubscriptionToServer(subscription);
                
                // Unsubscribe
                return subscription.unsubscribe();
            }
        })
        .catch(function(error) {
            console.error('Error unsubscribing from push notifications:', error);
        });
}

function sendSubscriptionToServer(subscription) {
    return fetch('/api/push-subscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            subscription: subscription.toJSON()
        })
    });
}

function sendUnsubscriptionToServer(subscription) {
    return fetch('/api/push-unsubscribe', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            subscription: subscription.toJSON()
        })
    });
}

function disablePushNotifications() {
    const pushNotificationsCheckbox = document.getElementById('push_notifications');
    if (pushNotificationsCheckbox) {
        pushNotificationsCheckbox.checked = false;
        pushNotificationsCheckbox.disabled = true;
        
        // Add a note about push notifications not being supported
        const noteElement = document.createElement('small');
        noteElement.className = 'text-muted d-block mt-1';
        noteElement.textContent = 'Push notifications are not supported in this browser.';
        
        const parentElement = pushNotificationsCheckbox.closest('.form-check');
        if (parentElement) {
            parentElement.appendChild(noteElement);
        }
    }
}

// Helper function to convert base64 to Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    
    return outputArray;
}
