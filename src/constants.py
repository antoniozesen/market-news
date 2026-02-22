from __future__ import annotations

PRIORITY_REGIONS_DEFAULT = ["Eurozone", "Germany", "UK", "USA", "Japan", "China"]

MACRO_KEYWORDS_DEFAULT = [
    "gdp", "inflation", "cpi", "ppi", "unemployment", "employment", "nonfarm", "payroll",
    "retail sales", "industrial production", "manufacturing", "pmi", "ism", "consumer confidence",
    "consumer sentiment", "housing", "durable goods", "trade deficit", "trade surplus", "current account",
    "balance of trade", "ifo", "zew", "central bank", "fed", "federal reserve", "ecb", "boe",
    "bank of japan", "pboc", "interest rate", "monetary policy", "fiscal policy", "rate decision",
    "fomc", "stimulus", "recession", "growth forecast", "economic outlook", "economic growth",
    "yield", "bond", "macroeconomic", "economic data",
]

GENERAL_ECON_TERMS = [
    "economy", "economic", "market", "markets", "finance", "financial", "bank", "banking",
    "trade", "investment", "growth", "inflation", "jobs", "employment", "rates", "policy",
    "fiscal", "monetary", "gdp", "bond", "yield", "currency", "treasury", "stock",
]

REGION_KEYWORDS_DEFAULT: dict[str, list[str]] = {
    "Eurozone": ["eurozone", "euro area", "ecb", "european central bank", "european union", "eu"],
    "Germany": ["germany", "german", "bundesbank", "berlin", "frankfurt"],
    "UK": ["uk", "united kingdom", "britain", "bank of england", "boe", "london"],
    "USA": ["u.s.", "united states", "federal reserve", "fed", "fomc", "treasury"],
    "Japan": ["japan", "japanese", "boj", "bank of japan", "tokyo", "yen"],
    "China": ["china", "chinese", "pboc", "beijing", "yuan", "renminbi"],
}

OFFICIAL_DOMAINS_DEFAULT = [
    "ecb.europa.eu", "ec.europa.eu", "eurostat", "bundesbank.de", "bankofengland.co.uk", "ons.gov.uk",
    "federalreserve.gov", "bea.gov", "bls.gov", "boj.or.jp", "bis.org", "oecd.org", "imf.org",
]

# Restored and expanded source registry with region grouping + optional flags.
SOURCES_DEFAULT: list[dict[str, str | bool]] = [
    # EUROZONE / EUROPE
    {"region": "Eurozone", "url": "https://www.ecb.europa.eu/home/html/rss.en.html", "name": "ECB RSS", "enabled": True},
    {"region": "Eurozone", "url": "https://ec.europa.eu/commission/presscorner/api/documents/1/feed", "name": "EU Commission PressCorner", "enabled": True},
    {"region": "Eurozone", "url": "https://www.ft.com/rss/markets/europe", "name": "FT Europe Markets", "enabled": True},
    {"region": "Eurozone", "url": "https://tradingeconomics.com/rss/euro-area.xml", "name": "TradingEconomics Euro Area", "enabled": True},
    {"region": "Eurozone", "url": "https://www.euractiv.com/feed/", "name": "Euractiv", "enabled": True},
    {"region": "Eurozone", "url": "https://www.politico.eu/feed/", "name": "Politico EU", "enabled": True},
    {"region": "Eurozone", "url": "https://www.euronews.com/rss", "name": "Euronews", "enabled": True},
    {"region": "Eurozone", "url": "https://www.bruegel.org/feed/", "name": "Bruegel", "enabled": True},
    # Germany
    {"region": "Germany", "url": "https://www.bundesbank.de/en/press/press-releases/rss", "name": "Bundesbank", "enabled": True},
    {"region": "Germany", "url": "https://www.handelsblatt.com/contentexport/feed/wirtschaft", "name": "Handelsblatt Wirtschaft", "enabled": True},
    {"region": "Germany", "url": "https://tradingeconomics.com/rss/germany.xml", "name": "TradingEconomics Germany", "enabled": True},
    {"region": "Germany", "url": "https://www.dw.com/en/top-stories/business/s-1431/rss", "name": "DW Business", "enabled": True},
    # UK
    {"region": "UK", "url": "https://www.bankofengland.co.uk/rss/news", "name": "Bank of England", "enabled": True},
    {"region": "UK", "url": "https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation/current/rss", "name": "ONS CPI", "enabled": True},
    {"region": "UK", "url": "https://tradingeconomics.com/rss/united-kingdom.xml", "name": "TradingEconomics UK", "enabled": True},
    # USA
    {"region": "USA", "url": "https://www.federalreserve.gov/feeds/press_all.xml", "name": "Federal Reserve", "enabled": True},
    {"region": "USA", "url": "https://www.bea.gov/rss/rss.xml", "name": "BEA", "enabled": True},
    {"region": "USA", "url": "https://www.bls.gov/feed/bls_latest_numbers.rss", "name": "BLS", "enabled": True},
    {"region": "USA", "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html", "name": "CNBC", "enabled": True},
    {"region": "USA", "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "name": "Dow Jones Markets", "enabled": True},
    # Japan
    {"region": "Japan", "url": "https://www.boj.or.jp/en/rss/release_2021.xml", "name": "BOJ", "enabled": True},
    {"region": "Japan", "url": "https://www3.nhk.or.jp/nhkworld/en/news/business/rss.xml", "name": "NHK World Business", "enabled": True},
    {"region": "Japan", "url": "https://tradingeconomics.com/rss/japan.xml", "name": "TradingEconomics Japan", "enabled": True},
    # China
    {"region": "China", "url": "https://www.scmp.com/rss/4/feed", "name": "SCMP", "enabled": True},
    {"region": "China", "url": "https://tradingeconomics.com/rss/china.xml", "name": "TradingEconomics China", "enabled": True},
    # Additional robust official/global
    {"region": "Eurozone", "url": "https://ec.europa.eu/eurostat/web/main/rss", "name": "Eurostat RSS", "enabled": True},
    {"region": "Global", "url": "https://www.bis.org/rss/press.xml", "name": "BIS Press Releases", "enabled": True},
    {"region": "Global", "url": "https://www.oecd.org/newsroom/rss.xml", "name": "OECD News", "enabled": True},
    {"region": "Global", "url": "https://www.imf.org/en/News/RSS", "name": "IMF News", "enabled": True},
]
