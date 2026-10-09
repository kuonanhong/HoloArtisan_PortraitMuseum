#!/usr/bin/env python3
"""Loopback-only CPU portrait API. Run locally; never upload this server to Pages."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlsplit
import time

MAX_BODY = 7 * 1024 * 1024
ENGINE = None
ARGS = None


def allowed_origin(origin):
    if not origin:
        return True  # CLI / native loopback clients.
    try:
        parsed = urlsplit(origin)
        return ((parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost', '[::1]', '::1'})
                or origin == 'https://kuonanhong.github.io')
    except ValueError:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = 'HoloPortraitCPU/2'

    def send_json(self, status, data):
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        origin = self.headers.get('Origin')
        if origin and allowed_origin(origin):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.end_headers()
        self.wfile.write(encoded)

    def authorize(self):
        # Reject web origins outside the museum deployment and local previews.
        if not allowed_origin(self.headers.get('Origin')):
            self.send_json(403, {'error': 'Origin not allowed. Serve the museum on localhost or kuonanhong.github.io.'})
            return False
        try:
            host = urlsplit('http://' + self.headers.get('Host', '')).hostname
        except ValueError:
            host = ''
        if host not in {'127.0.0.1', 'localhost', '::1'}:
            self.send_json(403, {'error': 'Loopback Host required'})
            return False
        return True

    def do_OPTIONS(self):
        if not self.authorize():
            return
        if self.path not in {'/health', '/respond'}:
            self.send_json(404, {'error': 'Not found'})
            return
        self.send_response(204)
        origin = self.headers.get('Origin')
        if origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if not self.authorize():
            return
        if self.path != '/health':
            self.send_json(404, {'error': 'Not found'})
            return
        self.send_json(200, {'ok': True, 'engine': 'LivePortrait', 'device': 'cpu', 'loaded': ENGINE is not None, 'maxImageBytes': 5 * 1024 * 1024, 'version': 2})

    def do_POST(self):
        global ENGINE
        if not self.authorize():
            return
        if self.path != '/respond':
            self.send_json(404, {'error': 'Not found'})
            return
        if self.headers.get_content_type() != 'application/json':
            self.send_json(415, {'error': 'Use application/json'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BODY:
                self.send_json(413, {'error': 'JSON body exceeds 7 MiB'})
                return
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Expected a JSON object')
            if ENGINE is None:
                from engine import PortraitEngine
                ENGINE = PortraitEngine(ARGS.threads)
            result = ENGINE.respond(payload)
            self.send_json(200, result)
        except (ValueError, TypeError, KeyError) as error:
            self.send_json(400, {'error': str(error)})
        except Exception as error:
            print('Inference error:', type(error).__name__, str(error), flush=True)
            self.send_json(500, {'error': 'Portrait inference failed. See the local server terminal.'})


def main():
    global ARGS, ENGINE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', default=8766, type=int)
    parser.add_argument('--threads', default=4, type=int)
    parser.add_argument('--preload', action='store_true')
    ARGS = parser.parse_args()
    if ARGS.preload:
        from engine import PortraitEngine
        started = time.perf_counter()
        ENGINE = PortraitEngine(ARGS.threads)
        print(f'CPU model loaded in {time.perf_counter()-started:.1f}s', flush=True)
    server = HTTPServer(('127.0.0.1', ARGS.port), Handler)
    server.timeout = 120
    print(f'LivePortrait CPU API: http://127.0.0.1:{ARGS.port}', flush=True)
    print('CPU only. Images remain on this machine. Ctrl+C stops.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
