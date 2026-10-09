#!/usr/bin/env python3
"""Rebuild a pan-CJK font for UI plus generated Chinese/Japanese/Korean text.
Pass a locally downloaded NotoSansCJKjp-Regular.otf from the source manifest.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
import sys,json,hashlib
root=Path(__file__).resolve().parents[1]
p=Path(sys.argv[1]);font=TTFont(p)
for n in font['name'].names:
 if n.nameID in (1,3,4,6):
  text={1:'Holo UI CJK',3:'HoloUICJK-v2-20261008',4:'Holo UI CJK',6:'HoloUICJK-Regular'}[n.nameID]
  n.string=text.encode(n.getEncoding(),errors='replace')
font.flavor='woff';output=root/'assets/HoloUICJK.woff';font.save(output)
(root/'assets/font-source.json').write_text(json.dumps({'source':'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf','license':'SIL Open Font License1.1','licenseUrl':'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE','modification':'Renamed Holo UI CJK; WOFF conversion, complete font retained for dynamic multilingual model output.','sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size},indent=2))
print(output.stat().st_size)
