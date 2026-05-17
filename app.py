"""
IPL Crowd Safety Management Dashboard — Streamlit (Light Theme)
Folder structure:
  IPL_CROUD_APP/
  ├── app.py
  └── data/
      ├── dim_gate.xlsx
      ├── dim_stadium.xlsx
      ├── dim_zone.xlsx
      ├── fact_events.xlsx
      ├── fact_incidents.xlsx
      └── fact_operations_main.xlsx
Run:  streamlit run app.py
Install: pip install streamlit pandas numpy plotly openpyxl cohere
Secrets: add COHERE_API_KEY in .streamlit/secrets.toml or Streamlit Cloud Secrets
"""

import os
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
# LIGHT THEMES — one accent colour per page
# legend_rgba uses rgba() format — Plotly does NOT accept 8-digit hex
# ─────────────────────────────────────────────────────────
THEMES = {
    "Overview": {
        "bg":          "#F6F4FF",
        "sidebar":     "#EDE9FE",
        "card":        "#FFFFFF",
        "accent":      "#7C3AED",
        "accent_lt":   "#EDE9FE",
        "accent2":     "#5B21B6",
        "text":        "#1E1B4B",
        "text2":       "#6B7280",
        "border":      "#C4B5FD",
        "plot_bg":     "#FFFFFF",
        "paper_bg":    "#F6F4FF",
        "grid":        "#F0EBFF",
        "legend_rgba": "rgba(246,244,255,0.92)",
        "palette": ["#7C3AED","#A78BFA","#F59E0B","#10B981","#EF4444","#3B82F6"],
        "crit_col":  "#EF4444",
        "warn_col":  "#F59E0B",
        "ok_col":    "#10B981",
        "info_col":  "#7C3AED",
    },
    "Crowd Flow": {
        "bg":          "#EFF6FF",
        "sidebar":     "#DBEAFE",
        "card":        "#FFFFFF",
        "accent":      "#1D4ED8",
        "accent_lt":   "#DBEAFE",
        "accent2":     "#1E40AF",
        "text":        "#1E2A4A",
        "text2":       "#6B7280",
        "border":      "#93C5FD",
        "plot_bg":     "#FFFFFF",
        "paper_bg":    "#EFF6FF",
        "grid":        "#E8F2FF",
        "legend_rgba": "rgba(239,246,255,0.92)",
        "palette": ["#1D4ED8","#60A5FA","#F59E0B","#10B981","#8B5CF6","#EF4444"],
        "crit_col":  "#EF4444",
        "warn_col":  "#F59E0B",
        "ok_col":    "#10B981",
        "info_col":  "#1D4ED8",
    },
    "Medical & Heat": {
        "bg":          "#FFF1F2",
        "sidebar":     "#FFE4E6",
        "card":        "#FFFFFF",
        "accent":      "#E11D48",
        "accent_lt":   "#FFE4E6",
        "accent2":     "#BE123C",
        "text":        "#3B0A14",
        "text2":       "#6B7280",
        "border":      "#FDA4AF",
        "plot_bg":     "#FFFFFF",
        "paper_bg":    "#FFF1F2",
        "grid":        "#FFF0F1",
        "legend_rgba": "rgba(255,241,242,0.92)",
        "palette": ["#E11D48","#FB7185","#F97316","#8B5CF6","#3B82F6","#10B981"],
        "crit_col":  "#E11D48",
        "warn_col":  "#F97316",
        "ok_col":    "#10B981",
        "info_col":  "#8B5CF6",
    },
    "Security": {
        "bg":          "#FFFBEB",
        "sidebar":     "#FEF3C7",
        "card":        "#FFFFFF",
        "accent":      "#D97706",
        "accent_lt":   "#FEF3C7",
        "accent2":     "#B45309",
        "text":        "#1C1007",
        "text2":       "#6B7280",
        "border":      "#FCD34D",
        "plot_bg":     "#FFFFFF",
        "paper_bg":    "#FFFBEB",
        "grid":        "#FFFCF0",
        "legend_rgba": "rgba(255,251,235,0.92)",
        "palette": ["#D97706","#F59E0B","#3B82F6","#10B981","#8B5CF6","#EF4444"],
        "crit_col":  "#EF4444",
        "warn_col":  "#D97706",
        "ok_col":    "#10B981",
        "info_col":  "#3B82F6",
    },
    "Resource Planning": {
        "bg":          "#F0FDFA",
        "sidebar":     "#CCFBF1",
        "card":        "#FFFFFF",
        "accent":      "#0D9488",
        "accent_lt":   "#CCFBF1",
        "accent2":     "#0F766E",
        "text":        "#042F2E",
        "text2":       "#6B7280",
        "border":      "#5EEAD4",
        "plot_bg":     "#FFFFFF",
        "paper_bg":    "#F0FDFA",
        "grid":        "#EDFDF8",
        "legend_rgba": "rgba(240,253,250,0.92)",
        "palette": ["#0D9488","#34D399","#3B82F6","#8B5CF6","#F59E0B","#EF4444"],
        "crit_col":  "#EF4444",
        "warn_col":  "#F59E0B",
        "ok_col":    "#0D9488",
        "info_col":  "#3B82F6",
    },
}

