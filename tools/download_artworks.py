#!/usr/bin/env python3
"""Restore the pinned, rights-reviewed 100-painting collection.

Requires Pillow: python -m pip install Pillow
Downloads sequentially with a 1-second pause. Respects provider HTTP 429
by stopping and reporting Retry-After instead of retrying immediately.
The source files are resized without cropping; metadata contains both hashes.
"""
import argparse, hashlib, io, json, time, urllib.request, urllib.error
from pathlib import Path
from PIL import Image, ImageOps
ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data/artworks.json'
UA = 'HoloArtisanPortraitMuseum/2.0 (public-domain educational artwork demo)'

def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(request, timeout=75) as response:
                data = response.read()
            with Image.open(io.BytesIO(data)) as check:
                check.verify()
            return data
        except urllib.error.HTTPError as error:
            if error.code == 429:
                delay = error.headers.get("Retry-After", "the provider-prescribed interval")
                raise RuntimeError(f"Provider rate limit: wait {delay} seconds before restarting. No automatic immediate retry.") from error
            if error.code in (401, 403, 404) or attempt == 2: raise
            time.sleep(2 + 2*attempt)
        except Exception:
            if attempt == 2: raise
            time.sleep(2 + 2*attempt)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='Download even if a verified local asset exists')
    args = parser.parse_args()
    works = json.loads(CATALOG.read_text(encoding='utf-8'))
    assert len(works) == 100
    for index, work in enumerate(works):
        path = ROOT / work['image']
        if path.exists() and not args.force:
            with Image.open(path) as check: check.verify()
            expected = work.get('sha256')
            if expected and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f'Local asset checksum mismatch: {path}; inspect it or use --force to restore.')
            print(f'{index+1:03}/100 verified {work["id"]}', flush=True)
            continue
        data = fetch(work['imageSource'])
        expected_source = work.get("sourceImageSha256")
        if expected_source and hashlib.sha256(data).hexdigest() != expected_source:
            raise ValueError(f"Upstream image changed for {work['id']}; review source rights and metadata before replacing.")
        with Image.open(io.BytesIO(data)) as original:
            im = ImageOps.exif_transpose(original).convert('RGB')
            source_size = list(im.size)
            im.thumbnail((1000,1000), Image.Resampling.LANCZOS)
            path.parent.mkdir(parents=True, exist_ok=True)
            im.save(path, 'JPEG', quality=89, optimize=True)
            work['width'], work['height'] = im.size
        work['sourceImageSha256'] = hashlib.sha256(data).hexdigest()
        work['sourceImageSize'] = source_size
        work['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        work['bytes'] = path.stat().st_size
        work['modifications'] = 'Proportional downsize to <=1000 px long edge and JPEG recompression. No crop, color edit, AI redraw or watermark removal.'
        CATALOG.write_text(json.dumps(works, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'{index+1:03}/100 saved {work["id"]}: {work["bytes"]} bytes', flush=True)
        time.sleep(1.05)
    (ROOT/'js/artworks.js').write_text('// Local public-domain museum collection. See data/artworks.json and docs/ARTWORK_RIGHTS.md.\nwindow.HOLO_ARTWORKS = '+json.dumps(works, ensure_ascii=False,separators=(',',':'))+';\n', encoding='utf-8')
    print('100 verified real paintings; catalog refreshed.', flush=True)

if __name__ == '__main__': main()
