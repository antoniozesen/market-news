from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from src.email_service import send_email
from src.html_builder import build_email_html
from src.leak_scanner import scan_editor_rows, scan_html
from src.news_service import default_last_week_range, dependency_status, fetch_news
from src.settings import load_settings

st.set_page_config(page_title="Macro News Digest", layout="wide")

st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg,#f8fafc 0%,#eef2ff 100%);
    color: #0f172a;
}
[data-testid="stSidebar"] {
    background: #f8fafc;
}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.stMarkdown, .stCaption, .stText, .stSubheader, .stHeader, label {
    color: #0f172a !important;
}
.card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.8rem 1rem;
}
.kpi {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: .5rem .8rem;
    text-align: center;
    color: #0f172a;
}
.preview-wrap {
    background:#ffffff;
    border:1px solid #dbe4ff;
    border-radius:12px;
    padding:8px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("📰 Macro News Digest Studio")
st.caption("Flujo editorial: fetch → editar → validar → preview → export/send")

settings, missing = load_settings()
if missing:
    st.warning(f"Secrets faltantes o inválidos: {', '.join(missing)}")

# Sidebar UX: controles de fecha + acciones
start_default, end_default = default_last_week_range()
with st.sidebar:
    st.header("⚙️ Controles")
    preset = st.radio(
        "Rango rápido",
        ["Semana pasada", "Últimos 7 días", "Mes actual", "Custom"],
        index=0,
        horizontal=False,
    )
    today = dt.date.today()
    if preset == "Semana pasada":
        start_seed, end_seed = default_last_week_range(today)
    elif preset == "Últimos 7 días":
        start_seed, end_seed = today - dt.timedelta(days=6), today
    elif preset == "Mes actual":
        start_seed, end_seed = today.replace(day=1), today
    else:
        start_seed, end_seed = start_default, end_default

    start_date = st.date_input("Start date", value=start_seed)
    end_date = st.date_input("End date", value=end_seed)

    deps_ok, missing_deps = dependency_status()
    if not deps_ok:
        st.error("Faltan dependencias: " + ", ".join(missing_deps))
        st.caption("Instala requirements.txt para habilitar ingestión.")

    fetch_clicked = st.button("🔄 Fetch / Build dataset", type="primary", use_container_width=True, disabled=not deps_ok)

if start_date > end_date:
    st.error("Start date must be <= end date")
    st.stop()

if fetch_clicked:
    with st.spinner("Fetching feeds..."):
        st.session_state["news_items"] = fetch_news(start_date, end_date, add_week_ahead=True)

rows = st.session_state.get("news_items", [])
if not rows:
    st.info("Pulsa **Fetch / Build dataset** para comenzar.")
    st.stop()

# KPIs
k1, k2, k3 = st.columns(3)
k1.markdown(f"<div class='kpi'><b>Total items</b><br><span style='font-size:1.4rem'>{len(rows)}</span></div>", unsafe_allow_html=True)
k2.markdown(
    f"<div class='kpi'><b>Rango</b><br><span style='font-size:1rem'>{start_date} → {end_date}</span></div>",
    unsafe_allow_html=True,
)
k3.markdown(
    f"<div class='kpi'><b>Email status</b><br><span style='font-size:1rem'>{'Ready ✅' if settings.email_ready else 'Missing secrets ⚠️'}</span></div>",
    unsafe_allow_html=True,
)

st.markdown("### ✍️ Editor")
df = pd.DataFrame(rows)
for c in ["included", "title", "description", "date", "region", "notes", "link", "relevance_score"]:
    if c not in df.columns:
        df[c] = "" if c != "included" else True

# Normalize dtypes for Streamlit data_editor compatibility
df["included"] = df["included"].fillna(True).astype(bool)
for text_col in ["title", "description", "region", "notes", "link"]:
    df[text_col] = df[text_col].fillna("").astype(str)
df["relevance_score"] = pd.to_numeric(df["relevance_score"], errors="coerce").fillna(1).astype(int)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["date"] = df["date"].fillna(pd.Timestamp(dt.date.today()))
df["date"] = df["date"].dt.date

edited = st.data_editor(
    df[["included", "title", "description", "date", "region", "notes", "link", "relevance_score"]],
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "included": st.column_config.CheckboxColumn("Include", default=True),
        "title": st.column_config.TextColumn("Title", width="large"),
        "description": st.column_config.TextColumn("Description", width="large"),
        "date": st.column_config.DateColumn("Date"),
        "region": st.column_config.TextColumn("Region", width="small"),
        "notes": st.column_config.TextColumn("Notes", width="medium"),
        "link": st.column_config.LinkColumn("Link"),
        "relevance_score": st.column_config.NumberColumn("Score", min_value=1, max_value=5),
    },
)

with st.expander("➕ Add manual item", expanded=False):
    c1, c2 = st.columns(2)
    m_title = c1.text_input("Title")
    m_region = c2.text_input("Region", value="Eurozone")
    m_desc = st.text_area("Description")
    c3, c4, c5 = st.columns([2, 1, 1])
    m_link = c3.text_input("Link", value="https://")
    m_date = c4.date_input("Date", value=dt.date.today(), key="manual_date")
    m_notes = c5.text_input("Notes")
    if st.button("Add item") and m_title:
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

st.markdown("### 👁️ Preview")
st.markdown("<div class='preview-wrap'>", unsafe_allow_html=True)
st.components.v1.html(html, height=700, scrolling=True)
st.markdown("</div>", unsafe_allow_html=True)

left, right = st.columns([1, 1])
left.download_button(
    "⬇️ Generate HTML",
    data=html,
    file_name=f"macro_news_{start_date}_to_{end_date}.html",
    mime="text/html",
    disabled=bool(html_findings),
    use_container_width=True,
)

recipient = right.text_input("Recipient", value=settings.email_recipient_default or "")
subject = f"News and Events Digest: {start_date} to {end_date}"
can_send = settings.email_ready and not findings and not html_findings
if not settings.email_ready:
    st.info("Completa secrets para habilitar envío de email.")

if st.button("📨 Send email", disabled=not can_send, use_container_width=True):
    ok, msg = send_email(html, recipient=recipient, subject=subject, settings=settings)
    st.success(msg) if ok else st.error(msg)
