from __future__ import annotations

import datetime as dt
from collections import defaultdict

from .constants import PRIORITY_REGIONS


def build_email_html(items: list[dict], start_date: dt.date, end_date: dt.date) -> str:
    by_date: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        if item.get("included", True):
            by_date[item["date"]].append(item)

    html = [
        "<html><head><meta charset='utf-8'>",
        """
        <style>
            body {font-family: Inter, Segoe UI, Arial, sans-serif; line-height:1.45; color:#0f172a; background:#f8fafc; margin:0;}
            .wrap {max-width: 1000px; margin: 0 auto; padding: 24px;}
            .hero {background: #ffffff; border:1px solid #dbeafe; border-radius:14px; padding:18px 20px;}
            h1 {margin:0 0 6px; color:#1e3a8a;}
            h2 {margin:18px 0 10px; color:#1e293b; border-bottom:1px solid #e2e8f0; padding-bottom:6px;}
            h3 {margin:12px 0 8px; color:#0f172a;}
            .day-card {background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:12px; margin-top:16px;}
            .item {background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:10px; margin:8px 0;}
            .muted {color:#64748b;}
            a {color:#1d4ed8; text-decoration:none;}
            a:hover {text-decoration:underline;}
        </style>
        """,
        "</head><body><div class='wrap'>",
        "<div class='hero'>",
        f"<h1>Macroeconomic News Digest</h1><div class='muted'>{start_date} → {end_date} · Internal use only</div>",
        "</div>",
    ]

    day = start_date
    while day <= end_date:
        key = day.isoformat()
        html.append("<div class='day-card'>")
        html.append(f"<h2>{day.strftime('%A, %Y-%m-%d')}</h2>")
        items_day = by_date.get(key, [])
        if not items_day:
            html.append("<p class='muted'><i>No significant macroeconomic news found for this date.</i></p>")
            html.append("</div>")
            day += dt.timedelta(days=1)
            continue

        by_region: dict[str, list[dict]] = defaultdict(list)
        for it in items_day:
            by_region[it.get("region", "Other")].append(it)

        ordered_regions = [r for r in PRIORITY_REGIONS if r in by_region] + [r for r in by_region if r not in PRIORITY_REGIONS]
        for region in ordered_regions:
            html.append(f"<h3>{region}</h3>")
            for it in sorted(by_region[region], key=lambda x: x.get("relevance_score", 1), reverse=True)[:10]:
                html.append(
                    f"<div class='item'><b>{it['title']}</b><br>{it['description']}<br><a href='{it['link']}'>Read more</a></div>"
                )
        html.append("</div>")
        day += dt.timedelta(days=1)

    html.append("</div></body></html>")
    return "\n".join(html)
