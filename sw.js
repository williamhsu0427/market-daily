// 已停用：舊版註冊過的 service worker 會自行解除
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.registration.unregister());
