#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
files=[]
for name in ['index.html','styles.css','js','assets/art','assets/icon.svg','assets/HoloUICJK.woff','model','vendor','manifest.webmanifest']:
 p=root/name
 if not p.exists():continue
 for f in sorted(p.rglob('*')) if p.is_dir() else [p]:
  if f.is_file() and (f.name.startswith('qwen2.5-0.5b-q4km.part') or f.suffix.lower() in ['.html','.css','.js','.json','.jpg','.jpeg','.png','.wasm','.bin','.part','.gguf','.woff','.woff2','.webmanifest','.svg']):
   files.append({'path':f.relative_to(root).as_posix(),'bytes':f.stat().st_size})
(root/'offline-manifest.json').write_text(json.dumps({'version':'20261008-v2','bytes':sum(f['bytes'] for f in files),'files':files},ensure_ascii=False,indent=2))
print('Offline manifest',len(files),'files',sum(f['bytes'] for f in files),'bytes')
