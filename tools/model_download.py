#!/usr/bin/env python3
"""Fetch and verify pinned upstream Qwen weights; split for normal GitHub commits."""
import hashlib,json,pathlib,urllib.request,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODEL_DIR=ROOT/'model';MODEL_DIR.mkdir(exist_ok=True)
REV='9217f5db79a29953eb74d5343926648285ec7e67'
NAME='qwen2.5-0.5b-instruct-q4_k_m.gguf'
URL=f'https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/{REV}/{NAME}'
EXPECTED='74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db'
SIZE=491400032; CHUNK=64*1024*1024

def main():
    whole=hashlib.sha256();parts=[];total=0;index=0;start=time.time()
    req=urllib.request.Request(URL,headers={'User-Agent':'Holo-Artisan/2.0 academic prototype'})
    with urllib.request.urlopen(req,timeout=180) as r:
        while total<SIZE:
            index+=1;want=min(CHUNK,SIZE-total);buf=bytearray()
            while len(buf)<want:
                data=r.read(min(1024*1024,want-len(buf)))
                if not data: raise RuntimeError('Upstream model download ended early')
                buf.extend(data)
            whole.update(buf);name=f'qwen2.5-0.5b-q4km.part{index:02d}';path=MODEL_DIR/name;path.write_bytes(buf)
            parts.append({'file':name,'bytes':len(buf),'sha256':hashlib.sha256(buf).hexdigest()});total+=len(buf)
            print(f'{total}/{SIZE} bytes ({time.time()-start:.1f}s)',flush=True)
    assert whole.hexdigest()==EXPECTED, 'Model SHA256 mismatch'
    for name in ['LICENSE','README.md']:
        u=f'https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/{REV}/{name}'
        urllib.request.urlretrieve(u,MODEL_DIR/('QWEN-'+name))
    manifest={'model':'Qwen2.5-0.5B-Instruct','variant':'Q4_K_M','parameters':'0.49B','license':'Apache-2.0','upstream':'Qwen/Qwen2.5-0.5B-Instruct-GGUF','revision':REV,'sourceURL':URL,'originalFile':NAME,'bytes':SIZE,'sha256':EXPECTED,'parts':parts,'runtime':{'name':'@wllama/wllama','version':'3.8.1','license':'MIT','gpuLayers':0,'threads':'1, or up to4 when cross-origin isolated'},'note':'Raw byte parts are concatenated into one Blob in the browser; every part is below 100 MB.'}
    (MODEL_DIR/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Pinned model verified; saved manifest.json',flush=True)
if __name__=='__main__':main()
