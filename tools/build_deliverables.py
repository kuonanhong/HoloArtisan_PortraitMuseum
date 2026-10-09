#!/usr/bin/env python3
"""Build the visual single-file HTML plus two complete, portable ZIP parts."""
from pathlib import Path
import base64,json,re,hashlib,zipfile
root=Path(__file__).resolve().parents[1];out=root.parent/'output';out.mkdir(exist_ok=True)
s=(root/'index.html').read_text();css=(root/'styles.css').read_text()
for match in list(re.finditer(r"url\(['\"]?(assets/[^)'\"]+)['\"]?\)",css)):
 p=root/match[1]
 if p.exists():css=css.replace(match[0],"url('data:font/woff;base64,"+base64.b64encode(p.read_bytes()).decode()+"')")
s=s.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>')
s=s.replace('<link rel="manifest" href="manifest.webmanifest">','')
art=json.loads((root/'data/artworks.json').read_text())
for a in art:a['image']='data:image/jpeg;base64,'+base64.b64encode((root/a['image']).read_bytes()).decode()
def embed(m):
 name=m[1]
 if name=='js/artworks.js':text='window.HOLO_ARTWORKS='+json.dumps(art,ensure_ascii=False,separators=(',',':'))+';'
 elif name=='js/offline.js':return ''
 else:text=(root/name).read_text()
 return '<script>\n'+text.replace('</script','<\\/script')+'\n</script>'
s=re.sub(r'<script src="([^"]+)"></script>',embed,s)
banner='<aside style="padding:12px 20px;text-align:center;background:#244d40;color:#fff;font:14px/1.6 system-ui">完整 AI：請解壓附件並啟動本機網站，再載入模型。此單檔已內含 100 幅畫，可直接瀏覽與操作。 / Full AI: launch the extracted package through its local server.</aside>'
s=s.replace('<body>','<body>'+banner)
s=s.replace('href="docs/guide.html"','href="#offlineInstructions"')
readme=(root/'README.md').read_text();import html
s=s.replace('</body>','<details id="offlineInstructions" style="margin:30px auto;padding:20px;max-width:1100px"><summary>使用與部署說明 / Setup guide</summary><pre style="white-space:pre-wrap;line-height:1.8">'+html.escape(readme)+'</pre></details></body>')
(out/'HoloArtisan_APR_Offline.html').write_text(s)
# Create checksums only for actual package members (not generated dist or runtime caches).
def useful(p):return p.is_file() and not any(part in ('__pycache__','.venv','dist','.git') for part in p.relative_to(root).parts) and p.suffix not in ('.pyc','.zip') and not p.name.endswith('.part')
files=[p for p in sorted(root.rglob('*')) if useful(p) and p.name!='PACKAGE_MANIFEST.json']
manifest={'project':'Holo-Artisan Portrait Museum v2','built':'2026-10-08','files':[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(root/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
files.append(root/'PACKAGE_MANIFEST.json')
def pack(name,select):
 with zipfile.ZipFile(out/name,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
  for p in files:
   if select(p.relative_to(root).as_posix()):z.write(p,root.name+'/'+p.relative_to(root).as_posix())
 print(name,(out/name).stat().st_size)
pack('HoloArtisan_APR_FullPackage.zip',lambda p:not p.startswith('optional-image-engine/weights/'))
pack('HoloArtisan_NeuralPortrait_Addon.zip',lambda p:p.startswith('optional-image-engine/'))
print('Single HTML',(out/'HoloArtisan_APR_Offline.html').stat().st_size)
