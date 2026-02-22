from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.parse import parse_qsl, urlparse, urlunparse

from src.constants import GENERAL_ECON_TERMS


@dataclass
class RuntimeSettings:
    macro_keywords: list[str]
    region_keywords: dict[str, list[str]]
    official_domains: list[str]
    priority_regions: list[str]
    strict_macro_filter: bool
    include_official_always: bool
    include_undated_items: bool
    min_score_threshold: float


def dependency_status() -> tuple[bool, list[str]]:
    missing: list[str] = []
    for mod in ("feedparser", "requests", "bs4", "rapidfuzz"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    return len(missing) == 0, missing


def pretty_float(value: float, min_dp: int = 2, max_dp: int = 4) -> str:
    if value is None:
        return "0.00"
    try:
        if math.isnan(value):
            return "0.00"
    except Exception:
        pass
    text = f"{float(value):.{max_dp}f}".rstrip("0").rstrip(".")
    if "." not in text:
        return f"{text}.{'0'*min_dp}"
    decimals = text.split(".", 1)[1]
    if len(decimals) < min_dp:
        text += "0" * (min_dp - len(decimals))
    return text


def parse_date_any(entry: Any) -> dt.date | None:
    if isinstance(entry, dt.date):
        return entry

    # feedparser struct_time fields first
    for key in ("published_parsed", "updated_parsed"):
        tm = None
        if isinstance(entry, dict):
            tm = entry.get(key)
        else:
            tm = getattr(entry, key, None)
        if tm:
            try:
                return dt.date(tm.tm_year, tm.tm_mon, tm.tm_mday)
            except Exception:
                pass

    for key in ("published", "updated", "created"):
        raw = None
        if isinstance(entry, dict):
            raw = entry.get(key)
        else:
            raw = getattr(entry, key, None)
        if not raw:
            continue
        raw_text = str(raw).strip()
        try:
            parsed = parsedate_to_datetime(raw_text)
            if parsed:
                return parsed.date()
        except Exception:
            pass
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%a, %d %b %Y %H:%M:%S %z"]:
            try:
                return dt.datetime.strptime(raw_text, fmt).date()
            except ValueError:
                continue
    return None


def clean_summary(text: str, max_len: int = 320) -> str:
    from bs4 import BeautifulSoup

    plain = BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)
    plain = unescape(" ".join(plain.split())).strip()
    if len(plain) <= max_len:
        return plain
    return plain[: max_len - 1].rstrip() + "…"


def extract_domain(url: str) -> str:
    host = (urlparse(url).netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path.rstrip("/"), "", "&".join([f"{k}={v}" for k, v in query]), ""))


def classify_region(content_text: str, default_region: str, region_keywords: dict[str, list[str]]) -> str:
    text = (content_text or "").lower()
    best_region = default_region
    best_hits = 0
    for region, keywords in region_keywords.items():
        hits = sum(1 for kw in keywords if kw.lower() in text)
        if hits > best_hits:
            best_region = region
            best_hits = hits
    return best_region


def score_item(
    *,
    title: str,
    description: str,
    domain: str,
    region: str,
    date_value: dt.date,
    start_date: dt.date,
    end_date: dt.date,
    rt: RuntimeSettings,
    duplicate_penalty: float = 0.0,
) -> float:
    corpus = f"{title} {description}".lower()
    official_bonus = 1.6 if any(d in domain for d in rt.official_domains) else 0.0
    macro_hits = sum(1 for kw in rt.macro_keywords if kw.lower() in corpus)
    macro_bonus = min(4.0, macro_hits * 0.22)

    region_bonus = 0.0
    if region in rt.priority_regions:
        idx = rt.priority_regions.index(region)
        region_bonus = max(0.2, (len(rt.priority_regions) - idx) * 0.1)

    total_days = max((end_date - start_date).days, 1)
    recency_bonus = max(0.0, min((date_value - start_date).days / total_days, 1.0))

    raw = 1.0 + official_bonus + macro_bonus + region_bonus + recency_bonus - duplicate_penalty
    return max(0.1, round(raw, 4))


def _should_capture_broad(text_blob: str, domain: str, rt: RuntimeSettings) -> bool:
    text = text_blob.lower()
    has_general = any(term in text for term in GENERAL_ECON_TERMS)
    has_macro = any(term.lower() in text for term in rt.macro_keywords)
    is_official = any(d in domain for d in rt.official_domains)
    if rt.include_official_always and is_official:
        return True
    return has_general or has_macro


