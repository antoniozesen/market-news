from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import streamlit as st

from src.constants import (
    MACRO_KEYWORDS_DEFAULT,
    OFFICIAL_DOMAINS_DEFAULT,
    PRIORITY_REGIONS_DEFAULT,
    REGION_KEYWORDS_DEFAULT,
    SOURCES_DEFAULT,
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
  [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] { background: #f8fafc !important; }
  .stApp, html, body, [class*="st-"] { color: #0f172a !important; }
  .kpi-card { background:#fff; border:1px solid #dbeafe; border-radius:12px; padding:12px; }
</style>
""",
    unsafe_allow_html=True,
)


def _init_state() -> None:
    if "settings" not in st.session_state:
        st.session_state["settings"] = {
            "macro_keywords": MACRO_KEYWORDS_DEFAULT.copy(),
            "region_keywords": json.loads(json.dumps(REGION_KEYWORDS_DEFAULT)),
            "official_domains": OFFICIAL_DOMAINS_DEFAULT.copy(),
            "region_priority": PRIORITY_REGIONS_DEFAULT.copy(),
            "sources": json.loads(json.dumps(SOURCES_DEFAULT)),
            "max_items_per_region_per_day": 6,
            "max_global_items": 6,
            "minimum_score": 1.4,
            "investopedia_override_url": "",
        }
    for k in ["fetched_df", "editor_df", "source_health_df"]:
        if k not in st.session_state:
            st.session_state[k] = pd.DataFrame()
    if "investopedia_block" not in st.session_state:
        st.session_state["investopedia_block"] = None


def _runtime_settings(strict_macro_filter: bool, include_official_always: bool, include_undated_items: bool, min_score: float) -> RuntimeSettings:
    s = st.session_state["settings"]
    return RuntimeSettings(
        macro_keywords=s["macro_keywords"],
        region_keywords=s["region_keywords"],
        official_domains=s["official_domains"],
        priority_regions=s["region_priority"],
        strict_macro_filter=strict_macro_filter,
        include_official_always=include_official_always,
        include_undated_items=include_undated_items,
        min_score_threshold=min_score,
    )


def _normalize_editor_df(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Include", "Date", "Region", "Title", "Description", "Notes", "Link", "Score", "Source", "CanonicalURL"]
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = True if c == "Include" else ""
    out["Include"] = out["Include"].fillna(True).astype(bool)
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.date
    out["Date"] = out["Date"].fillna(dt.date.today())
    for c in ["Region", "Title", "Description", "Notes", "Link", "Source", "CanonicalURL"]:
        out[c] = out[c].fillna("").astype(str)
    out["Score"] = pd.to_numeric(out["Score"], errors="coerce").fillna(1.0).astype(float)
    return out[cols]


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
    today = dt.date.today()
    start_date = st.date_input("Start date", value=today - dt.timedelta(days=6))
    end_date = st.date_input("End date", value=today)

    include_investopedia = st.toggle("Include Investopedia Week Ahead", value=True)
    strict_macro_filter = st.toggle("Strict macro filter", value=False)
    include_official_always = st.toggle("Include official sources always", value=True)
    include_undated_items = st.toggle("Include undated items", value=True)
    min_score = st.slider("Minimum score", min_value=0.0, max_value=8.0, value=1.4, step=0.1)

    region_priority_text = st.text_input("Region priority (comma-separated)", value=", ".join(st.session_state["settings"]["region_priority"]))
    st.session_state["settings"]["region_priority"] = [x.strip() for x in region_priority_text.split(",") if x.strip()]

    deps_ok, missing_deps = dependency_status()
    if not deps_ok:
        st.error("Missing runtime dependencies: " + ", ".join(missing_deps))
    fetch_clicked = st.button("Fetch / Build dataset", disabled=not deps_ok, type="primary", use_container_width=True)

if start_date > end_date:
    st.error("Start date must be <= end date.")
    st.stop()

if fetch_clicked:
    rt = _runtime_settings(strict_macro_filter, include_official_always, include_undated_items, min_score)
    rows, source_health = fetch_rss_news(st.session_state["settings"]["sources"], start_date, end_date, rt)

    investopedia_block = None
    if include_investopedia:
        override = st.session_state["settings"].get("investopedia_override_url", "")
        url = discover_investopedia_url(override)
        if url:
            investopedia_block = fetch_investopedia_week_ahead(url)
    st.session_state["investopedia_block"] = investopedia_block

    st.session_state["fetched_df"] = _normalize_editor_df(pd.DataFrame(rows))
    st.session_state["editor_df"] = st.session_state["fetched_df"].copy()

    health_df = pd.DataFrame(source_health)
    if not health_df.empty:
        health_df = health_df.sort_values(by=["entries_in_range", "entries_parsed"], ascending=[False, False])
    st.session_state["source_health_df"] = health_df

if st.session_state["editor_df"].empty:
    st.info("Use 'Fetch / Build dataset' to start.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.markdown(f"<div class='kpi-card'><b>Total rows</b><br>{len(st.session_state['editor_df'])}</div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi-card'><b>Date range</b><br>{start_date} → {end_date}</div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi-card'><b>SMTP status</b><br>{'Ready ✅' if smtp.ready else 'Missing ⚠️'}</div>", unsafe_allow_html=True)

tab_editor, tab_preview, tab_settings, tab_health = st.tabs(["Editor", "Preview", "Settings", "Source Health"])

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
            "Region": st.column_config.TextColumn("Region"),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Notes": st.column_config.TextColumn("Notes", width="medium"),
            "Link": st.column_config.LinkColumn("Link", width="medium"),
            "Score": st.column_config.NumberColumn("Score", min_value=0.0, max_value=20.0, step=0.1, format="%.4f"),
            "Source": st.column_config.TextColumn("Source"),
            "CanonicalURL": st.column_config.TextColumn("CanonicalURL", disabled=True),
        },
    )
    st.session_state["editor_df"] = _normalize_editor_df(edited)

    with st.expander("Add manual item", expanded=False):
        c1, c2 = st.columns(2)
        m_title = c1.text_input("Title", key="manual_title")
        m_region = c2.text_input("Region", value="Eurozone", key="manual_region")
        m_desc = st.text_area("Description (what happened / what will happen)", key="manual_desc")
        c3, c4, c5 = st.columns([2, 1, 1])
        m_link = c3.text_input("Link", value="https://", key="manual_link")
        m_date = c4.date_input("Date", value=today, key="manual_date")
        m_score = c5.number_input("Score", min_value=0.0, max_value=20.0, value=2.0, step=0.1, key="manual_score")
        if st.button("Add manual row") and m_title.strip():
            row = {
                "Include": True,
                "Date": m_date,
                "Region": m_region.strip() or "Global",
                "Title": m_title.strip(),
                "Description": m_desc.strip(),
                "Notes": "",
                "Link": m_link.strip() or "https://",
                "Score": float(m_score),
                "Source": "manual",
                "CanonicalURL": f"manual://{m_title[:24]}",
            }
            st.session_state["editor_df"] = _normalize_editor_df(pd.concat([st.session_state["editor_df"], pd.DataFrame([row])], ignore_index=True))
            st.success("Manual item added.")
            st.rerun()

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("Deduplicate", use_container_width=True):
        rows, removed = deduplicate_rows(st.session_state["editor_df"].to_dict(orient="records"))
        st.session_state["editor_df"] = _normalize_editor_df(pd.DataFrame(rows))
        st.success(f"Removed {removed} duplicates.")
        st.rerun()

    if b2.button("Re-score", use_container_width=True):
        rt = _runtime_settings(False, True, include_undated_items, min_score)
        rescored: list[dict] = []
        for row in st.session_state["editor_df"].to_dict(orient="records"):
            d = parse_date_any(row.get("Date")) or start_date
            row["Score"] = score_item(
                title=str(row.get("Title", "")),
                description=str(row.get("Description", "")),
                domain=str(row.get("Source", "")),
                region=str(row.get("Region", "Global")),
                date_value=d,
                start_date=start_date,
                end_date=end_date,
                rt=rt,
            )
            rescored.append(row)
        st.session_state["editor_df"] = _normalize_editor_df(pd.DataFrame(rescored))
        st.success("Scores refreshed.")
        st.rerun()

    if b3.button("Sort", use_container_width=True):
        st.session_state["editor_df"] = _normalize_editor_df(st.session_state["editor_df"].sort_values(by=["Date", "Score"], ascending=[True, False]))
        st.rerun()

    if b4.button("Reset to fetched dataset", use_container_width=True):
        st.session_state["editor_df"] = _normalize_editor_df(st.session_state["fetched_df"])
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

    st.components.v1.html(html, height=740, scrolling=True)

    c1, c2, c3 = st.columns(3)
    export_blocked = bool(html_findings)
    c1.download_button("Export HTML", data=html, file_name=f"macro_news_{start_date}_to_{end_date}.html", mime="text/html", disabled=export_blocked, use_container_width=True)
    if export_blocked:
        c1.caption("Export disabled because scanner found potential secrets.")

    test_to = c2.text_input("Test recipient", value=smtp.default_to or "")
    final_to = c3.text_input("Final recipient", value=smtp.default_to or "", key="final_to")

    blockers: list[str] = []
    if findings:
        blockers.append("Editor scanner alerts")
    if html_findings:
        blockers.append("HTML scanner alerts")
    if not smtp.ready:
        blockers.append("Missing SMTP secrets")
    if not test_to.strip() or not final_to.strip():
        blockers.append("Recipient is empty")
    if blockers:
        st.info("Actions disabled until resolved: " + " | ".join(blockers))

    send_disabled = bool(blockers)
    if st.button("Send test email", disabled=send_disabled, use_container_width=True):
        ok, msg = send_email(html, recipient=test_to.strip(), subject=f"[TEST] Macro Digest {start_date} → {end_date}", smtp=smtp)
        st.success(msg) if ok else st.error(msg)
    if st.button("Send final email", disabled=send_disabled, use_container_width=True):
        ok, msg = send_email(html, recipient=final_to.strip(), subject=f"Macro Digest {start_date} → {end_date}", smtp=smtp)
        st.success(msg) if ok else st.error(msg)

with tab_settings:
    s = st.session_state["settings"]
    st.subheader("Keywords and region logic")

    macro_text = st.text_area("Macro keywords (one per line)", value="\n".join(s["macro_keywords"]), height=180)
    s["macro_keywords"] = [x.strip() for x in macro_text.splitlines() if x.strip()]

    region_json = st.text_area("Region keywords JSON", value=json.dumps(s["region_keywords"], indent=2), height=250)
    try:
        parsed = json.loads(region_json)
        if isinstance(parsed, dict):
            s["region_keywords"] = {str(k): [str(i) for i in v] for k, v in parsed.items() if isinstance(v, list)}
        else:
            st.error("Region keywords must be a JSON object.")
    except json.JSONDecodeError as exc:
        st.error(f"Invalid JSON: {exc}")

    official_text = st.text_area("Official domains whitelist (one per line)", value="\n".join(s["official_domains"]), height=120)
    s["official_domains"] = [x.strip().lower() for x in official_text.splitlines() if x.strip()]

    st.subheader("Email caps")
    s["max_items_per_region_per_day"] = st.number_input("Max items per region/day", min_value=1, max_value=20, value=int(s["max_items_per_region_per_day"]))
    s["max_global_items"] = st.number_input("Max global items", min_value=0, max_value=20, value=int(s["max_global_items"]))
    s["minimum_score"] = st.number_input("Minimum score threshold", min_value=0.0, max_value=20.0, value=float(s["minimum_score"]), step=0.1)

    st.subheader("Investopedia override")
    s["investopedia_override_url"] = st.text_input("Manual Investopedia URL", value=s.get("investopedia_override_url", ""))

with tab_health:
    health_df = st.session_state.get("source_health_df", pd.DataFrame())
    if health_df.empty:
        st.info("No source diagnostics yet. Run Fetch / Build dataset.")
    else:
        health_df = health_df.copy()
        health_df["flag"] = health_df.apply(
            lambda r: "🚩" if (r.get("http_status") != 200 or int(r.get("entries_parsed", 0)) == 0) else "",
            axis=1,
        )
        st.dataframe(
            health_df[["flag", "region", "name", "http_status", "entries_parsed", "entries_with_dates", "entries_in_range", "error_message", "url"]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Diagnostics: HTTP status, parsed entries, dated entries and in-range entries. Any failing feed is visible here.")
