#!/usr/bin/env python3
"""Serve the entire museum locally with Python's standard library only."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse,functools,webbrowser
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8000);p.add_argument('--lan',action='store_true',help='Allow other devices on your private LAN');p.add_argument('--open',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.wasm':'application/wasm','.mjs':'text/javascript','.gguf':'application/octet-stream','.part':'application/octet-stream'}
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cross-Origin-Opener-Policy','same-origin')
        self.send_header('Cross-Origin-Embedder-Policy','require-corp')
        super().end_headers()
server=ThreadingHTTPServer(('0.0.0.0' if a.lan else '127.0.0.1',a.port),functools.partial(Handler,directory=str(root)))
url=f'http://127.0.0.1:{a.port}/';print(f'Holo-Artisan: {url}\nCtrl+C to stop. No cloud inference.')
if a.open:webbrowser.open(url)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
