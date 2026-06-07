import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
from google.oauth2.service_account import Credentials
import gspread
import json

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sandra · Job Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
section[data-testid="stSidebar"] { background: #0f1117; border-right: 1px solid #1e2a3a; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {
    color: #94a3b8 !important; font-size: 0.75rem;
    text-transform: uppercase; letter-spacing: 0.08em;
}
.main { background: #f8f7f4; }
.page-header {
    background: #0f1117; color: #f1f5f9;
    padding: 2rem 2.5rem 1.5rem; border-radius: 16px;
    margin-bottom: 1.5rem; position: relative; overflow: hidden;
}
.page-header::before {
    content: ''; position: absolute; top: -60px; right: -60px;
    width: 200px; height: 200px; border-radius: 50%;
    background: radial-gradient(circle, #22d3ee22, transparent 70%);
}
.page-header h1 {
    font-family: 'DM Serif Display', serif; font-size: 2.4rem;
    margin: 0 0 0.2rem; color: #f1f5f9;
}
.page-header p {
    font-family: 'DM Mono', monospace; font-size: 0.78rem;
    color: #64748b; margin: 0; letter-spacing: 0.05em;
}
.metric-card {
    background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-card .label {
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 0.4rem;
}
.metric-card .value {
    font-family: 'DM Serif Display', serif; font-size: 2rem;
    color: #0f1117; line-height: 1;
}
.section-title {
    font-family: 'DM Serif Display', serif; font-size: 1.3rem;
    color: #0f1117; margin: 1.5rem 0 0.8rem;
    border-bottom: 2px solid #0f1117; padding-bottom: 0.4rem;
}
.stButton > button {
    background: #0f1117 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1e293b !important; transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif; font-size: 0.85rem; font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
SHEET_NAME    = "JobTracker"
WORKSHEET     = "Applications"
STATUS_OPTS   = ["Applied", "Interview", "Offer", "Rejected", "Ghosted", "Withdrawn"]
TYPE_OPTS     = ["Full-time", "Freelance / Contract", "Part-time", "Internship"]
SECTOR_OPTS   = ["FinTech", "Insurance / FSP", "Banking", "Data & Analytics",
                 "Consulting", "Tech", "Risk & Compliance", "Other"]
PRIORITY_OPTS = ["🔥 High", "⚡ Medium", "💤 Low"]
COLUMNS       = ["company","role","sector","status","type","priority",
                 "date_applied","location","salary","url","contact","notes","next_step"]
STATUS_COLOR  = {
    "Applied":"#dbeafe","Interview":"#fef9c3","Offer":"#dcfce7",
    "Rejected":"#fee2e2","Ghosted":"#f1f5f9","Withdrawn":"#fce7f3",
}

# ── Google Sheets connection ───────────────────────────────────────────────────
@st.cache_resource
def get_worksheet():
    creds_dict = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc    = gspread.authorize(creds)
    try:
        sh = gc.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(SHEET_NAME)
    try:
        ws = sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(WORKSHEET, rows=1000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
    return ws


def load_data():
    try:
        ws      = get_worksheet()
        records = ws.get_all_records()
        return records if records else []
    except Exception as e:
        st.error(f"Could not load data from Google Sheets: {e}")
        return []


def save_all(data):
    """Overwrite the sheet with current data list."""
    ws = get_worksheet()
    ws.clear()
    ws.append_row(COLUMNS)
    if data:
        rows = [[str(d.get(c, "")) for c in COLUMNS] for d in data]
        ws.append_rows(rows, value_input_option="USER_ENTERED")


def to_df(data):
    if not data:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(data)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    df["date_applied"] = pd.to_datetime(df["date_applied"], errors="coerce")
    return df


# ── Session state ──────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    with st.spinner("Loading your applications…"):
        st.session_state.data = load_data()
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

data = st.session_state.data

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗂️ Filters")
    f_status = st.multiselect("Status",   STATUS_OPTS, default=STATUS_OPTS)
    f_type   = st.multiselect("Job type", TYPE_OPTS,   default=TYPE_OPTS)
    f_sector = st.multiselect("Sector",   SECTOR_OPTS, default=SECTOR_OPTS)
    f_search = st.text_input("🔍 Search company / role", "")
    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.session_state.data = load_data()
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <h1>Job Application Tracker</h1>
  <p>SANDRA · FINHEALTH RISK SOLUTIONS · DATA SCIENCE & ANALYTICS</p>
</div>
""", unsafe_allow_html=True)

# ── Metrics ────────────────────────────────────────────────────────────────────
total      = len(data)
active     = sum(1 for d in data if d.get("status") in ["Applied","Interview"])
interviews = sum(1 for d in data if d.get("status") == "Interview")
offers     = sum(1 for d in data if d.get("status") == "Offer")
rate       = f"{round(interviews/total*100)}%" if total else "—"

c1,c2,c3,c4,c5 = st.columns(5)
for col, label, val in zip(
    [c1,c2,c3,c4,c5],
    ["Total Applications","Active Pipeline","Interviews","Offers","Interview Rate"],
    [total, active, interviews, offers, rate]
):
    col.markdown(
        f'<div class="metric-card"><div class="label">{label}</div>'
        f'<div class="value">{val}</div></div>',
        unsafe_allow_html=True
    )

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋  Pipeline", "➕  Add / Edit", "📊  Analytics"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    filtered = [d for d in data
                if d.get("status","")  in f_status
                and d.get("type","")   in f_type
                and d.get("sector","") in f_sector
                and (f_search.lower() in d.get("company","").lower()
                     or f_search.lower() in d.get("role","").lower())]

    if not filtered:
        st.info("No applications match your filters. Add one in the ➕ tab!")
    else:
        df = to_df(filtered).sort_values("date_applied", ascending=False)

        st.markdown('<div class="section-title">Pipeline Overview</div>', unsafe_allow_html=True)
        cols = st.columns(len(STATUS_OPTS))
        for i, s in enumerate(STATUS_OPTS):
            n  = sum(1 for d in filtered if d.get("status") == s)
            bg = STATUS_COLOR.get(s, "#f1f5f9")
            cols[i].markdown(
                f'<div style="background:{bg};border-radius:10px;padding:0.8rem 1rem;text-align:center;">'
                f'<div style="font-size:1.5rem;font-weight:700;color:#0f1117;">{n}</div>'
                f'<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;color:#374151;">{s}</div>'
                f'</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Applications</div>', unsafe_allow_html=True)

        for _, row in df.iterrows():
            orig_idx = next((j for j,d in enumerate(data)
                             if d.get("company")==row["company"]
                             and d.get("role")==row["role"]
                             and str(d.get("date_applied",""))==str(row["date_applied"])), None)
            date_str = row["date_applied"].strftime('%d %b %Y') if pd.notna(row["date_applied"]) else "—"
            with st.expander(f"**{row['company']}** · {row['role']}  —  {date_str}", expanded=False):
                a,b,c = st.columns([2,2,1])
                with a:
                    st.markdown(f"**Status:** `{row.get('status','—')}`  \n**Type:** {row.get('type','—')}  \n**Sector:** {row.get('sector','—')}")
                    st.markdown(f"**Priority:** {row.get('priority','—')}")
                with b:
                    st.markdown(f"**Salary:** {row.get('salary','—')}  \n**Location:** {row.get('location','—')}  \n**Contact:** {row.get('contact','—')}")
                    if row.get("url"):
                        st.markdown(f"[🔗 Job posting]({row['url']})")
                with c:
                    if orig_idx is not None:
                        if st.button("✏️ Edit", key=f"edit_{orig_idx}"):
                            st.session_state.edit_idx = orig_idx
                            st.rerun()
                        if st.button("🗑️ Delete", key=f"del_{orig_idx}"):
                            st.session_state.data.pop(orig_idx)
                            with st.spinner("Saving…"):
                                save_all(st.session_state.data)
                            st.rerun()
                if row.get("notes"):
                    st.markdown(f"**Notes:** {row['notes']}")
                if row.get("next_step"):
                    st.markdown(f"**Next step:** _{row['next_step']}_")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ADD / EDIT
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    edit_idx = st.session_state.edit_idx
    existing = data[edit_idx] if edit_idx is not None else {}
    mode = "Edit Application" if edit_idx is not None else "Log New Application"
    st.markdown(f'<div class="section-title">{mode}</div>', unsafe_allow_html=True)

    if edit_idx is not None:
        if st.button("← Cancel edit"):
            st.session_state.edit_idx = None
            st.rerun()

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        company = st.text_input("Company *",      value=existing.get("company",""))
        role    = st.text_input("Role / Title *", value=existing.get("role",""))
        sector  = st.selectbox("Sector", SECTOR_OPTS,
                               index=SECTOR_OPTS.index(existing["sector"])
                               if existing.get("sector") in SECTOR_OPTS else 0)
    with r1c2:
        status   = st.selectbox("Status", STATUS_OPTS,
                                index=STATUS_OPTS.index(existing["status"])
                                if existing.get("status") in STATUS_OPTS else 0)
        job_type = st.selectbox("Type", TYPE_OPTS,
                                index=TYPE_OPTS.index(existing["type"])
                                if existing.get("type") in TYPE_OPTS else 0)
        priority = st.selectbox("Priority", PRIORITY_OPTS,
                                index=PRIORITY_OPTS.index(existing["priority"])
                                if existing.get("priority") in PRIORITY_OPTS else 1)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        raw_date     = existing.get("date_applied","")
        d_val        = date.fromisoformat(str(raw_date)[:10]) if raw_date else date.today()
        date_applied = st.date_input("Date applied", value=d_val)
        location     = st.text_input("Location / Remote", value=existing.get("location",""))
        salary       = st.text_input("Salary range (ZAR / USD)", value=existing.get("salary",""))
    with r2c2:
        url     = st.text_input("Job posting URL",   value=existing.get("url",""))
        contact = st.text_input("Recruiter / Contact", value=existing.get("contact",""))

    notes     = st.text_area("Notes", value=existing.get("notes",""), height=80)
    next_step = st.text_input("Next step / Follow-up", value=existing.get("next_step",""))

    if st.button("💾 Save Application"):
        if not company or not role:
            st.error("Company and Role are required.")
        else:
            entry = {
                "company":company,"role":role,"sector":sector,"status":status,
                "type":job_type,"priority":priority,"date_applied":str(date_applied),
                "location":location,"salary":salary,"url":url,
                "contact":contact,"notes":notes,"next_step":next_step,
            }
            if edit_idx is not None:
                st.session_state.data[edit_idx] = entry
                st.session_state.edit_idx = None
            else:
                st.session_state.data.append(entry)
            with st.spinner("Saving to Google Sheets…"):
                save_all(st.session_state.data)
            st.success("✅ Saved!")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    if not data:
        st.info("No data yet — add some applications first.")
    else:
        df_a = to_df(data)
        st.markdown('<div class="section-title">Analytics</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            sc = df_a["status"].value_counts().reset_index()
            sc.columns = ["Status","Count"]
            color_map = {"Applied":"#3b82f6","Interview":"#f59e0b","Offer":"#22c55e",
                         "Rejected":"#ef4444","Ghosted":"#94a3b8","Withdrawn":"#ec4899"}
            fig1 = px.pie(sc, names="Status", values="Count", hole=0.55,
                          title="Applications by Status", color="Status",
                          color_discrete_map=color_map)
            fig1.update_layout(font_family="DM Sans", paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", title_font_size=14,
                               margin=dict(t=40,b=0,l=0,r=0))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            sec = df_a["sector"].value_counts().reset_index()
            sec.columns = ["Sector","Count"]
            fig2 = px.bar(sec, x="Count", y="Sector", orientation="h",
                          title="Applications by Sector",
                          color_discrete_sequence=["#0f1117"])
            fig2.update_layout(font_family="DM Sans", paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", title_font_size=14,
                               yaxis=dict(categoryorder="total ascending"),
                               margin=dict(t=40,b=0,l=0,r=10))
            st.plotly_chart(fig2, use_container_width=True)

        df_t = df_a.dropna(subset=["date_applied"])
        if not df_t.empty:
            df_t = df_t.copy()
            df_t["week"] = df_t["date_applied"].dt.to_period("W").apply(lambda x: x.start_time)
            tl = df_t.groupby("week").size().reset_index(name="Applications")
            fig3 = px.area(tl, x="week", y="Applications", title="Applications Over Time",
                           color_discrete_sequence=["#0f1117"])
            fig3.update_traces(fill="tozeroy", line_color="#0f1117", fillcolor="rgba(15,17,23,0.1)")
            fig3.update_layout(font_family="DM Sans", paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", title_font_size=14,
                               xaxis_title="", yaxis_title="",
                               margin=dict(t=40,b=0,l=0,r=0))
            st.plotly_chart(fig3, use_container_width=True)

        tc = df_a["type"].value_counts().reset_index()
        tc.columns = ["Type","Count"]
        fig4 = px.bar(tc, x="Type", y="Count", title="Full-time vs Freelance Split",
                      color_discrete_sequence=["#22d3ee","#0f1117","#64748b","#f59e0b"])
        fig4.update_layout(font_family="DM Sans", paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", title_font_size=14,
                           showlegend=False, margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig4, use_container_width=True)
