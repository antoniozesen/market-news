from __future__ import annotations

import datetime as dt
from collections import defaultdict
from html import escape
from typing import Any

from src.news_service import pretty_float


def _group_by_day(rows: list[dict[str, Any]]) -> dict[dt.date, list[dict[str, Any]]]:
    grouped: dict[dt.date, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not row.get("Include", True):
            continue
        day = row.get("Date")
        if isinstance(day, str):
            try:
                day = dt.date.fromisoformat(day)
            except Exception:
                continue
        if isinstance(day, dt.datetime):
            day = day.date()
        if isinstance(day, dt.date):
            grouped[day].append(row)
    return grouped


def render_email_html(
    rows: list[dict[str, Any]],
    *,
    start_date: dt.date,
    end_date: dt.date,
    region_priority: list[str],
    investopedia_block: dict[str, Any] | None,
    max_items_per_region_per_day: int,
    max_global_items: int,
    minimum_score: float,
) -> str:
    grouped = _group_by_day(rows)

    html = [
        "<html><head><meta charset='utf-8'>",
        """
        <style>
          body { font-family: Arial, sans-serif; color:#0f172a; background:#f8fafc; margin:0; }
          .wrap { max-width: 980px; margin: 0 auto; padding: 20px; }
          .card { background:#fff; border:1px solid #dbeafe; border-radius:12px; padding:14px; margin-bottom:14px; }
          h1, h2, h3 { margin:0 0 10px 0; }
          h1 { color:#1e3a8a; }
          h2 { color:#1e293b; border-bottom:1px solid #e2e8f0; padding-bottom:6px; margin-top:14px; }
          h3 { color:#0f172a; margin-top:10px; }
          p { margin:6px 0; }
          .muted { color:#64748b; }
          .internal { color:#dc2626; font-weight:700; }
          .news-item { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:8px; margin:8px 0; }
          .global { opacity:0.82; }
          a { color:#2563eb; text-decoration:none; }
        </style>
        """,
        "</head><body><div class='wrap'>",
        "<div class='card'>",
        f"<h1>Macroeconomic News Digest ({escape(start_date.isoformat())} → {escape(end_date.isoformat())})</h1>",
        "<p>This report consolidates key macroeconomic headlines gathered from reliable media + official institutions.</p>",
        "<p>For questions, contact <a href='mailto:investment@caixabankwealthmanagement.lu'>investment@caixabankwealthmanagement.lu</a>.</p>",
        "<p class='internal'>This report is intended for internal use only.</p>",
        "</div>",
    ]

    if investopedia_block:
        html.append("<div class='card'>")
        html.append("<h2>Week Ahead</h2>")
        html.append(f"<p><strong>{escape(investopedia_block.get('title', 'Week Ahead'))}</strong> · <a href='{escape(investopedia_block.get('link', '#'))}'>Source</a></p>")
        for para in investopedia_block.get("summary_paragraphs", [])[:4]:
            html.append(f"<p>{escape(para)}</p>")
        events_by_day = investopedia_block.get("events_by_day", {})
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
            events = events_by_day.get(day, [])[:5]
            if events:
                html.append(f"<h3>{day}</h3>")
                for event in events:
                    html.append(f"<p>• {escape(event)}</p>")
        for para in investopedia_block.get("outlook_paragraphs", [])[:3]:
            html.append(f"<p>{escape(para)}</p>")
        html.append("</div>")

    global_count = 0
    day = start_date
    while day <= end_date:
        html.append("<div class='card'>")
        html.append(f"<h2>{escape(day.strftime('%A, %Y-%m-%d'))}</h2>")

        day_rows = [r for r in grouped.get(day, []) if float(r.get("Score", 0.0)) >= minimum_score]
        if not day_rows:
            html.append("<p class='muted'><em>No significant macroeconomic news found for this date.</em></p>")
            html.append("</div>")
            day += dt.timedelta(days=1)
            continue

        by_region: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in day_rows:
            by_region[str(row.get("Region") or "Other")].append(row)

        ordered_regions = [r for r in region_priority if r in by_region]
        ordered_regions += [r for r in by_region if r not in ordered_regions and r != "Global"]
        if "Global" in by_region:
            ordered_regions.append("Global")

        for region in ordered_regions:
            rows_region = sorted(by_region[region], key=lambda x: float(x.get("Score", 0.0)), reverse=True)
            if region == "Global":
                if global_count >= max_global_items:
                    continue
                remaining = max(0, max_global_items - global_count)
                rows_region = rows_region[:remaining]
                global_count += len(rows_region)
            else:
                rows_region = rows_region[:max_items_per_region_per_day]

            if not rows_region:
                continue

            cls = "news-item global" if region == "Global" else "news-item"
            html.append(f"<h3>{escape(region)}</h3>")
            for item in rows_region:
                html.append(f"<div class='{cls}'>")
                html.append(f"<p><strong>{escape(str(item.get('Title', 'Untitled')))}</strong></p>")
                html.append(f"<p>{escape(str(item.get('Description', '')))}</p>")
                notes = str(item.get("Notes") or "").strip()
                if notes:
                    html.append(f"<p class='muted'>Note: {escape(notes)}</p>")
                score = pretty_float(float(item.get("Score", 0.0)))
                html.append(f"<p class='muted'>Score: {escape(score)} | Source: {escape(str(item.get('Source', '')))}</p>")
                html.append(f"<p><a href='{escape(str(item.get('Link', '#')))}'>Read more</a></p>")
                html.append("</div>")

        html.append("</div>")
        day += dt.timedelta(days=1)

    html.append("</div></body></html>")
    return "\n".join(html)
