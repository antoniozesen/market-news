from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import streamlit as st

from src.constants import (
    DEFAULT_MACRO_KEYWORDS,
    DEFAULT_OFFICIAL_DOMAINS,
    DEFAULT_PRIORITY_REGIONS,
    DEFAULT_REGION_KEYWORDS,
    DEFAULT_RSS_SOURCES,
)
from src.email_service import send_email
from src.html_builder import render_email_html
from src.leak_scanner import scan_editor_rows, scan_html
from src.news_service import (
    RuntimeSettings,
    deduplicate_rows,
    dependency_status,
    discover_investopedia_url,
    fetch_investopedia_week_ahead,
    fetch_rss_news,
    parse_date_any,
    score_item,
)
from src.settings import load_smtp_settings

st.set_page_config(page_title="Macro News Digest Studio", layout="wide")

st.markdown(
    """
    <style>
      [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background: #f8fafc !important;
      }
      .stApp, html, body, [class*="st-"] { color: #0f172a !important; }
      .kpi-card { background:#fff; border:1px solid #dbeafe; border-radius:12px; padding:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _init_state() -> None:
    if "settings" not in st.session_state:
        st.session_state["settings"] = {
            "macro_keywords": DEFAULT_MACRO_KEYWORDS.copy(),
            "region_keywords": json.loads(json.dumps(DEFAULT_REGION_KEYWORDS)),
            "official_domains": DEFAULT_OFFICIAL_DOMAINS.copy(),
            "region_priority": DEFAULT_PRIORITY_REGIONS.copy(),
            "max_items_per_region_per_day": 6,
            "max_global_items": 5,
            "minimum_score": 1.4,
            "investopedia_override_url": "",
        }
    if "fetched_df" not in st.session_state:
        st.session_state["fetched_df"] = pd.DataFrame()
    if "editor_df" not in st.session_state:
        st.session_state["editor_df"] = pd.DataFrame()
    if "investopedia_block" not in st.session_state:
        st.session_state["investopedia_block"] = None


def _runtime_settings(strict_macro_filter: bool, include_official_always: bool) -> RuntimeSettings:
    s = st.session_state["settings"]
    return RuntimeSettings(
        macro_keywords=s["macro_keywords"],
        region_keywords=s["region_keywords"],
        official_domains=s["official_domains"],
        priority_regions=s["region_priority"],
        strict_macro_filter=strict_macro_filter,
        include_official_always=include_official_always,
    )


def _normalize_editor_df(df: pd.DataFrame) -> pd.DataFrame:
    columns = ["Include", "Date", "Region", "Title", "Description", "Notes", "Link", "Score", "Source", "CanonicalURL"]
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = True if col == "Include" else ""

    out["Include"] = out["Include"].fillna(True).astype(bool)
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.date
    out["Date"] = out["Date"].fillna(dt.date.today())
    for text_col in ["Region", "Title", "Description", "Notes", "Link", "Source", "CanonicalURL"]:
        out[text_col] = out[text_col].fillna("").astype(str)
    out["Score"] = pd.to_numeric(out["Score"], errors="coerce").fillna(1.0).astype(float)
    return out[columns]


def _build_html(start_date: dt.date, end_date: dt.date) -> str:
    rows = st.session_state["editor_df"].to_dict(orient="records")
    s = st.session_state["settings"]
    return render_email_html(
        rows,
        start_date=start_date,
        end_date=end_date,
        region_priority=s["region_priority"],
        investopedia_block=st.session_state.get("investopedia_block"),
        max_items_per_region_per_day=int(s["max_items_per_region_per_day"]),
        max_global_items=int(s["max_global_items"]),
        minimum_score=float(s["minimum_score"]),
    )


_init_state()

st.title("📰 Macro News Digest Studio")
st.caption("Workflow: fetch → edit → validate → preview → export/send")

smtp, missing_smtp = load_smtp_settings()
if missing_smtp:
    st.warning("Missing SMTP secrets: " + ", ".join(missing_smtp))

with st.sidebar:
    st.header("Data controls")
    default_end = dt.date.today()
    default_start = default_end - dt.timedelta(days=6)
    start_date = st.date_input("Start date", value=default_start)
    end_date = st.date_input("End date", value=default_end)

    include_investopedia = st.toggle("Include Investopedia Week Ahead", value=True)
    strict_macro_filter = st.toggle("Strict macro filter", value=True)
    include_official_always = st.toggle("Include official sources always", value=True)

    region_priority_text = st.text_input(
        "Region priority (comma-separated)",
        value=", ".join(st.session_state["settings"]["region_priority"]),
    )
    st.session_state["settings"]["region_priority"] = [x.strip() for x in region_priority_text.split(",") if x.strip()]

    deps_ok, missing = dependency_status()
    if not deps_ok:
        st.error("Missing runtime dependencies: " + ", ".join(missing))

    fetch_clicked = st.button("Fetch / Build dataset", type="primary", disabled=not deps_ok, use_container_width=True)

if start_date > end_date:
    st.error("Start date must be before or equal to end date.")
    st.stop()

if fetch_clicked:
    runtime = _runtime_settings(strict_macro_filter=strict_macro_filter, include_official_always=include_official_always)
    rows, errors = fetch_rss_news(DEFAULT_RSS_SOURCES, start_date, end_date, runtime)

    investopedia_block = None
    if include_investopedia:
        override = st.session_state["settings"].get("investopedia_override_url")
        url = discover_investopedia_url(override_url=override)
        if url:
            investopedia_block = fetch_investopedia_week_ahead(url)
    st.session_state["investopedia_block"] = investopedia_block

    st.session_state["fetched_df"] = _normalize_editor_df(pd.DataFrame(rows))
    st.session_state["editor_df"] = st.session_state["fetched_df"].copy()

    if errors:
        st.warning("Some feeds failed:\n- " + "\n- ".join(errors[:12]))

if st.session_state["editor_df"].empty:
    st.info("Use 'Fetch / Build dataset' to start.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.markdown(f"<div class='kpi-card'><b>Total rows</b><br>{len(st.session_state['editor_df'])}</div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi-card'><b>Date range</b><br>{start_date} → {end_date}</div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi-card'><b>SMTP</b><br>{'Ready ✅' if smtp.ready else 'Not ready ⚠️'}</div>", unsafe_allow_html=True)

tab_editor, tab_preview, tab_settings = st.tabs(["Editor", "Preview", "Settings"])

with tab_editor:
    editor_df = _normalize_editor_df(st.session_state["editor_df"])

    edited = st.data_editor(
        editor_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Include": st.column_config.CheckboxColumn("Include"),
            "Date": st.column_config.DateColumn("Date"),
            "Region": st.column_config.SelectboxColumn("Region", options=st.session_state["settings"]["region_priority"] + ["Global", "Other"]),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Notes": st.column_config.TextColumn("Notes", width="medium"),
            "Link": st.column_config.LinkColumn("Link", width="medium"),
            "Score": st.column_config.NumberColumn("Score", format="%.4f", min_value=0.0, max_value=20.0, step=0.1),
            "Source": st.column_config.TextColumn("Source", width="small", disabled=True),
            "CanonicalURL": st.column_config.TextColumn("CanonicalURL", disabled=True),
        },
    )
    st.session_state["editor_df"] = _normalize_editor_df(edited)

    c1, c2, c3, c4, c5 = st.columns(5)
    if c1.button("Add manual item", use_container_width=True):
        new_row = {
            "Include": True,
            "Date": dt.date.today(),
            "Region": "Global",
            "Title": "Manual item",
            "Description": "",
            "Notes": "",
            "Link": "https://",
            "Score": 1.0,
            "Source": "manual",
            "CanonicalURL": "manual://item",
        }
        st.session_state["editor_df"] = _normalize_editor_df(pd.concat([st.session_state["editor_df"], pd.DataFrame([new_row])], ignore_index=True))
        st.rerun()

    if c2.button("Deduplicate", use_container_width=True):
        deduped, removed = deduplicate_rows(st.session_state["editor_df"].to_dict(orient="records"))
        st.session_state["editor_df"] = _normalize_editor_df(pd.DataFrame(deduped))
        st.success(f"Removed {removed} duplicate rows.")
        st.rerun()

    if c3.button("Re-score", use_container_width=True):
        rt = _runtime_settings(strict_macro_filter=False, include_official_always=True)
        rescored: list[dict] = []
        for row in st.session_state["editor_df"].to_dict(orient="records"):
            d = parse_date_any(row.get("Date")) or start_date
            new_score = score_item(
                title=str(row.get("Title", "")),
                description=str(row.get("Description", "")),
                domain=str(row.get("Source", "")),
                region=str(row.get("Region", "Global")),
                date_value=d,
                start_date=start_date,
                end_date=end_date,
                rt=rt,
            )
            row["Score"] = new_score
            rescored.append(row)
        st.session_state["editor_df"] = _normalize_editor_df(pd.DataFrame(rescored))
        st.success("Scores refreshed.")
        st.rerun()

    if c4.button("Sort", use_container_width=True):
        sorted_df = st.session_state["editor_df"].sort_values(by=["Date", "Score"], ascending=[True, False])
        st.session_state["editor_df"] = _normalize_editor_df(sorted_df)
        st.success("Sorted by Date and Score.")
        st.rerun()

    if c5.button("Reset to fetched dataset", use_container_width=True):
        st.session_state["editor_df"] = _normalize_editor_df(st.session_state["fetched_df"])
        st.success("Editor reset.")
        st.rerun()

with tab_preview:
    rows = st.session_state["editor_df"].to_dict(orient="records")
    findings = scan_editor_rows(rows)
    if findings:
        st.warning("Leak scanner findings:\n- " + "\n- ".join(findings[:10]))

    html = _build_html(start_date, end_date)
    html_findings = scan_html(html)
    if html_findings:
        st.warning("HTML scanner findings:\n- " + "\n- ".join(html_findings))

    st.components.v1.html(html, height=720, scrolling=True)

    p1, p2, p3 = st.columns(3)
    p1.download_button(
        "Export HTML",
        data=html,
        file_name=f"macro_news_{start_date}_to_{end_date}.html",
        mime="text/html",
        use_container_width=True,
        disabled=bool(html_findings),
    )

    test_to = p2.text_input("Test recipient", value=smtp.default_to or "")
    final_to = p3.text_input("Final recipient", value=smtp.default_to or "", key="final_to")

    send_disabled = (not smtp.ready) or bool(findings) or bool(html_findings)
    if st.button("Send test email", disabled=send_disabled, use_container_width=True):
        ok, msg = send_email(html, recipient=test_to, subject=f"[TEST] Macro Digest {start_date} → {end_date}", smtp=smtp)
        st.success(msg) if ok else st.error(msg)

    if st.button("Send final email", disabled=send_disabled, use_container_width=True):
        ok, msg = send_email(html, recipient=final_to, subject=f"Macro Digest {start_date} → {end_date}", smtp=smtp)
        st.success(msg) if ok else st.error(msg)

with tab_settings:
    st.subheader("Keywords and policy")
    s = st.session_state["settings"]

    macro_text = st.text_area("Macro keywords (one per line)", value="\n".join(s["macro_keywords"]), height=180)
    s["macro_keywords"] = [x.strip() for x in macro_text.splitlines() if x.strip()]

    region_json = st.text_area("Region keywords JSON", value=json.dumps(s["region_keywords"], indent=2), height=220)
    try:
        parsed_region = json.loads(region_json)
        if isinstance(parsed_region, dict):
            s["region_keywords"] = {str(k): [str(i) for i in v] for k, v in parsed_region.items() if isinstance(v, list)}
        else:
            st.error("Region keywords must be a JSON object of lists.")
    except json.JSONDecodeError as exc:
        st.error(f"Invalid region keywords JSON: {exc}")

    official_text = st.text_area("Official domains whitelist (one per line)", value="\n".join(s["official_domains"]), height=140)
    s["official_domains"] = [x.strip().lower() for x in official_text.splitlines() if x.strip()]

    st.subheader("Caps and thresholds")
    s["max_items_per_region_per_day"] = st.number_input("Max items per region per day", min_value=1, max_value=20, value=int(s["max_items_per_region_per_day"]))
    s["max_global_items"] = st.number_input("Max global items", min_value=0, max_value=20, value=int(s["max_global_items"]))
    s["minimum_score"] = st.number_input("Minimum score threshold", min_value=0.0, max_value=20.0, value=float(s["minimum_score"]), step=0.1, format="%.2f")

    st.subheader("Investopedia override")
    s["investopedia_override_url"] = st.text_input("Manual Investopedia URL (optional)", value=s.get("investopedia_override_url", ""))

    st.caption("Settings are kept in current session state.")
