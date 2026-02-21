"""Constantes de negocio para recopilación macroeconómica."""

PRIORITY_REGIONS = ["Eurozone", "Germany", "UK", "USA", "Japan", "China"]

MACRO_KEYWORDS = [
    "gdp", "inflation", "cpi", "ppi", "unemployment", "employment", "nonfarm",
    "payroll", "retail sales", "industrial production", "manufacturing", "pmi", "ism",
    "consumer confidence", "consumer sentiment", "housing", "home sales", "durable goods",
    "trade deficit", "trade surplus", "current account", "balance of trade", "ifo", "zew",
    "central bank", "fed", "federal reserve", "ecb", "boe", "bank of japan", "boj", "pboc",
    "interest rate", "monetary policy", "fiscal policy", "rate decision", "fomc", "stimulus",
    "quantitative easing", "qe", "tapering", "rate hike", "rate cut", "recession",
    "growth forecast", "economic outlook", "economic growth", "contraction", "expansion",
    "yield curve", "bond yield", "treasury yield", "benchmark", "soft data", "hard data",
    "economic indicator", "economic data", "macroeconomic", "macro data", "economic statistics",
    "economic report", "economic survey",
]

REGION_KEYWORDS = {
    "Eurozone": ["eurozone", "euro area", "euro zone", "european union", "eu economy", "ecb", "european central bank", "europe"],
    "USA": ["us economy", "usa economy", "united states economy", "american economy", "fed", "federal reserve", "fomc", "u.s."],
    "Germany": ["german economy", "germany economy", "bundesbank", "german"],
    "UK": ["uk economy", "british economy", "bank of england", "boe", "united kingdom economy", "british"],
    "Japan": ["japan economy", "japanese economy", "bank of japan", "boj", "japanese"],
    "China": ["china economy", "chinese economy", "pboc", "peoples bank of china", "chinese"],
}

NEWS_SOURCES = [
    ("https://www.ecb.europa.eu/home/html/rss.en.html", "Eurozone"),
    ("https://ec.europa.eu/commission/presscorner/api/documents/1/feed", "Eurozone"),
    ("https://www.ft.com/rss/markets/europe", "Eurozone"),
    ("https://www.marketwatch.com/rss/topics/economy?x=1", "Eurozone"),
    ("https://tradingeconomics.com/rss/euro-area.xml", "Eurozone"),
    ("https://www.euractiv.com/feed/", "Eurozone"),
    ("https://www.politico.eu/feed/", "Eurozone"),
    ("https://www.euronews.com/rss", "Eurozone"),
    ("https://www.bruegel.org/feed/", "Eurozone"),
    ("https://www.bundesbank.de/en/press/press-releases/rss", "Germany"),
    ("https://www.ft.com/world/europe/germany/economy?format=rss", "Germany"),
    ("https://www.handelsblatt.com/contentexport/feed/wirtschaft", "Germany"),
    ("https://tradingeconomics.com/rss/germany.xml", "Germany"),
    ("https://www.dw.com/en/top-stories/business/s-1431/rss", "Germany"),
    ("https://www.bankofengland.co.uk/rss/news", "UK"),
    ("https://www.ft.com/rss/world/uk/economy", "UK"),
    ("https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation/current/rss", "UK"),
    ("https://tradingeconomics.com/rss/united-kingdom.xml", "UK"),
    ("https://www.federalreserve.gov/feeds/press_all.xml", "USA"),
    ("https://www.cnbc.com/id/20910258/device/rss/rss.html", "USA"),
    ("https://www.wsj.com/xml/rss/3_7031.xml", "USA"),
    ("https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "USA"),
    ("https://feeds.bloomberg.com/markets/news.rss", "USA"),
    ("https://www.bea.gov/rss/rss.xml", "USA"),
    ("https://www.bls.gov/feed/bls_latest_numbers.rss", "USA"),
    ("https://www.boj.or.jp/en/rss/release_2021.xml", "Japan"),
    ("https://www3.nhk.or.jp/nhkworld/en/news/business/rss.xml", "Japan"),
    ("https://tradingeconomics.com/rss/japan.xml", "Japan"),
    ("https://www.reuters.com/rssFeed/chinaNews", "China"),
    ("https://www.scmp.com/rss/4/feed", "China"),
    ("https://tradingeconomics.com/rss/china.xml", "China"),
]

OFFICIAL_SOURCES = [
    "federalreserve", "ecb.europa.eu", "bundesbank", "boj.or.jp", "ft.com", "bea.gov", "bankofengland", "ons.gov.uk", "ec.europa.eu",
]
