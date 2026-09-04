import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import subprocess
import sys
import textwrap
from pathlib import Path

from login import login
from gemini_explainer import generate_explanation

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="RecoverAI",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# LOGIN
# ==========================================================

if not login():
    st.stop()

# ==========================================================
# DESIGN TOKENS (single source of truth for the theme)
# ==========================================================

BG = "#F1F5F9"
PRIMARY = "#2563EB"
PRIMARY_DARK = "#1D4ED8"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
PURPLE = "#8B5CF6"
CYAN = "#06B6D4"
TEXT = "#111827"
TEXT_SECONDARY = "#6B7280"
BORDER = "#E5E7EB"

CHART_COLORS = [PRIMARY, SUCCESS, WARNING, DANGER, PURPLE, CYAN]

CHART_FONT = dict(family="Inter, -apple-system, Segoe UI, sans-serif", size=13, color=TEXT)

# ==========================================================
# FILE PATHS
# ==========================================================

BASE = Path(__file__).parent

AUDIT = BASE / "recovery_audit.csv"
METRICS = BASE / "recovery_metrics.csv"
SIMULATOR = BASE / "recovery_simulator.py"

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data():
    audit = pd.read_csv(AUDIT)
    metrics = pd.read_csv(METRICS)
    return audit, metrics

audit, metrics = load_data()
m = metrics.iloc[0]

# ==========================================================
# GLOBAL METRICS
# ==========================================================

automation_rate = round(
    (
        float(m.recovered_payments)
        / float(m.failed_payments)
    ) * 100,
    2
) if float(m.failed_payments) else 0.0

pending_cases = int(m.unresolved_cases)

# ==========================================================
# CHART HELPERS (Plotly Express / Graph Objects)
# Purely presentational — no business logic, no data changes.
# ==========================================================

def _apply_layout(fig, height=380, showlegend=False, title=None):
    fig.update_layout(
        height=height,
        showlegend=showlegend,
        title=dict(text=title, font=dict(size=16, color=TEXT, family=CHART_FONT["family"])) if title else None,
        font=CHART_FONT,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12, color=TEXT_SECONDARY)
        ),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family=CHART_FONT["family"], font_color=TEXT),
    )
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_SECONDARY, size=12),
        title_font=dict(color=TEXT_SECONDARY, size=12),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#EEF2F7",
        zeroline=False,
        tickfont=dict(color=TEXT_SECONDARY, size=12),
        title_font=dict(color=TEXT_SECONDARY, size=12),
    )
    return fig


def styled_bar_chart(df, x_col, y_col, title=None, height=380, horizontal=False, colors=None):
    """Render a single-series bar chart with value labels."""
    colors = colors or CHART_COLORS
    if horizontal:
        fig = px.bar(
            df, x=y_col, y=x_col, orientation="h",
            text=y_col, color=x_col, color_discrete_sequence=colors
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    else:
        fig = px.bar(
            df, x=x_col, y=y_col,
            text=y_col, color=x_col, color_discrete_sequence=colors
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)

    fig.update_traces(
        marker_line_width=0,
        marker=dict(cornerradius=8),
        textfont=dict(color=TEXT, size=12),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>" if not horizontal else "<b>%{y}</b><br>%{x:,.0f}<extra></extra>",
    )
    fig.update_layout(showlegend=False)
    return _apply_layout(fig, height=height, showlegend=False, title=title)


def styled_pie_chart(df, names_col, values_col, title=None, height=380, colors=None):
    colors = colors or CHART_COLORS
    fig = px.pie(
        df, names=names_col, values=values_col,
        color_discrete_sequence=colors, hole=0.45
    )
    fig.update_traces(
        textinfo="percent+label",
        textfont=dict(size=12, color=TEXT),
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} (%{percent})<extra></extra>",
    )
    return _apply_layout(fig, height=height, showlegend=True, title=title)


def styled_grouped_bar(labels, values, series_name, title=None, height=380, colors=None):
    """Two-category comparison bar (e.g. At Risk vs Recovered)."""
    colors = colors or [DANGER, SUCCESS]
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                text=[f"₹{v:,.0f}" for v in values],
                textposition="outside",
                marker=dict(color=colors[: len(labels)], cornerradius=8, line_width=0),
                hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
            )
        ]
    )
    return _apply_layout(fig, height=height, showlegend=False, title=title)

# ==========================================================
# PROFESSIONAL ENTERPRISE THEME (CSS)
# ==========================================================

st.markdown(f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}}

/* ---------------- GLOBAL BACKGROUND ---------------- */

.stApp{{
    background:
        radial-gradient(circle at 8% 6%, rgba(37,99,235,.10), transparent 28%),
        radial-gradient(circle at 94% 88%, rgba(6,182,212,.08), transparent 30%),
        {BG} !important;
    transition:background-color .35s ease;
}}

[data-testid="stAppViewContainer"]{{
    background:transparent !important;
}}

[data-testid="stHeader"]{{
    background:transparent !important;
}}

.main .block-container{{
    max-width:1600px !important;
    width:100% !important;
    margin:auto;
    padding-top:1.5rem;
    padding-left:2.5rem;
    padding-right:2.5rem;
    padding-bottom:3rem;
}}

/* ---------------- BASE TEXT COLORS ---------------- */

.stApp, .stApp p, .stApp span, .stApp li, .stApp label, .stMarkdown {{
    color:{TEXT};
}}

h1, h2, h3, h4, h5, h6 {{
    color:{TEXT} !important;
    font-weight:700 !important;
}}

/* ---------------- SIDEBAR ---------------- */

section[data-testid="stSidebar"]{{
    background:#111827;
    border-right:1px solid #1F2937;
}}

section[data-testid="stSidebar"] *{{
    color:#F9FAFB !important;
}}

section[data-testid="stSidebar"] .stRadio label{{
    font-size:15px;
    padding:8px 4px;
    border-radius:10px;
}}

section[data-testid="stSidebar"] hr{{
    border-color:#1F2937;
}}

section[data-testid="stSidebar"] [data-baseweb="select"]{{
    background:#1F2937;
    border-radius:10px;
}}

section[data-testid="stSidebar"] .stSelectbox label{{
    color:#CBD5E1 !important;
    font-weight:600;
    font-size:13px;
    text-transform:uppercase;
    letter-spacing:.04em;
}}

/* ---------------- HEADER BANNER ---------------- */

