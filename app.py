"""
IPL Crowd Safety Management Dashboard — Streamlit
Run: streamlit run app.py
Install: pip install streamlit pandas numpy plotly openpyxl cohere matplotlib
"""

import os
import io
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import cohere

# ─────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL Crowd Safety Management",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

PHASE_ORDER = ["Pre-match", "First innings", "Break", "Second innings", "Exit phase"]

# ─────────────────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────────────────
THEMES = {
    "Overview": {
        "bg": "#F6F4FF", "sidebar": "#EDE9FE", "card": "#FFFFFF",
        "accent": "#7C3AED", "accent_lt": "#EDE9FE", "accent2": "#5B21B6",
        "text": "#1E1B4B", "text2": "#6B7280", "border": "#C4B5FD",
        "plot_bg": "#FFFFFF", "paper_bg": "#F6F4FF", "grid": "#F0EBFF",
        "legend_rgba": "rgba(246,244,255,0.92)",
        "palette": ["#7C3AED", "#A78BFA", "#F59E0B", "#10B981", "#EF4444", "#3B82F6"],
        "crit_col": "#EF4444", "warn_col": "#F59E0B", "ok_col": "#10B981", "info_col": "#7C3AED",
    },
    "Crowd Flow": {
        "bg": "#EFF6FF", "sidebar": "#DBEAFE", "card": "#FFFFFF",
        "accent": "#1D4ED8", "accent_lt": "#DBEAFE", "accent2": "#1E40AF",
        "text": "#1E2A4A", "text2": "#6B7280", "border": "#93C5FD",
        "plot_bg": "#FFFFFF", "paper_bg": "#EFF6FF", "grid": "#E8F2FF",
        "legend_rgba": "rgba(239,246,255,0.92)",
        "palette": ["#1D4ED8", "#60A5FA", "#F59E0B", "#10B981", "#8B5CF6", "#EF4444"],
        "crit_col": "#EF4444", "warn_col": "#F59E0B", "ok_col": "#10B981", "info_col": "#1D4ED8",
    },
    "Medical & Heat": {
        "bg": "#FFF1F2", "sidebar": "#FFE4E6", "card": "#FFFFFF",
        "accent": "#E11D48", "accent_lt": "#FFE4E6", "accent2": "#BE123C",
        "text": "#3B0A14", "text2": "#6B7280", "border": "#FDA4AF",
        "plot_bg": "#FFFFFF", "paper_bg": "#FFF1F2", "grid": "#FFF0F1",
        "legend_rgba": "rgba(255,241,242,0.92)",
        "palette": ["#E11D48", "#FB7185", "#F97316", "#8B5CF6", "#3B82F6", "#10B981"],
        "crit_col": "#E11D48", "warn_col": "#F97316", "ok_col": "#10B981", "info_col": "#8B5CF6",
    },
    "Security": {
        "bg": "#FFFBEB", "sidebar": "#FEF3C7", "card": "#FFFFFF",
        "accent": "#D97706", "accent_lt": "#FEF3C7", "accent2": "#B45309",
        "text": "#1C1007", "text2": "#6B7280", "border": "#FCD34D",
        "plot_bg": "#FFFFFF", "paper_bg": "#FFFBEB", "grid": "#FFFCF0",
        "legend_rgba": "rgba(255,251,235,0.92)",
        "palette": ["#D97706", "#F59E0B", "#3B82F6", "#10B981", "#8B5CF6", "#EF4444"],
        "crit_col": "#EF4444", "warn_col": "#D97706", "ok_col": "#10B981", "info_col": "#3B82F6",
    },
    "Resource Planning": {
        "bg": "#F0FDFA", "sidebar": "#CCFBF1", "card": "#FFFFFF",
        "accent": "#0D9488", "accent_lt": "#CCFBF1", "accent2": "#0F766E",
        "text": "#042F2E", "text2": "#6B7280", "border": "#5EEAD4",
        "plot_bg": "#FFFFFF", "paper_bg": "#F0FDFA", "grid": "#EDFDF8",
        "legend_rgba": "rgba(240,253,250,0.92)",
        "palette": ["#0D9488", "#34D399", "#3B82F6", "#8B5CF6", "#F59E0B", "#EF4444"],
        "crit_col": "#EF4444", "warn_col": "#F59E0B", "ok_col": "#0D9488", "info_col": "#3B82F6",
    },
    "Risk Matrix": {
        "bg": "#F8FAFC", "sidebar": "#E2E8F0", "card": "#FFFFFF",
        "accent": "#DC2626", "accent_lt": "#FEE2E2", "accent2": "#991B1B",
        "text": "#111827", "text2": "#6B7280", "border": "#CBD5E1",
        "plot_bg": "#FFFFFF", "paper_bg": "#F8FAFC", "grid": "#E5E7EB",
        "legend_rgba": "rgba(248,250,252,0.92)",
        "palette": ["#DC2626", "#F97316", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6"],
        "crit_col": "#DC2626", "warn_col": "#F59E0B", "ok_col": "#10B981", "info_col": "#3B82F6",
    },
    "Ask AI": {
    "bg": "#F5F3FF", "sidebar": "#EDE9FE", "card": "#FFFFFF",
    "accent": "#8B5CF6", "accent_lt": "#EDE9FE", "accent2": "#6D28D9",
    "text": "#1E1B4B", "text2": "#6B7280", "border": "#C4B5FD",
    "plot_bg": "#FFFFFF", "paper_bg": "#F5F3FF", "grid": "#EDE9FE",
    "legend_rgba": "rgba(245,243,255,0.92)",
    "palette": ["#8B5CF6", "#A78BFA", "#F59E0B", "#10B981", "#EF4444", "#3B82F6"],
    "crit_col": "#EF4444", "warn_col": "#F59E0B", "ok_col": "#10B981", "info_col": "#8B5CF6",
    },
}

PAGES = [
    ("🏠", "Overview"),
    ("🌊", "Crowd Flow"),
    ("🏥", "Medical & Heat"),
    ("🔒", "Security"),
    ("📦", "Resource Planning"),
    ("🚨", "Risk Matrix"),
    ("💬", "Ask AI"),
]

if "active_page" not in st.session_state:
    st.session_state.active_page = "Overview"


# ─────────────────────────────────────────────────────────
# DATA LOAD
# ─────────────────────────────────────────────────────────
@st.cache_data
def load_all():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

    def _read(fname):
        path = os.path.join(base, fname)
        if not os.path.exists(path):
            st.error(f"❌ Missing file: data/{fname}")
            st.stop()
        return pd.read_excel(path)

    ops = _read("fact_operations_main.xlsx")
    inc = _read("fact_incidents.xlsx")
    evt = _read("fact_events.xlsx")
    zone = _read("dim_zone.xlsx")
    stadium = _read("dim_stadium.xlsx")

    for df in [ops, inc, evt, zone, stadium]:
        df.columns = df.columns.str.strip().str.lower()

    ops = ops.merge(zone[["zone_id", "zone_name", "zone_type"]], on="zone_id", how="left")

    zone_s = zone[["zone_id", "stadium_id"]].merge(
        stadium[["stadium_id", "stadium_name"]],
        on="stadium_id",
        how="left"
    )

    ops = ops.merge(zone_s[["zone_id", "stadium_name"]], on="zone_id", how="left")

    evt_cols = ["event_id", "season_year", "is_final_match", "total_attendance"]
    ops = ops.merge(evt[evt_cols], on="event_id", how="left")

    ops["heat_risk_index"] = ops["temperature_celsius"] * 0.7 + ops["humidity_percent"] * 0.3
    ops["occupancy_pct"] = ops["occupancy_rate"] * 100
    ops["capacity_breach"] = (ops["occupancy_rate"] >= 0.55).astype(int)

    ops["staff_adequacy_ratio"] = np.where(
        ops["people_count"] > 0,
        ops["required_staff"] / ops["people_count"] * 1000,
        0
    )

    ops["occupancy_risk_band"] = pd.cut(
        ops["occupancy_rate"],
        bins=[-np.inf, 0.45, 0.60, 0.70, np.inf],
        labels=["Low", "Moderate", "High", "Critical"]
    )

    ops["queue_stress"] = pd.cut(
        ops["avg_queue_wait_time"],
        bins=[-np.inf, 10, 20, 25, np.inf],
        labels=[
            "Acceptable under 10 min",
            "Moderate 10-20 min",
            "High 20-25 min",
            "Extreme 25+ min",
        ]
    )

    q75 = evt["total_attendance"].quantile(0.75)
    q40 = evt["total_attendance"].quantile(0.40)

    evt["match_category"] = np.select(
        [
            evt["is_final_match"] == 1,
            evt["total_attendance"] >= q75,
            evt["total_attendance"] >= q40,
        ],
        ["Final Match", "High Attendance Match", "Moderate Attendance Match"],
        default="Regular Match"
    )

    ops = ops.merge(evt[["event_id", "match_category"]], on="event_id", how="left")
    ops["match_category"] = ops["match_category"].fillna("Regular Match")

    inc = inc.merge(evt[["event_id", "season_year"]], on="event_id", how="left")
    inc = inc.merge(zone_s[["zone_id", "stadium_name"]], on="zone_id", how="left")

    return ops, inc


try:
    ops, inc = load_all()
except Exception as e:
    st.error(f"❌ Data load error: {e}")
    st.stop()


# ─────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────
def inject_css(t):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif;
}}

