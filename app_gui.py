
import io
import json
import os
from datetime import datetime
from typing import List

import pandas as pd
import streamlit as st
from PIL import Image

from discovery import discover_businesses, search_public_topics, expand_topic_queries
from enrichment import enrich_rows
from scoring import score_rows
from ui_theme import inject_brand_theme
import packager as packager_mod
import exports as exports_mod


# =========================================================
# PAGE SETUP
# =========================================================
favicon_path = os.path.join("assets", "favicon.png")
page_icon = "🧠"

if os.path.exists(favicon_path):
    try:
        page_icon = Image.open(favicon_path)
    except Exception:
        page_icon = "🧠"

st.set_page_config(
    page_title="TerraVaultIQ",
    page_icon=page_icon,
    layout="wide",
)

inject_brand_theme()

# ---------------------------------------------------------
# LIGHT UI OVERRIDE
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --tv-bg: #eef4f2;
        --tv-surface: #ffffff;
        --tv-surface-2: #f8fbfa;
        --tv-text: #0f172a;
        --tv-text-soft: #334155;
        --tv-border: #d7e3df;
        --tv-green: #0f5132;
        --tv-green-2: #166534;
        --tv-green-3: #dcfce7;
        --tv-accent: #ff5a5f;
        --tv-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background:
            radial-gradient(circle at top left, rgba(22,101,52,0.08), transparent 28%),
            linear-gradient(180deg, #f7fbfa 0%, #eef4f2 100%) !important;
        color: var(--tv-text) !important;
    }

    [data-testid="stHeader"] {
        background: rgba(255,255,255,0) !important;
    }

    [data-testid="stToolbar"] {
        right: 1rem;
    }

    .block-container {
        padding-top: 1.35rem !important;
        padding-bottom: 2.25rem !important;
    }

    /* Generic text */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: var(--tv-text);
    }

    .stMarkdown, .stCaption, .stText {
        color: var(--tv-text) !important;
    }

    /* Section cards */
    .tv-card,
    .tv-hero,
    div[data-testid="stVerticalBlock"] > div:has(> div .tv-card),
    div[data-testid="stVerticalBlock"] > div:has(> div .tv-hero) {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(215,227,223,0.95);
        box-shadow: var(--tv-shadow);
        border-radius: 28px;
        backdrop-filter: blur(10px);
    }

    .tv-card {
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
    }

    .tv-card h2 {
        margin: 0;
        font-size: 1.05rem;
        letter-spacing: 0.01em;
        color: var(--tv-text) !important;
    }

    .tv-card-sub {
        margin-top: 0.55rem;
        color: var(--tv-text-soft) !important;
        font-size: 0.96rem;
    }

    .tv-hero {
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
        background:
            linear-gradient(135deg, rgba(255,255,255,0.96) 0%, rgba(247,251,250,0.96) 55%, rgba(220,252,231,0.84) 100%);
    }

    .tv-hero h1 {
        margin: 0.45rem 0 0.7rem 0;
        line-height: 1.02;
        font-size: 2.7rem;
        color: var(--tv-text) !important;
    }

    .tv-hero p {
        margin: 0;
        color: var(--tv-text-soft) !important;
        font-size: 1rem;
        max-width: 760px;
    }

    .tv-pill,
    .tv-kicker {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: rgba(15,81,50,0.08);
        border: 1px solid rgba(15,81,50,0.18);
        color: var(--tv-green) !important;
        font-weight: 700;
        font-size: 0.82rem;
    }

    .accent {
        color: var(--tv-green) !important;
    }

    /* Labels and helper copy */
    .stTextInput label,
    .stTextArea label,
    .stNumberInput label,
    .stSelectbox label,
    .stMultiSelect label,
    .stCheckbox label,
    .stRadio label,
    .stSlider label,
    .stDownloadButton label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] * {
        color: var(--tv-text) !important;
        font-weight: 700 !important;
    }

    .stCaption, .stInfo, .stAlert {
        color: var(--tv-text) !important;
    }

    /* Tabs */
    [data-baseweb="tab-list"] {
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    button[data-baseweb="tab"] {
        background: rgba(255,255,255,0.7) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 999px !important;
        color: var(--tv-text) !important;
        font-weight: 700 !important;
        padding: 0.45rem 1rem !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, var(--tv-green) 0%, var(--tv-green-2) 100%) !important;
        color: #ffffff !important;
        border-color: var(--tv-green) !important;
    }

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    [data-testid="stNumberInput"] input {
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 0 rgba(15, 23, 42, 0.02);
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stNumberInput input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus {
        border-color: rgba(15,81,50,0.45) !important;
        box-shadow: 0 0 0 3px rgba(34,197,94,0.10) !important;
    }

    /* Number input stepper */
    [data-testid="stNumberInput"] button {
        background: #f8fafc !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border) !important;
    }

    /* Selects - closed state */
    div[data-baseweb="select"] > div {
        min-height: 3.25rem !important;
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 18px !important;
        box-shadow: 0 2px 0 rgba(15, 23, 42, 0.02);
    }

    div[data-baseweb="select"] * {
        color: var(--tv-text) !important;
        fill: var(--tv-text) !important;
    }

    div[data-baseweb="select"] svg {
        color: var(--tv-text) !important;
        fill: var(--tv-text) !important;
    }

    /* Dropdown menu */
    div[data-baseweb="popover"] {
        background: transparent !important;
    }

    div[data-baseweb="menu"] {
        background: var(--tv-surface) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 18px !important;
        box-shadow: 0 18px 40px rgba(15,23,42,0.12) !important;
        overflow: hidden !important;
    }

    ul[role="listbox"],
    div[role="listbox"] {
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        padding: 0.35rem !important;
    }

    li[role="option"],
    div[role="option"] {
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        border-radius: 12px !important;
    }

    li[role="option"] *,
    div[role="option"] * {
        color: var(--tv-text) !important;
    }

    li[role="option"]:hover,
    div[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    div[role="option"][aria-selected="true"] {
        background: #ecfdf3 !important;
        color: var(--tv-green) !important;
    }

    /* Checkbox / radio text and controls */
    .stCheckbox,
    .stRadio,
    .stCheckbox *,
    .stRadio * {
        color: var(--tv-text) !important;
    }

    .stCheckbox label p,
    .stRadio label p {
        color: var(--tv-text) !important;
        opacity: 1 !important;
    }

    [role="radiogroup"] label,
    [role="radiogroup"] div,
    [role="radiogroup"] p {
        color: var(--tv-text) !important;
        opacity: 1 !important;
    }

    .stCheckbox input + div,
    .stRadio input + div {
        border-color: var(--tv-border) !important;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        min-height: 3rem;
        background: linear-gradient(135deg, var(--tv-green) 0%, var(--tv-green-2) 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(15,81,50,0.85) !important;
        border-radius: 16px !important;
        font-weight: 800 !important;
        letter-spacing: 0.01em;
        box-shadow: 0 10px 20px rgba(22,101,52,0.18);
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover,
    button[kind="primary"]:hover,
    button[kind="secondary"]:hover {
        transform: translateY(-1px);
        filter: brightness(1.03);
        border-color: rgba(21,128,61,1) !important;
    }

    .stButton > button *,
    .stDownloadButton > button *,
    .stFormSubmitButton > button *,
    button[kind="primary"] *,
    button[kind="secondary"] * {
        color: #ffffff !important;
    }

    /* Metrics and dataframe */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.88) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 20px !important;
        box-shadow: var(--tv-shadow) !important;
        padding: 0.75rem 1rem !important;
    }

    [data-testid="stDataFrame"] {
        background: rgba(255,255,255,0.92) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 20px !important;
        overflow: hidden !important;
    }

    /* Expanders, alerts */
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.72) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 18px !important;
    }

    [data-testid="stInfo"],
    [data-testid="stSuccess"],
    [data-testid="stWarning"],
    [data-testid="stError"] {
        border-radius: 18px !important;
    }

    /* Helper card */
    .tv-helper-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbfa 100%);
        border: 1px solid var(--tv-border);
        border-radius: 22px;
        padding: 16px 18px;
        margin-top: 12px;
        margin-bottom: 12px;
        box-shadow: var(--tv-shadow);
    }

    .tv-helper-title {
        font-size: 1.05rem;
        font-weight: 800;
        margin-bottom: 8px;
        color: var(--tv-text) !important;
    }

    .tv-helper-label {
        color: var(--tv-green) !important;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 2px;
    }

    .tv-helper-copy {
        color: var(--tv-text-soft) !important;
        line-height: 1.5;
    }

    /* Horizontal rule and footer */
    hr {
        border-color: rgba(215,227,223,0.9) !important;
    }

    .stApp a {
        color: var(--tv-green) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

if "last_run_meta" not in st.session_state:
    st.session_state.last_run_meta = {}


# =========================================================
# CONSTANTS
# =========================================================
BUSINESS_SEARCH_MODES = [
    "Marketing Prospect Finder",
    "Custom Business Search",
]

PUBLIC_SEARCH_MODES = [
    "Public Intent Search",
    "Relocation Interest Finder",
    "Community Interest Finder",
]


# =========================================================
# AD PACK HELPER
# =========================================================
AD_PACK_DETAILS = {
    "SEO": {
        "best_for": "Long-term visibility and organic search traffic.",
        "why": "Helps the customer get found when people search for what they offer, without relying only on paid traffic.",
        "rep_talk_track": "SEO helps you show up more often in search results so customers can find you naturally over time.",
    },
    "Google Ads": {
        "best_for": "Fast leads, calls, and search demand capture.",
        "why": "Puts the customer in front of people already searching right now, which makes it one of the fastest paths to inbound leads.",
        "rep_talk_track": "Google Ads gets you in front of people already looking for your service, which means faster opportunities.",
    },
    "OTT": {
        "best_for": "Streaming TV awareness and premium local targeting.",
        "why": "Builds awareness with targeted streaming placements so the customer stays top-of-mind in the right households.",
        "rep_talk_track": "OTT helps people see and remember your brand on streaming TV, which is great for awareness and trust.",
    },
    "Social Media Ads": {
        "best_for": "Awareness, engagement, and audience building.",
        "why": "Gets the customer in front of the right audience where people already spend time every day.",
        "rep_talk_track": "Social ads help you stay visible, build attention, and get in front of the right people consistently.",
    },
    "Retargeting": {
        "best_for": "Bringing back past visitors who did not convert.",
        "why": "Keeps the brand in front of warm prospects and helps turn missed traffic into real opportunities.",
        "rep_talk_track": "Retargeting helps bring back people who already showed interest but did not take action the first time.",
    },
    "Local SEO + Google Ads": {
        "best_for": "Local businesses that need both quick wins and long-term growth.",
        "why": "Combines immediate lead generation with stronger long-term local visibility in search.",
        "rep_talk_track": "This gives you short-term traffic now and stronger long-term search visibility in your market.",
    },
    "Full Funnel Package": {
        "best_for": "Customers who need awareness, consideration, and conversion support together.",
        "why": "Covers the full buyer journey so the customer gets a more complete growth system instead of a one-channel play.",
        "rep_talk_track": "This package helps attract attention, build trust, and drive action across the full customer journey.",
    },
}


def recommend_frontend_pack(search_mode: str, keyword: str) -> str:
    text = f"{search_mode} {keyword}".lower()

    if any(term in text for term in ["moving", "relocation", "interstate", "movers"]):
        return "Google Ads"
    if any(term in text for term in ["event", "grand opening", "launch", "festival", "sale"]):
        return "Social Media Ads"
    if any(term in text for term in ["roofer", "roofing", "plumber", "plumbing", "hvac", "contractor", "cleaner", "cleaning", "landscaping"]):
        return "Local SEO + Google Ads"
    if "community" in text:
        return "Social Media Ads"
    if "public intent" in text:
        return "Google Ads"
    return "SEO"


def render_ad_pack_helper(selected_pack: str):
    info = AD_PACK_DETAILS[selected_pack]
    st.markdown(
        f"""
        <div class="tv-helper-card">
            <div class="tv-kicker">Sales Helper</div>
            <div class="tv-helper-title">{selected_pack}</div>
            <div class="tv-helper-label">Best for</div>
            <div class="tv-helper-copy">{info['best_for']}</div>
            <div class="tv-helper-label">Why this helps the customer</div>
            <div class="tv-helper-copy">{info['why']}</div>
            <div class="tv-helper-label">Easy rep talk track</div>
            <div class="tv-helper-copy">{info['rep_talk_track']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# AUTH GATE
# =========================================================
if not st.user.is_logged_in:
    st.markdown("""
    <div class="tv-hero">
        <div class="tv-pill">TerraVaultIQ • Midwest Horizons Internal</div>
        <h1>
            In-house<br>
            <span class="accent">Lead Engine</span>
        </h1>
        <p>
            Sign in with your Midwest Horizons Google account to access lead discovery,
            scoring, enrichment, and export tools.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.button("Sign in with Google", on_click=st.login, use_container_width=True)
    st.stop()

user_email = str(st.user.get("email", "")).strip().lower()
user_name = str(st.user.get("name", "")).strip()

if not user_email.endswith("@midwesthorizons.com"):
    st.error("This app is restricted to Midwest Horizons Google accounts.")
    st.button("Log out", on_click=st.logout, use_container_width=True)
    st.stop()


# =========================================================
# SAFE FALLBACKS
# =========================================================
def _fallback_normalize_zip_list(text: str) -> List[str]:
    if not text:
        return []
    parts = [p.strip() for p in text.replace("\n", ",").split(",")]
    return [p for p in parts if p]


normalize_zip_list = getattr(packager_mod, "normalize_zip_list", _fallback_normalize_zip_list)
build_client_export_df = getattr(packager_mod, "build_client_export_df", None)
build_crm_export_df = getattr(packager_mod, "build_crm_export_df", None)
build_package_manifest = getattr(packager_mod, "build_package_manifest", None)
build_package_summary = getattr(packager_mod, "build_package_summary", None)

build_package_zip_bytes = getattr(exports_mod, "build_package_zip_bytes", None)
dataframe_to_excel_bytes = getattr(exports_mod, "dataframe_to_excel_bytes", None)


# =========================================================
# UI HELPERS
# =========================================================
def render_hero():
    st.markdown(
        f"""
        <div class="tv-hero">
            <div class="tv-pill">TerraVaultIQ • Audience Intelligence Solutions</div>
            <h1>
                Build and activate<br>
                <span class="accent">hyper-targeted<br>audiences</span>
            </h1>
            <p>
                Internal V7 workspace for Midwest Horizons. Signed in as {user_name or user_email}.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_a, top_b = st.columns([8, 1])
    with top_b:
        st.button("Log out", on_click=st.logout, use_container_width=True)


def render_section_header(title: str, subtitle: str = ""):
    subtitle_html = f'<div class="tv-card-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="tv-card">
            <h2>{title}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def default_prompt(search_mode: str):
    defaults = {
        "Marketing Prospect Finder": ("INDUSTRY / CATEGORY", "roofing"),
        "Custom Business Search": ("CATEGORY / KEYWORD", "house cleaners"),
        "Public Intent Search": ("TOPIC / KEYWORD", "roofing company"),
        "Relocation Interest Finder": ("RELOCATION TOPIC", "moving to leavenworth"),
        "Community Interest Finder": ("COMMUNITY / INTEREST", "community events"),
    }
    return defaults.get(search_mode, ("KEYWORD", "roofing"))


def suggestion_title(search_mode: str) -> str:
    titles = {
        "Public Intent Search": "Suggested public intent phrases",
        "Relocation Interest Finder": "Suggested relocation phrases",
        "Community Interest Finder": "Suggested community phrases",
    }
    return titles.get(search_mode, "Suggested search phrases")


def dedupe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()

    for col in ["name", "address", "website", "phone"]:
        if col not in work.columns:
            work[col] = ""

    work["_dedupe_name"] = work["name"].astype(str).str.strip().str.lower()
    work["_dedupe_address"] = work["address"].astype(str).str.strip().str.lower()
    work["_dedupe_website"] = work["website"].astype(str).str.strip().str.lower()
    work["_dedupe_phone"] = work["phone"].astype(str).str.strip().str.lower()

    work = work.drop_duplicates(
        subset=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"],
        keep="first",
    )

    work = work.drop(
        columns=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"],
        errors="ignore",
    )

    return work.reset_index(drop=True)


def sort_by_score_if_present(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "needs_leads_score" not in df.columns:
        return df.reset_index(drop=True)

    work = df.copy()
    work["_needs_num"] = pd.to_numeric(work["needs_leads_score"], errors="coerce").fillna(-1)
    work = work.sort_values("_needs_num", ascending=False)
    work = work.drop(columns=["_needs_num"], errors="ignore")
    return work.reset_index(drop=True)


def safe_metric_count(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0
    s = df[column].astype(str).fillna("").str.strip()
    return int((s != "").sum())


def hot_lead_count(df: pd.DataFrame) -> int:
    if "needs_leads_tier" not in df.columns:
        return 0
    return int((df["needs_leads_tier"].astype(str) == "Hot").sum())


def add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()

    possible_contact_cols = [
        "best_contact_name",
        "contact_name",
        "primary_contact_name",
        "owner_name",
        "decision_maker",
    ]

    if "best_contact_name" not in work.columns:
        work["best_contact_name"] = ""

    for col in possible_contact_cols:
        if col in work.columns:
            vals = work[col].fillna("").astype(str).str.strip()
            work["best_contact_name"] = work["best_contact_name"].mask(
                work["best_contact_name"].eq("") & vals.ne(""),
                vals
            )

    opening = (
        work["pitch_opening_line"].fillna("").astype(str).str.strip()
        if "pitch_opening_line" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )
    offer = (
        work["pitch_offer"].fillna("").astype(str).str.strip()
        if "pitch_offer" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )
    cta = (
        work["pitch_cta"].fillna("").astype(str).str.strip()
        if "pitch_cta" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )

    work["pitch_summary"] = (opening + " | " + offer + " | " + cta).str.strip(" |")

    score_series = (
        pd.to_numeric(work["needs_leads_score"], errors="coerce")
        if "needs_leads_score" in work.columns
        else pd.Series([0] * len(work), index=work.index)
    )
    keyword_series = (
        work["search_keyword"].fillna("").astype(str).str.lower()
        if "search_keyword" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )
    mode_series = (
        work["search_mode"].fillna("").astype(str).str.lower()
        if "search_mode" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )
    type_series = (
        work["business_type"].fillna("").astype(str).str.lower()
        if "business_type" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )
    website_series = (
        work["website"].fillna("").astype(str).str.strip()
        if "website" in work.columns
        else pd.Series([""] * len(work), index=work.index)
    )

    work["_score_num"] = score_series.fillna(0)
    work["_keyword"] = keyword_series
    work["_search_mode"] = mode_series
    work["_business_type"] = type_series
    work["_website"] = website_series

    def pick_package(row):
        score = row.get("_score_num", 0)
        keyword = row.get("_keyword", "")
        search_mode = row.get("_search_mode", "")
        business_type = row.get("_business_type", "")
        website = row.get("_website", "")

        relocation_terms = ["moving", "relocation", "interstate", "out of state", "movers"]
        event_terms = ["event", "grand opening", "launch", "festival", "sale"]
        service_terms = ["roofing", "cleaning", "hvac", "plumbing", "contractor", "landscaping", "remodeling"]

        combined_text = f"{keyword} {search_mode} {business_type}".lower()

        if any(term in combined_text for term in relocation_terms):
            return (
                "Relocation Capture Package",
                "$1,500-$3,500 + ad spend",
                "Best for businesses tied to moving, relocation, or interstate intent where fast lead capture matters.",
            )

        if any(term in combined_text for term in event_terms):
            return (
                "Grand Opening / Event Push",
                "$1,200-$3,000 + ad spend",
                "Best for time-sensitive promotions, launches, and event-driven campaigns that need urgency.",
            )

        if score >= 85:
            return (
                "Full Funnel Growth Package",
                "$3,500-$7,500 + ad spend",
                "Strong fit for higher-priority leads that can support a bigger search, display, and retargeting strategy.",
            )

        if score >= 65:
            return (
                "Local Visibility Package",
                "$2,000-$4,500 + ad spend",
                "Good fit for businesses that need stronger local awareness, better lead flow, and more consistent visibility.",
            )

        if website == "":
            return (
                "Starter Lead Boost",
                "$750-$1,500 + ad spend",
                "Good entry package for businesses with low digital presence or missing core lead-capture assets.",
            )

        if any(term in combined_text for term in service_terms):
            return (
                "Local Service Lead Package",
                "$1,500-$3,000 + ad spend",
                "A strong option for service businesses that need inbound local calls, form fills, and booked jobs.",
            )

        return (
            "Starter Lead Boost",
            "$750-$1,500 + ad spend",
            "Solid starter package for testing lead generation and visibility before moving into a larger campaign.",
        )

    package_data = work.apply(pick_package, axis=1, result_type="expand")
    package_data.columns = [
        "ad_package_recommendation",
        "ad_package_price_range",
        "ad_package_reason",
    ]

    work["ad_package_recommendation"] = package_data["ad_package_recommendation"]
    work["ad_package_price_range"] = package_data["ad_package_price_range"]
    work["ad_package_reason"] = package_data["ad_package_reason"]

    work = work.drop(
        columns=["_score_num", "_keyword", "_search_mode", "_business_type", "_website"],
        errors="ignore",
    )

    return work


def build_summary_text(
    df: pd.DataFrame,
    package_name: str,
    prepared_by: str,
    search_mode: str,
    keyword: str,
    area_label: str,
) -> str:
    if callable(build_package_summary):
        try:
            return build_package_summary(
                package_name=package_name,
                prepared_by=prepared_by,
                row_count=len(df),
                search_mode=search_mode,
                keyword=keyword,
                area_label=area_label,
            )
        except Exception:
            pass

    lines = [
        f"Package: {package_name}",
        f"Prepared by: {prepared_by}",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Search mode: {search_mode}",
        f"Keyword: {keyword}",
        f"Area label: {area_label}",
        f"Rows included: {len(df)}",
    ]
    return "\n".join(lines)


def fallback_client_export_df(df: pd.DataFrame) -> pd.DataFrame:
    df = add_display_columns(df)

    preferred = [
        "name",
        "best_contact_name",
        "business_type",
        "search_keyword",
        "source_zip",
        "address",
        "website",
        "primary_email",
        "primary_phone",
        "rating",
        "ratings_total",
        "needs_leads_score",
        "needs_leads_tier",
        "needs_leads_reason",
        "pitch_opening_line",
        "pitch_offer",
        "pitch_cta",
        "pitch_summary",
        "ad_package_recommendation",
        "ad_package_price_range",
        "ad_package_reason",
    ]
    cols = [c for c in preferred if c in df.columns]
    remainder = [c for c in df.columns if c not in cols]
    return df[cols + remainder].copy()


def fallback_crm_export_df(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["name"] = df["name"] if "name" in df.columns else ""
    out["primary_email"] = df["primary_email"] if "primary_email" in df.columns else ""
    out["primary_phone"] = df["primary_phone"] if "primary_phone" in df.columns else (df["phone"] if "phone" in df.columns else "")
    out["website"] = df["website"] if "website" in df.columns else ""
    out["status"] = "new"
    out["priority"] = df["needs_leads_tier"] if "needs_leads_tier" in df.columns else ""
    out["owner"] = user_email
    out["notes"] = df["pitch_reason"] if "pitch_reason" in df.columns else ""
    out["offer_angle"] = df["pitch_angle"] if "pitch_angle" in df.columns else ""
    out["follow_up_date"] = ""
    return out


def get_client_export_df(df: pd.DataFrame) -> pd.DataFrame:
    if callable(build_client_export_df):
        try:
            return build_client_export_df(df)
        except Exception:
            pass
    return fallback_client_export_df(df)


def get_crm_export_df(df: pd.DataFrame) -> pd.DataFrame:
    if callable(build_crm_export_df):
        try:
            return build_crm_export_df(df)
        except Exception:
            pass
    return fallback_crm_export_df(df)


def dataframe_to_excel_fallback(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    output.seek(0)
    return output.read()


def get_excel_bytes(df: pd.DataFrame) -> bytes:
    if callable(dataframe_to_excel_bytes):
        try:
            return dataframe_to_excel_bytes(df)
        except Exception:
            pass
    return dataframe_to_excel_fallback(df)


def build_manifest(package_name: str, prepared_by: str, row_count: int, meta: dict) -> dict:
    if callable(build_package_manifest):
        try:
            return build_package_manifest(
                package_name=package_name,
                prepared_by=prepared_by,
                row_count=row_count,
                search_mode=meta.get("search_mode", ""),
                keyword=meta.get("keyword", ""),
                area_label=meta.get("area_label", ""),
            )
        except Exception:
            pass

    return {
        "package_name": package_name,
        "prepared_by": prepared_by,
        "generated_at": datetime.now().isoformat(),
        "total_rows": int(row_count),
        "search_mode": meta.get("search_mode", ""),
        "keyword": meta.get("keyword", ""),
        "area_label": meta.get("area_label", ""),
        "run_by": user_email,
    }


def build_package_zip_fallback(
    client_df: pd.DataFrame,
    crm_df: pd.DataFrame,
    summary_text: str,
    manifest: dict,
) -> bytes:
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("client_leads.csv", client_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("crm_import.csv", crm_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("package_summary.txt", summary_text.encode("utf-8"))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    buf.seek(0)
    return buf.read()


def get_package_zip_bytes(
    client_df: pd.DataFrame,
    crm_df: pd.DataFrame,
    summary_text: str,
    manifest: dict,
) -> bytes:
    if callable(build_package_zip_bytes):
        try:
            return build_package_zip_bytes(client_df, crm_df, summary_text, manifest)
        except Exception:
            pass
    return build_package_zip_fallback(client_df, crm_df, summary_text, manifest)


def render_results_card(df: pd.DataFrame, title: str = "Lead Results"):
    render_section_header(title, "Review, score, and export client-ready lead packages.")

    df = add_display_columns(df)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Results", len(df))
    m2.metric("With Website", safe_metric_count(df, "website"))
    m3.metric("With Email", safe_metric_count(df, "primary_email"))
    m4.metric("Hot Leads", hot_lead_count(df))

    preferred_cols = [
        "name",
        "best_contact_name",
        "primary_email",
        "primary_phone",
        "website",
        "address",
        "business_type",
        "needs_leads_score",
        "needs_leads_tier",
        "pitch_summary",
        "ad_package_recommendation",
        "ad_package_price_range",
        "ad_package_reason",
        "pitch_reason",
        "pitch_angle",
        "title",
        "snippet",
    ]

    visible_cols = [c for c in preferred_cols if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in visible_cols]

    st.dataframe(
        df[visible_cols + remaining_cols],
        use_container_width=True,
        hide_index=True,
        height=520,
    )


# =========================================================
# HERO
# =========================================================
render_hero()

tab1, tab2, tab3 = st.tabs(
    ["Campaign Search", "Client Package Builder", "Expansion Planner"]
)


# =========================================================
# TAB 1
# =========================================================
with tab1:
    left_col, right_col = st.columns([2.15, 1], gap="large")

    with left_col:
        render_section_header(
            "Location & Keywords",
            "Set the search area, vertical, and campaign discovery inputs.",
        )

        scan_mode = st.radio(
            "Scan Mode",
            ["Single ZIP Deep Scan", "Multi-ZIP Area Scan"],
            index=1,
            horizontal=True,
            key="scan_mode_main",
        )

        if scan_mode == "Single ZIP Deep Scan":
            zip_code = st.text_input("ZIP CODE", value="66048", key="zip_code_single")
            zip_list_text = ""
        else:
            zip_code = ""
            zip_list_text = st.text_area(
                "ZIP LIST",
                value="66048, 66044, 66086",
                height=120,
                key="zip_list_multi",
            )

        radius = st.number_input(
            "RADIUS (miles)",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            key="campaign_radius",
        )

        area_label = st.text_input(
            "CITY / AREA LABEL",
            value="Leavenworth",
            key="campaign_area_label",
        )

        search_mode = st.selectbox(
            "Search Mode",
            BUSINESS_SEARCH_MODES + PUBLIC_SEARCH_MODES,
            index=0,
            key="campaign_search_mode",
        )

        label, default_value = default_prompt(search_mode)
        category_or_topic = st.text_input(
            label,
            value=default_value,
            key="campaign_topic_keyword",
        )

        if search_mode in PUBLIC_SEARCH_MODES:
            with st.expander(suggestion_title(search_mode), expanded=False):
                phrases = expand_topic_queries(
                    search_mode,
                    category_or_topic.strip(),
                    zip_code=zip_code.strip(),
                    area_label=area_label.strip(),
                )

                if phrases:
                    st.markdown("\n".join([f"- `{phrase}`" for phrase in phrases]))
                else:
                    st.caption("No suggestions yet. Enter a keyword or area.")

            st.info(
                f"{search_mode} is currently using stable fallback phrase generation so the mode stays usable while you finalize external public-page search."
            )

        ad_pack_choice = recommend_frontend_pack(search_mode, category_or_topic.strip())

        run_search = st.button("FIND LEADS", use_container_width=True, key="run_search_main")

    with right_col:
        render_section_header(
            "Search Options",
            "Google key is stored in app secrets. Reps only need to run searches.",
        )

        use_google = st.checkbox("Use Google API if available", value=True, key="use_google_main")
        use_osm = st.checkbox("Use OpenStreetMap backup", value=False, key="use_osm_main")
        do_enrich = st.checkbox("Find public business contact info", value=True, key="do_enrich_main")
        enrich_limit = st.number_input(
            "Max rows to enrich",
            min_value=0,
            max_value=5000,
            value=100,
            step=25,
            key="enrich_limit_main",
        )
        do_score = st.checkbox("Score business leads", value=True, key="do_score_main")
        trim_results = st.checkbox("Trim final results", value=False, key="trim_results_main")
        final_cap = st.selectbox(
            "Final result cap",
            [100, 250, 500, 1000, 2500, 5000],
            index=2,
            key="final_cap_main",
        )
        show_debug = st.checkbox("Show debug counts", value=True, key="show_debug_main")

        public_pages_only = st.checkbox(
            "Public pages only",
            value=False if search_mode in PUBLIC_SEARCH_MODES else True,
            key="public_pages_only_main",
        )

        max_pages = st.slider(
            "Public search pages",
            1,
            10,
            6 if search_mode in PUBLIC_SEARCH_MODES else 4,
            key="max_pages_main",
        )

    if run_search:
        try:
            zips = (
                [zip_code.strip()]
                if scan_mode == "Single ZIP Deep Scan" and zip_code.strip()
                else normalize_zip_list(zip_list_text)
                if scan_mode != "Single ZIP Deep Scan"
                else []
            )

            all_rows = []

            if search_mode in BUSINESS_SEARCH_MODES:
                if not zips:
                    st.error("Please enter at least one ZIP code for business searches.")
                else:
                    mode = "marketing" if search_mode == "Marketing Prospect Finder" else "custom"
                    progress = st.progress(0, text="Searching businesses...")

                    for idx, z in enumerate(zips):
                        rows = discover_businesses(
                            z,
                            float(radius),
                            mode,
                            category_or_topic.strip(),
                            use_google,
                            use_osm,
                        )

                        for row in rows:
                            row["search_mode"] = search_mode
                            row["search_keyword"] = category_or_topic.strip()
                            row["source_zip"] = z
                            row["area_label"] = area_label.strip()
                            row["run_by"] = user_email
                            row["front_end_ad_pack_choice"] = ad_pack_choice

                        all_rows.extend(rows)
                        progress.progress((idx + 1) / len(zips), text=f"Business search {idx + 1}/{len(zips)}")

                    progress.empty()

                    if do_enrich and all_rows:
                        limit = min(len(all_rows), int(enrich_limit))
                        if limit > 0:
                            st.info(f"Enriching {limit} rows.")
                            enriched = enrich_rows(all_rows[:limit])
                            all_rows = enriched + all_rows[limit:]

                    if do_score and all_rows:
                        all_rows = score_rows(all_rows)

            else:
                target_zips = zips if zips else [""]
                progress = st.progress(0, text="Searching public pages...")

                for idx, z in enumerate(target_zips):
                    rows = search_public_topics(
                        search_mode,
                        category_or_topic.strip(),
                        z,
                        area_label.strip(),
                        max_pages,
                        use_google,
                        public_pages_only,
                    )

                    for row in rows:
                        row["search_mode"] = search_mode
                        row["search_keyword"] = category_or_topic.strip()
                        row["source_zip"] = z
                        row["area_label"] = area_label.strip()
                        row["run_by"] = user_email
                        row["front_end_ad_pack_choice"] = ad_pack_choice

                    all_rows.extend(rows)
                    progress.progress((idx + 1) / len(target_zips), text=f"Public search {idx + 1}/{len(target_zips)}")

                progress.empty()

            raw_count = len(all_rows)

            if not all_rows:
                st.warning("No results found.")

                if search_mode in PUBLIC_SEARCH_MODES:
                    st.info(
                        "No public results came back for this run. Try a broader phrase, increase Public search pages, or turn off Public pages only."
                    )
            else:
                df = pd.DataFrame(all_rows)
                before_dedupe_count = len(df)

                df = dedupe_dataframe(df)
                after_dedupe_count = len(df)

                df = sort_by_score_if_present(df)

                if trim_results:
                    df = df.head(int(final_cap)).copy()

                final_count = len(df)

                df = add_display_columns(df)

                st.session_state.results_df = df
                st.session_state.last_run_meta = {
                    "search_mode": search_mode,
                    "keyword": category_or_topic.strip(),
                    "area_label": area_label.strip(),
                    "scan_mode": scan_mode,
                    "radius": radius,
                    "run_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "run_by": user_email,
                    "ad_pack_choice": ad_pack_choice,
                }

                st.success(f"Found {len(df)} results.")

                if show_debug:
                    d1, d2, d3, d4 = st.columns(4)
                    d1.metric("Raw Rows", raw_count)
                    d2.metric("Before Dedupe", before_dedupe_count)
                    d3.metric("After Dedupe", after_dedupe_count)
                    d4.metric("Final Rows", final_count)

                render_results_card(df, title="Lead Results")

                csv_bytes = df.to_csv(index=False).encode("utf-8")
                excel_bytes = get_excel_bytes(df)

                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        "Download Search Results CSV",
                        data=csv_bytes,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_results_csv",
                    )
                with d2:
                    st.download_button(
                        "Download Search Results Excel",
                        data=excel_bytes,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="download_results_excel",
                    )

        except Exception as e:
            st.error(f"Error: {e}")


# =========================================================
# TAB 2
# =========================================================
with tab2:
    render_section_header(
        "Build a Client Package",
        "Turn current results into client-ready CSV, Excel, CRM, and ZIP exports.",
    )

    if st.session_state.results_df.empty:
        st.info("Run a search first in the Campaign Search tab.")
    else:
        df = sort_by_score_if_present(st.session_state.results_df.copy())
        df = add_display_columns(df)
        meta = st.session_state.last_run_meta or {}

        c1, c2, c3 = st.columns(3)
        with c1:
            package_name = st.text_input(
                "Package Name",
                value="MWH Lead Package",
                key="package_name_input"
            )
        with c2:
            prepared_by = st.text_input(
                "Prepared By",
                value=user_name or user_email,
                key="prepared_by_input"
            )
        with c3:
            max_rows_default = max(1, min(250, len(df)))

            max_rows = st.number_input(
                "Max Leads in Package",
                min_value=1,
                max_value=5000,
                value=max_rows_default,
                step=1,
                key="package_max_rows",
            )

        st.markdown("### What Package Should You Pitch?")

        default_pack = meta.get("ad_pack_choice", "Google Ads")
        package_options = [
            "SEO",
            "Google Ads",
            "OTT",
            "Social Media Ads",
            "Retargeting",
            "Local SEO + Google Ads",
            "Full Funnel Package",
        ]

        if default_pack not in package_options:
            default_pack = "Google Ads"

        ad_pack_choice = st.selectbox(
            "What ad pack should you offer?",
            package_options,
            index=package_options.index(default_pack),
            help="Choose the package you want reps to pitch in the client package area.",
            key="tab2_ad_pack_choice",
        )

        render_ad_pack_helper(ad_pack_choice)
        meta["ad_pack_choice"] = ad_pack_choice
        st.session_state.last_run_meta = meta

        package_df = df.head(int(max_rows)).copy()
        client_df = get_client_export_df(package_df)
        crm_df = get_crm_export_df(package_df)

        summary_text = build_summary_text(
            package_df,
            package_name=package_name,
            prepared_by=prepared_by,
            search_mode=meta.get("search_mode", ""),
            keyword=meta.get("keyword", ""),
            area_label=meta.get("area_label", ""),
        )

        manifest = build_manifest(
            package_name=package_name,
            prepared_by=prepared_by,
            row_count=len(package_df),
            meta=meta,
        )

        st.text_area("Package Summary", value=summary_text, height=220, key="package_summary_text")
        render_results_card(package_df, title="Package Preview")

        client_csv = client_df.to_csv(index=False).encode("utf-8")
        crm_csv = crm_df.to_csv(index=False).encode("utf-8")
        client_excel = get_excel_bytes(client_df)
        zip_bytes = get_package_zip_bytes(client_df, crm_df, summary_text, manifest)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button(
                "Client CSV",
                data=client_csv,
                file_name=f"{package_name.lower().replace(' ', '_')}_client.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_client_csv",
            )
        with d2:
            st.download_button(
                "CRM CSV",
                data=crm_csv,
                file_name=f"{package_name.lower().replace(' ', '_')}_crm.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_crm_csv",
            )
        with d3:
            st.download_button(
                "Client Excel",
                data=client_excel,
                file_name=f"{package_name.lower().replace(' ', '_')}_client.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_client_excel",
            )
        with d4:
            st.download_button(
                "Full ZIP Package",
                data=zip_bytes,
                file_name=f"{package_name.lower().replace(' ', '_')}_package.zip",
                mime="application/zip",
                use_container_width=True,
                key="download_full_zip",
            )


# =========================================================
# TAB 3
# =========================================================
with tab3:
    render_section_header(
        "Expansion Planner",
        "Generate public-intent and market-interest phrases to expand discovery coverage.",
    )

    planner_mode = st.selectbox(
        "Planner Mode",
        PUBLIC_SEARCH_MODES,
        index=0,
        key="planner_mode_select",
    )

    planner_topic = st.text_input(
        "Main Keyword",
        value="roofing company",
        key="planner_topic",
    )
    planner_zip = st.text_input("ZIP", value="66048", key="planner_zip")
    planner_area = st.text_input("Area Label", value="Leavenworth", key="planner_area")

    phrases = expand_topic_queries(
        planner_mode,
        planner_topic.strip(),
        planner_zip.strip(),
        planner_area.strip(),
    )

    render_section_header(
        suggestion_title(planner_mode),
        "Use these to widen discovery without lowering relevance too aggressively.",
    )

    if phrases:
        st.markdown("\n".join([f"- `{phrase}`" for phrase in phrases]))
    else:
        st.info("Enter a keyword and area to generate phrase ideas.")


st.markdown("---")
st.caption("Internal Midwest Horizons workspace for public business discovery, enrichment, scoring, and export.")