.mainHeader{{
    background:linear-gradient(135deg,#1E40AF 0%,#2563EB 55%,#3B82F6 100%);
    border-radius:20px;
    padding:34px 36px;
    color:white;
    box-shadow:0 12px 30px rgba(37,99,235,.25);
    margin-bottom:8px;
}}

.mainHeader h1{{
    color:white !important;
    font-size:34px;
    margin-bottom:4px;
}}

.mainHeader h3{{
    color:#DBEAFE !important;
    font-weight:600 !important;
    margin-top:0;
}}

.mainHeader p{{
    color:#EAF2FF !important;
    font-size:16px;
    margin-top:6px;
    max-width:780px;
}}

/* ---------------- KPI / METRIC CARDS ---------------- */

[data-testid="stMetric"]{{
    background:white;
    border-radius:16px;
    padding:20px 22px;
    min-height:118px;
    border:1px solid {BORDER};
    box-shadow:0 4px 14px rgba(15,23,42,.05);
    transition:all .18s ease;
}}

[data-testid="stMetric"]:hover{{
    transform:translateY(-2px);
    box-shadow:0 10px 24px rgba(37,99,235,.14);
    border-color:#C7D9FF;
}}

[data-testid="stMetricLabel"] {{
    color:{TEXT_SECONDARY} !important;
    font-weight:600 !important;
    font-size:13px !important;
    text-transform:uppercase;
    letter-spacing:.03em;
}}

[data-testid="stMetricLabel"] p {{
    color:{TEXT_SECONDARY} !important;
}}

[data-testid="stMetricValue"] {{
    color:{TEXT} !important;
    font-weight:800 !important;
    font-size:26px !important;
}}

[data-testid="stMetricDelta"] {{
    font-weight:600 !important;
}}

.dashboard-kpi-grid {{
    display:grid;
    grid-template-columns:repeat(4, minmax(0, 1fr));
    gap:14px;
    margin:8px 0 24px;
}}

.dashboard-kpi {{
    position:relative;
    overflow:hidden;
    min-height:132px;
    padding:18px;
    border:1px solid rgba(255,255,255,.7);
    border-radius:16px;
    color:white;
    box-shadow:0 10px 24px rgba(15,23,42,.10);
    transition:transform .2s ease, box-shadow .2s ease;
}}

.dashboard-kpi:hover {{
    transform:translateY(-4px);
    box-shadow:0 16px 30px rgba(37,99,235,.22);
}}

.dashboard-kpi.blue {{ background:linear-gradient(135deg,#1d4ed8,#2563eb); }}
.dashboard-kpi.cyan {{ background:linear-gradient(135deg,#0369a1,#0891b2); }}
.dashboard-kpi.green {{ background:linear-gradient(135deg,#047857,#10b981); }}
.dashboard-kpi.amber {{ background:linear-gradient(135deg,#b45309,#f59e0b); }}

.dashboard-kpi-top {{
    display:flex;
    align-items:center;
    justify-content:space-between;
    color:rgba(255,255,255,.82);
    font-size:12px;
    font-weight:700;
    letter-spacing:.04em;
    text-transform:uppercase;
}}

.dashboard-kpi-icon {{ font-size:22px; }}
.dashboard-kpi-value {{ margin-top:14px; font-size:26px; font-weight:800; letter-spacing:0; }}
.dashboard-kpi-trend {{ margin-top:4px; color:#DCFCE7; font-size:12px; font-weight:700; }}
.dashboard-kpi-trend span {{ color:#BBF7D0; }}
.dashboard-kpi.red {{ background:linear-gradient(135deg,#B91C1C,#EF4444); }}

.dashboard-hero {{ padding:24px 30px; margin-bottom:0; border-radius:16px; }}
.dashboard-hero h1 {{ font-size:30px; margin:8px 0 2px; color:#FFFFFF !important; font-weight:800 !important; }}
.dashboard-hero h3 {{ font-size:17px; color:#DBEAFE !important; }}
.dashboard-hero p {{ color:#EFF6FF !important; }}
.hero-eyebrow, .card-kicker {{ color:#BFDBFE; font-size:11px; font-weight:800; letter-spacing:.1em; }}
.hero-status {{ display:inline-block; margin-top:14px; padding:8px 12px; border:1px solid rgba(255,255,255,.24); border-radius:8px; color:#EFF6FF; font-size:12px; font-weight:600; }}
.status-dot {{ display:inline-block; width:7px; height:7px; margin-right:5px; border-radius:50%; background:#86EFAC; box-shadow:0 0 0 3px rgba(134,239,172,.2); }}
.section-block, .chart-card, .insight-card, .table-card, .search-card, .summary-layout {{ background:rgba(255,255,255,.78); border:1px solid rgba(255,255,255,.82); border-radius:14px; box-shadow:0 10px 28px rgba(15,23,42,.07), inset 0 1px 0 rgba(255,255,255,.7); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease; }}
.section-block {{ padding:20px; margin-bottom:18px; }}
.section-heading {{ display:flex; align-items:center; gap:9px; margin:22px 0 12px; }}
.section-heading h2 {{ margin:0; font-size:22px; color:{TEXT} !important; }}
.section-icon {{ color:{PRIMARY}; font-size:22px; font-weight:800; }}
.summary-layout {{ display:grid; grid-template-columns:1.25fr 1fr; overflow:hidden; box-shadow:none; }}
.summary-copy {{ padding:20px 22px; }}
.summary-copy .card-kicker {{ color:{PRIMARY}; }}
.summary-copy h3 {{ margin:8px 0; font-size:20px; }}
.summary-copy p {{ color:{TEXT_SECONDARY}; line-height:1.6; margin:0 0 15px; }}
.quick-stats {{ display:grid; grid-template-columns:1fr 1fr; background:#F8FAFC; }}
.quick-stats div {{ padding:16px 18px; border-left:1px solid #E2E8F0; border-bottom:1px solid #E2E8F0; }}
.quick-stats span {{ display:block; color:{TEXT_SECONDARY}; font-size:11px; text-transform:uppercase; letter-spacing:.05em; }}
.quick-stats strong {{ display:block; color:{TEXT}; font-size:21px; margin-top:5px; }}
.chart-card {{ padding:12px 14px 2px; height:100%; }}
.card-title {{ color:{TEXT}; font-size:15px; font-weight:800; padding:2px 2px 7px; }}
.insight-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:14px; margin-bottom:20px; }}
.insight-card {{ padding:18px; min-height:155px; transition:transform .2s ease, box-shadow .2s ease; }}
.insight-card:hover, .chart-card:hover, .summary-layout:hover, .section-block:hover {{ transform:translateY(-3px); border-color:rgba(147,197,253,.9); box-shadow:0 16px 34px rgba(37,99,235,.13), inset 0 1px 0 rgba(255,255,255,.85); }}
.insight-card h3 {{ margin:9px 0 7px; font-size:17px; }}
.insight-card p {{ color:{TEXT_SECONDARY}; font-size:13px; min-height:34px; margin:0 0 10px; }}
.insight-value {{ color:{TEXT}; font-size:22px; font-weight:800; }}
.insight-icon {{ font-size:20px; }}
.table-card {{ padding:3px 8px 8px; margin-bottom:16px; }}
.table-card [data-testid="stDataFrame"] {{ border:0; box-shadow:none; }}
.search-card {{ padding:18px; margin:20px 0 16px; }}
.search-header {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:8px; }}
.search-header h2 {{ margin:0; font-size:21px; }}
.search-card [data-testid="stTextInput"] input {{ border-radius:9px; border:1px solid #CBD5E1; padding:10px 12px; }}
.search-card .stDownloadButton {{ margin-top:0; }}
.search-card .stDownloadButton button {{ border:1px solid {PRIMARY}; color:{PRIMARY}; background:white; border-radius:8px; font-weight:700; transition:all .2s ease; }}
.search-card .stDownloadButton button:hover {{ color:white; background:{PRIMARY}; transform:translateY(-1px); }}
@media (max-width:900px) {{ .summary-layout, .insight-grid {{ grid-template-columns:1fr; }} .quick-stats div {{ border-left:0; }} }}

@media (max-width:900px) {{
    .dashboard-kpi-grid {{ grid-template-columns:repeat(2, minmax(0, 1fr)); }}
}}

@media (max-width:560px) {{
    .dashboard-kpi-grid {{ grid-template-columns:1fr; }}
}}

.recovery-card {{
    background:rgba(255,255,255,.86);
    border:1px solid #DCE6F3;
    border-radius:16px;
    padding:20px;
    box-shadow:0 8px 22px rgba(15,23,42,.07);
    margin-bottom:14px;
}}

.recovery-card h3 {{ margin:0 0 16px; color:{TEXT}; font-size:18px; }}
.recovery-card-label {{ color:{TEXT_SECONDARY}; font-size:11px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; }}
.recovery-card-value {{ color:{TEXT}; font-size:18px; font-weight:800; margin-top:4px; word-break:break-word; }}
.recovery-card-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }}
.recovery-badge {{ display:inline-block; padding:5px 10px; border-radius:999px; font-size:12px; font-weight:700; background:#DBEAFE; color:#1D4ED8; }}
.recovery-badge.success {{ background:#D1FAE5; color:#047857; }}
.recovery-badge.warning {{ background:#FEF3C7; color:#B45309; }}
.recovery-badge.danger {{ background:#FEE2E2; color:#B91C1C; }}
.recommendation-card {{ background:linear-gradient(135deg,#0F3B82,#2563EB); color:white; border-radius:18px; padding:24px; box-shadow:0 12px 28px rgba(37,99,235,.22); }}
.recommendation-card h3, .recommendation-card .recovery-card-value {{ color:white; }}
.recommendation-card .recovery-card-label {{ color:#BFDBFE; }}
.recommendation-card .recovery-badge {{ background:rgba(255,255,255,.16); color:white; }}
.audit-timeline {{ position:relative; margin:8px 0 24px 10px; padding-left:28px; border-left:2px solid #BFDBFE; }}
.audit-event {{ position:relative; margin:0 0 14px; padding:16px 18px; background:white; border:1px solid #DBEAFE; border-radius:14px; box-shadow:0 5px 16px rgba(15,23,42,.06); }}
.audit-event::before {{ content:""; position:absolute; width:11px; height:11px; left:-35px; top:21px; background:{PRIMARY}; border:3px solid {BG}; border-radius:50%; box-shadow:0 0 0 2px #93C5FD; }}
.audit-event-title {{ color:{TEXT}; font-weight:800; font-size:14px; }}
.audit-event-detail {{ color:{TEXT_SECONDARY}; font-size:13px; margin-top:5px; }}
@media (max-width:560px) {{ .recovery-card-grid {{ grid-template-columns:1fr; }} }}

.analytics-card-grid {{
    display:grid;
    grid-template-columns:repeat(4, minmax(0, 1fr));
    gap:14px;
    margin:8px 0 24px;
}}
.analytics-card {{
    background:white;
    border:1px solid #DCE6F3;
    border-radius:16px;
    padding:18px 20px;
    box-shadow:0 8px 22px rgba(15,23,42,.06);
    transition:transform .2s ease, box-shadow .2s ease;
}}
.analytics-card:hover {{ transform:translateY(-3px); box-shadow:0 14px 28px rgba(37,99,235,.14); }}
.analytics-card-label {{ color:{TEXT_SECONDARY}; font-size:11px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; }}
.analytics-card-value {{ color:{TEXT}; font-size:25px; font-weight:800; margin-top:8px; }}
.analytics-card-trend {{ color:{PRIMARY}; font-size:12px; font-weight:700; margin-top:4px; }}
@media (max-width:900px) {{ .analytics-card-grid {{ grid-template-columns:repeat(2, minmax(0, 1fr)); }} }}
@media (max-width:560px) {{ .analytics-card-grid {{ grid-template-columns:1fr; }} }}

/* ---------------- BUTTONS ---------------- */

.stButton>button{{
    background:{PRIMARY};
    color:white !important;
    border:none;
    border-radius:12px;
    height:46px;
    font-weight:600;
    box-shadow:0 4px 12px rgba(37,99,235,.25);
    transition:all .15s ease;
}}

.main .stMarkdown, .main [data-testid="stText"], .main label{{
    color:{TEXT} !important;
}}

.main input, .main textarea, .main [data-baseweb="select"]{{
    transition:border-color .2s ease, box-shadow .2s ease, background-color .2s ease;
}}

.main input:focus, .main textarea:focus{{
    border-color:#93C5FD !important;
    box-shadow:0 0 0 3px rgba(37,99,235,.14) !important;
}}

.stButton>button:hover{{
    background:{PRIMARY_DARK};
    box-shadow:0 6px 16px rgba(37,99,235,.35);
}}

.stDownloadButton>button{{
    background:{SUCCESS};
    color:white !important;
    border:none;
    border-radius:12px;
    font-weight:600;
    box-shadow:0 4px 12px rgba(16,185,129,.25);
}}

.stDownloadButton>button:hover{{
    background:#059669;
}}

/* ---------------- INPUTS ---------------- */

.stTextInput input{{
    border-radius:12px;
    border:1px solid #CBD5E1;
    color:{TEXT} !important;
    background:white;
}}

.stSelectbox div[data-baseweb="select"]{{
    border-radius:12px;
}}

.main .stSelectbox label, .main .stTextInput label {{
    color:{TEXT} !important;
    font-weight:600;
    font-size:13px;
}}

/* ---------------- SECTION HEADERS ---------------- */

.main h2 {{
    font-size:22px !important;
    margin-top:6px;
    margin-bottom:14px;
    padding-bottom:8px;
    border-bottom:2px solid {BORDER};
}}

.main h3 {{
    font-size:17px !important;
}}

/* ---------------- SUMMARY CARD ---------------- */

.summary{{
    background:white;
    border-left:6px solid {PRIMARY};
    padding:28px 30px;
    border-radius:16px;
    box-shadow:0 4px 16px rgba(15,23,42,.06);
    margin-bottom:20px;
    color:{TEXT};
}}

.summary h2{{
    border-bottom:none !important;
    margin-top:0;
}}

.summary table td{{
    padding:10px 6px;
    color:{TEXT};
    border-bottom:1px solid #F1F5F9;
    font-size:15px;
}}

/* ---------------- AUDIT / TIMELINE CARDS ---------------- */

.audit{{
    background:white;
    border-left:5px solid {PURPLE};
    padding:16px 20px;
    border-radius:14px;
    margin-bottom:10px;
    box-shadow:0 3px 10px rgba(15,23,42,.05);
    color:{TEXT};
    font-size:14.5px;
    line-height:1.6;
}}

/* ---------------- SECTION WRAPPER CARD ---------------- */

.section-card{{
    background:white;
    border-radius:18px;
    padding:26px 28px;
    border:1px solid {BORDER};
    box-shadow:0 4px 16px rgba(15,23,42,.05);
    margin-bottom:24px;
}}

/* ---------------- NATIVE ALERT BOXES (info/success/warning/error) ---------------- */

div[data-testid="stAlert"]{{
    border-radius:16px !important;
    padding:20px 22px !important;
    box-shadow:0 4px 14px rgba(15,23,42,.05);
    border:1px solid transparent;
}}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] li,
div[data-testid="stAlert"] div{{
    color:{TEXT} !important;
}}

div[data-testid="stAlert"] h1,
div[data-testid="stAlert"] h2,
div[data-testid="stAlert"] h3,
div[data-testid="stAlert"] h4{{
    color:{TEXT} !important;
}}

/* success */
div[data-testid="stAlert"]:has(svg[fill="rgb(23, 178, 106)"]),
div[data-testid="stAlertContentSuccess"]{{
    background:#ECFDF5 !important;
    border-color:#A7F3D0 !important;
}}

/* info */
div[data-testid="stAlertContentInfo"]{{
    background:#EFF6FF !important;
    border-color:#BFDBFE !important;
}}

/* warning */
div[data-testid="stAlertContentWarning"]{{
    background:#FFFBEB !important;
    border-color:#FDE68A !important;
}}

/* error */
div[data-testid="stAlertContentError"]{{
    background:#FEF2F2 !important;
    border-color:#FECACA !important;
}}

/* ---------------- TABLES ---------------- */

[data-testid="stDataFrame"]{{
    border-radius:16px;
    border:1px solid {BORDER};
    overflow:hidden;
    box-shadow:0 3px 12px rgba(15,23,42,.04);
}}

/* ---------------- CODE BLOCK (workflow) ---------------- */

.stCodeBlock, [data-testid="stCodeBlock"], pre{{
    border-radius:14px !important;
}}

.stCodeBlock, [data-testid="stCodeBlock"], pre, .stCodeBlock pre, [data-testid="stCodeBlock"] pre{{
    background:#FFFFFF !important;
    color:{TEXT} !important;
}}

.stCodeBlock code, [data-testid="stCodeBlock"] code, pre code{{
    color:{TEXT} !important;
}}

/* ---------------- DIVIDER SPACING ---------------- */

hr{{
    margin-top:1.4rem !important;
    margin-bottom:1.4rem !important;
    border-color:{BORDER} !important;
}}

/* ---------------- PROGRESS BAR ---------------- */

.stProgress > div > div > div > div{{
    background:linear-gradient(90deg,{PRIMARY},{CYAN}) !important;
}}

div[data-testid="stMarkdownContainer"] .dashboard-hero h1{{
    color:#FDE68A !important;
    font-weight:800 !important;
}}

</style>
""", unsafe_allow_html=True)

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.image(
    "https://img.icons8.com/fluency/96/artificial-intelligence.png",
    width=80
)

st.sidebar.title("RecoverAI")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🤖 Recovery Center",
        "📊 Analytics",
        "📜 Audit Logs",
        "ℹ️ About"
    ]
)

st.sidebar.markdown("---")

result_filter = st.sidebar.selectbox(
    "Recovery Result",
    ["All"] + sorted(audit["result"].dropna().unique().tolist())
)

action_filter = st.sidebar.selectbox(
    "AI Action",
    ["All"] + sorted(audit["action"].dropna().unique().tolist())
)

failure_filter = st.sidebar.selectbox(
    "Failure Reason",
    ["All"] + sorted(
        audit["failure_reason"]
        .fillna("SUCCESS")
        .unique()
        .tolist()
    )
)

filtered = audit.copy()

if result_filter != "All":
    filtered = filtered[filtered["result"] == result_filter]

if action_filter != "All":
    filtered = filtered[filtered["action"] == action_filter]

if failure_filter != "All":
    filtered = filtered[
        filtered["failure_reason"].fillna("SUCCESS") == failure_filter
    ]

# ==========================================================
# DASHBOARD
# ==========================================================
if page != "🏠 Dashboard":
    st.markdown("""
    <div class="mainHeader">
    <h1>💳 RecoverAI</h1>
    <h3>AI Revenue Recovery Platform</h3>
    <p>Recover failed digital payments using Explainable AI, smart retry strategies and complete audit transparency.</p>
    </div>
    """, unsafe_allow_html=True)
    st.success("🟢 Recovery Engine Online | 🤖 Gemini Connected | 🔒 Audit Logging Enabled")

if page == "🏠 Dashboard":

    # ------------------------------------------------------
    # Dashboard Header
    # ------------------------------------------------------

    st.markdown("""
    <div class="mainHeader dashboard-hero">
        <div class="hero-eyebrow">RECOVERAI / EXECUTIVE CONTROL CENTER</div>
        <h1>RecoverAI Enterprise Dashboard</h1>
        <h3>AI Revenue Recovery Platform</h3>
        <p>Explainable recovery decisions, protected revenue, and audit-ready operations in one view.</p>
        <div class="hero-status"><span class="status-dot"></span> Current system status: Recovery Engine Online &nbsp;•&nbsp; Gemini Connected &nbsp;•&nbsp; Audit Logging Enabled</div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------------------------------------
    # KPI CARDS
    # ------------------------------------------------------

    dashboard_kpis = [
        ("At Risk Revenue", f"₹{float(m.at_risk_revenue_inr):,.0f}", "₹", "amber", "MONITORED"),
        ("Recovered Revenue", f"₹{float(m.recovered_revenue_inr):,.0f}", "✓", "green", "PROTECTED"),
        ("Recovery Rate", f"{float(m.recovery_rate_percent):.2f}%", "📈", "blue", "↑ outcome"),
        ("Automation Rate", f"{automation_rate:.2f}%", "⚙", "blue", "AUTOMATED"),
        ("Total Payments", f"{int(m.total_payments):,}", "▣", "blue", "PROCESSED"),
        ("Recovered Payments", f"{int(m.recovered_payments):,}", "↗", "green", "SUCCESSFUL"),
        ("Escalated Cases", f"{int(m.escalated_cases):,}", "!", "amber", "HUMAN REVIEW"),
        ("Pending Cases", f"{pending_cases:,}", "…", "red", "QUEUE ACTIVE"),
    ]

    kpi_markup = '<div class="dashboard-kpi-grid">'
    for label, value, icon, tone, trend in dashboard_kpis:
        kpi_markup += f'<div class="dashboard-kpi {tone}">'
        kpi_markup += f'<div class="dashboard-kpi-top"><span>{label}</span><span class="dashboard-kpi-icon">{icon}</span></div>'
        kpi_markup += f'<div class="dashboard-kpi-value">{value}</div>'
        kpi_markup += f'<div class="dashboard-kpi-trend"><span>●</span> {trend}</div>'
        kpi_markup += '</div>'
    kpi_markup += "</div>"
    st.markdown(textwrap.dedent(kpi_markup), unsafe_allow_html=True)

    # ======================================================
    # EXECUTIVE SUMMARY
    # ======================================================

    st.markdown(f"""
    <section class="section-block">
        <div class="section-heading"><span class="section-icon">▤</span><h2>Executive Summary</h2></div>
        <div class="summary-layout">
            <div class="summary-copy">
                <div class="card-kicker">BUSINESS SUMMARY</div>
                <h3>Revenue recovery is actively protecting your payment book.</h3>
                <p>RecoverAI analysed <strong>{int(m.total_payments)}</strong> transactions and recovered <strong>₹{float(m.recovered_revenue_inr):,.0f}</strong> with explainable decisions, audit logging, and human oversight.</p>
                <span class="recovery-badge success">SYSTEM OPERATING WITH OVERSIGHT</span>
            </div>
            <div class="quick-stats">
                <div><span>Total payments</span><strong>{int(m.total_payments):,}</strong></div>
                <div><span>Failed payments</span><strong>{int(m.failed_payments):,}</strong></div>
                <div><span>Escalated cases</span><strong>{int(m.escalated_cases):,}</strong></div>
                <div><span>Pending cases</span><strong>{pending_cases:,}</strong></div>
            </div>
        </div>
    </section>
    """, unsafe_allow_html=True)

    # ======================================================
    # REVENUE OVERVIEW
    # ======================================================

    st.markdown('<div class="section-heading"><span class="section-icon">▥</span><h2>Revenue Overview</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        fig_revenue = styled_grouped_bar(
            labels=["At Risk", "Recovered"],
            values=[float(m.at_risk_revenue_inr), float(m.recovered_revenue_inr)],
            series_name="Revenue (₹)",
            colors=[DANGER, SUCCESS],
        )

        st.markdown('<div class="chart-card"><div class="card-title">Revenue Comparison</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_revenue, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:

        outcome = (
            audit["result"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Count")
        )

        fig_outcome = styled_bar_chart(outcome, "Status", "Count")

        st.markdown('<div class="chart-card"><div class="card-title">Recovery Result</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_outcome, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    trend = audit.copy()
    trend["cohort"] = pd.qcut(trend.index + 1, q=6, labels=["01", "02", "03", "04", "05", "06"])
    trend_data = trend.groupby("cohort", observed=False).agg(Recovered=("recovered_amount_inr", "sum"), At_Risk=("amount_inr", "sum")).reset_index()
    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(x=trend_data["cohort"], y=trend_data["Recovered"], mode="lines+markers", name="Recovered", line=dict(color=SUCCESS, width=3), marker=dict(size=8)))
    trend_fig.add_trace(go.Scatter(x=trend_data["cohort"], y=trend_data["At_Risk"], mode="lines+markers", name="Processed", line=dict(color=PRIMARY, width=3), marker=dict(size=8)))
    trend_fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
    trend_fig = _apply_layout(trend_fig, height=290, showlegend=True)
    funnel_data = pd.DataFrame({"Stage": ["Total Payments", "Failed Payments", "Recovered Payments", "Escalated Cases"], "Count": [int(m.total_payments), int(m.failed_payments), int(m.recovered_payments), int(m.escalated_cases)]})
    funnel_fig = go.Figure(go.Funnel(y=funnel_data["Stage"], x=funnel_data["Count"], textinfo="value+percent initial", marker=dict(color=[PRIMARY, WARNING, SUCCESS, DANGER])))
    funnel_fig = _apply_layout(funnel_fig, height=290, showlegend=False)
    confidence = pd.cut(audit["confidence"], bins=[0, .6, .8, .9, 1.01], labels=["0–60%", "61–80%", "81–90%", "91–100%"], include_lowest=True).value_counts().sort_index().reset_index()
    confidence.columns = ["Confidence", "Count"]
    confidence_fig = styled_bar_chart(confidence, "Confidence", "Count", height=290, colors=[PRIMARY, PRIMARY, SUCCESS, SUCCESS])
    trend_col, funnel_col, confidence_col = st.columns(3)
    for chart_col, chart_title, chart in [(trend_col, "Recovery Trend", trend_fig), (funnel_col, "Recovery Funnel", funnel_fig), (confidence_col, "Confidence Distribution", confidence_fig)]:
        with chart_col:
            st.markdown(f'<div class="chart-card"><div class="card-title">{chart_title}</div>', unsafe_allow_html=True)
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)
    # ==========================================================
    # BUSINESS INSIGHTS
    # ==========================================================

    st.markdown('<div class="section-heading"><span class="section-icon">✦</span><h2>AI Business Insights</h2></div>', unsafe_allow_html=True)

    highest_failure = (
        audit["failure_reason"]
        .fillna("SUCCESS")
        .value_counts()
        .idxmax()
    )

    st.markdown(f"""
    <div class="insight-grid">
        <div class="insight-card"><div class="insight-icon">▥</div><h3>Performance</h3><p>Recovered revenue is being converted from failed payment volume.</p><div class="insight-value">₹{float(m.recovered_revenue_inr):,.0f}</div><span class="recovery-badge success">{float(m.recovery_rate_percent):.2f}% recovery</span></div>
        <div class="insight-card"><div class="insight-icon">!</div><h3>Risk</h3><p>Focus human review where the recovery engine sees the most exposure.</p><div class="insight-value">{highest_failure}</div><span class="recovery-badge warning">{int(m.escalated_cases)} escalated</span></div>
        <div class="insight-card"><div class="insight-icon">✦</div><h3>AI Recommendation</h3><p>Prioritise pending cases and preserve the automated path for high-confidence decisions.</p><div class="insight-value">{automation_rate:.2f}%</div><span class="recovery-badge">AUTOMATION RATE</span></div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================
    # TOP FAILURE REASONS
    # ==========================================================

    st.markdown('<div class="section-heading"><span class="section-icon">!</span><h2>Top Failure Reasons</h2></div>', unsafe_allow_html=True)

    failure_summary = (
        audit["failure_reason"]
        .fillna("SUCCESS")
        .value_counts()
        .reset_index()
    )

    failure_summary.columns = [
        "Failure Reason",
        "Occurrences"
    ]

    left, right = st.columns([2, 1])

    with left:
        failure_view = failure_summary.copy()
        failure_view["Occurrences"] = failure_view["Occurrences"].map(lambda value: f"{int(value):,}")
        failure_view = failure_view.style.set_properties(**{"font-size": "12px", "background-color": "#FFFFFF", "color": "#334155"}).set_table_styles([{"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#EFF6FF")]}, {"selector": "tbody tr:hover", "props": [("background-color", "#DBEAFE")]}, {"selector": "thead", "props": [("background-color", "#2563EB"), ("color", "#FFFFFF")]}])
        st.dataframe(
            failure_view,
            use_container_width=True,
            hide_index=True
        )

    with right:

        st.metric(
            "Most Common Failure",
            failure_summary.iloc[0]["Failure Reason"]
        )

        st.metric(
            "Occurrences",
            int(failure_summary.iloc[0]["Occurrences"])
        )

    # ==========================================================
    # AI DECISION STATISTICS
    # ==========================================================

    st.markdown('<div class="section-heading"><span class="section-icon">✦</span><h2>AI Decision Statistics</h2></div>', unsafe_allow_html=True)

    action_summary = (
        audit["action"]
        .value_counts()
        .reset_index()
    )

    action_summary.columns = [
        "AI Action",
        "Count"
    ]

    c1, c2 = st.columns([2, 1])

    with c1:
        action_view = action_summary.copy()
        action_view["Count"] = action_view["Count"].map(lambda value: f"{int(value):,}")
        action_view = action_view.style.set_properties(**{"font-size": "12px", "background-color": "#FFFFFF", "color": "#334155"}).set_table_styles([{"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#EFF6FF")]}, {"selector": "tbody tr:hover", "props": [("background-color", "#DBEAFE")]}, {"selector": "thead", "props": [("background-color", "#2563EB"), ("color", "#FFFFFF")]}])
        st.dataframe(
            action_view,
            use_container_width=True,
            hide_index=True
        )

    with c2:

        best_action = action_summary.iloc[0]["AI Action"]
        best_count = int(action_summary.iloc[0]["Count"])

        st.metric(
            "Most Used Action",
            best_action
        )

        st.metric(
            "Executions",
            best_count
        )

    # ==========================================================
    # RECOVERY SUMMARY
    # ==========================================================

    st.markdown('<div class="section-heading"><span class="section-icon">⌖</span><h2>Recovery Summary</h2></div>', unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:

        st.markdown(f"""
        <div class="recovery-card"><h3>₹ &nbsp;Revenue Summary</h3>
        <div class="quick-stats"><div><span>At risk revenue</span><strong>₹{float(m.at_risk_revenue_inr):,.0f}</strong></div><div><span>Recovered revenue</span><strong>₹{float(m.recovered_revenue_inr):,.0f}</strong></div><div><span>Recovery rate</span><strong>{float(m.recovery_rate_percent):.2f}%</strong></div></div></div>
        """, unsafe_allow_html=True)

    with right:

        st.markdown(f"""
        <div class="recovery-card"><h3>▥ &nbsp;Operations Summary</h3>
        <div class="quick-stats"><div><span>Total payments</span><strong>{int(m.total_payments):,}</strong></div><div><span>Failed payments</span><strong>{int(m.failed_payments):,}</strong></div><div><span>Escalated cases</span><strong>{int(m.escalated_cases):,}</strong></div><div><span>Pending cases</span><strong>{int(m.unresolved_cases):,}</strong></div></div></div>
        """, unsafe_allow_html=True)

    # ==========================================================
    # SEARCH TRANSACTIONS
    # ==========================================================

    st.markdown('<div class="search-card">', unsafe_allow_html=True)
    search_header, download_slot = st.columns([4, 1])
    with search_header:
        st.markdown('<div class="search-header"><h2>⌕ &nbsp;Search Transactions</h2></div>', unsafe_allow_html=True)
        search = st.text_input("Search Payment ID", placeholder="Search by payment ID", label_visibility="collapsed")
    with download_slot:
        st.markdown('<div style="height:29px"></div>', unsafe_allow_html=True)
        download_slot_placeholder = st.empty()

    table = filtered.copy()

    if search:

        table = table[
            table["payment_id"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    st.markdown('<div class="card-title">▤ &nbsp;Recovery Decisions</div>', unsafe_allow_html=True)

    display = table[
        [
            "payment_id",
            "amount_inr",
            "failure_reason",
            "action",
            "result",
            "recovered_amount_inr"
        ]
    ].copy()

    display.columns = [
        "Payment ID",
        "Amount (₹)",
        "Failure Reason",
        "AI Action",
        "Result",
        "Recovered (₹)"
    ]

    csv = display.to_csv(index=False).encode("utf-8")
    styled_display = display.style.format({"Amount (₹)": "₹{:,.2f}", "Recovered (₹)": "₹{:,.2f}"}).set_properties(**{"font-size": "12px", "background-color": "#FFFFFF", "color": "#334155"}).set_table_styles([{"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#EFF6FF")]}, {"selector": "tbody tr:hover", "props": [("background-color", "#DBEAFE")]}, {"selector": "thead", "props": [("background-color", "#2563EB"), ("color", "#FFFFFF")]}])
    st.dataframe(styled_display, use_container_width=True, hide_index=True)
    with download_slot_placeholder:
        st.download_button(label="⇩  Download report", data=csv, file_name="RecoverAI_Report.csv", mime="text/csv", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================================
# END OF DASHBOARD
# ==========================================================
# ==========================================================
# RECOVERY CENTER PAGE
# ==========================================================

if page == "🤖 Recovery Center":

    st.markdown("""
    <div class="mainHeader">

    <h1>🤖 AI Recovery Center</h1>

    <p>
    Investigate failed payments • View AI reasoning • Recover revenue
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.success(
        "🟢 Gemini AI Ready • Recovery Engine Active • Human Review Enabled"
    )

    st.divider()

    if filtered.empty:
        st.warning("No transactions found for the selected filters.")
        st.stop()

    # ======================================================
    # SELECT TRANSACTION
    # ======================================================

    payment = st.selectbox(
        "💳 Select Payment Transaction",
        filtered["payment_id"].tolist()
    )

    row = filtered[
        filtered["payment_id"] == payment
    ].iloc[0]

    left, right = st.columns([1, 1])

    # ======================================================
    # PAYMENT DETAILS
    # ======================================================

    with left:

        failure = row["failure_reason"]

        if pd.isna(failure):
            failure = "SUCCESS"

        result = str(row["result"]).upper()
        result_class = "success" if result == "RECOVERED" else "danger" if result in {"ESCALATED", "FAILED_AFTER_RETRY"} else "warning"

        st.markdown(f"""
        <div class="recovery-card">
            <h3>💳 Payment Information</h3>
            <div class="recovery-card-grid">
                <div><div class="recovery-card-label">Payment ID</div><div class="recovery-card-value">{row['payment_id']}</div></div>
                <div><div class="recovery-card-label">Transaction Amount</div><div class="recovery-card-value">₹{float(row['amount_inr']):,.2f}</div></div>
                <div><div class="recovery-card-label">Failure Reason</div><div class="recovery-card-value">{failure}</div></div>
                <div><div class="recovery-card-label">Attempts</div><div class="recovery-card-value">{int(row['attempts'])}</div></div>
                <div><div class="recovery-card-label">Recovery Action</div><div class="recovery-card-value">{row['action']}</div></div>
                <div><div class="recovery-card-label">Final Status</div><div class="recovery-card-value"><span class="recovery-badge {result_class}">{result.replace('_', ' ')}</span></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if result == "RECOVERED":

            st.success("✅ Payment Successfully Recovered")

        elif result == "ESCALATED":

            st.error("🚨 Escalated For Manual Review")

        elif result == "CUSTOMER_ACTION_REQUIRED":

            st.warning("📩 Waiting For Customer Action")

        elif result == "FAILED_AFTER_RETRY":

            st.error("❌ Recovery Failed")

        else:

            st.info("ℹ️ No Recovery Needed")

    # ======================================================
    # AI PANEL
    # ======================================================

    with right:

        st.markdown("## 🤖 Gemini AI Decision")

        with st.spinner("Generating AI explanation..."):

            explanation = generate_explanation(row)

        confidence = float(row["confidence"])
        expected_recovery = float(row["recovered_amount_inr"])
        risk_level = "Low" if str(row["action"]).upper() == "RETRY" else "Medium" if str(row["action"]).upper() == "REMIND" else "High"
        review_required = "Yes" if str(row["action"]).upper() == "ESCALATE" or confidence < .7 else "No"
        risk_class = "success" if risk_level == "Low" else "warning" if risk_level == "Medium" else "danger"

        st.markdown(f"""
        <div class="recommendation-card">
            <h3>⚡ AI Recommendation</h3>
            <div class="recovery-card-grid">
                <div><div class="recovery-card-label">Recommended Action</div><div class="recovery-card-value">{row['action']}</div></div>
                <div><div class="recovery-card-label">Confidence</div><div class="recovery-card-value">{confidence * 100:.0f}%</div></div>
                <div><div class="recovery-card-label">Expected Recovery</div><div class="recovery-card-value">₹{expected_recovery:,.2f}</div></div>
                <div><div class="recovery-card-label">Risk Level</div><div class="recovery-card-value"><span class="recovery-badge {risk_class}">{risk_level}</span></div></div>
                <div><div class="recovery-card-label">Expected Success Rate</div><div class="recovery-card-value">{confidence * 100:.0f}%</div></div>
                <div><div class="recovery-card-label">Human Review Required</div><div class="recovery-card-value">{review_required}</div></div>
            </div>
            <div style="margin-top:18px;color:#DBEAFE;font-size:13px;line-height:1.55;"><strong>Business Impact:</strong> ₹{expected_recovery:,.2f} recovered value currently attributed to this decision.</div>
        </div>
        """, unsafe_allow_html=True)

        st.info(explanation)

    st.divider()
    # ======================================================
    # AI INSIGHTS
    # ======================================================

    st.header("💡 AI Recovery Insights")

    action = str(row["action"]).upper()

    if action == "RETRY":

        st.success("""
### 🟢 Low Risk

RecoverAI detected a temporary payment failure.

**Recommended Strategy**

• Retry automatically

• Monitor payment gateway

• Notify merchant after successful recovery

**Expected Outcome**

High probability of successful recovery.
""")

    elif action == "REMIND":

        st.warning("""
### 🟡 Customer Action Required

RecoverAI believes customer intervention is needed.

**Recommended Strategy**

• Send payment reminder

• Generate secure payment link

• Wait before retrying

**Expected Outcome**

Recovery likely after customer completes payment.
""")

    elif action == "ESCALATE":

        st.error("""
### 🔴 High Risk

Automatic recovery has reached stopping rules.

**Recommended Strategy**

• Escalate to Finance Team

• Investigate payment gateway

• Contact customer if required

**Expected Outcome**

Manual intervention required.
""")

    else:

        st.info("""
### ℹ️ No Action Required

Transaction completed successfully.

No further recovery workflow is necessary.
""")

    st.divider()

    # ======================================================
    # RECOVERY CONFIDENCE
    # ======================================================

    st.header("🎯 AI Confidence Assessment")

    confidence = float(row["confidence"]) * 100

    col1, col2 = st.columns([1, 2])

    with col1:

        st.metric(
            "Confidence",
            f"{confidence:.0f}%"
        )

        st.progress(confidence / 100)

    with col2:

        if confidence >= 90:

            st.success("""
The AI model is highly confident about this recommendation.

Human intervention is generally unnecessary unless business policies require review.
""")

        elif confidence >= 70:

            st.warning("""
The AI recommendation is reliable but additional verification is recommended before executing recovery.
""")

        else:

            st.error("""
Confidence is relatively low.

A finance team member should verify the recommendation before proceeding.
""")

    st.divider()
    # ======================================================
    # AUDIT TIMELINE
    # ======================================================

    st.header("📝 Recovery Audit Timeline")

    timeline = [
        ("🔴 Payment Failure Detected", f"{failure} • ₹{float(row['amount_inr']):,.2f}"),
        ("🤖 AI Diagnosis Generated", str(row["diagnosis"])),
        ("⚡ Recovery Strategy Selected", f"{row['action']} • {confidence * 100:.0f}% confidence"),
        ("📈 Recovery Result Recorded", str(row["result"]).replace("_", " ")),
        ("🛑 Stopping Rule Applied", str(row["stopping_rule"])),
        ("📁 Audit Record Stored", f"Audit ID: {row['payment_id']} • Prompt: RecoverAI policy v1"),
    ]

    timeline_markup = '<div class="audit-timeline">'
    for event, detail in timeline:
        timeline_markup += f'<div class="audit-event">'
        timeline_markup += f'<div class="audit-event-title">{event}</div>'
        timeline_markup += f'<div class="audit-event-detail">{detail}</div>'
        timeline_markup += '</div>'
    timeline_markup += "</div>"
    st.markdown(timeline_markup, unsafe_allow_html=True)

    st.divider()

    # ======================================================
    # NEXT STEPS
    # ======================================================

    st.header("🚀 Recommended Next Steps")

    result = str(row["result"]).upper()

    if result == "RECOVERED":

        st.success("""
### ✅ Payment Successfully Recovered

Recommended Next Steps

• Close recovery workflow

• Notify merchant

• Update accounting records

• Archive transaction

• Continue monitoring future payments
""")

    elif result == "ESCALATED":

        st.error("""
### 🚨 Manual Review Required

Recommended Next Steps

• Finance team investigation

• Gateway verification

• Merchant notification

• Root cause analysis

• Create escalation report
""")

    elif result == "CUSTOMER_ACTION_REQUIRED":

        st.warning("""
### 📩 Customer Follow-up

Recommended Next Steps

• Send reminder email

• Generate payment link

• Wait 24 hours

• Retry payment

• Escalate if still unsuccessful
""")

    else:

        st.info("""
No additional recovery action is required.
""")

    st.divider()

    # ======================================================
    # DOWNLOAD AI REPORT
    # ======================================================

    st.header("📄 Export AI Report")

    st.download_button(
        label="⬇ Download AI Explanation",
        data=explanation,
        file_name=f"{row['payment_id']}_AI_Report.txt",
        mime="text/plain"
    )

    st.success("Recovery analysis completed successfully.")
# ==========================================================
# ANALYTICS PAGE
# ==========================================================

if page == "📊 Analytics":

    st.markdown("""
    <div class="mainHeader">

    <h1>📊 Recovery Analytics</h1>

    <p>
    Monitor AI performance, recovery trends and revenue insights.
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.success(
        "📈 Analytics Engine Active • Live Recovery Metrics"
    )

    st.divider()

    # ======================================================
    # ANALYTICS OVERVIEW
    # ======================================================

    analytics_kpis = [
        ("Recovery Rate", f"{float(m.recovery_rate_percent):.2f}%", "Outcome efficiency"),
        ("Recovered Revenue", f"₹{float(m.recovered_revenue_inr):,.0f}", "Value protected"),
        ("Failed Payments", f"{int(m.failed_payments):,}", "Recovery workload"),
        ("Escalated Cases", f"{int(m.escalated_cases):,}", "Human review queue"),
    ]
    analytics_markup = '<div class="analytics-card-grid">'
    for label, value, trend in analytics_kpis:
        analytics_markup += '<div class="analytics-card">'
        analytics_markup += f'<div class="analytics-card-label">{label}</div>'
        analytics_markup += f'<div class="analytics-card-value">{value}</div>'
        analytics_markup += f'<div class="analytics-card-trend">{trend}</div>'
        analytics_markup += '</div>'
    analytics_markup += "</div>"
    st.markdown(analytics_markup, unsafe_allow_html=True)

    analytics_rows = audit.copy()
    analytics_rows["Transaction"] = range(1, len(analytics_rows) + 1)
    analytics_rows["Recovered Revenue"] = pd.to_numeric(analytics_rows["recovered_amount_inr"], errors="coerce").fillna(0)
    analytics_rows["Cumulative Recovery"] = analytics_rows["Recovered Revenue"].cumsum()
    analytics_rows["Recovered Payments"] = analytics_rows["result"].astype(str).str.upper().eq("RECOVERED").cumsum()

    trend_col, funnel_col = st.columns([1.5, 1])
    with trend_col:
        st.subheader("Recovery Trends")
        analytics_trend = go.Figure()
        analytics_trend.add_trace(go.Scatter(
            x=analytics_rows["Transaction"], y=analytics_rows["Cumulative Recovery"],
            mode="lines", name="Recovered Revenue", fill="tozeroy",
            line={"color": PRIMARY, "width": 3}, fillcolor="rgba(37,99,235,.12)",
            hovertemplate="Transaction %{x}<br>₹%{y:,.0f}<extra></extra>",
        ))
        analytics_trend.add_trace(go.Scatter(
            x=analytics_rows["Transaction"], y=analytics_rows["Recovered Payments"],
            mode="lines", name="Recovered Payments", yaxis="y2",
            line={"color": SUCCESS, "width": 2, "dash": "dot"},
            hovertemplate="Transaction %{x}<br>%{y} recovered<extra></extra>",
        ))
        analytics_trend = _apply_layout(analytics_trend, height=390, showlegend=True)
        analytics_trend.update_layout(
            yaxis={"title": "Revenue (₹)"},
            yaxis2={"title": "Payments", "overlaying": "y", "side": "right", "showgrid": False},
            margin={"l": 10, "r": 10, "t": 18, "b": 10},
        )
        st.plotly_chart(analytics_trend, use_container_width=True)

    with funnel_col:
        st.subheader("Recovery Funnel")
        analytics_failed = audit["failure_reason"].notna() & audit["failure_reason"].astype(str).ne("")
        analytics_diagnosed = audit["diagnosis"].notna() & audit["diagnosis"].astype(str).ne("")
        analytics_retried = pd.to_numeric(audit["attempts"], errors="coerce").fillna(0).gt(1)
        analytics_recovered = audit["result"].astype(str).str.upper().eq("RECOVERED")
        analytics_escalated = audit["result"].astype(str).str.upper().eq("ESCALATED")
        analytics_funnel = go.Figure(go.Funnel(
            y=["Total", "Failed", "Diagnosed", "Retried", "Recovered", "Escalated"],
            x=[int(m.total_payments), int(analytics_failed.sum()), int(analytics_diagnosed.sum()), int(analytics_retried.sum()), int(analytics_recovered.sum()), int(analytics_escalated.sum())],
            textinfo="value+percent initial",
            marker={"color": [PRIMARY, "#3B82F6", "#60A5FA", "#93C5FD", SUCCESS, WARNING]},
        ))
        analytics_funnel = _apply_layout(analytics_funnel, height=390, showlegend=False)
        analytics_funnel.update_layout(margin={"l": 10, "r": 10, "t": 18, "b": 10})
        st.plotly_chart(analytics_funnel, use_container_width=True)

    st.subheader("Recovery Heatmap")
    analytics_heatmap_data = pd.crosstab(
        audit["failure_reason"].fillna("SUCCESS"),
        audit["action"].fillna("UNASSIGNED"),
    )
    analytics_heatmap = px.imshow(
        analytics_heatmap_data,
        labels={"x": "AI Action", "y": "Failure Reason", "color": "Transactions"},
        color_continuous_scale=[[0, "#EFF6FF"], [.5, "#93C5FD"], [1, PRIMARY]],
        aspect="auto",
        text_auto=True,
    )
    analytics_heatmap = _apply_layout(analytics_heatmap, height=420, showlegend=False)
    analytics_heatmap.update_layout(margin={"l": 10, "r": 10, "t": 18, "b": 10})
    st.plotly_chart(analytics_heatmap, use_container_width=True)

    st.divider()

    # ======================================================
    # KPI METRICS
    # ======================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Recovery Rate",
        f"{float(m.recovery_rate_percent):.2f}%"
    )

    c2.metric(
        "Recovered Revenue",
        f"₹{float(m.recovered_revenue_inr):,.0f}"
    )

    c3.metric(
        "Failed Payments",
        int(m.failed_payments)
    )

    c4.metric(
        "Escalated",
        int(m.escalated_cases)
    )

    st.divider()

    # ======================================================
    # RECOVERY RESULT
    # ======================================================

    st.subheader("📈 Recovery Result Distribution")

    result_chart = (
        audit["result"]
        .value_counts()
        .reset_index()
    )

    result_chart.columns = ["Result", "Count"]

    fig_result = styled_bar_chart(result_chart, "Result", "Count", height=420)

    st.plotly_chart(fig_result, use_container_width=True)

    st.divider()

    # ======================================================
    # FAILURE REASONS
    # ======================================================

    st.subheader("🚨 Failure Reasons")

    failure_chart = (
        audit["failure_reason"]
        .fillna("SUCCESS")
        .value_counts()
        .reset_index()
    )

    failure_chart.columns = [
        "Failure Reason",
        "Count"
    ]

    fig_failure = styled_bar_chart(
        failure_chart, "Failure Reason", "Count", height=420, horizontal=True
    )

    st.plotly_chart(fig_failure, use_container_width=True)

    st.divider()

    # ======================================================
    # AI ACTIONS
    # ======================================================

    st.subheader("🤖 AI Recovery Actions")

    action_chart = (
        audit["action"]
        .value_counts()
        .reset_index()
    )

    action_chart.columns = [
        "Action",
        "Count"
    ]

    fig_action = styled_bar_chart(action_chart, "Action", "Count", height=420)

    st.plotly_chart(fig_action, use_container_width=True)

    st.divider()

    # ======================================================
    # REVENUE COMPARISON
    # ======================================================

    st.subheader("💰 Revenue Comparison")

    fig_rev_compare = styled_grouped_bar(
        labels=["At Risk", "Recovered"],
        values=[float(m.at_risk_revenue_inr), float(m.recovered_revenue_inr)],
        series_name="Revenue",
        height=420,
        colors=[DANGER, SUCCESS],
    )

    st.plotly_chart(fig_rev_compare, use_container_width=True)

    st.divider()

    # ======================================================
    # PIE CHARTS
    # ======================================================

    left, right = st.columns(2)

    with left:

        st.subheader("Recovery Outcome")

        outcome_pie = (
            audit["result"]
            .value_counts()
            .rename_axis("Result")
            .reset_index(name="Count")
        )

        fig_outcome_pie = styled_pie_chart(outcome_pie, "Result", "Count", height=380)

        st.plotly_chart(fig_outcome_pie, use_container_width=True)

    with right:

        st.subheader("Failure Distribution")

        failure_pie = (
            audit["failure_reason"]
            .fillna("SUCCESS")
            .value_counts()
            .rename_axis("Failure Reason")
            .reset_index(name="Count")
        )

        fig_failure_pie = styled_pie_chart(
            failure_pie, "Failure Reason", "Count", height=380
        )

        st.plotly_chart(fig_failure_pie, use_container_width=True)

    st.divider()

    # ======================================================
    # ANALYTICS TABLE
    # ======================================================

    st.subheader("📋 Recovery Dataset")

    analytics_table = filtered.copy()
    analytics_format = {
        "amount_inr": "₹{:,.2f}",
        "recovered_amount_inr": "₹{:,.2f}",
        "confidence": "{:.0%}",
    }
    analytics_table = analytics_table.style.format(
        {column: pattern for column, pattern in analytics_format.items() if column in analytics_table.columns}
    ).set_properties(
        **{"font-size": "12px", "background-color": "#FFFFFF", "color": "#334155"}
    ).set_table_styles([
        {"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#EFF6FF")]},
        {"selector": "tbody tr:hover", "props": [("background-color", "#DBEAFE")]},
        {"selector": "thead", "props": [("background-color", "#2563EB"), ("color", "#FFFFFF")]},
    ])

    st.dataframe(analytics_table, use_container_width=True, hide_index=True)
# ==========================================================
# AUDIT LOGS PAGE
# ==========================================================

if page == "📜 Audit Logs":

    st.markdown("""
    <div class="mainHeader">

    <h1>📜 Recovery Audit Logs</h1>

    <p>
    Complete audit trail of every AI recovery decision.
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.success(
        "🔒 Audit Logging Enabled • Compliance Ready"
    )

    st.divider()

    # ======================================================
    # SEARCH
    # ======================================================

    search = st.text_input(
        "🔍 Search Payment ID",
        placeholder="Example: PAY1001"
    )

    logs = filtered.copy()

    if search:

        logs = logs[
            logs["payment_id"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # ======================================================
    # SUMMARY METRICS
    # ======================================================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Audit Records",
        len(logs)
    )

    c2.metric(
        "Recovered",
        len(logs[logs["result"] == "RECOVERED"])
    )

    c3.metric(
        "Escalated",
        len(logs[logs["result"] == "ESCALATED"])
    )

    c4.metric(
        "Customer Action",
        len(
            logs[
                logs["result"] ==
                "CUSTOMER_ACTION_REQUIRED"
            ]
        )
    )

    st.divider()

    # ======================================================
    # AUDIT TABLE
    # ======================================================

    st.subheader("📋 Audit Records")

    audit_table = logs[
        [
            "payment_id",
            "amount_inr",
            "failure_reason",
            "action",
            "confidence",
            "result",
            "stopping_rule",
            "recovered_amount_inr"
        ]
    ].copy()

    audit_table.columns = [
        "Payment ID",
        "Amount (₹)",
        "Failure Reason",
        "AI Action",
        "Confidence",
        "Result",
        "Stopping Rule",
        "Recovered (₹)"
    ]

    audit_csv = audit_table.to_csv(index=False).encode("utf-8")

    audit_table = audit_table.style.format({
        "Amount (₹)": "₹{:,.2f}",
        "Recovered (₹)": "₹{:,.2f}",
        "Confidence": "{:.0%}",
    }).set_properties(
        **{"font-size": "12px", "background-color": "#FFFFFF", "color": "#334155"}
    ).set_table_styles([
        {"selector": "tbody tr:nth-child(even)", "props": [("background-color", "#EFF6FF")]},
        {"selector": "tbody tr:hover", "props": [("background-color", "#DBEAFE")]},
        {"selector": "thead", "props": [("background-color", "#2563EB"), ("color", "#FFFFFF")]},
    ])

    st.dataframe(audit_table, use_container_width=True, hide_index=True)

    st.divider()

    # ======================================================
    # AUDIT TIMELINE
    # ======================================================

    st.subheader("📝 Audit Timeline")

    for _, row in logs.iterrows():

        st.markdown(
            f"""
<div class="audit">

<b>{row['payment_id']}</b>

<br><br>

💰 Amount:
₹{float(row['amount_inr']):,.2f}

<br>

⚠ Failure:
{row['failure_reason']}

<br>

🤖 AI Action:
{row['action']}

<br>

📈 Result:
{row['result']}

<br>

🎯 Confidence:
{float(row['confidence'])*100:.0f}%

<br>

🛑 Stopping Rule:
{row['stopping_rule']}

</div>
""",
            unsafe_allow_html=True
        )

    st.divider()

    # ======================================================
    # DOWNLOAD AUDIT
    # ======================================================

    st.download_button(
        label="📥 Download Audit Logs",
        data=audit_csv,
        file_name="RecoverAI_AuditLogs.csv",
        mime="text/csv"
    )
# ==========================================================
# ABOUT PAGE
# ==========================================================

if page == "ℹ️ About":

    st.title("💳 About RecoverAI")

    st.markdown("""
RecoverAI is an AI-powered revenue recovery platform that helps businesses recover failed online payments automatically while keeping every AI decision transparent and auditable.

The platform detects failed transactions, recommends the best recovery action, generates explainable AI insights using Google Gemini, and maintains a complete audit trail for finance and operations teams.
""")

    st.divider()

    # ======================================================
    # MISSION
    # ======================================================

    st.subheader("🎯 Our Mission")

    st.info("""
RecoverAI combines Artificial Intelligence with explainable decision-making to reduce revenue loss caused by payment failures while ensuring human oversight and regulatory transparency.
""")

    st.divider()

    # ======================================================
    # CORE FEATURES
    # ======================================================

    st.subheader("🚀 Core Features")

    col1, col2 = st.columns(2)

    with col1:

        st.success("""
### 🤖 AI Intelligence

• AI Recovery Recommendations

• Google Gemini Explanations

• Confidence Scoring

• Explainable AI

• Smart Retry Strategy

• Human-in-the-loop
""")

    with col2:

        st.success("""
### 📊 Business Platform

• Executive Dashboard

• Revenue Analytics

• Audit Logs

• CSV Export

• Search & Filters

• Recovery Reports
""")

    st.divider()

    # ======================================================
    # TECHNOLOGY STACK
    # ======================================================

    st.subheader("🛠 Technology Stack")

    tech1, tech2, tech3 = st.columns(3)

    with tech1:

        st.info("""
### Frontend

• Streamlit

• HTML + CSS

• Interactive Dashboard
""")

    with tech2:

        st.info("""
### Backend

• Python

• Pandas

• Recovery Engine
""")

    with tech3:

        st.info("""
### AI

• Google Gemini

• Prompt Engineering

• Explainable AI
""")

    st.divider()

    # ======================================================
    # WORKFLOW
    # ======================================================

    st.subheader("🔄 RecoverAI Workflow")

    st.code("""
Payment Failure
        │
        ▼
Failure Detection
        │
        ▼
AI Diagnosis
        │
        ▼
Recovery Recommendation
        │
        ▼
Gemini Explanation
        │
        ▼
Recovery Action
        │
        ▼
Audit Logging
        │
        ▼
Business Analytics
""")

    st.divider()

    # ======================================================
    # BUILDATHON GOALS
    # ======================================================

    st.subheader("🏆 Razorpay Buildathon Goals")

    st.markdown("""
✅ Detect failed payments automatically

✅ Recover maximum revenue

✅ Explain every AI decision

✅ Maintain complete audit trail

✅ Keep humans in control

✅ Improve merchant trust
""")

    st.divider()

    # ======================================================
    # LIVE PLATFORM METRICS
    # ======================================================

    st.subheader("📈 Live Platform Statistics")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Payments",
        int(m.total_payments)
    )

    m2.metric(
        "Recovered",
        int(m.recovered_payments)
    )

    m3.metric(
        "Recovery Rate",
        f"{float(m.recovery_rate_percent):.2f}%"
    )

    m4.metric(
        "AI Decisions",
        len(audit)
    )

    st.divider()

    # ======================================================
    # PROJECT INFORMATION
    # ======================================================

    st.subheader("👩‍💻 Project Information")

    st.info("""
**Project Name:** RecoverAI

**Category:** AI Revenue Recovery Agent

**Event:** Razorpay Buildathon 2026

**Frontend:** Streamlit

**Backend:** Python

**Artificial Intelligence:** Google Gemini

**Database:** CSV Dataset

**Version:** 1.0
""")

    st.divider()

    # ======================================================
    # FOOTER
    # ======================================================

    st.success("""
RecoverAI is designed to make payment recovery smarter, faster and more transparent by combining AI-driven decision making with complete auditability and human oversight.
""")