from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.settings import SmtpSettings


def send_email(html: str, recipient: str, subject: str, smtp: SmtpSettings) -> tuple[bool, str]:
    if not smtp.ready:
        return False, "SMTP secrets are incomplete."

    msg = MIMEMultipart("alternative")
    msg["From"] = smtp.user or ""
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host=smtp.host, port=smtp.port, timeout=30) as server:
            server.starttls()
            server.login(smtp.user, smtp.password)
            server.sendmail(smtp.user, [recipient], msg.as_string())
        return True, f"Email sent to {recipient}."
    except Exception as exc:
        return False, f"Email send failed: {exc}"
