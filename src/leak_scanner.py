from __future__ import annotations

import re
from typing import Iterable

# High-confidence secret indicators to reduce false positives in normal news text/URLs.
SECRET_PATTERNS = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),  # GitHub personal token
    re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),  # Google API key
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{20,}\b"),  # Slack tokens
    re.compile(r"\bsk_(live|test)_[A-Za-z0-9]{20,}\b", re.IGNORECASE),  # Stripe-like
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP) PRIVATE KEY-----"),
]

SENSITIVE_FIELD_NAMES = {
    "smtp_user",
    "smtp_pass",
    "smtp_to",
    "smtp_host",
    "smtp_port",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "password",
    "secret",
}


def _contains_secret_pattern(text: str) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def scan_editor_rows(rows: Iterable[dict]) -> list[str]:
    findings: list[str] = []
    for idx, row in enumerate(rows, start=1):
        for field, value in row.items():
            name = str(field).strip().lower()
            val = str(value or "").strip()

            # Only apply strict checks to secret/config-like fields to avoid
            # false positives in regular news title/description/link text.
            if name in SENSITIVE_FIELD_NAMES:
                if "@" in val or _contains_secret_pattern(val):
                    findings.append(f"Row {idx}: suspicious secret-like value in field '{field}'.")
                # suspicious high-entropy fallback if this is explicitly sensitive field
                if len(val) >= 24 and re.fullmatch(r"[A-Za-z0-9_\-+/=]+", val):
                    findings.append(f"Row {idx}: high-entropy value in sensitive field '{field}'.")
    return findings


def scan_html(html: str) -> list[str]:
    findings: list[str] = []
    text = html or ""

    # Detect accidental inclusion of secret key names + assigned values in HTML payload.
    assignment_patterns = [
        re.compile(r"SMTP_PASS\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
        re.compile(r"SMTP_USER\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
        re.compile(r"API_KEY\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
        re.compile(r"TOKEN\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    ]

    if _contains_secret_pattern(text) or any(p.search(text) for p in assignment_patterns):
        findings.append("Generated HTML appears to include secret-like content.")
    return findings
