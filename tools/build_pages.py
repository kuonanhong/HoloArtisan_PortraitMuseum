#!/usr/bin/env python3
"""Create deployable static site, excluding the desktop neural engine."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1];dest=root/'dist'
if dest.exists():shutil.rmtree(dest)
dest.mkdir()
for name in ['index.html','styles.css','js','assets','data','model','vendor','service-worker.js','manifest.webmanifest','offline-manifest.json','docs']:
    src=root/name
    if not src.exists():continue
    if src.is_dir():shutil.copytree(src,dest/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    else:shutil.copy2(src,dest/name)
(dest/'.nojekyll').touch()
print('Static site:',dest,'bytes:',sum(p.stat().st_size for p in dest.rglob('*') if p.is_file()))
