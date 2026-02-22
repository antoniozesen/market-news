from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass
class SmtpSettings:
    user: str | None
    password: str | None
    default_to: str | None
    host: str | None
    port: int | None

    @property
    def ready(self) -> bool:
        return all([self.user, self.password, self.default_to, self.host, self.port])


def _read_secret(key: str) -> str | None:
    try:
        value = st.secrets.get(key)
    except Exception:
        value = None
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() == "CHANGE_ME":
        return None
    return text


def load_smtp_settings() -> tuple[SmtpSettings, list[str]]:
    user = _read_secret("SMTP_USER")
    password = _read_secret("SMTP_PASS")
    default_to = _read_secret("SMTP_TO")
    host = _read_secret("SMTP_HOST")

    port_raw = _read_secret("SMTP_PORT")
    port: int | None = None
    missing: list[str] = []

    if port_raw:
        try:
            port = int(port_raw)
        except ValueError:
            missing.append("SMTP_PORT (must be integer)")
    else:
        missing.append("SMTP_PORT")

    if not user:
        missing.append("SMTP_USER")
    if not password:
        missing.append("SMTP_PASS")
    if not default_to:
        missing.append("SMTP_TO")
    if not host:
        missing.append("SMTP_HOST")

    return SmtpSettings(user=user, password=password, default_to=default_to, host=host, port=port), missing
