/* Holo-Artisan Portrait Museum — actual local Qwen generation, MIT adapter. */
(function (global) {
  'use strict';
  const scriptURL = document.currentScript?.src || new URL('js/generator.js', location.href).href;
  const base = new URL('../', scriptURL);
  const MODEL = 'Qwen2.5-0.5B-Instruct Q4_K_M';
  let runtime = null, loadPromise = null, controller = null, toTraditional = value => value;
  let state = { status: 'unloaded', ready: false, model: MODEL, backend: 'llama.cpp / WebAssembly CPU', gpu: false, threads: 1, bytes: 491400032, error: null, generations: 0 };
  const emotions = ['joy','anger','sadness','delight'];
  const gestures = ['smile','nod','listen','reassure','wonder'];
  const localeNames = {'zh-TW':'Traditional Chinese','zh-CN':'Simplified Chinese',en:'English',ja:'Japanese',ko:'Korean',es:'Spanish'};
  const schema = {type:'object',properties:{text:{type:'string'},emotion:{type:'string',enum:emotions},gesture:{type:'string',enum:gestures}},required:['text','emotion','gesture'],additionalProperties:false};
  const hex = bytes => Array.from(new Uint8Array(bytes), n => n.toString(16).padStart(2,'0')).join('');
  const limit = (v,n=280) => String(v == null ? '' : v).replace(/<\|[^>]*\|>/g,'').slice(0,n);
  function info() { return {...state}; }
  function report(cb, stage, loaded=0, total=state.bytes) {
    if (cb) cb({stage,loaded,total,percent:Math.round(100*loaded/Math.max(1,total)),model:MODEL});
  }
  async function load(progressCb) {
    if (state.ready) { report(progressCb,'ready',state.bytes); return info(); }
    if (loadPromise) return loadPromise;
    loadPromise = (async () => {
      if (location.protocol === 'file:') throw new Error('LOCAL_HTTP_REQUIRED: Start tools/serve.py and open http://localhost:8000. Browser workers cannot read model files through file://.');
      if (!global.WebAssembly) throw new Error('WEBASSEMBLY_UNAVAILABLE');
      state.status='loading'; state.error=null;
      report(progressCb,'runtime');
      await import(new URL('vendor/model-opencc.js',base).href);
      if(global.OpenCC) toTraditional=global.OpenCC.Converter({from:'cn',to:'tw'});
      const {Wllama} = await import(new URL('vendor/model-wllama/esm/index.js',base).href);
      const manifestResponse = await fetch(new URL('model/manifest.json',base));
      if (!manifestResponse.ok) throw new Error('MODEL_MANIFEST_MISSING: keep the model folder beside index.html.');
      const manifest = await manifestResponse.json();
      const parts = []; let loaded=0;
      for (const part of manifest.parts) {
        const response = await fetch(new URL('model/'+part.file,base));
        if (!response.ok) throw new Error('MODEL_PART_MISSING: '+part.file);
        const buffer = await response.arrayBuffer();
        if (buffer.byteLength !== part.bytes) throw new Error('MODEL_PART_SIZE_MISMATCH: '+part.file);
        // Integrity checks are mandatory on HTTPS / localhost (Web Crypto secure contexts).
        if (global.crypto?.subtle) {
          const sha = hex(await crypto.subtle.digest('SHA-256',buffer));
          if (sha!==part.sha256) throw new Error('MODEL_PART_SHA256_MISMATCH: '+part.file);
        }
        parts.push(new Blob([buffer])); loaded+=part.bytes; report(progressCb,'weights',loaded,manifest.bytes);
      }
      const modelBlob = new Blob(parts,{type:'application/octet-stream'});
      if (modelBlob.size!==manifest.bytes) throw new Error('MODEL_SIZE_MISMATCH');
      runtime = new Wllama({default:new URL('vendor/model-wllama/esm/wasm/wllama.wasm',base).href},{suppressNativeLog:true,logger:{debug(){},log(){},warn(...a){console.warn(...a)},error(...a){console.error(...a)}}});
      // Self-host Safari compatibility assets; never fetch the default CDN. GPU is disabled below.
      runtime.setCompat({wasm:new URL('vendor/model-wllama-compat/wasm/wllama.wasm',base).href,worker:new URL('vendor/model-wllama-compat/wasm/wllama.js',base).href});
      report(progressCb,'initializing',manifest.bytes);
      const threads=global.crossOriginIsolated && typeof global.SharedArrayBuffer!=='undefined' ? Math.max(1,Math.min(4,navigator.hardwareConcurrency||1)) : 1;
      state.threads=threads;
      await runtime.loadModel([modelBlob],{n_ctx:1024,n_batch:128,n_ubatch:128,n_threads:threads,n_gpu_layers:0,offload_kqv:false,no_kv_offload:true,n_parallel:1,jinja:true,warmup:false,seed:42});
      state={...state,status:'ready',ready:true,error:null,bytes:manifest.bytes,runtimeVersion:'3.8.1',libllama:Wllama.getLibllamaVersion(),integrityChecked:Boolean(global.crypto?.subtle)};
      report(progressCb,'ready',manifest.bytes); return info();
    })().catch(error => {state.status='error';state.error=String(error.message||error);state.ready=false;loadPromise=null;throw error;});
    return loadPromise;
  }
  function buildMessages(input={}) {
    const art=input.artwork||{};
    const title=typeof art.title==='object' ? (art.title[input.language]||art.title.en||art.title['zh-TW']||JSON.stringify(art.title)) : art.title;
    const language=localeNames[input.language]||localeNames[String(input.language||'').split('-')[0]]||'Traditional Chinese';
    const gaze=input.gaze||{};
    const x=Number(gaze.x ?? gaze.u ?? gaze.gazeU ?? 0.5), y=Number(gaze.y ?? gaze.v ?? gaze.gazeV ?? 0.5);
    const region=limit(gaze.label || gaze.region || gaze.target || (y<.35?'upper area':y>.7?'lower area':x<.35?'left area':x>.65?'right area':'center'),70);
    const emotion=limit(input.emotion||'joy',40);
    if (String(input.language||'zh-TW').startsWith('zh')) {
      return [
        {role:'system',content:`你是畫作《${limit(title||'人物畫',80)}》中的人物。用第一人稱和觀眾直接對話，以繁體中文回答他的問題。請提到你的${region}，說一句溫暖安慰的話。不要複述問題，不要說座標。這是虛構對話。`},
        {role:'user',content:`觀眾心情：${emotion}。觀眾注視：${region}，位置${x.toFixed(2)},${y.toFixed(2)}。觀眾的問題：${limit(input.utterance,200)}`}
      ];
    }
    return [
      {role:'system',content:`You are the painted person in ${limit(title||'Portrait',100)}. Answer the visitor directly in ${language}, using first person. Mention your ${region} and offer a warm, kind reply in one sentence under25 words. Do not repeat the question or say coordinates. Fictional conversation.`},
      {role:'user',content:`Visitor mood: ${emotion}. Gaze: ${region} (x=${x.toFixed(2)},y=${y.toFixed(2)}). Visitor question: ${limit(input.utterance,220)}`}
    ];
  }
  function partialText(raw) {
    const m=raw.match(/"text"\s*:\s*"((?:[^"\\]|\\.)*)/s);
    if (!m) return '';
    return m[1].replace(/\\n/g,'\n').replace(/\\"/g,'"').replace(/\\\\/g,'\\');
  }
  async function generate(input, onToken) {
    if (!state.ready || !runtime) throw new Error('MODEL_NOT_LOADED');
    if (state.status==='generating') throw new Error('GENERATION_BUSY');
    if (!String(input?.utterance||'').trim()) throw new Error('UTTERANCE_REQUIRED');
    controller=new AbortController(); state.status='generating';state.error=null;
    const started=performance.now();let raw='',usage=null,lastText='';
    try {
      const messages=buildMessages(input);
      // A single first-person pronoun is a decoding constraint, not a prepared reply.
      const chinese=String(input.language||'zh-TW').startsWith('zh');
      const prefix=chinese?'我':({en:'I',ja:'私',ko:'저',es:'Yo'}[input.language]);
      const grammar=prefix?'root ::= '+JSON.stringify(prefix)+' [^\\n]*':undefined;
      let rawText='';
      await runtime.createChatCompletion({messages,max_tokens:72,temperature:0.2,top_k:30,top_p:0.9,seed:42,cache_prompt:true,abortSignal:controller.signal,grammar,stream:true,onData(chunk){
        rawText+=chunk.choices?.[0]?.delta?.content||'';
        const current=input.language==='zh-TW'?toTraditional(rawText):rawText;
        if(current!==lastText){lastText=current;if(onToken)onToken(current);}
      }});
      const text=rawText.trim();
      if(!text)throw new Error('MODEL_EMPTY_REPLY');
      const controlSchema={type:'object',properties:{emotion:{type:'string',enum:emotions},gesture:{type:'string',enum:gestures}},required:['emotion','gesture'],additionalProperties:false};
      const controls=await runtime.createChatCompletion({messages:[{role:'system',content:'Choose the portrait response emotion and gesture for its spoken reply. Output JSON only.'},{role:'user',content:`Visitor feels ${limit(input.emotion,40)}. Portrait says: ${text}`}],max_tokens:40,temperature:0.4,seed:42,cache_prompt:true,abortSignal:controller.signal,response_format:{type:'json_schema',json_schema:{name:'portrait_controls',strict:true,schema:controlSchema}}});
      const rawControls=controls.choices?.[0]?.message?.content||'';
      const result=JSON.parse(rawControls);
      if(!emotions.includes(result.emotion)||!gestures.includes(result.gesture))throw new Error('MODEL_OUTPUT_SCHEMA_INVALID');
      state.status='ready';state.generations++;
      return {...result,text:limit(input.language==='zh-TW'?toTraditional(text):text,600),source:'local-llm',model:MODEL,backend:'wasm-cpu',elapsedMs:Math.round(performance.now()-started),usage:controls.usage,raw:JSON.stringify({text,emotion:result.emotion,gesture:result.gesture}),rawText,rawControls,generationPasses:2,visualMode:'portrait-animation',inputContext:{emotion:input.emotion,gaze:input.gaze,utterance:input.utterance,artworkId:input.artwork?.id}};
    } catch(error){state.status='ready';state.error=String(error.message||error);throw error;} finally {controller=null;}
  }
  function cancel(){ if(controller)controller.abort(); }
  global.HoloGenerator={load,generate,info,cancel,buildMessages};
})(window);
