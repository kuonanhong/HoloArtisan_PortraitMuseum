/* Explicit, device-local offline cache. No analytics or external requests. */
const CACHE='holo-portrait-v2-20261008';
self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',event=>{
 const req=event.request,u=new URL(req.url);
 if(req.method!=='GET'||u.origin!==self.location.origin||!u.pathname.startsWith(new URL(self.registration.scope).pathname))return;
 event.respondWith((async()=>{const cache=await caches.open(CACHE);const hit=await cache.match(req);if(hit)return hit;if(req.mode==='navigate'){const index=await cache.match(new URL('index.html',self.registration.scope).href);if(index)return index}return fetch(req)})());
});
self.addEventListener('message',event=>{
 if(event.data?.type!=='CACHE_MUSEUM')return;
 const port=event.ports[0];
 event.waitUntil((async()=>{
  const manifestResponse=await fetch(new URL('offline-manifest.json',self.registration.scope),{cache:'reload'});if(!manifestResponse.ok)throw Error('Offline manifest missing');
  const manifest=await manifestResponse.json(),cache=await caches.open(CACHE);let bytes=0,count=0;
  for(const item of manifest.files){const url=new URL(item.path,self.registration.scope);const old=await cache.match(url.href);if(!old){const response=await fetch(url.href,{cache:'reload'});if(!response.ok)throw Error('Download failed: '+item.path);await cache.put(url.href,response)}bytes+=item.bytes;count++;port.postMessage({type:'progress',bytes,total:manifest.bytes,count,files:manifest.files.length})}
  const root=new URL('index.html',self.registration.scope);const response=await cache.match(root.href);if(response)await cache.put(self.registration.scope,response.clone());
  port.postMessage({type:'done',bytes,count});
 })().catch(e=>port.postMessage({type:'error',message:e.message})));
});
