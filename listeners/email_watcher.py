import imaplib
import email
from email.header import decode_header
from typing import List, Dict
from loguru import logger
from config.settings import settings
from tracker.database import db


class EmailWatcher:
    """
    Monitors Gmail inbox via IMAP for application status updates,
    shortlisting notices, interview calls, and rejection alerts.
    """

    def __init__(self):
        self.host = settings.IMAP_SERVER
        self.port = settings.IMAP_PORT
        self.user = settings.IMAP_USER
        self.password = settings.IMAP_PASSWORD

    def check_inbox(self) -> List[Dict[str, str]]:
        if not self.password:
            logger.info("IMAP password not configured. Email check skipped.")
            return []

        results = []
        try:
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.user, self.password)
            mail.select("inbox")

            # Search recent emails
            status, messages = mail.search(None, '(SINCE "01-Jan-2026")')
            if status != "OK":
                return []

            email_ids = messages[0].split()
            # Check latest 30 emails
            for eid in email_ids[-30:]:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

                        sender = msg.get("From", "")
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode(errors="ignore")
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="ignore")

                        subject_lower = subject.lower()
                        body_lower = body.lower()

                        # Classify intent
                        if any(k in subject_lower or k in body_lower for k in ["interview", "assessment", "shortlist", "test link", "round 1"]):
                            logger.success(f"🎯 INTERVIEW CALL DETECTED! From: {sender} | Subject: {subject}")
                            results.append({"type": "INTERVIEW", "from": sender, "subject": subject})
                        elif any(k in subject_lower or k in body_lower for k in ["unfortunately", "not moving forward", "other candidates"]):
                            logger.info(f"Rejection update: From: {sender} | Subject: {subject}")
                            results.append({"type": "REJECTED", "from": sender, "subject": subject})

            mail.close()
            mail.logout()
            return results

        except Exception as e:
            logger.error(f"Email check failed: {e}")
            return []
