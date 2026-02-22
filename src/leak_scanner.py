from __future__ import annotations

import re
from typing import Iterable

SUSPICIOUS_TOKEN_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9_\-]{28,}\b"),
    re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b"),
]


CONFIG_FIELD_NAMES = {"smtp_user", "smtp_pass", "smtp_to", "smtp_host", "smtp_port", "api_key", "token", "password"}


def _looks_like_token(text: str) -> bool:
    return any(pattern.search(text) for pattern in SUSPICIOUS_TOKEN_PATTERNS)


def scan_editor_rows(rows: Iterable[dict]) -> list[str]:
    findings: list[str] = []
    for idx, row in enumerate(rows, start=1):
        for field, value in row.items():
            field_lower = str(field).lower()
            val = str(value or "")
            if field_lower in CONFIG_FIELD_NAMES:
                if "@" in val or _looks_like_token(val):
                    findings.append(f"Row {idx}: suspicious secret-like value in field '{field}'.")
            elif _looks_like_token(val):
                findings.append(f"Row {idx}: possible token-like string in field '{field}'.")
    return findings


def scan_html(html: str) -> list[str]:
    findings: list[str] = []
    if _looks_like_token(html):
        findings.append("Generated HTML contains token-like strings.")
    return findings
