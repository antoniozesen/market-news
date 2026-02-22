from __future__ import annotations

DEFAULT_PRIORITY_REGIONS = ["Eurozone", "Germany", "UK", "USA", "Japan", "China", "Global"]

DEFAULT_MACRO_KEYWORDS = [
    "gdp",
    "inflation",
    "cpi",
    "ppi",
    "unemployment",
    "employment",
    "nonfarm payroll",
    "retail sales",
    "industrial production",
    "pmi",
    "ism",
    "consumer confidence",
    "housing",
    "durable goods",
    "trade deficit",
    "trade surplus",
    "central bank",
    "federal reserve",
    "fed",
    "ecb",
    "boe",
    "bank of japan",
    "pboc",
    "interest rate",
    "monetary policy",
    "fiscal policy",
    "fomc",
    "recession",
    "economic outlook",
    "yield",
    "bond",
    "macroeconomic",
]

DEFAULT_REGION_KEYWORDS: dict[str, list[str]] = {
    "Eurozone": ["eurozone", "euro area", "ecb", "european central bank", "eu"],
    "USA": ["united states", "u.s.", "fed", "federal reserve", "treasury"],
    "Germany": ["germany", "german", "bundesbank", "berlin", "frankfurt"],
    "UK": ["uk", "united kingdom", "britain", "boe", "bank of england"],
    "Japan": ["japan", "japanese", "boj", "bank of japan", "tokyo"],
    "China": ["china", "chinese", "pboc", "beijing", "yuan"],
}

DEFAULT_OFFICIAL_DOMAINS = [
    "ecb.europa.eu",
    "ec.europa.eu",
    "federalreserve.gov",
    "bea.gov",
    "bls.gov",
    "bundesbank.de",
    "bankofengland.co.uk",
    "ons.gov.uk",
    "boj.or.jp",
]

DEFAULT_RSS_SOURCES: list[tuple[str, str]] = [
    ("https://www.ecb.europa.eu/home/html/rss.en.html", "Eurozone"),
    ("https://ec.europa.eu/commission/presscorner/api/documents/1/feed", "Eurozone"),
    ("https://www.ft.com/rss/markets/europe", "Eurozone"),
    ("https://www.marketwatch.com/rss/topics/economy?x=1", "Global"),
    ("https://www.bundesbank.de/en/press/press-releases/rss", "Germany"),
    ("https://www.bankofengland.co.uk/rss/news", "UK"),
    ("https://www.federalreserve.gov/feeds/press_all.xml", "USA"),
    ("https://www.bls.gov/feed/bls_latest_numbers.rss", "USA"),
    ("https://www.bea.gov/rss/rss.xml", "USA"),
    ("https://www.boj.or.jp/en/rss/release_2021.xml", "Japan"),
    ("https://www.reuters.com/rssFeed/chinaNews", "China"),
]