PAGES = [
    ("🏠", "Overview"),
    ("🌊", "Crowd Flow"),
    ("🏥", "Medical & Heat"),
    ("🔒", "Security"),
    ("📦", "Resource Planning"),
]

# ─────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────
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
            st.error(
                f"❌ **Missing file:** `data/{fname}`  "
                "— make sure it is inside the `data/` folder next to `app.py`."
            )
            st.stop()
        return pd.read_excel(path)

    ops     = _read("fact_operations_main.xlsx")
    inc     = _read("fact_incidents.xlsx")
    evt     = _read("fact_events.xlsx")
    zone    = _read("dim_zone.xlsx")
    stadium = _read("dim_stadium.xlsx")

    for df in [ops, inc, evt, zone, stadium]:
        df.columns = df.columns.str.strip().str.lower()

    # Dims → ops
    ops = ops.merge(zone[["zone_id", "zone_name", "zone_type"]], on="zone_id", how="left")
    zone_s = zone[["zone_id", "stadium_id"]].merge(
        stadium[["stadium_id", "stadium_name"]], on="stadium_id")
    ops = ops.merge(zone_s[["zone_id", "stadium_name"]], on="zone_id", how="left")

    # Event fields
    evt_cols = ["event_id", "season_year", "is_final_match", "total_attendance"]
    ops = ops.merge(evt[evt_cols], on="event_id", how="left")

    # Derived columns
    ops["heat_risk_index"]      = ops["temperature_celsius"] * 0.7 + ops["humidity_percent"] * 0.3
    ops["occupancy_pct"]        = ops["occupancy_rate"] * 100
    ops["capacity_breach"]      = (ops["occupancy_rate"] >= 0.55).astype(int)
    ops["staff_adequacy_ratio"] = np.where(
        ops["people_count"] > 0,
        ops["required_staff"] / ops["people_count"] * 1000, 0)

    ops["occupancy_risk_band"] = pd.cut(
        ops["occupancy_rate"],
        bins=[-np.inf, 0.45, 0.60, 0.70, np.inf],
        labels=["Low", "Moderate", "High", "Critical"])

    ops["queue_stress"] = pd.cut(
        ops["avg_queue_wait_time"],
        bins=[-np.inf, 10, 20, 25, np.inf],
        labels=["Acceptable under 10 min", "Moderate 10-20 min",
                "High 20-35 min", "Extreme 25+ min"])

    # Match category
    q75 = evt["total_attendance"].quantile(0.75)
    q40 = evt["total_attendance"].quantile(0.40)
    evt["match_category"] = np.select(
        [evt["is_final_match"] == 1,
         evt["total_attendance"] >= q75,
         evt["total_attendance"] >= q40],
        ["Final Match", "High Attendance Match", "Moderate Attendace Match"],
        default="Regular Match")
    ops = ops.merge(evt[["event_id", "match_category"]], on="event_id", how="left")
    ops["match_category"] = ops["match_category"].fillna("Regular Match")

    # Incidents enrichment
    inc = inc.merge(evt[["event_id", "season_year"]], on="event_id", how="left")
    inc = inc.merge(zone_s[["zone_id", "stadium_name"]], on="zone_id", how="left")

    return ops, inc


try:
    ops, inc = load_all()
except Exception as e:
    st.error(f"❌ Data load error: {e}")
    st.stop()

# ─────────────────────────────────────────────────────────
# CSS INJECTION — light theme, per page
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

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background-color: {t['sidebar']};
    border-right: 2px solid {t['border']};
    min-width: 228px !important;
    max-width: 228px !important;
}}
section[data-testid="stSidebar"] * {{
    color: {t['text']} !important;
}}
section[data-testid="stSidebar"] label {{
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: {t['text2']} !important;
}}

/* ── Nav buttons in sidebar ── */
section[data-testid="stSidebar"] .stButton > button {{
    width: 100% !important;
    text-align: left !important;
    background: {t['card']} !important;
    border: 1px solid {t['border']} !important;
    border-radius: 10px !important;
    padding: 9px 14px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    color: {t['text']} !important;
    margin-bottom: 4px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    transition: all 0.15s !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: {t['accent_lt']} !important;
    border-color: {t['accent']} !important;
    color: {t['accent2']} !important;
}}

/* ── Page header ── */
.dash-header {{
    background: linear-gradient(120deg, {t['card']} 60%, {t['accent_lt']});
    border: 1px solid {t['border']};
    border-left: 6px solid {t['accent']};
    border-radius: 16px;
    padding: 18px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    display: flex;
    align-items: center;
    gap: 16px;
}}
.dash-title {{
    font-family: 'Sora', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: {t['text']};
    margin: 0;
    line-height: 1.25;
}}
.dash-sub {{
    font-size: 12.5px;
    color: {t['text2']};
    margin: 5px 0 0 0;
    font-weight: 500;
}}

