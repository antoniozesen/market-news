# Macro News Digest Studio

Editorial Streamlit app to build a macro-news digest email:
1. Fetch RSS macro news + optional Investopedia “Week Ahead”.
2. Curate/edit rows in an editor table.
3. Preview **exact HTML email**.
4. Export HTML or send by SMTP.

---

## Features

- Streamlit Community Cloud deployable.
- Secrets hygiene: SMTP credentials are read **only** from `st.secrets`.
- Tabs workflow: **Editor | Preview | Settings**.
- Sidebar controls for date range, filter toggles, region priority, fetch action.
- Deduplication using canonical URL + fuzzy title similarity (RapidFuzz).
- Re-scoring engine (official source bonus, macro keyword hits, region priority bonus, recency bonus).
- Human-readable number formatting (2–4 decimals, no noisy `0.000000`).
- Safe HTML rendering with escaped user-entered text.

---

## Repository structure

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

## Create a public GitHub repo (web UI only)

1. Open [https://github.com/new](https://github.com/new).
2. Repository name: `macro-news-digest-studio` (or your preferred name).
3. Visibility: **Public**.
4. Click **Create repository**.
5. In your new repo page, click **Add file → Upload files**.
6. Drag and drop all files from this project.
7. Add commit message, e.g. `Initial upload`.
8. Click **Commit changes**.

---

## Deploy on Streamlit Community Cloud (web UI only)

1. Open [https://share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your repository and branch.
4. Main file path: `app.py`.
5. Click **Deploy**.

---

## Add secrets in Streamlit Cloud

In Streamlit Cloud app page:
1. Click **⋮ (menu) → Settings → Secrets**.
2. Paste TOML (replace values):

```toml
SMTP_USER = "your_smtp_user@example.com"
SMTP_PASS = "your_smtp_password_or_app_password"
SMTP_TO = "default.recipient@example.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
```

3. Click **Save** and **Reboot app**.

### Required secrets checklist

- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_TO`
- `SMTP_HOST`
- `SMTP_PORT`

If any are missing/invalid, send buttons are disabled and a warning is shown.

---

## How to use the app

### Sidebar
- Select **start/end date**.
- Toggle:
  - Include Investopedia Week Ahead
  - Strict macro filter
  - Include official sources always
- Edit region priority (comma-separated).
- Click **Fetch / Build dataset**.

### Editor tab
- Edit columns:
  - Include, Date, Region, Title, Description, Notes, Link, Score, Source
- Buttons:
  - Add manual item
  - Deduplicate
  - Re-score
  - Sort
  - Reset to fetched dataset

### Preview tab
- Renders exact final HTML.
- Actions:
  - Export HTML
  - Send test email
  - Send final email

### Settings tab
- Edit:
  - macro keywords list
  - region keywords dictionary (JSON)
  - official domains whitelist
  - caps and minimum score threshold
  - manual Investopedia URL override

---

## Local run (conceptual, no CLI dependency)

If you prefer local execution, any Python environment that can install `requirements.txt` and run Streamlit is enough. The same `st.secrets` keys must be provided in Streamlit’s local secrets file.

---

## Notes

- Free-source only stack: `feedparser`, `requests`, `beautifulsoup4`, `pandas`, `rapidfuzz`, `streamlit`.
- Avoid mixing incompatible chart scales; this app currently focuses on editorial table + HTML digest preview.
