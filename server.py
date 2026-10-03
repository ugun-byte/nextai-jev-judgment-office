#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NextAI Jev Judgment Office Server
Combines static file serving (HTML/CSS/JS) with Gmail IMAP & Webhook API endpoints.
"""

import sys
import os
import json
import http.server
import socketserver
from gmail_service import GmailService
import ai_service

PORT = 8888
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        pass

gmail_service = GmailService()
inbound_queue = []
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".gmail_config.json")

class NextAIRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local cross-origin development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _read_body_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        if self.path == "/api/health":
            self._send_json({"status": "ok", "server": "NextAI Jev Server", "port": PORT})
            return

        if self.path == "/api/email/config":
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        # Hide actual password in response for safety
                        has_pw = bool(cfg.get("app_password"))
                        self._send_json({
                            "ok": True,
                            "email": cfg.get("email", ""),
                            "has_password": has_pw,
                            "auto_sync": cfg.get("auto_sync", False),
                            "sync_interval": cfg.get("sync_interval", 30),
                            "mark_read": cfg.get("mark_read", False)
                        })
                        return
                except Exception as e:
                    self._send_json({"ok": False, "error": str(e)})
                    return
            self._send_json({"ok": True, "email": "", "has_password": False, "auto_sync": False, "mark_read": False})
            return

        if self.path == "/api/email/queue":
            global inbound_queue
            queued = list(inbound_queue)
            inbound_queue = []
            self._send_json({"ok": True, "emails": queued, "count": len(queued)})
            return

        # Fallback to standard static file serving
        return super().do_GET()

    def do_POST(self):
        # 0. Clear Gmail config
        if self.path == "/api/email/clear_config":
            if os.path.exists(CONFIG_FILE):
                try:
                    os.remove(CONFIG_FILE)
                except Exception:
                    pass
            self._send_json({"ok": True, "message": "Gmail 설정이 초기화되었습니다."})
            return

        # 1. Test Gmail connection
        if self.path == "/api/email/test":
            data = self._read_body_json()
            email_addr = data.get("email", "").strip()
            password = data.get("app_password", "").strip()

            if not email_addr or not password:
                # Try reading from config file if not provided in body
                if os.path.exists(CONFIG_FILE):
                    try:
                        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                            email_addr = email_addr or cfg.get("email", "")
                            password = password or cfg.get("app_password", "")
                    except Exception:
                        pass

            if not email_addr or not password:
                self._send_json({"ok": False, "error": "Gmail 계정 및 16자리 앱 비밀번호를 입력해주세요."})
                return

            res = gmail_service.test_connection(email_addr, password)
            self._send_json(res)
            return

        # 2. Fetch unread emails
        if self.path == "/api/email/fetch":
            data = self._read_body_json()
            email_addr = data.get("email", "").strip()
            password = data.get("app_password", "").strip()
            limit = int(data.get("limit", 5))
            mark_read = data.get("mark_read")

            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        if not email_addr:
                            email_addr = cfg.get("email", "")
                        if not password:
                            password = cfg.get("app_password", "")
                        if mark_read is None:
                            mark_read = cfg.get("mark_read", False)
                except Exception:
                    pass

            mark_read = bool(mark_read)

            if not email_addr or not password:
                self._send_json({"ok": False, "error": "저장된 Gmail 계정 정보가 없습니다. 설정을 먼저 진행해주세요."})
                return

            res = gmail_service.fetch_unread_emails(email_addr, password, limit=limit, mark_read=mark_read)
            self._send_json(res)
            return

        # 3. Save Gmail configuration
        if self.path == "/api/email/save_config":
            data = self._read_body_json()
            email_addr = data.get("email", "").strip()
            password = data.get("app_password", "").strip()
            auto_sync = bool(data.get("auto_sync", False))
            sync_interval = int(data.get("sync_interval", 30))
            mark_read = bool(data.get("mark_read", False))

            if not email_addr:
                self._send_json({"ok": False, "error": "이메일 주소를 입력해주세요."})
                return

            save_data = {
                "email": email_addr,
                "auto_sync": auto_sync,
                "sync_interval": sync_interval,
                "mark_read": mark_read
            }
            if password:
                save_data["app_password"] = password
            else:
                # Keep existing password if not updated
                if os.path.exists(CONFIG_FILE):
                    try:
                        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                            old = json.load(f)
                            if "app_password" in old:
                                save_data["app_password"] = old["app_password"]
                    except Exception:
                        pass

            try:
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                self._send_json({"ok": True, "message": "Gmail 설정이 안전하게 로컬에 저장되었습니다."})
            except Exception as e:
                self._send_json({"ok": False, "error": f"설정 저장 실패: {str(e)}"})
            return

        # 4. Inbound Webhook (External email / CS form push)
        if self.path == "/api/email/webhook":
            data = self._read_body_json()
            sender = data.get("sender") or data.get("from") or "webhook@customer.com"
            subject = data.get("subject") or data.get("title") or "(제목 없음)"
            body = data.get("body") or data.get("content") or data.get("message") or ""

            item = {
                "sender": sender,
                "subject": subject,
                "body": body,
                "source": "webhook"
            }
            global inbound_queue
            inbound_queue.append(item)
            self._send_json({"ok": True, "message": "새 메일이 수신 큐에 등록되었습니다.", "queue_size": len(inbound_queue)})
            return

        # 5. Test commercial frontier AI connection
        if self.path == "/api/ai/test":
            data = self._read_body_json()
            provider = data.get("provider", "gemini")
            api_key = data.get("api_key", "").strip()
            model = data.get("model", "")
            res = ai_service.test_ai_connection(provider, api_key, model)
            self._send_json(res)
            return

        # 6. Solve unfamiliar/ambiguous customer inquiry via commercial AI fallback
        if self.path == "/api/ai/solve":
            data = self._read_body_json()
            provider = data.get("provider", "gemini")
            api_key = data.get("api_key", "").strip()
            model = data.get("model", "")
            subject = data.get("subject") or data.get("mail_subject") or ""
            body = data.get("body") or data.get("mail_body") or ""
            question_id = data.get("question_id", "")
            question_def = data.get("question_def", {})
            res = ai_service.solve_unfamiliar_issue(provider, api_key, model, subject, body, question_id, question_def)
            self._send_json(res)
            return

        self._send_json({"error": "Not Found"}, status=404)

def run():
    # Ensure current directory is served
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), NextAIRequestHandler) as httpd:
        print(f"🚀 [NextAI] 웹 서버 & Gmail 연동 엔진 시작 (포트: {PORT})")
        print(f"👉 접속 주소: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 종료합니다.")

if __name__ == "__main__":
    run()
