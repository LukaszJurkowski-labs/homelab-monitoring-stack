#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"# HELP uptime_seconds Uptime in seconds\n")
            self.wfile.write(f"uptime_seconds {time.time()}".encode())
            self.wfile.write(b"\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # ciche logi

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), MetricsHandler)
    print("Exporter running on port 8000")
    server.serve_forever()
