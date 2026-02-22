from __future__ import annotations

import datetime as dt
import math
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import parse_qsl, urlparse, urlunparse

from src.constants import DEFAULT_MACRO_KEYWORDS, DEFAULT_OFFICIAL_DOMAINS, DEFAULT_REGION_KEYWORDS


@dataclass
class RuntimeSettings:
    macro_keywords: list[str]
    region_keywords: dict[str, list[str]]
    official_domains: list[str]
    priority_regions: list[str]
    strict_macro_filter: bool
    include_official_always: bool


def dependency_status() -> tuple[bool, list[str]]:
    missing: list[str] = []
    for mod in ("feedparser", "requests", "bs4", "rapidfuzz"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    return (len(missing) == 0, missing)


def pretty_float(value: float, min_dp: int = 2, max_dp: int = 4) -> str:
    if value is None or math.isnan(value):
        return "0.00"
    text = f"{value:.{max_dp}f}".rstrip("0").rstrip(".")
    if "." not in text:
        return f"{text}.{'0'*min_dp}"
    decimals = text.split(".", 1)[1]
    if len(decimals) < min_dp:
        text += "0" * (min_dp - len(decimals))
    return text


def parse_date_any(raw: Any) -> dt.date | None:
    if raw is None:
        return None
    if isinstance(raw, dt.date):
        return raw

    import email.utils

    text = str(raw).strip()
    parsed = email.utils.parsedate_to_datetime(text)
    if parsed:
        return parsed.date()
    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%a, %d %b %Y %H:%M:%S %z"]:
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def clean_summary(text: str, max_len: int = 320) -> str:
    from bs4 import BeautifulSoup

    plain = BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)
    plain = unescape(re.sub(r"\s+", " ", plain)).strip()
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


def classify_region(text: str, default_region: str, region_keywords: dict[str, list[str]]) -> str:
    t = (text or "").lower()
    best_region = default_region
    best_hits = 0
    for region, keywords in region_keywords.items():
        hits = sum(1 for kw in keywords if kw.lower() in t)
        if hits > best_hits:
            best_hits = hits
            best_region = region
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
    official_bonus = 1.5 if any(d in domain for d in rt.official_domains) else 0.0
    keyword_hits = sum(1 for kw in rt.macro_keywords if kw.lower() in corpus)
    macro_score = min(4.0, keyword_hits * 0.2)

    region_bonus = 0.0
    if region in rt.priority_regions:
        idx = rt.priority_regions.index(region)
        region_bonus = max(0.2, (len(rt.priority_regions) - idx) * 0.1)

    total_days = max((end_date - start_date).days, 1)
    recency = (date_value - start_date).days / total_days
    recency_bonus = max(0.0, min(recency, 1.0))

    raw = 1.0 + official_bonus + macro_score + region_bonus + recency_bonus - duplicate_penalty
    return max(0.1, round(raw, 4))


def fetch_rss_news(
    sources: list[tuple[str, str]],
    start_date: dt.date,
    end_date: dt.date,
    rt: RuntimeSettings,
) -> tuple[list[dict[str, Any]], list[str]]:
    import feedparser

    errors: list[str] = []
    rows: list[dict[str, Any]] = []

    for feed_url, fallback_region in sources:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as exc:
            errors.append(f"Feed load failed {feed_url}: {exc}")
            continue

        for entry in getattr(feed, "entries", []):
            raw_date = entry.get("published") or entry.get("updated") or entry.get("created")
            date_value = parse_date_any(raw_date)
            if not date_value or date_value < start_date or date_value > end_date:
                continue

            title = str(entry.get("title", "")).strip()
            link = str(entry.get("link", "")).strip()
            description = clean_summary(entry.get("summary") or entry.get("description") or "")
            if not title or not link:
                continue

            domain = extract_domain(link)
            text_blob = f"{title} {description}"
            region = classify_region(text_blob, fallback_region, rt.region_keywords)
            is_official = any(d in domain for d in rt.official_domains)
            has_macro = any(kw.lower() in text_blob.lower() for kw in rt.macro_keywords)

            if rt.strict_macro_filter and not has_macro and not (rt.include_official_always and is_official):
                continue

            score = score_item(
                title=title,
                description=description,
                domain=domain,
                region=region,
                date_value=date_value,
                start_date=start_date,
                end_date=end_date,
                rt=rt,
            )
            rows.append(
                {
                    "Include": True,
                    "Date": date_value,
                    "Region": region,
                    "Title": title,
                    "Description": description,
                    "Notes": "",
                    "Link": link,
                    "Score": score,
                    "Source": domain,
                    "CanonicalURL": canonicalize_url(link),
                }
            )
    return rows, errors


def deduplicate_rows(rows: list[dict[str, Any]], fuzzy_threshold: int = 92) -> tuple[list[dict[str, Any]], int]:
    from rapidfuzz import fuzz

    unique: list[dict[str, Any]] = []
    removed = 0

    for row in sorted(rows, key=lambda r: float(r.get("Score", 0)), reverse=True):
        is_dup = False
        canon = row.get("CanonicalURL", "")
        title = str(row.get("Title", ""))
        for existing in unique:
            if canon and canon == existing.get("CanonicalURL"):
                is_dup = True
                break
            ratio = fuzz.token_set_ratio(title, str(existing.get("Title", "")))
            if ratio >= fuzzy_threshold:
                is_dup = True
                break
        if is_dup:
            removed += 1
            continue
        unique.append(row)
    return unique, removed


def discover_investopedia_url(override_url: str | None = None) -> str | None:
    if override_url:
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
                text = a.get_text(" ", strip=True).lower()
                if any(k in text for k in ["week ahead", "what to expect", "market outlook", "economic calendar"]):
                    href = a["href"]
                    if not href.startswith("http"):
                        href = "https://www.investopedia.com" + href
                    return href
        except Exception:
            continue
    return None


def fetch_investopedia_week_ahead(url: str) -> dict[str, Any] | None:
    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")

        title = (soup.find("h1").get_text(strip=True) if soup.find("h1") else "Week Ahead")
        article = soup.find("article") or soup.find("main") or soup
        paragraphs = [clean_summary(p.get_text(" ", strip=True), max_len=500) for p in article.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 40]

        events_by_day: dict[str, list[str]] = {d: [] for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        current_day: str | None = None
        for node in article.find_all(["h2", "h3", "h4", "p", "li", "strong"]):
            text = clean_summary(node.get_text(" ", strip=True), max_len=240)
            if not text:
                continue
            day_found = next((d for d in events_by_day if re.search(rf"\b{d}\b", text, re.IGNORECASE)), None)
            if day_found:
                current_day = day_found
                continue
            if current_day and len(text) > 20:
                events_by_day[current_day].append(text)

        summary_paragraphs = paragraphs[:3]
        outlook_paragraphs = [p for p in paragraphs[-4:] if any(w in p.lower() for w in ["outlook", "expect", "forecast", "trend"])]

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
