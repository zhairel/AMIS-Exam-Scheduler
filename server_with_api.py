#!/usr/bin/env python3
import http.server
import json
import os
import sys
import time

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
LAST_SCHEDULE_UPDATED_AT = int(time.time() * 1000)

class AMISHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        global LAST_SCHEDULE_UPDATED_AT
        clean_path = self.path.split('?')[0].rstrip('/')
        if clean_path in ("/api/save-schedule", "/api/schedule-state", "/api/schedule-sync"):
            try:
                target_json = os.path.join(DIRECTORY, "exam_data_2nd_term.json")
                if not os.path.exists(target_json):
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": False, "error": "Schedule file not found"}).encode('utf-8'))
                    return

                mtime = int(os.path.getmtime(target_json) * 1000)
                if mtime > LAST_SCHEDULE_UPDATED_AT:
                    LAST_SCHEDULE_UPDATED_AT = mtime

                with open(target_json, "r", encoding="utf-8") as f:
                    exams = json.load(f)

                locked_file = os.path.join(DIRECTORY, "locked_sections.json")
                locked_sections = []
                if os.path.exists(locked_file):
                    try:
                        with open(locked_file, "r", encoding="utf-8") as lf:
                            locked_sections = json.load(lf)
                    except:
                        pass

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                res = {
                    "ok": True,
                    "status": "success",
                    "count": len(exams),
                    "updated_at": LAST_SCHEDULE_UPDATED_AT,
                    "schedule": exams,
                    "locked_sections": locked_sections
                }
                self.wfile.write(json.dumps(res).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode('utf-8'))
            return

        super().do_GET()

    def do_POST(self):
        global LAST_SCHEDULE_UPDATED_AT
        clean_path = self.path.split('?')[0].rstrip('/')
        if clean_path in ("/api/save-schedule", "/api/schedule-sync"):
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                post_body = self.rfile.read(content_len)
                body = json.loads(post_body.decode('utf-8'))

                data = None
                updated_at = int(time.time() * 1000)

                if isinstance(body, list):
                    data = body
                elif isinstance(body, dict):
                    data = body.get("schedule") or body.get("data")
                    if body.get("updated_at"):
                        try:
                            updated_at = int(body.get("updated_at"))
                        except (ValueError, TypeError):
                            pass

                has_schedule = isinstance(data, list) and len(data) >= 50
                has_locked = isinstance(body, dict) and "locked_sections" in body and isinstance(body["locked_sections"], list)

                if not has_schedule and not has_locked:
                    raise ValueError("Invalid payload: expected schedule array (>= 50) or locked_sections array")

                if has_schedule:
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

                if has_locked:
                    locked_file = os.path.join(DIRECTORY, "locked_sections.json")
                    with open(locked_file, "w", encoding="utf-8") as lf:
                        json.dump(body["locked_sections"], lf, indent=2)

                LAST_SCHEDULE_UPDATED_AT = max(updated_at, int(time.time() * 1000))

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                response = {
                    "ok": True,
                    "status": "success",
                    "count": len(data) if isinstance(data, list) else 0,
                    "locked_sections_count": len(body["locked_sections"]) if has_locked else 0,
                    "updated_at": LAST_SCHEDULE_UPDATED_AT,
                    "message": "Saved to server successfully"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                records_count = len(data) if isinstance(data, list) else 0
                locks_count = len(body["locked_sections"]) if has_locked else 0
                print(f"[API] Successfully saved {records_count} exam records and {locks_count} locked sections to disk (timestamp: {LAST_SCHEDULE_UPDATED_AT}).")
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "status": "error", "message": str(e)}).encode('utf-8'))
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
