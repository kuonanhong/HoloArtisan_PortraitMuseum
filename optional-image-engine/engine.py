"""CPU-only LivePortrait portrait synthesis. No face detector, cloud, or GPU.

Uses official pretrained networks and MIT expressive controls from LivePortrait.
The caller supplies a normalized face rectangle; this avoids InsightFace weights.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image, ImageOps
import torch

from liveportrait.modules.appearance_feature_extractor import AppearanceFeatureExtractor
from liveportrait.modules.motion_extractor import MotionExtractor
from liveportrait.modules.warping_network import WarpingNetwork
from liveportrait.modules.spade_generator import SPADEDecoder
from liveportrait.camera import headpose_pred_to_degree, get_rotation_matrix

ROOT = Path(__file__).resolve().parent
MAX_IMAGE_BYTES = 5 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 16_000_000


def number(value, default, low, high):
    try:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError()
    except (ValueError, TypeError):
        result = default
    return max(low, min(high, result))


def decode_image(value):
    if not isinstance(value, str) or not value.startswith(('data:image/jpeg;base64,', 'data:image/png;base64,', 'data:image/webp;base64,')):
        raise ValueError('image must be a JPEG, PNG, or WebP base64 data URL')
    raw = base64.b64decode(value.split(',', 1)[1], validate=True)
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError('Image exceeds 5 MiB')
    im = Image.open(io.BytesIO(raw))
    if im.width * im.height > 16_000_000:
        raise ValueError('Image exceeds 16 megapixels')
    im = ImageOps.exif_transpose(im).convert('RGB')
    im.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    return im


def face_crop(image, box):
    """Expand a facial bounding box to a square head crop suitable for the net."""
    if isinstance(box, dict):
        box = [box.get(k) for k in ('x', 'y', 'w', 'h')]
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        box = [.3, .16, .4, .4]
    x, y, w, h = [number(v, d, 0, 1) for v, d in zip(box, [.3, .16, .4, .4])]
    if w < .03 or h < .03:
        raise ValueError('faceBox must have nonzero width and height')
    iw, ih = image.size
    # Include hair and shoulders, keeping the face near the upper center.
    side = max(w * iw * 1.8, h * ih * 1.7)
    side = min(side, iw, ih)
    cx, cy = (x + w / 2) * iw, (y + h / 2 + h * .06) * ih
    left = max(0, min(iw - side, cx - side / 2))
    top = max(0, min(ih - side, cy - side / 2))
    rect = tuple(int(round(v)) for v in (left, top, left + side, top + side))
    return image.crop(rect), rect


class PortraitEngine:
    def __init__(self, threads=4):
        torch.set_num_threads(max(1, min(threads, 8)))
        self.device = torch.device('cpu')
        self.models = {}
        configs = {
            'appearance_feature_extractor': (AppearanceFeatureExtractor, dict(image_channel=3, block_expansion=64, num_down_blocks=2, max_features=512, reshape_channel=32, reshape_depth=16, num_resblocks=6)),
            'motion_extractor': (MotionExtractor, dict(num_kp=21, backbone='convnextv2_tiny')),
            'warping_module': (WarpingNetwork, dict(num_kp=21, block_expansion=64, max_features=512, num_down_blocks=2, reshape_channel=32, estimate_occlusion_map=True, dense_motion_params=dict(block_expansion=32, max_features=1024, num_blocks=5, reshape_depth=16, compress=4))),
            'spade_generator': (SPADEDecoder, dict(upscale=2, block_expansion=64, max_features=512, num_down_blocks=2)),
        }
        manifest = json.loads((ROOT / 'weights-manifest.json').read_text())
        for name, (cls, cfg) in configs.items():
            path = ROOT / 'weights' / (name + '.pth')
            expected = next(f for f in manifest['files'] if f['file'] == 'weights/' + path.name)
            if path.stat().st_size != expected['size']:
                raise ValueError('Weight size mismatch: ' + path.name)
            with path.open('rb') as fh:
                if hashlib.file_digest(fh, 'sha256').hexdigest() != expected['sha256']:
                    raise ValueError('Weight checksum mismatch: ' + path.name)
            model = cls(**cfg)
            weights = torch.load(path, map_location='cpu', weights_only=True)
            model.load_state_dict(weights)
            self.models[name] = model.eval().to(self.device)
        self.cached = None

    @torch.inference_mode()
    def respond(self, payload):
        started = time.perf_counter()
        original = decode_image(payload.get('image'))
        crop, rect = face_crop(original, payload.get('faceBox'))
        crop_small = crop.resize((256, 256), Image.Resampling.LANCZOS)
        cache_key = hashlib.sha256(crop_small.tobytes()).hexdigest()
        if self.cached is not None and self.cached[0] == cache_key:
            info, feature, source_keypoints = self.cached[1:]
        else:
            tensor = torch.from_numpy(np.asarray(crop_small, dtype=np.float32).copy() / 255).permute(2, 0, 1).unsqueeze(0)
            info = self.models['motion_extractor'](tensor)
            for name in ['pitch', 'yaw', 'roll']:
                info[name] = headpose_pred_to_degree(info[name]).reshape(1, 1)
            info['kp'] = info['kp'].reshape(1, 21, 3)
            info['exp'] = info['exp'].reshape(1, 21, 3)
            rotation = get_rotation_matrix(info['pitch'], info['yaw'], info['roll'])
            source_keypoints = info['scale'][..., None] * (info['kp'] @ rotation + info['exp'])
            source_keypoints[:, :, :2] += info['t'][:, None, :2]
            feature = self.models['appearance_feature_extractor'](tensor)
            self.cached = (cache_key, info, feature, source_keypoints)

        emotion = payload.get('emotion', 'joy')
        aliases = {'happy': 'joy', 'sad': 'sadness', 'angry': 'anger', 'excited': 'delight', '喜': 'joy', '怒': 'anger', '哀': 'sadness', '樂': 'delight'}
        emotion = aliases.get(emotion, emotion)
        smiles = {'joy': .8, 'anger': -.35, 'sadness': -.4, 'delight': 1.2}
        brows = {'joy': .5, 'anger': -8, 'sadness': 5, 'delight': 2}
        intensity = number(payload.get('intensity'), .8, 0, 1)
        smile, brow = smiles.get(emotion, .4) * intensity, brows.get(emotion, 0) * intensity
        gaze = payload.get('gaze') or {}
        if not isinstance(gaze, dict):
            raise ValueError('gaze must be an object')
        gx = (number(gaze.get('x'), .5, 0, 1) - .5) * 2
        gy = (number(gaze.get('y'), .5, 0, 1) - .5) * 2
        dialogue = str(payload.get('dialogue', ''))[:2000]
        # Generated text drives a bounded speaking pose. This is not phoneme lip sync.
        mouth = (min(len(dialogue), 120) / 120 * 1.6 + (.45 if '?' in dialogue or '？' in dialogue else 0)) * intensity
        delta = info['exp'].clone()
        for idx, axis, factor in [(20,1,-.01),(14,1,-.02),(17,1,.0065),(17,2,.003),(13,1,-.00275),(16,1,-.00275),(3,1,-.0035),(7,1,-.0035)]:
            delta[0, idx, axis] += smile * factor
        if brow > 0:
            delta[0,1,1] += brow * .001
            delta[0,2,1] -= brow * .001
        else:
            delta[0,1,0] -= brow * .001
            delta[0,2,0] += brow * .001
            delta[0,1,1] += brow * .0003
            delta[0,2,1] -= brow * .0003
        ex, ey = gx * 5, gy * -4
        delta[0,11,0] += ex * (.0007 if ex > 0 else .001)
        delta[0,15,0] += ex * (.001 if ex > 0 else .0007)
        for idx in (11,15):
            delta[0,idx,1] -= ey * .0005
        for idx in (13,16):
            delta[0,idx,1] -= ey * .00015
        delta[0,19,1] += mouth * .001
        delta[0,19,2] += mouth * .0001
        delta[0,17,1] -= mouth * .0001
        rotation = get_rotation_matrix(info['pitch'] + gy * 4, info['yaw'] + gx * 6, info['roll'])
        driving = info['scale'][..., None] * (info['kp'] @ rotation + delta)
        driving[:, :, :2] += info['t'][:, None, :2]
        warped = self.models['warping_module'](feature, kp_driving=driving, kp_source=source_keypoints)
        generated = self.models['spade_generator'](warped['out'])
        rgb = np.clip(generated[0].permute(1,2,0).numpy() * 255, 0, 255).astype(np.uint8)
        neural = Image.fromarray(rgb).resize(crop.size, Image.Resampling.LANCZOS)
        # Feather the crop into the unmodified artwork; the portrait interior is neural.
        cw, ch = crop.size
        yy, xx = np.mgrid[0:ch, 0:cw]
        edge = np.minimum.reduce([xx, cw-1-xx, yy, ch-1-yy]).astype(np.float32)
        mask = Image.fromarray(np.uint8(np.clip(edge / (min(cw,ch) * .1), 0, 1) * 255))
        result = original.copy()
        result.paste(neural, (rect[0], rect[1]), mask)
        buffer = io.BytesIO()
        result.save(buffer, format='PNG')
        seconds = time.perf_counter() - started
        return {
            'image': 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii'),
            'seconds': round(seconds, 3), 'engine': 'LivePortrait CPU', 'neural': True,
            'cropPixels': list(rect), 'emotion': emotion,
            'controls': {'smile': smile, 'brow': brow, 'gazeX': gx, 'gazeY': gy, 'mouth': mouth},
            'description': 'Learned feature warping and SPADE portrait synthesis; manually selected face crop; emotion/gaze/dialogue mapped to latent controls. Not diffusion, historical reconstruction, or optical holography.'
        }