.stApp {{
    background-color: {t['bg']};
    color: {t['text']};
}}

.block-container {{
    padding-top: 4.2rem;
    padding-bottom: 1rem;
    max-width: 1580px;
}}

section[data-testid="stSidebar"] {{
    background-color: {t['sidebar']};
    border-right: 2px solid {t['border']};
    min-width: 235px !important;
    max-width: 235px !important;
}}

section[data-testid="stSidebar"] * {{
    color: {t['text']} !important;
}}

section[data-testid="stSidebar"] .stButton > button {{
    width: 100% !important;
    text-align: left !important;
    background: {t['card']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    color: {t['text']} !important;
    margin-bottom: 5px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}}

section[data-testid="stSidebar"] .stButton > button:hover {{
    background: {t['accent_lt']} !important;
    border-color: {t['accent']} !important;
    color: {t['accent2']} !important;
}}

.dash-header {{
    background: linear-gradient(120deg, {t['card']} 60%, {t['accent_lt']});
    border: 1px solid {t['border']};
    border-left: 6px solid {t['accent']};
    border-radius: 18px;
    padding: 18px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    display: flex;
    align-items: center;
    gap: 16px;
}}

.dash-title {{
    font-family: 'Sora', sans-serif;
    font-size: 23px;
    font-weight: 800;
    color: {t['text']};
    margin: 0;
}}

.dash-sub {{
    font-size: 12.5px;
    color: {t['text2']};
    margin-top: 5px;
}}

.kpi-card {{
    background: {t['card']};
    border: 1px solid {t['border']};
    border-radius: 16px;
    padding: 16px 18px 14px;
    min-height: 100px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.055);
    position: relative;
    overflow: hidden;
}}

.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
}}

.kpi-info::before {{ background: {t['info_col']}; }}
.kpi-warn::before {{ background: {t['warn_col']}; }}
.kpi-crit::before {{ background: {t['crit_col']}; }}
.kpi-ok::before {{ background: {t['ok_col']}; }}

.kpi-label {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    color: {t['text2']};
    margin-bottom: 7px;
}}

.kpi-val {{
    font-family: 'Sora', sans-serif;
    font-size: 27px;
    font-weight: 800;
    color: {t['text']};
    line-height: 1;
}}

.kpi-sub {{
    font-size: 10px;
    color: {t['text2']};
    margin-top: 6px;
}}

.sec-lbl {{
    font-family: 'Sora', sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: {t['accent2']};
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin: 14px 0 8px 0;
    padding-bottom: 5px;
    border-bottom: 2px solid {t['accent_lt']};
}}

.ai-card {{
    background: {t["card"]};
    border: 1px solid {t["border"]};
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    margin-bottom: 14px;
    color: {t["text"]};
}}

.ai-mini-card {{
    background: {t["card"]};
    border: 1px solid {t["border"]};
    border-left: 5px solid {t["accent"]};
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.045);
}}

.ai-metric {{
    font-size: 28px;
    font-weight: 800;
    color: {t["text"]};
    font-family: 'Sora', sans-serif;
}}

.ai-label {{
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.7px;
    color: {t["text2"]};
}}

.ai-status-critical {{
    color: #DC2626;
    font-weight: 700;
    font-size: 12px;
}}

.ai-status-warning {{
    color: #F59E0B;
    font-weight: 700;
    font-size: 12px;
}}

.ai-status-good {{
    color: #10B981;
    font-weight: 700;
    font-size: 12px;
}}

.insight-pill {{
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 8px;
    background: {t["accent_lt"]};
    color: {t["accent2"]};
}}

.risk-critical {{
    background:#FEE2E2;
    color:#991B1B;
    padding:4px 10px;
    border-radius:999px;
    font-size:11px;
    font-weight:800;
}}

.risk-monitor {{
    background:#FEF3C7;
    color:#92400E;
    padding:4px 10px;
    border-radius:999px;
    font-size:11px;
    font-weight:800;
}}

.risk-safe {{
    background:#DCFCE7;
    color:#166534;
    padding:4px 10px;
    border-radius:999px;
    font-size:11px;
    font-weight:800;
}}

div[data-testid="stPlotlyChart"] > div {{
    border-radius: 14px !important;
    border: 1px solid {t['border']} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.045) !important;
}}

[data-testid="stDataFrame"] {{
    border-radius: 12px;
    border: 1px solid {t['border']};
    overflow: hidden;
}}

::-webkit-scrollbar {{
    width: 5px;
    height: 5px;
}}

::-webkit-scrollbar-track {{
    background: {t['bg']};
}}

::-webkit-scrollbar-thumb {{
    background: {t['border']};
    border-radius: 3px;
}}

