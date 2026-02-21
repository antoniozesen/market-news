from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from src.email_service import send_email
from src.html_builder import build_email_html
from src.leak_scanner import scan_editor_rows, scan_html
from src.news_service import default_last_week_range, fetch_news
from src.settings import load_settings

st.set_page_config(page_title="Macro News Digest", layout="wide")
st.title("Macro News Digest Editor")

settings, missing = load_settings()
if missing:
    st.warning(f"Secrets faltantes o inválidos: {', '.join(missing)}")

start_default, end_default = default_last_week_range()
col1, col2 = st.columns(2)
start_date = col1.date_input("Start date", value=start_default)
end_date = col2.date_input("End date", value=end_default)

if start_date > end_date:
    st.error("Start date must be <= end date")
    st.stop()

if st.button("Fetch / Build dataset", type="primary"):
    with st.spinner("Fetching feeds..."):
        st.session_state["news_items"] = fetch_news(start_date, end_date, add_week_ahead=True)

rows = st.session_state.get("news_items", [])
if rows:
    st.subheader("Editorial dataset")
    df = pd.DataFrame(rows)
    for c in ["included", "title", "description", "date", "region", "notes", "link", "relevance_score"]:
        if c not in df.columns:
            df[c] = "" if c != "included" else True

    edited = st.data_editor(
        df[["included", "title", "description", "date", "region", "notes", "link", "relevance_score"]],
        use_container_width=True,
        num_rows="dynamic",
    )

    st.caption("Add manual item")
    with st.form("manual_item"):
        m_title = st.text_input("Title")
        m_desc = st.text_area("Description")
        m_link = st.text_input("Link", value="https://")
        m_date = st.date_input("Date", value=dt.date.today(), key="manual_date")
        m_region = st.text_input("Region", value="Eurozone")
        m_notes = st.text_input("Notes")
        if st.form_submit_button("Add item") and m_title:
            new_row = {
                "included": True,
                "title": m_title,
                "description": m_desc,
                "date": m_date.isoformat(),
                "region": m_region,
                "notes": m_notes,
                "link": m_link,
                "relevance_score": 2,
            }
            edited = pd.concat([edited, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Manual item added")

    edited_rows = edited.to_dict(orient="records")
    findings = scan_editor_rows(edited_rows)
    if findings:
        st.warning("Secret leakage scanner encontró posibles tokens:\n- " + "\n- ".join(findings))

    html = build_email_html(edited_rows, start_date, end_date)
    html_findings = scan_html(html)
    if html_findings:
        st.warning("HTML scanner:\n- " + "\n- ".join(html_findings))

    st.subheader("Preview")
    st.components.v1.html(html, height=500, scrolling=True)

    st.download_button(
        "Generate HTML (download)",
        data=html,
        file_name=f"macro_news_{start_date}_to_{end_date}.html",
        mime="text/html",
        disabled=bool(html_findings),
    )

    recipient = st.text_input("Recipient", value=settings.email_recipient_default or "")
    subject = f"News and Events Digest: {start_date} to {end_date}"
    can_send = settings.email_ready and not findings and not html_findings
    if not settings.email_ready:
        st.info("Completa secrets para habilitar envío de email.")

    if st.button("Send email", disabled=not can_send):
        ok, msg = send_email(html, recipient=recipient, subject=subject, settings=settings)
        st.success(msg) if ok else st.error(msg)
else:
    st.info("Pulsa 'Fetch / Build dataset' para comenzar.")
