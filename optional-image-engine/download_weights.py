#!/usr/bin/env python3
"""Repair missing weights from pinned official URLs; validates SHA-256."""
import hashlib
import json
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parent
manifest = json.loads((root/'weights-manifest.json').read_text())
for item in manifest['files']:
    path = root/item['file']
    if path.exists() and path.stat().st_size == item['size']:
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']:
                print('Verified', path.name)
                continue
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.part')
    print('Downloading', path.name, item['size'], 'bytes', flush=True)
    with urllib.request.urlopen(item['url'],timeout=120) as remote, temporary.open('wb') as local:
        while chunk := remote.read(1024*1024):
            local.write(chunk)
    with temporary.open('rb') as stream:
        checksum = hashlib.file_digest(stream,'sha256').hexdigest()
    if checksum != item['sha256'] or temporary.stat().st_size != item['size']:
        raise RuntimeError('Checksum mismatch: '+path.name)
    temporary.replace(path)
    print('Verified',path.name)
