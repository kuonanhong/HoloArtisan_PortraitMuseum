(function(){
 const strings={
 'zh-TW':['保存到此瀏覽器，供離線使用（約 560 MB）','準備離線資料…','離線資料已備妥；可斷網重新開啟此網址。','無法完成保存，請改用完整附件的本機啟動方式。','請以完整包的本機網址或 HTTPS 網站開啟，才能保存離線模型。'],
 en:['Save this museum for offline use (~560 MB)','Preparing offline files…','Offline files ready. You can disconnect and reopen this URL.','Offline save failed. Use the full package with the local launcher.','Use the local server or an HTTPS site to save the offline model.'],
 ja:['オフライン用に保存（約560 MB）','保存しています…','保存完了。同じURLをオフラインで開けます。','保存できませんでした。ローカル起動版をご使用ください。','ローカルサーバーまたはHTTPSサイトを開いてください。'],
 ko:['오프라인용 저장 (약560 MB)','오프라인 파일 저장 중…','저장 완료. 연결을 끊고 이 URL을 다시 열 수 있습니다.','저장 실패. 전체 패키지의 로컬 실행기를 사용하세요.','로컬 서버 또는 HTTPS 사이트로 여세요.'],
 es:['Guardar para usar sin conexión (~560 MB)','Preparando archivos…','Listo. Puedes desconectarte y abrir esta URL de nuevo.','No se pudo guardar. Usa el paquete completo con el servidor local.','Abre el servidor local o un sitio HTTPS.']};
 const footer=document.querySelector('footer');if(!footer)return;
 const wrap=document.createElement('div');wrap.style='max-width:1460px;margin:0 auto;padding:16px 5%;font:13px/1.6 system-ui;color:#53635e';
 const b=document.createElement('button');b.type='button';b.id='saveOffline';b.style='padding:10px 15px;border:1px solid #899a90;border-radius:6px;background:transparent;color:inherit;cursor:pointer;min-height:44px';
 const status=document.createElement('span');status.id='offlineStatus';status.setAttribute('role','status');status.style='display:inline-block;margin:8px 12px';wrap.append(b,status);footer.before(wrap);
 const lang=()=>localStorage.getItem('holo-language')||document.documentElement.lang;
 const texts=()=>strings[lang()]||strings[(lang()||'').startsWith('zh')?'zh-TW':lang().split('-')[0]]||strings.en;
 const update=()=>{if(!b.disabled)b.textContent=texts()[0]};update();document.getElementById('language')?.addEventListener('change',()=>setTimeout(update,0));
 let regPromise=null;
 if('serviceWorker' in navigator&&location.protocol!=='file:')regPromise=navigator.serviceWorker.register('service-worker.js').then(()=>navigator.serviceWorker.ready).catch(()=>null);
 b.onclick=async()=>{
  if(!regPromise){status.textContent=texts()[4];return}b.disabled=true;status.textContent=texts()[1];
  try{const reg=await regPromise;if(!reg?.active)throw Error('No service worker');if(navigator.storage?.persist)await navigator.storage.persist();const c=new MessageChannel();c.port1.onmessage=e=>{const d=e.data;if(d.type==='progress')status.textContent=`${Math.round(d.bytes/d.total*100)}% · ${d.count}/${d.files}`;else if(d.type==='done'){status.textContent=texts()[2];b.disabled=false}else{status.textContent=texts()[3]+' '+d.message;b.disabled=false}};reg.active.postMessage({type:'CACHE_MUSEUM'},[c.port2])}catch(e){status.textContent=texts()[3];b.disabled=false}
 };
})();
