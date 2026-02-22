# Macro News Digest Studio

A Streamlit editorial app to fetch macro RSS news, curate items, preview the exact HTML digest, and send via SMTP.

## What this app fixes
- Better Europe coverage (Eurozone/Germany/UK) by restoring high-coverage European feeds and adding robust official sources.
- Fewer false negatives using broad capture + score-based filtering (strict mode optional).
- No silent feed failures: each source shows diagnostics in **Source Health**.

---

## File tree

```text
.
├── .streamlit/
│   └── config.toml
├── app.py
├── LICENSE
├── README.md
├── requirements.txt
├── secrets.toml.example
└── src/
    ├── __init__.py
    ├── constants.py
    ├── email_service.py
    ├── html_builder.py
    ├── leak_scanner.py
    ├── news_service.py
    └── settings.py
```

---

## Create a public GitHub repository (web UI only)

1. Go to https://github.com/new
2. Choose a name (example: `macro-news-digest-studio`)
3. Set visibility to **Public**
4. Click **Create repository**
5. In the repo page: **Add file → Upload files**
6. Upload all project files from this repository tree
7. Commit with message like `Initial upload`

---

## Deploy to Streamlit Community Cloud (web UI only)

1. Open https://share.streamlit.io
2. Sign in with GitHub
3. Click **New app**
4. Select your repo + branch
5. Main file path: `app.py`
6. Click **Deploy**

---

## Secrets (required) in Streamlit Cloud

In your Streamlit app settings:
1. Open **Settings → Secrets**
2. Paste TOML (replace with your real values):

```toml
SMTP_USER = "your_user@example.com"
SMTP_PASS = "your_password_or_app_password"
SMTP_TO = "default_recipient@example.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
```

Only these `st.secrets` keys are used for SMTP.

---

## Sources included (coverage-oriented)

### Eurozone / Europe
- ECB RSS: https://www.ecb.europa.eu/home/html/rss.en.html
- EU Commission PressCorner: https://ec.europa.eu/commission/presscorner/api/documents/1/feed
- FT Europe Markets: https://www.ft.com/rss/markets/europe
- TradingEconomics Euro Area: https://tradingeconomics.com/rss/euro-area.xml
- Euractiv: https://www.euractiv.com/feed/
- Politico EU: https://www.politico.eu/feed/
- Euronews: https://www.euronews.com/rss
- Bruegel: https://www.bruegel.org/feed/

### Germany
- Bundesbank: https://www.bundesbank.de/en/press/press-releases/rss
- Handelsblatt Wirtschaft: https://www.handelsblatt.com/contentexport/feed/wirtschaft
- TradingEconomics Germany: https://tradingeconomics.com/rss/germany.xml
- DW Business: https://www.dw.com/en/top-stories/business/s-1431/rss

### UK
- Bank of England: https://www.bankofengland.co.uk/rss/news
- ONS CPI: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceinflation/current/rss
- TradingEconomics UK: https://tradingeconomics.com/rss/united-kingdom.xml

### USA
- Federal Reserve: https://www.federalreserve.gov/feeds/press_all.xml
- BEA: https://www.bea.gov/rss/rss.xml
- BLS: https://www.bls.gov/feed/bls_latest_numbers.rss
- CNBC: https://www.cnbc.com/id/20910258/device/rss/rss.html
- Dow Jones Markets RSS: https://feeds.a.dj.com/rss/RSSMarketsMain.xml

### Japan
- BOJ: https://www.boj.or.jp/en/rss/release_2021.xml
- NHK World Business: https://www3.nhk.or.jp/nhkworld/en/news/business/rss.xml
- TradingEconomics Japan: https://tradingeconomics.com/rss/japan.xml

### China
- SCMP: https://www.scmp.com/rss/4/feed
- TradingEconomics China: https://tradingeconomics.com/rss/china.xml

### Additional robust official sources
- Eurostat RSS: https://ec.europa.eu/eurostat/web/main/rss
- BIS press RSS: https://www.bis.org/rss/press.xml
- OECD news RSS: https://www.oecd.org/newsroom/rss.xml
- IMF news RSS: https://www.imf.org/en/News/RSS

---

## How to use

### Sidebar
- Choose start/end date
- Toggle:
  - Include Investopedia Week Ahead
  - Strict macro filter (**OFF by default**)
  - Include official sources always
  - Include undated items
- Set minimum score
- Click **Fetch / Build dataset**

### Tabs
- **Editor**: curate table rows (Include, Date, Region, Title, Description, Notes, Link, Score, Source)
- **Preview**: exact HTML preview + Export HTML + Send test/final email
- **Settings**: keywords, region map, official domains, caps/thresholds
- **Source Health**: diagnostics per feed with red flags for failures

---

## Troubleshooting: Source Health

If Europe looks sparse, open **Source Health** and check:
- `http_status` (must ideally be 200)
- `entries_parsed` (if 0, feed likely blocked/changed)
- `entries_with_dates` and `entries_in_range`
- `error_message` for parser/network hints

The app performs browser-like requests with timeout + one retry, and keeps failures visible (no silent drop).

---

## Notes

- Strict mode filters by score threshold after scoring.
- Broad capture mode includes general econ/markets terms and official domains to reduce false negatives.
- Numbers are formatted human-readably (2–4 decimals).
