from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import streamlit as st


REQUIRED_KEYS = [
    "EMAIL_SENDER",
    "EMAIL_PASSWORD",
    "EMAIL_RECIPIENT_DEFAULT",
]
OPTIONAL_KEYS_WITH_DEFAULT = {
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "FRED_API_KEY": None,
}


@dataclass
class AppSettings:
    email_sender: str | None
    email_password: str | None
    email_recipient_default: str | None
    smtp_host: str
    smtp_port: int
    fred_api_key: str | None

    @property
    def email_ready(self) -> bool:
        return bool(self.email_sender and self.email_password and self.email_recipient_default)


def _read_secret_or_env(key: str, default: Any = None) -> Any:
    value = None
    try:
        if key in st.secrets:
            value = st.secrets[key]
    except Exception:
        value = None
    if value in (None, ""):
        value = os.getenv(key, default)
    return value


def load_settings() -> tuple[AppSettings, list[str]]:
    missing: list[str] = []
    values: dict[str, Any] = {}

    for key in REQUIRED_KEYS:
        val = _read_secret_or_env(key)
        values[key] = val
        if not val or val == "CHANGE_ME":
            missing.append(key)

    for key, default in OPTIONAL_KEYS_WITH_DEFAULT.items():
        values[key] = _read_secret_or_env(key, default)

    try:
        smtp_port = int(values["SMTP_PORT"])
    except (TypeError, ValueError):
        smtp_port = 587
        missing.append("SMTP_PORT (must be int)")

    settings = AppSettings(
        email_sender=values["EMAIL_SENDER"],
        email_password=values["EMAIL_PASSWORD"],
        email_recipient_default=values["EMAIL_RECIPIENT_DEFAULT"],
        smtp_host=values["SMTP_HOST"] or "smtp.gmail.com",
        smtp_port=smtp_port,
        fred_api_key=values["FRED_API_KEY"],
    )
    return settings, missing
