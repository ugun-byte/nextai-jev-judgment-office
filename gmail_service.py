# -*- coding: utf-8 -*-
"""
Gmail IMAP Service for NextAI Jev Judgment Office
Connects to Gmail via IMAP4_SSL and parses incoming customer emails.
"""

import imaplib
import email
from email.header import decode_header
import re

class GmailService:
    def __init__(self, host="imap.gmail.com", port=993):
        self.host = host
        self.port = port

    def _decode_mime_words(self, s):
        if not s:
            return ""
        decoded_fragments = decode_header(s)
        text_parts = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                try:
                    text_parts.append(fragment.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    text_parts.append(fragment.decode("utf-8", errors="replace"))
            else:
                text_parts.append(str(fragment))
        return "".join(text_parts).strip()

    def _clean_body_text(self, text):
        if not text:
            return ""
        # Remove multiple newlines and carriage returns
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def test_connection(self, user, app_password):
        """Test authentication and inbox access."""
        clean_pass = app_password.replace(" ", "").strip()
        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port, timeout=10)
            mail.login(user.strip(), clean_pass)
            status, _ = mail.select("INBOX", readonly=True)
            mail.logout()
            if status == "OK":
                return {"ok": True, "message": f"Gmail 계정 [{user}] 인증 및 접속 성공!"}
            return {"ok": False, "error": f"INBOX 접근 실패 (상태: {status})"}
        except imaplib.IMAP4.error as e:
            return {"ok": False, "error": f"Gmail 인증 실패: {str(e)}. (Google 계정의 16자리 '앱 비밀번호'를 입력하셨는지 확인해주세요.)"}
        except Exception as e:
            return {"ok": False, "error": f"연결 오류: {str(e)}"}

    def fetch_unread_emails(self, user, app_password, limit=5, mark_read=False):
        """Fetch latest unread emails from INBOX."""
        clean_pass = app_password.replace(" ", "").strip()
        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port, timeout=15)
            mail.login(user.strip(), clean_pass)
            mail.select("INBOX", readonly=not mark_read)

            status, response = mail.search(None, "UNSEEN")
            if status != "OK":
                mail.logout()
                return {"ok": False, "error": "메일 검색 실패", "emails": []}

            mail_ids = response[0].split()
            if not mail_ids:
                mail.logout()
                return {"ok": True, "emails": [], "total_unread": 0}

            # Take latest 'limit' emails
            target_ids = mail_ids[-limit:]
            target_ids.reverse()

            parsed_emails = []

            for mid in target_ids:
                fetch_cmd = "(RFC822)" if mark_read else "(BODY.PEEK[])"
                res, msg_data = mail.fetch(mid, fetch_cmd)
                if res != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode sender and subject
                sender = self._decode_mime_words(msg.get("From", ""))
                subject = self._decode_mime_words(msg.get("Subject", "(제목 없음)"))
                date_str = self._decode_mime_words(msg.get("Date", ""))

                # Extract body
                body_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        if "attachment" in content_disposition:
                            continue
                        if content_type == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or "utf-8"
                                body_text = payload.decode(charset, errors="replace")
                                break
                            except Exception:
                                pass
                        elif content_type == "text/html" and not body_text:
                            try:
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or "utf-8"
                                html_content = payload.decode(charset, errors="replace")
                                # Strip tags for clean classification
                                body_text = re.sub(r'<[^>]+>', ' ', html_content)
                            except Exception:
                                pass
                else:
                    try:
                        payload = msg.get_payload(decode=True)
                        charset = msg.get_content_charset() or "utf-8"
                        body_text = payload.decode(charset, errors="replace")
                        if msg.get_content_type() == "text/html":
                            body_text = re.sub(r'<[^>]+>', ' ', body_text)
                    except Exception:
                        body_text = str(msg.get_payload())

                body_text = self._clean_body_text(body_text)
                if not body_text:
                    body_text = "(본문 내용 없음)"

                parsed_emails.append({
                    "id": mid.decode("utf-8", errors="ignore"),
                    "sender": sender,
                    "subject": subject,
                    "body": body_text[:2000], # Keep top 2000 chars for prompt classification
                    "date": date_str
                })

            mail.logout()
            return {
                "ok": True,
                "emails": parsed_emails,
                "total_unread": len(mail_ids)
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "emails": []}
