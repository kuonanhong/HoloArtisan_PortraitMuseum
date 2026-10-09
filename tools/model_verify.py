#!/usr/bin/env python3
"""Check every bundled Qwen shard and the reconstructed original SHA-256."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((root/'model/manifest.json').read_text())
whole=hashlib.sha256();total=0
for p in m['parts']:
 path=root/'model'/p['file']; h=hashlib.sha256();size=0
 with path.open('rb') as f:
  while data:=f.read(1024*1024):whole.update(data);h.update(data);size+=len(data)
 assert size==p['bytes'] and h.hexdigest()==p['sha256'],f'Mismatch: {path.name}'
 assert size<100*1024*1024,'A shard exceeds GitHub normal-file limit'
 total+=size
assert total==m['bytes'] and whole.hexdigest()==m['sha256'],'Whole model mismatch'
print(json.dumps({'ok':True,'parts':len(m['parts']),'bytes':total,'sha256':whole.hexdigest()}))
