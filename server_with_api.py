#!/usr/bin/env python3
import http.server
import json
import os
import sys

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class AMISHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == "/api/save-schedule":
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len)
                data = json.loads(post_body.decode('utf-8'))
                
                if not isinstance(data, list) or len(data) < 100:
                    raise ValueError(f"Invalid exam data payload: expected array of >= 100 exams, got {len(data) if isinstance(data, list) else type(data)}")

                json_str = json.dumps(data, indent=2)
                js_str = f"window.AMIS_EXAM_DATA = {json_str};\n"

                # Write to current directory
                target_json = os.path.join(DIRECTORY, "exam_data_2nd_term.json")
                target_js = os.path.join(DIRECTORY, "exam_data_2nd_term.js")
                with open(target_json, "w", encoding="utf-8") as f:
                    f.write(json_str)
                with open(target_js, "w", encoding="utf-8") as f:
                    f.write(js_str)

                # Sync to parent workspace if different
                parent_dir = os.path.dirname(DIRECTORY)
                parent_json = os.path.join(parent_dir, "exam_data_2nd_term.json")
                parent_js = os.path.join(parent_dir, "exam_data_2nd_term.js")
                if os.path.exists(parent_json):
                    with open(parent_json, "w", encoding="utf-8") as f:
                        f.write(json_str)
                if os.path.exists(parent_js):
                    with open(parent_js, "w", encoding="utf-8") as f:
                        f.write(js_str)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {"status": "success", "count": len(data), "message": "Saved to server successfully"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                print(f"[API] Successfully saved {len(data)} exam records to disk.")
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                print(f"[API] Error saving schedule: {e}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        # Disable caching for hot dev
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

if __name__ == "__main__":
    server_address = ("", PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, AMISHandler)
    print(f"AMIS Live Dev & API Server running at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
