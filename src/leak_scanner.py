from __future__ import annotations

import re
from typing import Iterable

TOKEN_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9_\-]{24,}\b"),
    re.compile(r"\b[A-Za-z0-9+/]{32,}={0,2}\b"),
]


def _has_suspicious_token(text: str) -> bool:
    return any(p.search(text or "") for p in TOKEN_PATTERNS)


def scan_editor_rows(rows: Iterable[dict]) -> list[str]:
    findings: list[str] = []
    for idx, row in enumerate(rows):
        for field in ("notes", "title", "description"):
            v = str(row.get(field, ""))
            if _has_suspicious_token(v):
                findings.append(f"Fila {idx + 1}: posible token expuesto en {field}.")
    return findings


def scan_html(html: str) -> list[str]:
    findings: list[str] = []
    if _has_suspicious_token(html):
        findings.append("El HTML contiene cadenas con apariencia de token/API key.")
    return findings
