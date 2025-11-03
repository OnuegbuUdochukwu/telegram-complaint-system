#!/usr/bin/env python3
"""Simple HTTP receiver that logs JSON POST bodies to a file and returns a mock complaint id.
Run in the project root and it will write to catcher.log.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
from urllib.parse import urlparse

LOG = 'catcher.log'

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length) if length else b''
        try:
            data = json.loads(body.decode('utf-8')) if body else None
        except Exception:
            data = {'raw': body.decode('utf-8', errors='replace')}
        entry = {
            'path': self.path,
            'headers': dict(self.headers),
            'body': data
        }
        with open(LOG, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        # respond with mock complaint id
        resp = {'status': 'received', 'complaint_id': 'CAUGHT-12345'}
        self._set_headers(201)
        self.wfile.write(json.dumps(resp).encode('utf-8'))

    def log_message(self, format, *args):
        # silence default logging
        return

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f'Listening on http://127.0.0.1:{port} (logs -> {LOG})')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down')
        server.server_close()
