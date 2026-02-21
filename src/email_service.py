from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .settings import AppSettings


def send_email(html: str, recipient: str, subject: str, settings: AppSettings) -> tuple[bool, str]:
    if not settings.email_ready:
        return False, "Secrets incompletos: no se puede enviar correo."

    msg = MIMEMultipart()
    msg["From"] = settings.email_sender or ""
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.email_sender, settings.email_password)
            server.send_message(msg)
        return True, "Correo enviado correctamente."
    except Exception as exc:
        return False, f"Error al enviar correo: {exc}"