/* ── KPI cards ── */
.kpi-card {{
    background: {t['card']};
    border: 1px solid {t['border']};
    border-radius: 14px;
    padding: 16px 18px 14px;
    min-height: 96px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.055);
    position: relative;
    overflow: hidden;
}}
.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 4px;
    border-radius: 14px 14px 0 0;
}}
.kpi-info::before  {{ background: {t['info_col']}; }}
.kpi-warn::before  {{ background: {t['warn_col']}; }}
.kpi-crit::before  {{ background: {t['crit_col']}; }}
.kpi-ok::before    {{ background: {t['ok_col']}; }}

.kpi-label {{
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    color: {t['text2']};
    margin-bottom: 7px;
    margin-top: 2px;
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
    margin-top: 5px;
    font-weight: 500;
}}

/* ── Charts ── */
div[data-testid="stPlotlyChart"] > div {{
    border-radius: 14px !important;
    border: 1px solid {t['border']} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.045) !important;
}}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    border: 1px solid {t['border']};
    overflow: hidden;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
}}

/* ── Section label ── */
.sec-lbl {{
    font-family: 'Sora', sans-serif;
    font-size: 12px;
    font-weight: 700;
    color: {t['accent2']};
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin: 10px 0 5px 0;
    padding-bottom: 4px;
    border-bottom: 2px solid {t['accent_lt']};
}}

/* scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {t['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {t['border']}; border-radius: 3px; }}

hr {{ border-color: {t['border']} !important; opacity: 0.6; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────
def kpi_card(label, value, style="info", sub=""):
    """Render a KPI card inside whatever st.column it is called from."""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
<div class="kpi-card kpi-{style}">
  <div class="kpi-label">{label}</div>
  <div class="kpi-val">{value}</div>
  {sub_html}
</div>""", unsafe_allow_html=True)


def page_header(icon, title, subtitle):
    st.markdown(f"""
<div class="dash-header">
  <span style="font-size:34px;line-height:1">{icon}</span>
  <div>
    <div class="dash-title">{title}</div>
    <div class="dash-sub">{subtitle}</div>
  </div>
</div>""", unsafe_allow_html=True)


def sec_label(text):
    st.markdown(f'<div class="sec-lbl">{text}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# COHERE AI INSIGHTS HELPERS
# ─────────────────────────────────────────────────────────
def get_cohere_key():
    """Read Cohere API key from Streamlit secrets."""
    try:
        return st.secrets.get("COHERE_API_KEY", "")
    except Exception:
        return ""


def generate_cohere_insights(summary_text, temperature_value=0.4, token_value=700):
    """Generate dashboard insights and recommendations using Cohere."""
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

Based on the selected dashboard metrics below, generate:
1. Key insights
2. Risk observations
3. Practical recommendations
4. Presentation-friendly explanation

Rules:
- Use simple professional language.
- Keep it useful for dashboard presentation.
- Focus on crowd safety, bottlenecks, medical readiness, security, and resource planning.
- Give clear actions for stadium operations teams.

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


def sfig(fig, t, h=320):
    """Apply light theme styling to a plotly figure. Uses rgba() for legend bgcolor."""
    fig.update_layout(
        height=h,
        paper_bgcolor=t["paper_bg"],
        plot_bgcolor=t["plot_bg"],
        font=dict(color=t["text"], family="Plus Jakarta Sans", size=12),
        title_font=dict(color=t["text"], size=14, family="Sora"),
        title_x=0.03,
        legend=dict(
            bgcolor=t["legend_rgba"],        # rgba() — never 8-digit hex
            bordercolor=t["border"],
            borderwidth=1,
            font=dict(color=t["text2"], size=11),
        ),
        margin=dict(l=30, r=20, t=50, b=30),
        colorway=t["palette"],
    )
    fig.update_xaxes(
        gridcolor=t["grid"], zerolinecolor=t["grid"],
        linecolor=t["border"],
        tickfont=dict(color=t["text2"]),
        title_font=dict(color=t["text2"]),
    )
    fig.update_yaxes(
        gridcolor=t["grid"], zerolinecolor=t["grid"],
        linecolor=t["border"],
        tickfont=dict(color=t["text2"]),
        title_font=dict(color=t["text2"]),
    )
    return fig


# ─────────────────────────────────────────────────────────
# SIDEBAR  — navigation + global filters
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
</div>""", unsafe_allow_html=True)

    for icon, name in PAGES:
        if st.button(f"{icon}  {name}", key=f"nav_{name}"):
            st.session_state.active_page = name
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:10px;font-weight:700;letter-spacing:0.8px;'
        'margin:0 0 8px 0;opacity:0.6;">FILTERS</p>',
        unsafe_allow_html=True)

    all_stadiums = sorted(ops["stadium_name"].dropna().unique())
    sel_stadium  = st.multiselect("Stadium", all_stadiums, default=all_stadiums, key="f_stad")

    sel_phase = st.multiselect("Phase", PHASE_ORDER, default=PHASE_ORDER, key="f_ph")

    all_years = sorted(ops["season_year"].dropna().astype(int).unique())
    sel_year  = st.multiselect("Year", all_years, default=all_years, key="f_yr")

    all_zones = sorted(ops["zone_type"].dropna().unique())
    sel_zone  = st.multiselect("Zone Type", all_zones, default=all_zones, key="f_zt")

    all_cats  = sorted(ops["match_category"].dropna().unique())
    sel_cat   = st.multiselect("Match Category", all_cats, default=all_cats, key="f_mc")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:10px;font-weight:700;letter-spacing:0.8px;'
        'margin:0 0 8px 0;opacity:0.6;">COHERE AI SETTINGS</p>',
        unsafe_allow_html=True)

    ai_temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.4,
        step=0.1,
        help="Lower values give professional and consistent insights. Higher values make responses more creative."
    )

    ai_max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=2000,
        value=700,
        step=100,
        help="Controls the maximum length of the AI-generated insights."
    )

# ─────────────────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────────────────
f = ops[
    ops["stadium_name"].isin(sel_stadium) &
    ops["phase"].isin(sel_phase) &
    ops["season_year"].astype(int).isin(sel_year) &
    ops["zone_type"].isin(sel_zone) &
    ops["match_category"].isin(sel_cat)
].copy()

if f.empty:
    t = THEMES[st.session_state.active_page]
    inject_css(t)
    st.warning("⚠️ No data for the selected filters. Please widen your selection.")
    st.stop()

f["phase_cat"] = pd.Categorical(f["phase"], categories=PHASE_ORDER, ordered=True)

inc_f = inc[
    inc["stadium_name"].isin(sel_stadium) &
    inc["season_year"].astype(int).isin(sel_year)
].copy() if "stadium_name" in inc.columns and "season_year" in inc.columns else inc.copy()

# ─────────────────────────────────────────────────────────
# KPI CALCULATIONS
# ─────────────────────────────────────────────────────────
safety_risk    = round(f["crowd_pressure_index"].mean() * 0.40
                       + f["bottleneck_risk_score"].mean() * 0.35
                       + f["avg_queue_wait_time"].mean() * 0.25, 2)
med_rate       = round(f["medical_incidents"].sum() / max(f["people_count"].sum(), 1) * 1000, 2)
cap_breach     = round(f["capacity_breach"].mean() * 100, 2)
amb_resp       = round(f["ambulance_response_time"].mean(), 2)
avg_queue      = round(f["avg_queue_wait_time"].mean(), 2)
avg_pressure   = round(f["crowd_pressure_index"].mean(), 2)
avg_bottleneck = round(f["bottleneck_risk_score"].mean(), 2)
avg_heat       = round(f["heat_risk_index"].mean(), 2)

high_risk_zones = int(f[f["bottleneck_risk_score"] >= 70]["zone_id"].nunique()) \
    if "zone_id" in f.columns else 0
delayed_med     = int(f[f["ambulance_response_time"] >= 10]["zone_id"].nunique()) \
    if "zone_id" in f.columns else 0

res_rate    = round(
    inc_f[inc_f["status"] == "Resolved"].shape[0] / max(len(inc_f), 1) * 100, 2
) if not inc_f.empty and "status" in inc_f.columns else 0

unauthorized = int(f["unauthorized_entry_attempts"].sum())
counterfeit  = int(f["counterfeit_ticket_cases"].sum())
pitch_inv    = int(f["pitch_invasion_attempt"].sum())
fan_ej       = int(f["fan_ejections"].sum())
req_staff    = int(f["required_staff"].sum())
req_barr     = int(f["required_barricades"].sum())
med_teams    = int(f["deployed_medical_teams"].sum())
staff_ratio  = round(f["staff_adequacy_ratio"].mean(), 2)

# ─────────────────────────────────────────────────────────
# COHERE AI SUMMARY TEXT
# ─────────────────────────────────────────────────────────
summary_text = f"""
Selected Filters Summary:
Stadiums: {', '.join(map(str, sel_stadium))}
Phases: {', '.join(map(str, sel_phase))}
Years: {', '.join(map(str, sel_year))}
Zone Types: {', '.join(map(str, sel_zone))}
Match Categories: {', '.join(map(str, sel_cat))}

Dashboard KPIs:
Safety Risk Score: {safety_risk}
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
"""

# ─────────────────────────────────────────────────────────
# RENDER ACTIVE PAGE
# ─────────────────────────────────────────────────────────
page = st.session_state.active_page
t    = THEMES[page]
inject_css(t)


# ═══════════════════════════════════════════════════════════
# PAGE 1  ·  OVERVIEW
# ═══════════════════════════════════════════════════════════
if page == "Overview":
    page_header("🏏",
                "IPL Stadium Crowd Management & Public Safety Dashboard",
                "Executive overview — crowd movement, stadium risk, medical response and match safety performance")

    # KPI row — individual columns, no HTML flex
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: kpi_card("Safety Risk Score",     safety_risk,        "crit")
    with k2: kpi_card("Medical Incident Rate", med_rate,           "warn")
    with k3: kpi_card("Capacity Breach %",     f"{cap_breach}%",   "info")
    with k4: kpi_card("Resolution Rate",       f"{res_rate}%",     "ok")
    with k5: kpi_card("Ambulance Response",    f"{amb_resp} min",  "warn")

    st.write("")
    sec_label("AI Insights & Recommendations")
    ai_col1, ai_col2 = st.columns([1, 3])
    with ai_col1:
        generate_ai = st.button("🤖 Generate AI Insights", use_container_width=True)
        st.caption(f"Temperature: {ai_temperature} | Max Tokens: {ai_max_tokens}")
    with ai_col2:
        st.info("Click the button to generate Cohere-powered insights based on the current dashboard filters and KPIs.")

    if generate_ai:
        with st.spinner("Generating AI insights with Cohere..."):
            insights = generate_cohere_insights(summary_text, ai_temperature, ai_max_tokens)
        st.markdown(
            f'<div style="background:{t["card"]};border:1px solid {t["border"]};'
            f'border-left:5px solid {t["accent"]};border-radius:14px;padding:16px 18px;'
            f'box-shadow:0 2px 8px rgba(0,0,0,0.045);color:{t["text"]};">'
            f'{insights.replace(chr(10), "<br>")}'
            '</div>',
            unsafe_allow_html=True
        )

    st.write("")
    c1, c2 = st.columns([1.6, 1])

    with c1:
        tr = (f.groupby(["phase_cat", "zone_type"], as_index=False)["bottleneck_risk_score"]
              .mean().sort_values("phase_cat"))
        tr["phase"] = tr["phase_cat"].astype(str)
        fig = px.line(tr, x="phase", y="bottleneck_risk_score", color="zone_type",
                      markers=True, color_discrete_sequence=t["palette"],
                      title="Operational Risk Trend by Phase",
                      labels={"phase": "Phase",
                               "bottleneck_risk_score": "Bottleneck Risk Score",
                               "zone_type": "Zone Type"})
        st.plotly_chart(sfig(fig, t, 310), use_container_width=True)

    with c2:
        occ = f.groupby(["stadium_name", "phase"], as_index=False)["occupancy_pct"].mean()
        fig = px.bar(occ, y="stadium_name", x="occupancy_pct", color="phase",
                     orientation="h", color_discrete_sequence=t["palette"],
                     title="Occupancy Rate by Stadium and Phase",
                     labels={"occupancy_pct": "Occupancy %", "stadium_name": ""})
        st.plotly_chart(sfig(fig, t, 310), use_container_width=True)

    c3, c4 = st.columns([1.6, 1])

    with c3:
        mc = f["match_category"].value_counts().reset_index()
        mc.columns = ["match_category", "count"]
        fig = px.bar(mc, y="match_category", x="count", orientation="h",
                     color="match_category", color_discrete_sequence=t["palette"],
                     title="Match Distribution",
                     labels={"count": "", "match_category": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 290), use_container_width=True)

    with c4:
        pres = f.groupby("zone_type", as_index=False)["crowd_pressure_index"].mean()
        fig = px.bar(pres, x="zone_type", y="crowd_pressure_index",
                     color="zone_type", color_discrete_sequence=t["palette"],
                     title="Average Crowd Pressure Index by Zone Type",
                     labels={"crowd_pressure_index": "Avg Pressure", "zone_type": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 290), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 2  ·  CROWD FLOW & CONGESTION
# ═══════════════════════════════════════════════════════════
elif page == "Crowd Flow":
    page_header("🌊",
                "Crowd Flow and Congestion Intelligence",
                "Zone congestion, crowd pressure trends, and high-risk areas across match phases")

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("High Risk Zones",     high_risk_zones,     "crit", "bottleneck ≥ 70")
    with k2: kpi_card("Avg Bottleneck Risk", avg_bottleneck,      "warn")
    with k3: kpi_card("Avg Queue Wait",      f"{avg_queue} min",  "info")
    with k4: kpi_card("Avg Crowd Pressure",  avg_pressure,        "ok")

    c1, c2 = st.columns([1.5, 1])

    with c1:
        pc = (f.groupby(["phase_cat", "zone_type"], as_index=False)["people_count"]
              .sum().sort_values("phase_cat"))
        pc["phase"] = pc["phase_cat"].astype(str)
        fig = px.line(pc, x="phase", y="people_count", color="zone_type",
                      markers=True, color_discrete_sequence=t["palette"],
                      title="People Count by Phase Order and Zone Type",
                      labels={"people_count": "People Count",
                               "zone_type": "Zone Type", "phase": "Phase"})
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    with c2:
        mat = (f.groupby(["phase", "zone_type"])["avg_queue_wait_time"]
               .mean().round(2).unstack("zone_type"))
        mat = mat.reindex([p for p in PHASE_ORDER if p in mat.index])
        sec_label("Avg Queue Wait Time (min)")
        st.dataframe(mat.style.format("{:.2f}").background_gradient(
            cmap="Blues", axis=None), use_container_width=True, height=220)

    c3, c4 = st.columns([1, 1.1])

    with c3:
        bn = f.groupby("zone_type", as_index=False)["bottleneck_risk_score"].mean().round(1)
        fig = px.bar(bn, y="zone_type", x="bottleneck_risk_score", orientation="h",
                     color_discrete_sequence=[t["crit_col"]],
                     title="Avg Bottleneck Risk Score by Zone Type",
                     labels={"bottleneck_risk_score": "Avg Score", "zone_type": ""},
                     text="bottleneck_risk_score")
        fig.update_traces(texttemplate="%{text:.0f}",
                          textposition="outside",
                          textfont_color=t["text"])
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    with c4:
        qs = f["queue_stress"].value_counts().reset_index()
        qs.columns = ["queue_stress", "count"]
        fig = px.pie(qs, names="queue_stress", values="count", hole=0.56,
                     color_discrete_sequence=t["palette"],
                     title="Match Event by Queue Stress Category")
        fig.update_traces(textinfo="percent+label", textfont_size=10)
        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    # ── Dual metric grouped bar — Crowd Pressure vs Bottleneck Risk by Zone ──
    dual = (
        f.groupby("zone_name", as_index=False)
        .agg(
            crowd_pressure=("crowd_pressure_index",  "mean"),
            bottleneck=    ("bottleneck_risk_score",  "mean"),
            zone_type=     ("zone_type",              "first"),
        )
        .sort_values("bottleneck", ascending=False)
    )
    dual["crowd_pressure"] = dual["crowd_pressure"].round(2)
    dual["bottleneck"]     = dual["bottleneck"].round(2)

    fig = go.Figure()

    # ── FIX: replaced deprecated `titlefont` with `title=dict(font=dict(...))` ──
    fig.add_trace(go.Bar(
        name="Avg Crowd Pressure Index",
        y=dual["zone_name"],
        x=dual["crowd_pressure"],
        orientation="h",
        marker=dict(
            color=dual["crowd_pressure"],
            colorscale=[
                [0.0, t["accent_lt"]],
                [0.5, t["accent"]],
                [1.0, t["crit_col"]],
            ],
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Pressure",
                    font=dict(color=t["text2"], size=11),
                ),
                thickness=12,
                len=0.45,
                x=1.02,
                xanchor="left",
                y=1.0,
                yanchor="top",
                tickfont=dict(color=t["text2"], size=10),
            ),
        ),
        text=dual["crowd_pressure"],
        texttemplate="%{text:.1f}",
        textposition="outside",
        textfont=dict(color=t["text2"], size=10),
        hovertemplate="<b>%{y}</b><br>Crowd Pressure: %{x:.2f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Avg Bottleneck Risk Score",
        y=dual["zone_name"],
        x=dual["bottleneck"],
        orientation="h",
        marker=dict(
            color=dual["bottleneck"],
            colorscale=[
                [0.0, "#FEF3C7"],
                [0.5, t["warn_col"]],
                [1.0, "#DC2626"],
            ],
            showscale=True,
            colorbar=dict(
                title=dict(
                    text="Bottleneck",
                    font=dict(color=t["text2"], size=11),
                ),
                thickness=12,
                len=0.45,
                x=1.02,
                xanchor="left",
                y=0.45,
                yanchor="top",
                tickfont=dict(color=t["text2"], size=10),
            ),
        ),
        text=dual["bottleneck"],
        texttemplate="%{text:.1f}",
        textposition="outside",
        textfont=dict(color=t["text2"], size=10),
        hovertemplate="<b>%{y}</b><br>Bottleneck Risk: %{x:.2f}<extra></extra>",
    ))

    fig.update_layout(
        barmode="group",
        title="Crowd Pressure vs Bottleneck Risk by Zone",
        yaxis=dict(categoryorder="total ascending"),
        bargap=0.18,
        bargroupgap=0.06,
        margin=dict(l=30, r=110, t=50, b=60),
        legend=dict(
            orientation="h",
            x=0.0,
            y=-0.15,
            xanchor="left",
            yanchor="top",
            font=dict(size=11),
        ),
    )
    st.plotly_chart(sfig(fig, t, 440), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 3  ·  MEDICAL & HEAT
# ═══════════════════════════════════════════════════════════
elif page == "Medical & Heat":
    page_header("🏥",
                "Medical and Heat Intelligence",
                "Heat stress, medical incidents, ambulance response and emergency readiness")

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Medical Incident Rate",  med_rate,          "warn", "per 1K people")
    with k2: kpi_card("Avg Ambulance Response", f"{amb_resp} min", "crit")
    with k3: kpi_card("Avg Heat Risk Index",    avg_heat,          "warn")
    with k4: kpi_card("Delayed Medical Zones",  delayed_med,       "crit", "response ≥ 10 min")

    c1, c2 = st.columns([1.55, 1])

    with c1:
        heat = (f.groupby("phase_cat", as_index=False)["heat_risk_index"]
                .mean().sort_values("phase_cat"))
        heat["phase"] = heat["phase_cat"].astype(str)
        fig = px.line(heat, x="phase", y="heat_risk_index", markers=True,
                      color_discrete_sequence=[t["accent"]],
                      title="Heat Risk Index by Phase",
                      labels={"heat_risk_index": "Heat Risk Index", "phase": "Phase"})
        fig.update_traces(line_width=3, marker_size=10)
        for _, row in heat.iterrows():
            fig.add_annotation(x=row["phase"], y=row["heat_risk_index"],
                               text=f"{row['heat_risk_index']:.3f}",
                               showarrow=False, yshift=15,
                               font=dict(color=t["text2"], size=11))
        st.plotly_chart(sfig(fig, t, 300), use_container_width=True)

    with c2:
        med_s = (f.groupby("stadium_name", as_index=False)["medical_incidents"]
                 .sum().sort_values("medical_incidents"))
        fig = px.bar(med_s, y="stadium_name", x="medical_incidents", orientation="h",
                     color="stadium_name", color_discrete_sequence=t["palette"],
                     title="Medical Incidents by Stadium Name",
                     labels={"medical_incidents": "", "stadium_name": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 300), use_container_width=True)

    c3, c4 = st.columns([1, 1.6])

    with c3:
        if not inc_f.empty and "severity" in inc_f.columns:
            sev = inc_f["severity"].value_counts().reset_index()
            sev.columns = ["severity", "count"]
            fig = px.pie(sev, names="severity", values="count", hole=0.55,
                         color_discrete_sequence=t["palette"],
                         title="Incident by Severity")
            fig.update_traces(textinfo="percent+value", textfont_size=11)
            st.plotly_chart(sfig(fig, t, 285), use_container_width=True)
        else:
            st.info("No incident data for current filters.")

    with c4:
        hr_med = (f.groupby("zone_name", as_index=False)
                  .agg(heat=("heat_risk_index", "mean"),
                       med=("medical_incidents", "mean")))
        fig = px.scatter(hr_med, x="heat", y="med", color="zone_name",
                         color_discrete_sequence=t["palette"],
                         title="Heat Risk vs Medical Incidents by Zone",
                         labels={"heat": "Heat Risk Index",
                                  "med": "Avg Medical Incidents",
                                  "zone_name": "Zone"})
        fig.update_traces(marker_size=11)
        st.plotly_chart(sfig(fig, t, 285), use_container_width=True)

    amb = (f.groupby(["phase_cat", "zone_type"], as_index=False)["ambulance_response_time"]
           .mean().sort_values("phase_cat"))
    amb["phase"] = amb["phase_cat"].astype(str)
    fig = px.line(amb, x="phase", y="ambulance_response_time", color="zone_type",
                  markers=True, color_discrete_sequence=t["palette"],
                  title="Ambulance Response Time by Phase and Zone Type",
                  labels={"ambulance_response_time": "Avg Response (min)",
                           "phase": "Phase", "zone_type": "Zone Type"})
    for tr in fig.data:
        tr.mode = "lines+markers+text"
        tr.texttemplate = "%{y:.2f}"
        tr.textposition = "top center"
    st.plotly_chart(sfig(fig, t, 310), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 4  ·  SECURITY
# ═══════════════════════════════════════════════════════════
elif page == "Security":
    page_header("🔒",
                "Security & Unauthorized Activity Monitoring",
                "Unauthorized entries, security incidents, ticket fraud, fan ejections and stadium safety")

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Unauthorized Entries", f"{unauthorized:,}", "crit")
    with k2: kpi_card("Counterfeit Cases",    f"{counterfeit:,}",  "warn")
    with k3: kpi_card("Pitch Invasions",      f"{pitch_inv:,}",    "crit")
    with k4: kpi_card("Fan Ejections",        f"{fan_ej:,}",       "warn")

    c1, c2 = st.columns([1.4, 1])

    with c1:
        ua = (f.groupby(["phase_cat", "zone_type"], as_index=False)["unauthorized_entry_attempts"]
              .mean().sort_values("phase_cat"))
        ua["phase"] = ua["phase_cat"].astype(str)
        fig = px.line(ua, x="phase", y="unauthorized_entry_attempts", color="zone_type",
                      markers=True, color_discrete_sequence=t["palette"],
                      title="Unauthorized Entry by Phases and Zone Type",
                      labels={"unauthorized_entry_attempts": "Avg Entries",
                               "zone_type": "Zone Type", "phase": "Phase"})
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    with c2:
        sec_s = (f.groupby("stadium_name", as_index=False)["security_incidents"]
                 .sum().sort_values("security_incidents"))
        fig = px.bar(sec_s, y="stadium_name", x="security_incidents", orientation="h",
                     color_discrete_sequence=[t["accent"]],
                     title="Security Incidents by Stadium Name",
                     labels={"security_incidents": "", "stadium_name": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    c3, c4 = st.columns([1.2, 1])

    with c3:
        cs = (f.groupby("zone_name", as_index=False)
              .agg(pressure=("crowd_pressure_index", "mean"),
                   security=("security_incidents", "sum"),
                   people=("people_count", "sum")))
        fig = px.scatter(cs, x="people", y="pressure", color="zone_name",
                         size="security", color_discrete_sequence=t["palette"],
                         title="Crowd Pressure vs Security Incidents",
                         labels={"people": "People Count",
                                  "pressure": "Crowd Pressure Index",
                                  "zone_name": "Zone",
                                  "security": "Security Incidents"})
        fig.update_traces(marker_sizemin=6)
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    with c4:
        sp = (f.groupby(["phase_cat", "zone_type"], as_index=False)["security_incidents"]
              .mean().sort_values("phase_cat"))
        sp["phase"] = sp["phase_cat"].astype(str)
        fig = px.bar(sp, x="phase", y="security_incidents", color="zone_type",
                     barmode="group", color_discrete_sequence=t["palette"],
                     title="Security Incidents by Phase and Zone Type",
                     labels={"security_incidents": "Avg Incidents",
                              "phase": "Phase", "zone_type": "Zone Type"})
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PAGE 5  ·  RESOURCE PLANNING
# ═══════════════════════════════════════════════════════════
elif page == "Resource Planning":
    page_header("📦",
                "Resource Planning & Operational Readiness",
                "Staff requirements, barricade deployment, medical teams and readiness across phases")

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Staff Adequacy Ratio", staff_ratio,      "ok")
    with k2: kpi_card("Total Required Staff", f"{req_staff:,}", "info")
    with k3: kpi_card("Total Barricades",     f"{req_barr:,}",  "warn")
    with k4: kpi_card("Total Medical Teams",  f"{med_teams:,}", "ok")

    c1, c2 = st.columns([1.55, 1])

    with c1:
        rd = (f.groupby(["phase_cat", "zone_type"], as_index=False)["staff_adequacy_ratio"]
              .mean().sort_values("phase_cat"))
        rd["phase"] = rd["phase_cat"].astype(str)
        fig = px.line(rd, x="phase", y="staff_adequacy_ratio", color="zone_type",
                      markers=True, color_discrete_sequence=t["palette"],
                      title="Operational Readiness Across Match Phases",
                      labels={"staff_adequacy_ratio": "Staff Adequacy Ratio",
                               "phase": "Phase", "zone_type": "Zone Type"})
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    with c2:
        md = (f.groupby("zone_type", as_index=False)
              .agg(people=("people_count", "sum"),
                   med_t=("deployed_medical_teams", "sum")))
        fig = px.scatter(md, x="people", y="med_t", color="zone_type",
                         size="med_t", color_discrete_sequence=t["palette"],
                         title="Medical Team Deployment vs Crowd Size",
                         labels={"people": "Total People",
                                  "med_t": "Deployed Medical Teams",
                                  "zone_type": "Zone Type"})
        fig.update_traces(marker_sizemin=14)
        st.plotly_chart(sfig(fig, t, 295), use_container_width=True)

    c3, c4 = st.columns([1, 1])

    with c3:
        res = f.groupby("zone_type", as_index=False).agg(
            staff=("required_staff", "sum"),
            med=("deployed_medical_teams", "sum"))
        fig = go.Figure()
        fig.add_bar(y=res["zone_type"], x=res["staff"],
                    name="Sum of required_staff",
                    orientation="h", marker_color=t["palette"][0])
        fig.add_bar(y=res["zone_type"], x=res["med"],
                    name="Sum of deployed_medical_teams",
                    orientation="h", marker_color=t["palette"][1])
        fig.update_layout(barmode="group",
                          title="Required Staff vs Medical Deployment",
                          xaxis_title="", yaxis_title="")
        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    with c4:
        br = (f.groupby("zone_type", as_index=False)["required_barricades"]
              .sum().sort_values("required_barricades"))
        fig = px.bar(br, y="zone_type", x="required_barricades", orientation="h",
                     color_discrete_sequence=[t["palette"][0]],
                     title="Barricade Requirements by Zone",
                     labels={"required_barricades": "Total Barricades", "zone_type": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(sfig(fig, t, 275), use_container_width=True)

    # Readiness matrix
    mat2 = f.pivot_table(values="staff_adequacy_ratio",
                         index="stadium_name", columns="phase", aggfunc="mean").round(2)
    ord_cols = [p for p in PHASE_ORDER if p in mat2.columns]
    mat2 = mat2[ord_cols]
    sec_label("Staff Adequacy Ratio — Stadium × Phase")
    st.dataframe(mat2.style.format("{:.2f}").background_gradient(
        cmap="Greens", axis=None), use_container_width=True)


# ─────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f'<p style="text-align:center;font-size:11px;color:{t["text2"]};padding:4px 0;">'
    "🏏 IPL Crowd Safety Management Dashboard &nbsp;|&nbsp; Powered by Streamlit, Plotly & Cohere AI"
    "</p>",
    unsafe_allow_html=True)