#!/usr/bin/env python3
"""Reproduce the 8-image CPU validation with network connections disabled."""
import base64
import hashlib
import json
from pathlib import Path
import socket

import numpy as np
from PIL import Image
import torch
from engine import PortraitEngine

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'examples' / 'recheck'
OUT.mkdir(parents=True, exist_ok=True)
engine = PortraitEngine(threads=4)


def blocked_network(*args, **kwargs):
    raise RuntimeError('Network access disabled for offline inference validation')


socket.create_connection = blocked_network
results = []
for name, box in [
    ('mona-lisa', [.34, .145, .28, .25]),
    ('girl-pearl-earring', [.31, .28, .33, .33]),
]:
    path = ROOT.parent / 'assets' / 'art' / (name + '.jpg')
    if not path.exists():
        raise SystemExit('Extract the main museum package and CPU add-on into the same parent folder first.')
    original = Image.open(path).convert('RGB')
    hashes = set()
    for emotion, gaze in [('joy', [.5,.5]), ('anger', [.3,.3]), ('sadness', [.4,.7]), ('delight', [.7,.45])]:
        result = engine.respond({
            'image': 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode(),
            'faceBox': box, 'emotion': emotion, 'gaze': dict(zip(['x','y'], gaze)),
            'dialogue': 'You ask about my eyes and my smile. I am listening to you and looking at what you noticed.',
        })
        binary = base64.b64decode(result.pop('image').split(',', 1)[1])
        output = OUT / (name + '-' + emotion + '.png')
        output.write_bytes(binary)
        image = Image.open(output).convert('RGB')
        assert image.size == original.size
        difference = float(np.abs(np.asarray(image).astype(float) - np.asarray(original).astype(float)).mean())
        assert difference > 0
        digest = hashlib.sha256(binary).hexdigest()
        hashes.add(digest)
        result.update(artwork=name, sha256=digest, mean_abs_pixel_difference=difference, offline=True)
        results.append(result)
        print(name, emotion, result['seconds'], 'seconds', flush=True)
    assert len(hashes) == 4, 'Four distinct controls must produce four distinct neural images'
(OUT/'validation.json').write_text(json.dumps({'device':'cpu', 'torch':torch.__version__, 'threads':4, 'results':results}, indent=2))
print('PASS: 8 genuine CPU neural images, offline, original size preserved.')
