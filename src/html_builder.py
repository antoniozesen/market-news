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
        "<html><body>",
        f"<h1>Macroeconomic News Digest: {start_date} to {end_date}</h1>",
        "<p><strong>Internal use only.</strong></p>",
    ]

    day = start_date
    while day <= end_date:
        key = day.isoformat()
        html.append(f"<h2>{day.strftime('%A, %Y-%m-%d')}</h2>")
        items_day = by_date.get(key, [])
        if not items_day:
            html.append("<p><i>No significant macroeconomic news found for this date.</i></p>")
            day += dt.timedelta(days=1)
            continue

        by_region: dict[str, list[dict]] = defaultdict(list)
        for it in items_day:
            by_region[it.get("region", "Other")].append(it)

        ordered_regions = [r for r in PRIORITY_REGIONS if r in by_region] + [r for r in by_region if r not in PRIORITY_REGIONS]
        for region in ordered_regions:
            html.append(f"<h3>{region}</h3>")
            for it in sorted(by_region[region], key=lambda x: x.get("relevance_score", 1), reverse=True)[:10]:
                html.append(f"<p><b>{it['title']}</b><br>{it['description']}<br><a href='{it['link']}'>Read more</a></p>")
        day += dt.timedelta(days=1)

    html.append("</body></html>")
    return "\n".join(html)