def fetch_rss_news(
    sources: list[dict[str, Any]],
    start_date: dt.date,
    end_date: dt.date,
    rt: RuntimeSettings,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import feedparser
    import requests

    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    for source in sources:
        if not source.get("enabled", True):
            continue

        region = str(source.get("region", "Global"))
        url = str(source.get("url", ""))
        name = str(source.get("name", url))

        status: int | None = None
        error_message = ""
        entries_parsed = 0
        entries_with_dates = 0
        entries_in_range = 0

        content = ""
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=headers, timeout=18)
                status = resp.status_code
                if resp.status_code == 200 and resp.text:
                    content = resp.text
                    break
                error_message = f"HTTP {resp.status_code}"
            except Exception as exc:
                error_message = str(exc)

            if attempt == 0:
                continue

        if not content:
            diagnostics.append(
                {
                    "region": region,
                    "name": name,
                    "url": url,
                    "http_status": status,
                    "error_message": error_message or "No content",
                    "entries_parsed": entries_parsed,
                    "entries_with_dates": entries_with_dates,
                    "entries_in_range": entries_in_range,
                }
            )
            continue

        feed = feedparser.parse(content)
        entries = list(getattr(feed, "entries", []))
        entries_parsed = len(entries)

        for entry in entries:
            title = str(entry.get("title", "")).strip()
            link = str(entry.get("link", "")).strip()
            description = clean_summary(entry.get("summary") or entry.get("description") or "")
            if not title or not link:
                continue

            parsed_date = parse_date_any(entry)
            source_label_suffix = ""
            if parsed_date:
                entries_with_dates += 1
            elif rt.include_undated_items:
                parsed_date = start_date
                source_label_suffix = " | Undated"
            else:
                continue

            if not (start_date <= parsed_date <= end_date):
                continue

            entries_in_range += 1
            domain = extract_domain(link)
            text_blob = f"{title} {description}"

            if not _should_capture_broad(text_blob, domain, rt):
                continue

            assigned_region = classify_region(text_blob, region, rt.region_keywords)
            score = score_item(
                title=title,
                description=description,
                domain=domain,
                region=assigned_region,
                date_value=parsed_date,
                start_date=start_date,
                end_date=end_date,
                rt=rt,
            )

            if rt.strict_macro_filter and score < rt.min_score_threshold:
                continue

            rows.append(
                {
                    "Include": True,
                    "Date": parsed_date,
                    "Region": assigned_region,
                    "Title": title,
                    "Description": description,
                    "Notes": "",
                    "Link": link,
                    "Score": score,
                    "Source": f"{domain}{source_label_suffix}",
                    "CanonicalURL": canonicalize_url(link),
                }
            )

        diagnostics.append(
            {
                "region": region,
                "name": name,
                "url": url,
                "http_status": status,
                "error_message": error_message,
                "entries_parsed": entries_parsed,
                "entries_with_dates": entries_with_dates,
                "entries_in_range": entries_in_range,
            }
        )

    return rows, diagnostics


def deduplicate_rows(rows: list[dict[str, Any]], fuzzy_threshold: int = 92) -> tuple[list[dict[str, Any]], int]:
    from rapidfuzz import fuzz

    unique: list[dict[str, Any]] = []
    removed = 0

    for row in sorted(rows, key=lambda r: float(r.get("Score", 0.0)), reverse=True):
        canon = str(row.get("CanonicalURL", ""))
        title = str(row.get("Title", ""))
        duplicate = False

        for existing in unique:
            if canon and canon == str(existing.get("CanonicalURL", "")):
                duplicate = True
                break
            if fuzz.token_set_ratio(title, str(existing.get("Title", ""))) >= fuzzy_threshold:
                duplicate = True
                break

        if duplicate:
            removed += 1
        else:
            unique.append(row)

    return unique, removed


def discover_investopedia_url(override_url: str | None = None) -> str | None:
    if override_url and override_url.strip():
        return override_url.strip()

    import requests
    from bs4 import BeautifulSoup

    candidates = [
        "https://www.investopedia.com/markets-news-4427704",
        "https://www.investopedia.com/markets/",
        "https://www.investopedia.com/",
    ]

    headers = {"User-Agent": "Mozilla/5.0"}
    for url in candidates:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                t = a.get_text(" ", strip=True).lower()
                if any(k in t for k in ["week ahead", "what to expect", "market outlook", "economic calendar"]):
                    href = a["href"]
                    if not href.startswith("http"):
                        href = "https://www.investopedia.com" + href
                    return href
        except Exception:
            continue
    return None


def fetch_investopedia_week_ahead(url: str) -> dict[str, Any] | None:
    import re

    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Week Ahead"

        article = soup.find("article") or soup.find("main") or soup
        paragraphs = [clean_summary(p.get_text(" ", strip=True), max_len=500) for p in article.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 30]

        events_by_day: dict[str, list[str]] = {d: [] for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        current_day: str | None = None

        for node in article.find_all(["h2", "h3", "h4", "p", "li", "strong"]):
            text = clean_summary(node.get_text(" ", strip=True), max_len=260)
            if not text:
                continue
            day_found = next((d for d in events_by_day if re.search(rf"\b{d}\b", text, re.IGNORECASE)), None)
            if day_found:
                current_day = day_found
                continue
            if current_day and len(text) > 20:
                events_by_day[current_day].append(text)

        summary_paragraphs = paragraphs[:3]
        outlook_paragraphs = [p for p in paragraphs[-5:] if any(w in p.lower() for w in ["outlook", "expect", "forecast", "trend"])]

        if not summary_paragraphs and not any(events_by_day.values()):
            return None

        return {
            "title": title,
            "link": url,
            "summary_paragraphs": summary_paragraphs,
            "events_by_day": events_by_day,
            "outlook_paragraphs": outlook_paragraphs,
        }
    except Exception:
        return None
