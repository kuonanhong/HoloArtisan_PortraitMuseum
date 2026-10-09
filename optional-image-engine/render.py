#!/usr/bin/env python3
"""Render one local painting with the optional CPU neural portrait engine."""
import argparse
import base64
import json
from pathlib import Path
from engine import PortraitEngine

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('input', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--face-box', nargs=4, type=float, default=[.3,.16,.4,.4], metavar=('X','Y','W','H'))
parser.add_argument('--emotion', choices=['joy','anger','sadness','delight'], default='joy')
parser.add_argument('--gaze', nargs=2, type=float, default=[.5,.5])
parser.add_argument('--dialogue', default='Hello, welcome to my portrait.')
parser.add_argument('--threads', type=int, default=4)
args = parser.parse_args()
mime = {'.jpg':'jpeg','.jpeg':'jpeg','.png':'png','.webp':'webp'}.get(args.input.suffix.lower())
if mime is None:
    parser.error('Input must be a JPEG, PNG, or WebP')
engine = PortraitEngine(args.threads)
result = engine.respond({'image': 'data:image/'+mime+';base64,'+base64.b64encode(args.input.read_bytes()).decode(), 'faceBox':args.face_box, 'emotion':args.emotion,'gaze':dict(zip(['x','y'],args.gaze)), 'dialogue':args.dialogue})
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(base64.b64decode(result.pop('image').split(',',1)[1]))
print(json.dumps(result, ensure_ascii=False, indent=2))
