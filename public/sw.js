const CACHE='rod-assistant-v5-massive';
const ASSETS=['./','./index.html','./config.js','./styles-core.css','./styles-extra.css','./app-core.js','./app-identity.js','./app-cpe-pj.js','./app-batch.js','./app-init.js','./manifest.webmanifest','./rod-icon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request).then(x=>x||caches.match('./index.html'))))});
