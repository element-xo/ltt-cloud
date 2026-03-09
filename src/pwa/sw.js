const CACHE_NAME = 'ltt-lca-v1';

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll([
                '/',
                '/index.html',
                '/manifest.json',
                '/icons/icon-192.png'
            ]);
        })
    );
});

self.addEventListener('fetch', event => {
    if (event.request.url.includes('/api/')) {
        // Network first for API
        event.respondWith(
            fetch(event.request).catch(() => caches.match(event.request))
        );
    } else {
        // Cache first for static
        event.respondWith(
            caches.match(event.request).then(response => {
                return response || fetch(event.request);
            })
        );
    }
});