import subprocess
import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

MAIN_SCRIPT = Path(__file__).parent / 'main.py'
server_process = None

class WatcherHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/watcher/status':
            running = server_process and server_process.poll() is None
            self._json(200, {"watcher": "running", "agent": "running" if running else "stopped"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global server_process
        if self.path == '/api/watcher/start':
            if server_process and server_process.poll() is None:
                self._json(200, {"status": "already_running"})
                return
            try:
                server_process = subprocess.Popen(
                    [sys.executable, str(MAIN_SCRIPT)],
                    cwd=str(MAIN_SCRIPT.parent),
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                self._json(200, {"status": "started"})
            except Exception as e:
                self._json(500, {"error": str(e)})
        elif self.path == '/api/watcher/stop':
            if server_process and server_process.poll() is None:
                server_process.terminate()
                server_process = None
                self._json(200, {"status": "stopped"})
            else:
                self._json(200, {"status": "not_running"})
        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    print('PDD Agent Watcher 启动中...')
    print('监听端口: 8766')
    print('扩展可通过此端口控制Agent启动/停止')
    server = HTTPServer(('127.0.0.1', 8766), WatcherHandler)
    server.serve_forever()
