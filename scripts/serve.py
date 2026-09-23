#!/usr/bin/env python3
"""Local preview with byte-range support for video seeking."""
import argparse
import os
from pathlib import Path
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from urllib.parse import urlsplit, unquote


class MediaHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.allowed_request():
            super().do_GET()

    def do_HEAD(self):
        if self.allowed_request():
            super().do_HEAD()

    def allowed_request(self):
        # Reject DNS-rebinding hosts and never serve dotfiles or links outside the site.
        try:
            host = urlsplit('//' + self.headers.get('Host', '')).hostname
            requested = unquote(urlsplit(self.path).path)
            root = Path(self.directory).resolve()
            path = Path(self.translate_path(self.path)).resolve()
            allowed = host in {'localhost', '127.0.0.1', '::1'} and path.is_relative_to(root)
            allowed = allowed and not any(part.startswith('.') for part in Path(requested).parts)
            allowed = allowed and not any(part.startswith('.') for part in path.relative_to(root).parts)
        except (ValueError, OSError):
            allowed = False
        if not allowed:
            self.send_error(403, 'Forbidden')
        return allowed

    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')
        return None

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def send_head(self):
        self.remaining = None
        path = self.translate_path(self.path)
        header = self.headers.get('Range')
        if not header or not os.path.isfile(path) or self.headers.get('If-Range'):
            return super().send_head()
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', header.strip())
        if not match or not any(match.groups()):
            return super().send_head()
        try:
            stream = open(path, 'rb')
        except OSError:
            self.send_error(404, 'File not found')
            return None
        size = os.fstat(stream.fileno()).st_size
        first, last = match.groups()
        start = int(first) if first else max(0, size - int(last))
        end = min(int(last), size - 1) if first and last else size - 1
        if start >= size or start > end:
            stream.close()
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Last-Modified', self.date_time_string(os.fstat(stream.fileno()).st_mtime))
        self.end_headers()
        stream.seek(start)
        self.remaining = end - start + 1
        return stream

    def copyfile(self, source, outputfile):
        try:
            if self.remaining is None:
                return super().copyfile(source, outputfile)
            while self.remaining:
                block = source.read(min(256 * 1024, self.remaining))
                if not block:
                    break
                outputfile.write(block)
                self.remaining -= len(block)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Browsers cancel old requests when seeking.


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'site')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(MediaHandler, directory=str(args.directory)))
    print(f'Preview: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