hr {{
    border-color: {t['border']} !important;
    opacity: 0.6;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def kpi_card(label, value, style="info", sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
<div class="kpi-card kpi-{style}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-val">{value}</div>
  {sub_html}
</div>
""", unsafe_allow_html=True)


def page_header(icon, title, subtitle):
    st.markdown(f"""
<div class="dash-header">
  <span style="font-size:34px;line-height:1">{icon}</span>
  <div>
    <div class="dash-title">{title}</div>
    <div class="dash-sub">{subtitle}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def sec_label(text):
    st.markdown(f'<div class="sec-lbl">{text}</div>', unsafe_allow_html=True)


def get_cohere_key():
    try:
        return st.secrets.get("COHERE_API_KEY", "")
    except Exception:
        return ""


def generate_cohere_insights(summary_text, temperature_value=0.4, token_value=700):
    api_key = get_cohere_key()

    if not api_key:
        return (
            "⚠️ Cohere API key not found. Add your key in `.streamlit/secrets.toml` "
            "or Streamlit Cloud Secrets as: `COHERE_API_KEY = \"your_api_key_here\"`."
        )

    try:
        co = cohere.Client(api_key)

        prompt = f"""
You are a professional data analyst for an IPL Crowd Safety Management Dashboard.

Based on the dashboard metrics below, generate:
1. Key insights
2. Risk observations
3. Practical recommendations
4. Presentation-friendly explanation

Rules:
- Use simple professional language.
- Keep it useful for dashboard presentation.
- Focus on crowd safety, bottlenecks, medical readiness, heat exposure, security, and resource planning.
- Give clear actions for stadium operations teams.
- Mention priority zones and actions.
- Keep the response short and dashboard friendly.

Dashboard Summary:
{summary_text}
"""

        response = co.chat(
            model="command-r-plus-08-2024",
            message=prompt,
            temperature=temperature_value,
            max_tokens=token_value,
        )
        return response.text

    except Exception as e:
        return f"❌ Cohere insight generation failed: {e}"
def ask_ai_question(question, context_text, temperature_value=0.3, token_value=500):
    api_key = get_cohere_key()

    if not api_key:
        return (
            "⚠️ Cohere API key not found. Add your key in `.streamlit/secrets.toml` "
            "or Streamlit Cloud Secrets."
        )

    try:
        co = cohere.Client(api_key)

        prompt = f"""
You are an AI assistant inside an IPL Crowd Safety Management Dashboard.

Answer the user's question using only the dashboard context below.

Rules:
- Answer in simple professional language.
- Be concise.
- If the question asks for action, give practical stadium operation recommendations.
- Do not invent data outside the dashboard context.
- Mention if the answer is based on selected filters.

Dashboard Context:
{context_text}

User Question:
{question}
"""

        response = co.chat(
            model="command-r-plus-08-2024",
            message=prompt,
            temperature=temperature_value,
            max_tokens=token_value,
        )

        return response.text

    except Exception as e:
        return f"❌ Q&A failed: {e}"

def sfig(fig, t, h=320):
    fig.update_layout(
        height=h,
        paper_bgcolor=t["paper_bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Plus Jakarta Sans", size=12),
        title_font=dict(color=t["text"], size=14, family="Sora"),
        title_x=0.03,
        legend=dict(
            bgcolor=t["legend_rgba"],
            bordercolor=t["border"],
            borderwidth=1,
            font=dict(color=t["text2"], size=11),
        ),
        margin=dict(l=30, r=20, t=50, b=30),
        colorway=t["palette"],
    )

    fig.update_xaxes(
        gridcolor=t["grid"],
        zerolinecolor=t["grid"],
        linecolor=t["border"],
        tickfont=dict(color=t["text2"]),
        title_font=dict(color=t["text2"]),
    )

    fig.update_yaxes(
        gridcolor=t["grid"],
        zerolinecolor=t["grid"],
        linecolor=t["border"],
        tickfont=dict(color=t["text2"]),
        title_font=dict(color=t["text2"]),
    )

    return fig


def safe_norm(series):
    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
        return pd.Series(0, index=series.index)

    return ((series - min_val) / (max_val - min_val)) * 100


def add_advanced_risk_features(df):
    df = df.copy()

    df["security_total"] = (
        df["security_incidents"].fillna(0)
        + df["unauthorized_entry_attempts"].fillna(0)
        + df["counterfeit_ticket_cases"].fillna(0)
        + df["fan_ejections"].fillna(0)
    )

    df["risk_score"] = (
        safe_norm(df["crowd_pressure_index"].fillna(0)) * 0.25
        + safe_norm(df["bottleneck_risk_score"].fillna(0)) * 0.25
        + safe_norm(df["avg_queue_wait_time"].fillna(0)) * 0.15
        + safe_norm(df["ambulance_response_time"].fillna(0)) * 0.15
        + safe_norm(df["heat_risk_index"].fillna(0)) * 0.10
        + safe_norm(df["security_total"].fillna(0)) * 0.10
    ).round(2)

    df["risk_band"] = pd.cut(
        df["risk_score"],
        bins=[-1, 40, 70, 101],
        labels=["Safe", "Monitor", "Critical"]
    )

    df["risk_reason"] = np.select(
        [
            df["bottleneck_risk_score"] >= 70,
            df["ambulance_response_time"] >= 10,
            df["avg_queue_wait_time"] >= 20,
            df["heat_risk_index"] >= df["heat_risk_index"].quantile(0.75),
            df["security_total"] >= df["security_total"].quantile(0.75),
        ],
        [
            "High bottleneck risk",
            "Delayed medical response",
            "Long queue wait time",
            "High heat exposure",
            "High security activity",
        ],
        default="Normal operating condition"
    )

    df["recommended_action"] = np.select(
        [
            df["risk_reason"] == "High bottleneck risk",
            df["risk_reason"] == "Delayed medical response",
            df["risk_reason"] == "Long queue wait time",
            df["risk_reason"] == "High heat exposure",
            df["risk_reason"] == "High security activity",
        ],
        [
            "Add barricades and redirect crowd flow",
            "Deploy extra medical team and ambulance support",
            "Open additional gates and improve queue control",
            "Provide water points and cooling zones",
            "Increase security staff and access checks",
        ],
        default="Continue monitoring"
    )

    return df


def create_risk_priority_matrix(df):
    cols = [
        "stadium_name", "zone_name", "zone_type", "phase",
        "risk_score", "risk_band", "risk_reason", "recommended_action",
        "people_count", "avg_queue_wait_time", "ambulance_response_time",
        "bottleneck_risk_score", "heat_risk_index"
    ]

    available_cols = [c for c in cols if c in df.columns]

    matrix = (
        df[available_cols]
        .sort_values("risk_score", ascending=False)
        .head(15)
        .copy()
    )

    matrix.rename(columns={
        "stadium_name": "Stadium",
        "zone_name": "Zone",
        "zone_type": "Zone Type",
        "phase": "Phase",
        "risk_score": "Risk Score",
        "risk_band": "Risk Band",
        "risk_reason": "Main Risk Reason",
        "recommended_action": "Recommended Action",
        "people_count": "People Count",
        "avg_queue_wait_time": "Queue Wait",
        "ambulance_response_time": "Ambulance Response",
        "bottleneck_risk_score": "Bottleneck Score",
        "heat_risk_index": "Heat Risk",
    }, inplace=True)

    return matrix


def create_anomaly_table(df):
    metrics = [
        "avg_queue_wait_time",
        "ambulance_response_time",
        "bottleneck_risk_score",
        "crowd_pressure_index",
        "heat_risk_index",
        "security_total",
        "medical_incidents",
    ]

    temp = df.copy()
    existing_metrics = [m for m in metrics if m in temp.columns]

    anomaly_flags = []

    for metric in existing_metrics:
        threshold = temp[metric].quantile(0.90)
        flag_col = f"{metric}_anomaly"
        temp[flag_col] = temp[metric] >= threshold
        anomaly_flags.append(flag_col)

    temp["anomaly_count"] = temp[anomaly_flags].sum(axis=1)

    temp["anomaly_reason"] = temp.apply(
        lambda row: ", ".join([
            metric.replace("_", " ").title()
            for metric in existing_metrics
            if row.get(f"{metric}_anomaly", False)
        ]),
        axis=1
    )

    anomalies = temp[temp["anomaly_count"] > 0].copy()

    cols = [
        "stadium_name", "zone_name", "zone_type", "phase",
        "anomaly_count", "anomaly_reason", "risk_score",
        "avg_queue_wait_time", "ambulance_response_time",
        "bottleneck_risk_score", "heat_risk_index"
    ]

    available_cols = [c for c in cols if c in anomalies.columns]

    anomalies = anomalies[available_cols].sort_values(
        ["anomaly_count", "risk_score"],
        ascending=False
    ).head(15)

    anomalies.rename(columns={
        "stadium_name": "Stadium",
        "zone_name": "Zone",
        "zone_type": "Zone Type",
        "phase": "Phase",
        "anomaly_count": "Anomaly Count",
        "anomaly_reason": "Anomaly Reason",
        "risk_score": "Risk Score",
        "avg_queue_wait_time": "Queue Wait",
        "ambulance_response_time": "Ambulance Response",
        "bottleneck_risk_score": "Bottleneck Score",
        "heat_risk_index": "Heat Risk",
    }, inplace=True)

    return anomalies


def dataframe_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="text-align:center;padding:6px 0 14px 0;">
  <div style="font-size:30px;">🏏</div>
  <div style="font-family:'Sora',sans-serif;font-size:15px;font-weight:800;margin-top:4px;">
    IPL Crowd Safety
  </div>
  <div style="font-size:9.5px;letter-spacing:0.8px;font-weight:600;opacity:0.5;margin-top:2px;">
    MANAGEMENT DASHBOARD
  </div>
</div>
""", unsafe_allow_html=True)

    for icon, name in PAGES:
        if st.button(f"{icon}  {name}", key=f"nav_{name}"):
            st.session_state.active_page = name
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:10px;font-weight:700;letter-spacing:0.8px;margin:0 0 8px 0;opacity:0.6;">FILTERS</p>',
        unsafe_allow_html=True
    )

    all_stadiums = sorted(ops["stadium_name"].dropna().unique())
    sel_stadium = st.multiselect("Stadium", all_stadiums, default=all_stadiums, key="f_stad")

    sel_phase = st.multiselect("Phase", PHASE_ORDER, default=PHASE_ORDER, key="f_ph")

    all_years = sorted(ops["season_year"].dropna().astype(int).unique())
    sel_year = st.multiselect("Year", all_years, default=all_years, key="f_yr")

    all_zones = sorted(ops["zone_type"].dropna().unique())
    sel_zone = st.multiselect("Zone Type", all_zones, default=all_zones, key="f_zt")

    all_cats = sorted(ops["match_category"].dropna().unique())
    sel_cat = st.multiselect("Match Category", all_cats, default=all_cats, key="f_mc")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:10px;font-weight:700;letter-spacing:0.8px;margin:0 0 8px 0;opacity:0.6;">COHERE AI SETTINGS</p>',
        unsafe_allow_html=True
    )

    ai_temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.1,
    )

    ai_max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=2000,
        value=700,
        step=100,
    )


# ─────────────────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────────────────
f = ops[
    ops["stadium_name"].isin(sel_stadium)
    & ops["phase"].isin(sel_phase)
    & ops["season_year"].astype(int).isin(sel_year)
    & ops["zone_type"].isin(sel_zone)
    & ops["match_category"].isin(sel_cat)
].copy()

page = st.session_state.active_page
t = THEMES[page]
inject_css(t)

if f.empty:
    st.warning("⚠️ No data for the selected filters. Please widen your selection.")
    st.stop()

f["phase_cat"] = pd.Categorical(f["phase"], categories=PHASE_ORDER, ordered=True)

inc_f = inc[
    inc["stadium_name"].isin(sel_stadium)
    & inc["season_year"].astype(int).isin(sel_year)
].copy() if "stadium_name" in inc.columns and "season_year" in inc.columns else inc.copy()

f = add_advanced_risk_features(f)

risk_matrix = create_risk_priority_matrix(f)
anomaly_table = create_anomaly_table(f)

# ─────────────────────────────────────────────────────────
# KPI CALCULATIONS
# ─────────────────────────────────────────────────────────
safety_risk = round(
    f["crowd_pressure_index"].mean() * 0.40
    + f["bottleneck_risk_score"].mean() * 0.35
    + f["avg_queue_wait_time"].mean() * 0.25,
    2
)

overall_risk_score = round(f["risk_score"].mean(), 2)
critical_zone_count = int((f["risk_band"] == "Critical").sum())
monitor_zone_count = int((f["risk_band"] == "Monitor").sum())

med_rate = round(f["medical_incidents"].sum() / max(f["people_count"].sum(), 1) * 1000, 2)
cap_breach = round(f["capacity_breach"].mean() * 100, 2)
amb_resp = round(f["ambulance_response_time"].mean(), 2)
avg_queue = round(f["avg_queue_wait_time"].mean(), 2)
avg_pressure = round(f["crowd_pressure_index"].mean(), 2)
avg_bottleneck = round(f["bottleneck_risk_score"].mean(), 2)
avg_heat = round(f["heat_risk_index"].mean(), 2)

high_risk_zones = int(f[f["bottleneck_risk_score"] >= 70]["zone_id"].nunique())
delayed_med = int(f[f["ambulance_response_time"] >= 10]["zone_id"].nunique())

res_rate = round(
    inc_f[inc_f["status"] == "Resolved"].shape[0] / max(len(inc_f), 1) * 100,
    2,
) if not inc_f.empty and "status" in inc_f.columns else 0

unauthorized = int(f["unauthorized_entry_attempts"].sum())
counterfeit = int(f["counterfeit_ticket_cases"].sum())
pitch_inv = int(f["pitch_invasion_attempt"].sum())
fan_ej = int(f["fan_ejections"].sum())
req_staff = int(f["required_staff"].sum())
req_barr = int(f["required_barricades"].sum())
med_teams = int(f["deployed_medical_teams"].sum())
staff_ratio = round(f["staff_adequacy_ratio"].mean(), 2)

top_risk_text = risk_matrix.head(5).to_string(index=False)

summary_text = f"""
Selected Filters Summary:
Stadiums: {', '.join(map(str, sel_stadium))}
Phases: {', '.join(map(str, sel_phase))}
Years: {', '.join(map(str, sel_year))}
Zone Types: {', '.join(map(str, sel_zone))}
Match Categories: {', '.join(map(str, sel_cat))}

Dashboard KPIs:
Overall Risk Score: {overall_risk_score}
Safety Risk Score: {safety_risk}
Critical Records/Zones Count: {critical_zone_count}
Monitor Records/Zones Count: {monitor_zone_count}
Medical Incident Rate: {med_rate} per 1000 people
Capacity Breach Percentage: {cap_breach}%
Resolution Rate: {res_rate}%
Average Ambulance Response Time: {amb_resp} minutes
Average Queue Wait Time: {avg_queue} minutes
Average Crowd Pressure Index: {avg_pressure}
Average Bottleneck Risk Score: {avg_bottleneck}
Average Heat Risk Index: {avg_heat}
High Risk Zones: {high_risk_zones}
Delayed Medical Zones: {delayed_med}
Unauthorized Entries: {unauthorized}
Counterfeit Ticket Cases: {counterfeit}
Pitch Invasion Attempts: {pitch_inv}
Fan Ejections: {fan_ej}
Required Staff: {req_staff}
Required Barricades: {req_barr}
Medical Teams: {med_teams}
Staff Adequacy Ratio: {staff_ratio}

Top Risk Priority Matrix:
{top_risk_text}
"""


# ═══════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════
if page == "Overview":
    page_header(
        "🏏",
        "IPL Stadium Crowd Management & Public Safety Dashboard",
        "Executive overview — crowd movement, stadium risk, medical response and match safety performance"
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("Overall Risk Score", overall_risk_score, "crit", "Advanced combined score")
    with k2:
        kpi_card("Medical Incident Rate", med_rate, "warn", "Per 1K people")
    with k3:
        kpi_card("Capacity Breach", f"{cap_breach}%", "info")
    with k4:
        kpi_card("Resolution Rate", f"{res_rate}%", "ok")
    with k5:
        kpi_card("Ambulance Response", f"{amb_resp} min", "warn")

    sec_label("Executive AI Intelligence Panel")

    top1, top2 = st.columns([1, 2.4])

    with top1:
        generate_ai = st.button("🤖 Generate AI Insights", use_container_width=True)
        st.caption(f"Temperature: {ai_temperature} | Max Tokens: {ai_max_tokens}")

    with top2:
        st.markdown(f"""
        <div class="ai-card">
            <div class="insight-pill">AI Executive Summary</div>
            This panel uses filtered dashboard KPIs, advanced risk scores, anomaly detection, and the
            risk priority matrix to generate Cohere-powered operational recommendations.
        </div>
        """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
        <div class="ai-mini-card">
            <div class="ai-label">Overall Risk Score</div>
            <div class="ai-metric">{overall_risk_score}</div>
            <div class="ai-status-warning">● Weighted Risk Score</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="ai-mini-card">
            <div class="ai-label">Critical Risk Records</div>
            <div class="ai-metric">{critical_zone_count}</div>
            <div class="ai-status-critical">● Immediate Attention</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="ai-mini-card">
            <div class="ai-label">Medical Delay Zones</div>
            <div class="ai-metric">{delayed_med}</div>
            <div class="ai-status-critical">● Response Delays</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="ai-mini-card">
            <div class="ai-label">Anomaly Alerts</div>
            <div class="ai-metric">{len(anomaly_table)}</div>
            <div class="ai-status-warning">● Unusual Patterns</div>
        </div>
        """, unsafe_allow_html=True)

    p1, p2 = st.columns(2)

    with p1:
        st.markdown("##### 🚦 Capacity Breach Risk")
        st.progress(min(cap_breach / 100, 1.0))
        st.caption(f"{cap_breach}% zones near/exceeding threshold")

        st.markdown("##### 🌊 Crowd Pressure")
        st.progress(min(avg_pressure / 100, 1.0))
        st.caption(f"Average Pressure Index: {avg_pressure}")

    with p2:
        st.markdown("##### ⏳ Queue Congestion")
        st.progress(min(avg_queue / 30, 1.0))
        st.caption(f"Average Wait Time: {avg_queue} min")

        st.markdown("##### 🚑 Emergency Readiness")
        readiness_score = max(0, min(1, 1 - (amb_resp / 20)))
        st.progress(readiness_score)
        st.caption(f"Ambulance Response: {amb_resp} min")

    if generate_ai:
        with st.spinner("Generating Executive AI Insights..."):
            insights = generate_cohere_insights(
                summary_text,
                ai_temperature,
                ai_max_tokens,
            )

        tab1, tab2, tab3, tab4 = st.tabs([
            "📌 Key Insights",
            "⚠️ Risks",
            "✅ Recommendations",
            "📖 Detailed AI Output",
        ])

        with tab1:
            st.markdown(f"""
            <div class="ai-card">
            <h3>📌 Key Operational Insights</h3>
            <ul>
                <li>Overall risk score is <b>{overall_risk_score}</b>, showing the current safety pressure level.</li>
                <li><b>{critical_zone_count}</b> records are classified as critical risk.</li>
                <li>Medical delay zones and queue congestion require operational attention.</li>
                <li>High bottleneck scores indicate possible crowd-control pressure points.</li>
                <li>Anomaly detection found <b>{len(anomaly_table)}</b> unusual operating patterns.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.markdown(f"""
            <div class="ai-card">
            <h3>⚠️ Critical Risk Observations</h3>
            <ul>
                <li>🔴 High bottleneck risk zones should receive immediate control support.</li>
                <li>🔴 Delayed ambulance response can affect emergency readiness.</li>
                <li>🟠 Long queue wait times may increase congestion during entry/exit phase.</li>
                <li>🟠 Heat exposure increases medical vulnerability in open zones.</li>
                <li>🟠 Security activity indicates access-control pressure.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

        with tab3:
            st.markdown(f"""
            <div class="ai-card">
            <h3>✅ Priority Action Plan</h3>
            <ul>
                <li>Deploy extra staff in top-ranked risk zones.</li>
                <li>Open additional gates during queue spikes.</li>
                <li>Move medical teams closer to delayed-response zones.</li>
                <li>Add temporary barricades for high bottleneck zones.</li>
                <li>Use the Risk Matrix page before match start and during exit phase.</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

        with tab4:
            st.markdown(f"""
            <div class="ai-card">
            {insights.replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

    sec_label("AI Risk Priority Matrix — Top Risk Zones")
    st.dataframe(risk_matrix, use_container_width=True, height=360)

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "⬇️ Download Risk Priority Matrix CSV",
            data=dataframe_to_csv_bytes(risk_matrix),
            file_name="risk_priority_matrix.csv",
            mime="text/csv",
            use_container_width=True
        )

    with dl2:
        st.download_button(
            "⬇️ Download Filtered Dashboard Data CSV",
            data=dataframe_to_csv_bytes(f),
            file_name="filtered_dashboard_data.csv",
            mime="text/csv",
            use_container_width=True
        )

    sec_label("Anomaly Detection — Unusual Safety Patterns")
    st.dataframe(anomaly_table, use_container_width=True, height=300)

    st.write("")

    c1, c2 = st.columns([1.6, 1])

    with c1:
        tr = (
            f.groupby(["phase_cat", "zone_type"], as_index=False)["bottleneck_risk_score"]
            .mean()
            .sort_values("phase_cat")
        )
        tr["phase"] = tr["phase_cat"].astype(str)

        fig = px.line(
            tr,
            x="phase",
            y="bottleneck_risk_score",
            color="zone_type",
            markers=True,
            color_discrete_sequence=t["palette"],
            title="Operational Risk Trend by Phase",
        )

        st.plotly_chart(sfig(fig, t, 310), use_container_width=True)

    with c2:
        risk_band_count = f["risk_band"].value_counts().reset_index()
        risk_band_count.columns = ["Risk Band", "Count"]

        fig = px.pie(
            risk_band_count,
            names="Risk Band",
            values="Count",
            hole=0.55,
            color="Risk Band",
            color_discrete_map={
                "Critical": t["crit_col"],
                "Monitor": t["warn_col"],
                "Safe": t["ok_col"],
            },
            title="Risk Band Distribution",
        )

        st.plotly_chart(sfig(fig, t, 310), use_container_width=True)

    c3, c4 = st.columns([1.6, 1])

    with c3:
        mc = f["match_category"].value_counts().reset_index()
        mc.columns = ["match_category", "count"]

        fig = px.bar(
            mc,
            y="match_category",
            x="count",
            orientation="h",
            color="match_category",
            color_discrete_sequence=t["palette"],
            title="Match Distribution",
        )

        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 290), use_container_width=True)

    with c4:
        pres = f.groupby("zone_type", as_index=False)["risk_score"].mean()

        fig = px.bar(
            pres,
            x="zone_type",
            y="risk_score",
            color="zone_type",
            color_discrete_sequence=t["palette"],
            title="Average Advanced Risk Score by Zone Type",
        )

        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 290), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 2 — CROWD FLOW
# ═══════════════════════════════════════════════════════════
elif page == "Crowd Flow":
    page_header(
        "🌊",
        "Crowd Flow and Congestion Intelligence",
        "Zone congestion, crowd pressure trends, and high-risk areas across match phases"
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("High Risk Zones", high_risk_zones, "crit", "bottleneck ≥ 70")
    with k2:
        kpi_card("Avg Bottleneck Risk", avg_bottleneck, "warn")
    with k3:
        kpi_card("Avg Queue Wait", f"{avg_queue} min", "info")
    with k4:
        kpi_card("Avg Crowd Pressure", avg_pressure, "ok")

    c1, c2 = st.columns([1.5, 1])

    with c1:
        pc = (
            f.groupby(["phase_cat", "zone_type"], as_index=False)["people_count"]
            .sum()
            .sort_values("phase_cat")
        )
        pc["phase"] = pc["phase_cat"].astype(str)

        fig = px.line(
            pc,
            x="phase",
            y="people_count",
            color="zone_type",
            markers=True,
            color_discrete_sequence=t["palette"],
            title="People Count by Phase Order and Zone Type",
        )

        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    with c2:
        mat = (
            f.groupby(["phase", "zone_type"])["avg_queue_wait_time"]
            .mean()
            .round(2)
            .unstack("zone_type")
        )
        mat = mat.reindex([p for p in PHASE_ORDER if p in mat.index])

        sec_label("Avg Queue Wait Time Matrix")
        st.dataframe(
            mat.style.format("{:.2f}").background_gradient(cmap="Blues", axis=None),
            use_container_width=True,
            height=220,
        )

    c3, c4 = st.columns([1, 1.1])

    with c3:
        bn = f.groupby("zone_type", as_index=False)["bottleneck_risk_score"].mean().round(1)

        fig = px.bar(
            bn,
            y="zone_type",
            x="bottleneck_risk_score",
            orientation="h",
            color_discrete_sequence=[t["crit_col"]],
            title="Avg Bottleneck Risk Score by Zone Type",
            text="bottleneck_risk_score",
        )

        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    with c4:
        qs = f["queue_stress"].value_counts().reset_index()
        qs.columns = ["queue_stress", "count"]

        fig = px.pie(
            qs,
            names="queue_stress",
            values="count",
            hole=0.56,
            color_discrete_sequence=t["palette"],
            title="Queue Stress Category",
        )

        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    sec_label("Top Crowd Flow Risk Zones")
    crowd_flow_risk = risk_matrix[
        risk_matrix["Main Risk Reason"].isin([
            "High bottleneck risk",
            "Long queue wait time"
        ])
    ].head(10)

    st.dataframe(crowd_flow_risk, use_container_width=True, height=300)

    dual = (
        f.groupby("zone_name", as_index=False)
        .agg(
            crowd_pressure=("crowd_pressure_index", "mean"),
            bottleneck=("bottleneck_risk_score", "mean"),
            risk_score=("risk_score", "mean"),
        )
        .sort_values("risk_score", ascending=False)
        .head(15)
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Avg Crowd Pressure Index",
        y=dual["zone_name"],
        x=dual["crowd_pressure"],
        orientation="h",
        marker_color=t["accent"],
    ))

    fig.add_trace(go.Bar(
        name="Avg Bottleneck Risk Score",
        y=dual["zone_name"],
        x=dual["bottleneck"],
        orientation="h",
        marker_color=t["warn_col"],
    ))

    fig.update_layout(
        barmode="group",
        title="Crowd Pressure vs Bottleneck Risk by Zone",
        yaxis=dict(categoryorder="total ascending"),
    )

    st.plotly_chart(sfig(fig, t, 440), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 3 — MEDICAL & HEAT
# ═══════════════════════════════════════════════════════════
elif page == "Medical & Heat":
    page_header(
        "🏥",
        "Medical and Heat Intelligence",
        "Heat stress, medical incidents, ambulance response and emergency readiness"
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Medical Incident Rate", med_rate, "warn", "per 1K people")
    with k2:
        kpi_card("Avg Ambulance Response", f"{amb_resp} min", "crit")
    with k3:
        kpi_card("Avg Heat Risk Index", avg_heat, "warn")
    with k4:
        kpi_card("Delayed Medical Zones", delayed_med, "crit", "response ≥ 10 min")

    c1, c2 = st.columns([1.55, 1])

    with c1:
        heat = (
            f.groupby("phase_cat", as_index=False)["heat_risk_index"]
            .mean()
            .sort_values("phase_cat")
        )
        heat["phase"] = heat["phase_cat"].astype(str)

        fig = px.line(
            heat,
            x="phase",
            y="heat_risk_index",
            markers=True,
            color_discrete_sequence=[t["accent"]],
            title="Heat Risk Index by Phase",
        )

        st.plotly_chart(sfig(fig, t, 300), use_container_width=True)

    with c2:
        med_s = (
            f.groupby("stadium_name", as_index=False)["medical_incidents"]
            .sum()
            .sort_values("medical_incidents")
        )

        fig = px.bar(
            med_s,
            y="stadium_name",
            x="medical_incidents",
            orientation="h",
            color="stadium_name",
            color_discrete_sequence=t["palette"],
            title="Medical Incidents by Stadium",
        )

        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 300), use_container_width=True)

    sec_label("Medical & Heat Priority Zones")
    medical_risk = risk_matrix[
        risk_matrix["Main Risk Reason"].isin([
            "Delayed medical response",
            "High heat exposure"
        ])
    ].head(10)

    st.dataframe(medical_risk, use_container_width=True, height=300)

    c3, c4 = st.columns([1, 1.6])

    with c3:
        if not inc_f.empty and "severity" in inc_f.columns:
            sev = inc_f["severity"].value_counts().reset_index()
            sev.columns = ["severity", "count"]

            fig = px.pie(
                sev,
                names="severity",
                values="count",
                hole=0.55,
                color_discrete_sequence=t["palette"],
                title="Incident by Severity",
            )

            st.plotly_chart(sfig(fig, t, 285), use_container_width=True)
        else:
            st.info("No incident data for current filters.")

    with c4:
        hr_med = f.groupby("zone_name", as_index=False).agg(
            heat=("heat_risk_index", "mean"),
            med=("medical_incidents", "mean"),
            risk_score=("risk_score", "mean")
        )

        fig = px.scatter(
            hr_med,
            x="heat",
            y="med",
            size="risk_score",
            color="zone_name",
            color_discrete_sequence=t["palette"],
            title="Heat Risk vs Medical Incidents by Zone",
        )

        fig.update_traces(marker_size=11)
        st.plotly_chart(sfig(fig, t, 285), use_container_width=True)

    amb = (
        f.groupby(["phase_cat", "zone_type"], as_index=False)["ambulance_response_time"]
        .mean()
        .sort_values("phase_cat")
    )
    amb["phase"] = amb["phase_cat"].astype(str)

    fig = px.line(
        amb,
        x="phase",
        y="ambulance_response_time",
        color="zone_type",
        markers=True,
        color_discrete_sequence=t["palette"],
        title="Ambulance Response Time by Phase and Zone Type",
    )

    st.plotly_chart(sfig(fig, t, 310), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 4 — SECURITY
# ═══════════════════════════════════════════════════════════
elif page == "Security":
    page_header(
        "🔒",
        "Security & Unauthorized Activity Monitoring",
        "Unauthorized entries, security incidents, ticket fraud, fan ejections and stadium safety"
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        kpi_card("Unauthorized Entries", f"{unauthorized:,}", "crit")

    with k2:
        kpi_card("Counterfeit Cases", f"{counterfeit:,}", "warn")

    with k3:
        kpi_card("Pitch Invasions", f"{pitch_inv:,}", "crit")

    with k4:
        kpi_card("Fan Ejections", f"{fan_ej:,}", "warn")

    # ─────────────────────────────────────────────
    # CHARTS
    # ─────────────────────────────────────────────
    c1, c2 = st.columns([1.4, 1])

    with c1:
        ua = (
            f.groupby(["phase_cat", "zone_type"], as_index=False)["unauthorized_entry_attempts"]
            .mean()
            .sort_values("phase_cat")
        )

        ua["phase"] = ua["phase_cat"].astype(str)

        fig = px.line(
            ua,
            x="phase",
            y="unauthorized_entry_attempts",
            color="zone_type",
            markers=True,
            color_discrete_sequence=t["palette"],
            title="Unauthorized Entry by Phase and Zone Type",
        )

        st.plotly_chart(
            sfig(fig, t, 295),
            use_container_width=True
        )

    with c2:
        sec_s = (
            f.groupby("stadium_name", as_index=False)["security_incidents"]
            .sum()
            .sort_values("security_incidents")
        )

        fig = px.bar(
            sec_s,
            y="stadium_name",
            x="security_incidents",
            orientation="h",
            color_discrete_sequence=[t["accent"]],
            title="Security Incidents by Stadium",
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            sfig(fig, t, 295),
            use_container_width=True
        )

    c3, c4 = st.columns([1.2, 1])

    with c3:
        cs = f.groupby("zone_name", as_index=False).agg(
            pressure=("crowd_pressure_index", "mean"),
            security=("security_incidents", "sum"),
            people=("people_count", "sum"),
            risk_score=("risk_score", "mean"),
        )

        fig = px.scatter(
            cs,
            x="people",
            y="pressure",
            color="zone_name",
            size="risk_score",
            color_discrete_sequence=t["palette"],
            title="Crowd Pressure vs Security Risk",
        )

        fig.update_traces(marker_size=11)

        st.plotly_chart(
            sfig(fig, t, 295),
            use_container_width=True
        )

    with c4:
        sp = (
            f.groupby(["phase_cat", "zone_type"], as_index=False)["security_incidents"]
            .mean()
            .sort_values("phase_cat")
        )

        sp["phase"] = sp["phase_cat"].astype(str)

        fig = px.bar(
            sp,
            x="phase",
            y="security_incidents",
            color="zone_type",
            barmode="group",
            color_discrete_sequence=t["palette"],
            title="Security Incidents by Phase and Zone Type",
        )

        st.plotly_chart(
            sfig(fig, t, 295),
            use_container_width=True
        )


# ═══════════════════════════════════════════════════════════
# PAGE 5 — RESOURCE PLANNING
# ═══════════════════════════════════════════════════════════
elif page == "Resource Planning":
    page_header(
        "📦",
        "Resource Planning & Operational Readiness",
        "Staff requirements, barricade deployment, medical teams and readiness across phases"
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Staff Adequacy Ratio", staff_ratio, "ok")
    with k2:
        kpi_card("Total Required Staff", f"{req_staff:,}", "info")
    with k3:
        kpi_card("Total Barricades", f"{req_barr:,}", "warn")
    with k4:
        kpi_card("Total Medical Teams", f"{med_teams:,}", "ok")

    sec_label("Resource Action Plan Based on Risk Matrix")
    resource_plan = risk_matrix[
        [
            "Stadium", "Zone", "Zone Type", "Phase",
            "Risk Score", "Risk Band", "Main Risk Reason", "Recommended Action"
        ]
    ].head(12)

    st.dataframe(resource_plan, use_container_width=True, height=320)

    c1, c2 = st.columns([1.55, 1])

    with c1:
        rd = (
            f.groupby(["phase_cat", "zone_type"], as_index=False)["staff_adequacy_ratio"]
            .mean()
            .sort_values("phase_cat")
        )
        rd["phase"] = rd["phase_cat"].astype(str)

        fig = px.line(
            rd,
            x="phase",
            y="staff_adequacy_ratio",
            color="zone_type",
            markers=True,
            color_discrete_sequence=t["palette"],
            title="Operational Readiness Across Match Phases",
        )

        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    with c2:
        md = f.groupby("zone_type", as_index=False).agg(
            people=("people_count", "sum"),
            med_t=("deployed_medical_teams", "sum"),
        )

        fig = px.scatter(
            md,
            x="people",
            y="med_t",
            color="zone_type",
            size="med_t",
            color_discrete_sequence=t["palette"],
            title="Medical Team Deployment vs Crowd Size",
        )

        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    c3, c4 = st.columns([1, 1])

    with c3:
        res = f.groupby("zone_type", as_index=False).agg(
            staff=("required_staff", "sum"),
            med=("deployed_medical_teams", "sum"),
        )

        fig = go.Figure()

        fig.add_bar(
            y=res["zone_type"],
            x=res["staff"],
            name="Required Staff",
            orientation="h",
            marker_color=t["palette"][0],
        )

        fig.add_bar(
            y=res["zone_type"],
            x=res["med"],
            name="Medical Teams",
            orientation="h",
            marker_color=t["palette"][1],
        )

        fig.update_layout(
            barmode="group",
            title="Required Staff vs Medical Deployment",
        )

        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    with c4:
        br = (
            f.groupby("zone_type", as_index=False)["required_barricades"]
            .sum()
            .sort_values("required_barricades")
        )

        fig = px.bar(
            br,
            y="zone_type",
            x="required_barricades",
            orientation="h",
            color_discrete_sequence=[t["palette"][0]],
            title="Barricade Requirements by Zone",
        )

        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    mat2 = f.pivot_table(
        values="staff_adequacy_ratio",
        index="stadium_name",
        columns="phase",
        aggfunc="mean",
    ).round(2)

    ord_cols = [p for p in PHASE_ORDER if p in mat2.columns]
    mat2 = mat2[ord_cols]

    sec_label("Staff Adequacy Ratio — Stadium × Phase")
    st.dataframe(
        mat2.style.format("{:.2f}").background_gradient(cmap="Greens", axis=None),
        use_container_width=True,
    )


# ═══════════════════════════════════════════════════════════
# PAGE 6 — RISK MATRIX
# ═══════════════════════════════════════════════════════════
elif page == "Risk Matrix":

    page_header(
        "🚨",
        "AI Risk Priority Matrix & Anomaly Intelligence",
        "Advanced decision-support page for identifying critical zones, reasons, and recommended actions"
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        kpi_card("Overall Risk Score", overall_risk_score, "crit")

    with k2:
        kpi_card("Critical Records", critical_zone_count, "crit")

    with k3:
        kpi_card("Monitor Records", monitor_zone_count, "warn")

    with k4:
        kpi_card("Anomaly Alerts", len(anomaly_table), "info")

    # ─────────────────────────────────────────────
    # RISK MATRIX TABLE
    # ─────────────────────────────────────────────
    sec_label("Top 15 Risk Priority Matrix")

    st.dataframe(
        risk_matrix,
        use_container_width=True,
        height=420
    )

    st.download_button(
        "⬇️ Download Full Risk Priority Matrix",
        data=dataframe_to_csv_bytes(risk_matrix),
        file_name="risk_priority_matrix.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ─────────────────────────────────────────────
    # CHARTS
    # ─────────────────────────────────────────────
    sec_label("Risk Score by Stadium and Zone Type")

    c1, c2 = st.columns([1.3, 1])

    with c1:

        stadium_risk = (
            f.groupby(["stadium_name", "zone_type"], as_index=False)["risk_score"]
            .mean()
            .sort_values("risk_score", ascending=False)
        )

        fig = px.bar(
            stadium_risk,
            x="risk_score",
            y="stadium_name",
            color="zone_type",
            orientation="h",
            color_discrete_sequence=t["palette"],
            title="Average Risk Score by Stadium and Zone Type",
        )

        st.plotly_chart(
            sfig(fig, t, 360),
            use_container_width=True
        )

    with c2:

        risk_dist = f["risk_band"].value_counts().reset_index()

        risk_dist.columns = ["Risk Band", "Count"]

        fig = px.pie(
            risk_dist,
            names="Risk Band",
            values="Count",
            hole=0.55,
            color="Risk Band",
            color_discrete_map={
                "Critical": t["crit_col"],
                "Monitor": t["warn_col"],
                "Safe": t["ok_col"],
            },
            title="Risk Band Distribution",
        )

        st.plotly_chart(
            sfig(fig, t, 360),
            use_container_width=True
        )

    # ─────────────────────────────────────────────
    # ANOMALY TABLE
    # ─────────────────────────────────────────────
    sec_label("Anomaly Detection Table")

    st.dataframe(
        anomaly_table,
        use_container_width=True,
        height=360
    )

    st.download_button(
        "⬇️ Download Anomaly Detection CSV",
        data=dataframe_to_csv_bytes(anomaly_table),
        file_name="anomaly_detection.csv",
        mime="text/csv",
        use_container_width=True,
    )
   # ═══════════════════════════════════════════════════════════
# PAGE 7 — ASK AI
# ═══════════════════════════════════════════════════════════
elif page == "Ask AI":

    page_header(
        "💬",
        "Ask AI — Dashboard Q&A Assistant",
        "Ask questions about crowd risk, medical readiness, security, staffing, and priority zones"
    )

    if "ai_question" not in st.session_state:
        st.session_state.ai_question = ""

    if "ai_answer" not in st.session_state:
        st.session_state.ai_answer = ""

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        kpi_card("Overall Risk Score", overall_risk_score, "crit")

    with k2:
        kpi_card("Critical Records", critical_zone_count, "crit")

    with k3:
        kpi_card("Anomaly Alerts", len(anomaly_table), "warn")

    with k4:
        kpi_card("Avg Queue Wait", f"{avg_queue} min", "info")

    sec_label("Suggested Questions")

    q1, q2, q3 = st.columns(3)

    with q1:
        if st.button("Which zones need urgent attention?", use_container_width=True):
            st.session_state.ai_question = "Which zones need urgent attention and why?"
            st.session_state.ai_answer = ""

    with q2:
        if st.button("What should operations team do first?", use_container_width=True):
            st.session_state.ai_question = "What should the stadium operations team do first based on current dashboard?"
            st.session_state.ai_answer = ""

    with q3:
        if st.button("Explain this dashboard simply", use_container_width=True):
            st.session_state.ai_question = "Explain this dashboard output in simple presentation-friendly language."
            st.session_state.ai_answer = ""

    q4, q5, q6 = st.columns(3)

    with q4:
        if st.button("Why is medical risk important?", use_container_width=True):
            st.session_state.ai_question = "Why is medical risk important in the current selected filters?"
            st.session_state.ai_answer = ""

    with q5:
        if st.button("Which phase is most risky?", use_container_width=True):
            st.session_state.ai_question = "Which match phase is most risky and what action should be taken?"
            st.session_state.ai_answer = ""

    with q6:
        if st.button("Give 5 interview talking points", use_container_width=True):
            st.session_state.ai_question = "Give me 5 interview talking points for explaining this project."
            st.session_state.ai_answer = ""

    user_question = st.text_area(
        "Ask your own dashboard question",
        value=st.session_state.ai_question,
        placeholder="Example: Which stadium has the highest crowd risk and why?",
        height=120,
        key="qa_text_area"
    )

    ask_btn = st.button("💬 Ask AI", use_container_width=True)

    if ask_btn:

        if not user_question.strip():
            st.warning("Please type or select a question first.")

        else:
            qa_context = f"""
Dashboard KPIs:
Overall Risk Score: {overall_risk_score}
Safety Risk Score: {safety_risk}
Critical Records: {critical_zone_count}
Monitor Records: {monitor_zone_count}
Medical Incident Rate: {med_rate}
Capacity Breach: {cap_breach}%
Resolution Rate: {res_rate}%
Ambulance Response: {amb_resp} minutes
Average Queue Wait: {avg_queue} minutes
Average Crowd Pressure: {avg_pressure}
Average Bottleneck Risk: {avg_bottleneck}
Average Heat Risk: {avg_heat}
High Risk Zones: {high_risk_zones}
Delayed Medical Zones: {delayed_med}
Unauthorized Entries: {unauthorized}
Counterfeit Ticket Cases: {counterfeit}
Pitch Invasion Attempts: {pitch_inv}
Fan Ejections: {fan_ej}
Required Staff: {req_staff}
Required Barricades: {req_barr}
Medical Teams: {med_teams}
Staff Adequacy Ratio: {staff_ratio}

Top Risk Matrix:
{risk_matrix.head(10).to_string(index=False)}

Anomaly Table:
{anomaly_table.head(10).to_string(index=False)}
"""

            with st.spinner("AI is analyzing your dashboard question..."):
                st.session_state.ai_answer = ask_ai_question(
                    user_question,
                    qa_context,
                    temperature_value=0.3,
                    token_value=700
                )

    if st.session_state.ai_answer:
        st.markdown(f"""
        <div class="ai-card">
        <h3>💬 AI Answer</h3>
        {st.session_state.ai_answer.replace(chr(10), "<br>")}
        </div>
        """, unsafe_allow_html=True)

    sec_label("Q&A Context Tables")

    c1, c2 = st.columns(2)

    with c1:
        st.caption("Top risk records used by AI")
        st.dataframe(risk_matrix.head(8), use_container_width=True, height=260)

    with c2:
        st.caption("Top anomaly records used by AI")
        st.dataframe(anomaly_table.head(8), use_container_width=True, height=260)
# ─────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    f'<p style="text-align:center;font-size:11px;color:{t["text2"]};padding:4px 0;">'
    "🏏 IPL Crowd Safety Management Dashboard &nbsp;|&nbsp; Power BI + Streamlit + Cohere AI &nbsp;|&nbsp; Advanced Risk Matrix Enabled"
    "</p>",
    unsafe_allow_html=True,
)
