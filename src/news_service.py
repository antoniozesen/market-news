from __future__ import annotations

import datetime as dt
import importlib.util
import re
import time
from typing import Any

from .constants import MACRO_KEYWORDS, NEWS_SOURCES, OFFICIAL_SOURCES, REGION_KEYWORDS


def dependency_status() -> tuple[bool, list[str]]:
    required = ["feedparser", "bs4", "requests"]
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    return len(missing) == 0, missing


def default_last_week_range(today: dt.date | None = None) -> tuple[dt.date, dt.date]:
    today = today or dt.date.today()
    days_since_monday = today.weekday()
    start = today - dt.timedelta(days=days_since_monday + 7)
    return start, start + dt.timedelta(days=6)


def parse_date(date_str: str) -> dt.date | None:
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return dt.datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    m = re.search(r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})", date_str)
    if m:
        day, mon, year = m.groups()
        months = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
        return dt.date(int(year), months[mon], int(day))
    return None


def determine_region_from_content(content_text: str, default_region: str) -> str:
    content_text = content_text.lower()
    region_mentions = {r: 0 for r in REGION_KEYWORDS}
    for region, keywords in REGION_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in content_text:
                region_mentions[region] += 1
    max_mentions = max(region_mentions.values()) if region_mentions else 0
    if max_mentions == 0:
        return default_region
    return max(region_mentions, key=region_mentions.get)


def get_feed_news(feed_url: str, start_date: dt.date, end_date: dt.date, region: str) -> list[dict[str, Any]]:
    import feedparser
    from bs4 import BeautifulSoup

    try:
        feed = feedparser.parse(feed_url)
        news_items: list[dict[str, Any]] = []
        for entry in feed.entries:
            date_str = entry.get("published") or entry.get("updated")
            if not date_str:
                continue
            pub_date = parse_date(date_str)
            if not pub_date or not (start_date <= pub_date <= end_date):
                continue

            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary") or entry.get("description") or ""
            description = BeautifulSoup(summary, "html.parser").get_text()[:250]

            content_text = f"{title} {description}".lower()
            is_relevant = any(k in content_text for k in MACRO_KEYWORDS)
            is_official = any(s in feed_url for s in OFFICIAL_SOURCES)
            has_economic_terms = any(
                t in content_text
                for t in ["economy", "economic", "financial", "market", "bond", "currency", "trade", "investment", "fiscal", "monetary", "bank"]
            )
            if not (is_relevant or is_official or has_economic_terms):
                continue

            assigned_region = determine_region_from_content(content_text, region)
            news_items.append(
                {
                    "included": True,
                    "date": pub_date.isoformat(),
                    "title": title,
                    "description": description,
                    "link": link,
                    "region": assigned_region,
                    "notes": "",
                    "relevance_score": 3 if is_official else (2 if is_relevant else 1),
                }
            )
        return sorted(news_items, key=lambda x: x["relevance_score"], reverse=True)
    except Exception:
        return []


def extract_investopedia_weekly_report() -> dict[str, Any] | None:
    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0"}
    urls = [
        "https://www.investopedia.com/markets-news-4427704",
        "https://www.investopedia.com/market-news-4689632",
        "https://www.investopedia.com/markets/",
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, "html.parser")
            for link in soup.find_all("a", href=True):
                txt = link.get_text(" ", strip=True).lower()
                if any(p in txt for p in ["week ahead", "what to expect", "market outlook", "economic calendar"]):
                    href = link["href"]
                    if not href.startswith("http"):
                        href = "https://www.investopedia.com" + href
                    return {
                        "included": True,
                        "date": dt.date.today().isoformat(),
                        "title": "Investopedia Week Ahead",
                        "description": "Weekly market outlook and key events.",
                        "link": href,
                        "region": "Week Ahead",
                        "notes": "Auto-detected.",
                        "relevance_score": 3,
                    }
        except Exception:
            continue
    return None


def fetch_news(start_date: dt.date, end_date: dt.date, add_week_ahead: bool = True) -> list[dict[str, Any]]:
    deps_ok, _ = dependency_status()
    if not deps_ok:
        return []

    all_news: list[dict[str, Any]] = []
    for feed_url, region in NEWS_SOURCES:
        all_news.extend(get_feed_news(feed_url, start_date, end_date, region))
        time.sleep(0.2)
    if add_week_ahead:
        report = extract_investopedia_weekly_report()
        if report:
            all_news.append(report)
    return all_news
