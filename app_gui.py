import io
import json
import os
from datetime import datetime
from typing import Dict, List

import pandas as pd
import streamlit as st
from PIL import Image

from discovery import discover_businesses, search_public_topics, expand_topic_queries
from enrichment import enrich_rows
from scoring import score_rows
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

st.markdown(
    """
    <style>
    :root {
        --tv-bg: #f4f7f5;
        --tv-surface: #ffffff;
        --tv-surface-soft: #f8faf9;
        --tv-text: #0f172a;
        --tv-muted: #64748b;
        --tv-border: #d9e2dd;
        --tv-green: #166534;
        --tv-green-2: #0f6b3b;
        --tv-green-soft: #eef6f2;
        --tv-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: var(--tv-bg) !important;
        color: var(--tv-text) !important;
    }

    .block-container {
        max-width: 1320px !important;
        padding-top: 1.25rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }

    section.main > div {
        padding-right: 0.5rem !important;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 1.5rem !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: var(--tv-text);
    }

    .tv-hero,
    .tv-card,
    .tv-strategy-card {
        background: var(--tv-surface) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 24px !important;
        box-shadow: var(--tv-shadow) !important;
        padding: 1.5rem 1.6rem !important;
        margin-bottom: 1rem !important;
    }

    .tv-hero h1 {
        font-size: 2.2rem !important;
        line-height: 1.05 !important;
        margin: 0 0 0.65rem 0 !important;
        color: var(--tv-text) !important;
    }

    .tv-hero p,
    .tv-card-sub {
        color: var(--tv-muted) !important;
        font-size: 1rem !important;
    }

    .tv-pill,
    .tv-chip {
        display: inline-block !important;
        background: var(--tv-green-soft) !important;
        color: var(--tv-green) !important;
        border: 1px solid #cfe3d7 !important;
        border-radius: 999px !important;
        padding: 0.35rem 0.7rem !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.85rem !important;
        margin-right: 0.4rem !important;
    }

    .accent {
        color: var(--tv-green) !important;
    }

    .tv-strategy-title {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.65rem !important;
    }

    .tv-strategy-body {
        color: var(--tv-muted) !important;
        line-height: 1.55 !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 14px !important;
        box-shadow: none !important;
        background-image: none !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder,
    .stNumberInput input::placeholder {
        color: var(--tv-muted) !important;
        opacity: 1 !important;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-baseweb="select"] > div {
        width: 100% !important;
        min-height: 3.25rem !important;
        box-sizing: border-box !important;
        background: var(--tv-surface) !important;
        background-color: var(--tv-surface) !important;
        background-image: none !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 14px !important;
        box-shadow: none !important;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] *,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] *,
    div[data-baseweb="select"] * {
        color: var(--tv-text) !important;
        -webkit-text-fill-color: var(--tv-text) !important;
        fill: var(--tv-text) !important;
    }

    div[data-baseweb="popover"] {
        background: transparent !important;
    }

    div[data-baseweb="menu"],
    ul[role="listbox"],
    div[role="listbox"] {
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12) !important;
        padding: 4px !important;
    }

    div[data-baseweb="menu"] *,
    ul[role="listbox"] *,
    div[role="listbox"] * {
        color: var(--tv-text) !important;
        fill: var(--tv-text) !important;
        -webkit-text-fill-color: var(--tv-text) !important;
    }

    li[role="option"],
    div[role="option"] {
        background: var(--tv-surface) !important;
        color: var(--tv-text) !important;
        border-radius: 8px !important;
    }

    li[role="option"]:hover,
    div[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    div[role="option"][aria-selected="true"] {
        background: var(--tv-green-soft) !important;
        color: var(--tv-text) !important;
    }

    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button,
    button[kind="primary"],
    button[kind="secondary"] {
        background: linear-gradient(90deg, var(--tv-green-2) 0%, var(--tv-green) 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        min-height: 3.35rem !important;
        font-weight: 700 !important;
        box-shadow: 0 8px 20px rgba(22, 101, 52, 0.18) !important;
    }

    .stButton > button *,
    .stDownloadButton > button *,
    .stFormSubmitButton > button *,
    button[kind="primary"] *,
    button[kind="secondary"] * {
        color: #ffffff !important;
    }

    .stRadio label,
    .stCheckbox label,
    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stTextArea label,
    .stNumberInput label,
    .stSlider label {
        color: var(--tv-text) !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetric"] {
        background: var(--tv-surface) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 22px !important;
        padding: 1rem 1.2rem !important;
        box-shadow: var(--tv-shadow) !important;
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {
        color: var(--tv-text) !important;
    }

    [data-testid="stDataFrame"] {
        background: var(--tv-surface) !important;
        border: 1px solid var(--tv-border) !important;
        border-radius: 18px !important;
        overflow: hidden !important;
    }

    .tv-helper-card {
        background: linear-gradient(180deg, rgba(15,23,42,0.96) 0%, rgba(2,6,23,0.98) 100%) !important;
        border: 1px solid rgba(51, 65, 85, 0.95) !important;
        border-radius: 18px !important;
        padding: 16px 18px !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
    }

    .tv-helper-title {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        margin-bottom: 8px !important;
        color: #ffffff !important;
    }

    .tv-helper-label {
        color: #86efac !important;
        font-weight: 700 !important;
        margin-top: 8px !important;
        margin-bottom: 2px !important;
    }

    .tv-helper-copy {
        color: #e5e7eb !important;
        line-height: 1.5 !important;
    }

    .tv-kicker {
        display: inline-block !important;
        padding: 4px 10px !important;
        border-radius: 999px !important;
        background: rgba(20, 83, 45, 0.25) !important;
        border: 1px solid rgba(34, 197, 94, 0.45) !important;
        color: #dcfce7 !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        margin-bottom: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "results_df" not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

if "last_run_meta" not in st.session_state:
    st.session_state.last_run_meta = {}


BUSINESS_SEARCH_MODES = [
    "Marketing Prospect Finder",
    "Custom Business Search",
]

PUBLIC_SEARCH_MODES = [
    "Public Intent Search",
    "Relocation Interest Finder",
    "Community Interest Finder",
]

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
    "Relocation Capture Package": {
        "best_for": "Realtors, movers, lenders, and apartments targeting people likely planning a move.",
        "why": "Turns modeled relocation signals into search, social, and landing-page campaigns built around move intent.",
        "rep_talk_track": "This package helps you show up when people are researching a move and gives them a reason to convert with a guide, home list, or quote.",
    },
}


# =========================================================
# AUTH
# =========================================================
favicon_path = os.path.join("assets", "favicon.png")

if not st.user.is_logged_in:
    st.markdown("""
    <div class="tv-hero">
        <div class="tv-pill">TerraVaultIQ • Midwest Horizons Internal</div>
        <h1>In-house<br><span class="accent">Lead Engine</span></h1>
        <p>Sign in with your Midwest Horizons Google account to access lead discovery, scoring, enrichment, and export tools.</p>
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
# FALLBACKS
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
            <h1>Build and activate<br><span class="accent">hyper-targeted<br>audiences</span></h1>
            <p>Internal V7 workspace for Midwest Horizons. Signed in as {user_name or user_email}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, top_b = st.columns([8, 1])
    with top_b:
        st.button("Log out", on_click=st.logout, use_container_width=True)


def render_section_header(title: str, subtitle: str = ""):
    subtitle_html = f'<div class="tv-card-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="tv-card"><h2>{title}</h2>{subtitle_html}</div>', unsafe_allow_html=True)


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


def recommend_frontend_pack(search_mode: str, keyword: str) -> str:
    text = f"{search_mode} {keyword}".lower()
    if "relocation interest finder" in text:
        return "Relocation Capture Package"
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
# DATA HELPERS
# =========================================================
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
    work = work.drop_duplicates(subset=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"], keep="first")
    work = work.drop(columns=["_dedupe_name", "_dedupe_address", "_dedupe_website", "_dedupe_phone"], errors="ignore")
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


def is_public_audience_df(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    if "intent_phrase" in df.columns:
        return True
    if "search_mode" in df.columns:
        modes = set(df["search_mode"].dropna().astype(str))
        return any(mode in PUBLIC_SEARCH_MODES for mode in modes)
    return False


def add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    work = df.copy()
    possible_contact_cols = ["best_contact_name", "contact_name", "primary_contact_name", "owner_name", "decision_maker"]
    if "best_contact_name" not in work.columns:
        work["best_contact_name"] = ""

    for col in possible_contact_cols:
        if col in work.columns:
            vals = work[col].fillna("").astype(str).str.strip()
            work["best_contact_name"] = work["best_contact_name"].mask(work["best_contact_name"].eq("") & vals.ne(""), vals)

    opening = work["pitch_opening_line"].fillna("").astype(str).str.strip() if "pitch_opening_line" in work.columns else pd.Series([""] * len(work), index=work.index)
    offer = work["pitch_offer"].fillna("").astype(str).str.strip() if "pitch_offer" in work.columns else pd.Series([""] * len(work), index=work.index)
    cta = work["pitch_cta"].fillna("").astype(str).str.strip() if "pitch_cta" in work.columns else pd.Series([""] * len(work), index=work.index)
    work["pitch_summary"] = (opening + " | " + offer + " | " + cta).str.strip(" |")

    score_series = pd.to_numeric(work["needs_leads_score"], errors="coerce") if "needs_leads_score" in work.columns else pd.Series([0] * len(work), index=work.index)
    keyword_series = work["search_keyword"].fillna("").astype(str).str.lower() if "search_keyword" in work.columns else pd.Series([""] * len(work), index=work.index)
    mode_series = work["search_mode"].fillna("").astype(str).str.lower() if "search_mode" in work.columns else pd.Series([""] * len(work), index=work.index)
    type_series = work["business_type"].fillna("").astype(str).str.lower() if "business_type" in work.columns else pd.Series([""] * len(work), index=work.index)
    website_series = work["website"].fillna("").astype(str).str.strip() if "website" in work.columns else pd.Series([""] * len(work), index=work.index)

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

        if "relocation interest finder" in combined_text or any(term in combined_text for term in relocation_terms):
            return ("Relocation Capture Package", "$1,500-$3,500 + ad spend", "Built for campaigns targeting people researching a move into or out of a market.")
        if any(term in combined_text for term in event_terms):
            return ("Grand Opening / Event Push", "$1,200-$3,000 + ad spend", "Best for time-sensitive promotions, launches, and event-driven campaigns that need urgency.")
        if score >= 85:
            return ("Full Funnel Growth Package", "$3,500-$7,500 + ad spend", "Strong fit for higher-priority leads that can support a bigger search, display, and retargeting strategy.")
        if score >= 65:
            return ("Local Visibility Package", "$2,000-$4,500 + ad spend", "Good fit for businesses that need stronger local awareness, better lead flow, and more consistent visibility.")
        if website == "":
            return ("Starter Lead Boost", "$750-$1,500 + ad spend", "Good entry package for businesses with low digital presence or missing core lead-capture assets.")
        if any(term in combined_text for term in service_terms):
            return ("Local Service Lead Package", "$1,500-$3,000 + ad spend", "A strong option for service businesses that need inbound local calls, form fills, and booked jobs.")
        return ("Starter Lead Boost", "$750-$1,500 + ad spend", "Solid starter package for testing lead generation and visibility before moving into a larger campaign.")

    package_data = work.apply(pick_package, axis=1, result_type="expand")
    package_data.columns = ["ad_package_recommendation", "ad_package_price_range", "ad_package_reason"]
    work["ad_package_recommendation"] = package_data["ad_package_recommendation"]
    work["ad_package_price_range"] = package_data["ad_package_price_range"]
    work["ad_package_reason"] = package_data["ad_package_reason"]

    work = work.drop(columns=["_score_num", "_keyword", "_search_mode", "_business_type", "_website"], errors="ignore")
    return work


# =========================================================
# STRATEGY ENGINE
# =========================================================
def infer_target_intent(row: pd.Series) -> str:
    mode = str(row.get("search_mode", "")).lower()
    phrase = str(row.get("intent_phrase", row.get("search_keyword", ""))).lower()
    business_type = str(row.get("business_type", "")).lower()
    tier = str(row.get("needs_leads_tier", "")).lower()

    if "relocation" in mode:
        if "homes for sale" in phrase:
            return "Destination home-shopping intent"
        if "apartments" in phrase or "rent" in phrase:
            return "Rental relocation intent"
        if "moving to" in phrase or "relocation to" in phrase:
            return "Move-planning intent"
        return "General relocation research intent"

    if "community" in mode:
        return "Local exploration and awareness intent"

    if "public intent" in mode:
        if "near me" in phrase or "best " in phrase:
            return "High-intent service comparison intent"
        return "Local service search intent"

    if tier == "hot":
        return "Immediate growth and lead-generation intent"

    if business_type:
        return f"{business_type.title()} growth and visibility intent"

    return "Local market activation intent"


def infer_audience_stage(row: pd.Series) -> str:
    mode = str(row.get("search_mode", "")).lower()
    phrase = str(row.get("intent_phrase", row.get("search_keyword", ""))).lower()
    tier = str(row.get("needs_leads_tier", "")).lower()

    if "relocation" in mode:
        if "homes for sale" in phrase or "apartments" in phrase:
            return "hot"
        if "moving to" in phrase or "relocation" in phrase:
            return "warm"
        return "cold"

    if "public intent" in mode:
        if "near me" in phrase or "best " in phrase:
            return "hot"
        return "warm"

    if "community" in mode:
        return "cold"

    if tier in {"hot", "warm", "cold"}:
        return tier
    return "warm"


def offer_diagnosis(row: pd.Series) -> Dict[str, str]:
    mode = str(row.get("search_mode", ""))
    offer = str(row.get("recommended_offer", "") or row.get("ad_package_recommendation", "Lead Growth Package"))
    stage = infer_audience_stage(row)

    clarity = "strong" if offer else "fair"
    outcome = "strong" if stage in {"warm", "hot"} else "fair"
    proof = "fair"
    friction = "fair"
    urgency = "fair" if stage == "hot" else "weak"

    note = (
        f"The offer is usable for {mode}, but performance improves if the next step is ultra-specific "
        f"and low-friction for a {stage} audience."
    )
    return {
        "clarity": clarity,
        "outcome": outcome,
        "proof": proof,
        "friction": friction,
        "urgency": urgency,
        "note": note,
    }


def persona_map(row: pd.Series) -> List[Dict[str, str]]:
    mode = str(row.get("search_mode", "")).lower()
    phrase = str(row.get("intent_phrase", row.get("search_keyword", "")))
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))

    if "relocation" in mode:
        return [
            {
                "persona": "Active mover",
                "what_they_want": f"Fast, local guidance for {market}",
                "objection": "Not ready to commit yet",
                "best_message": "Guide-first with low-friction next step",
            },
            {
                "persona": "Research-stage shopper",
                "what_they_want": f"Clarity on homes, rentals, schools, and neighborhoods around {market}",
                "objection": "Still comparing markets",
                "best_message": "Educational landing page + soft CTA",
            },
        ]

    if "community" in mode:
        return [
            {
                "persona": "Local explorer",
                "what_they_want": f"Useful local information about {market}",
                "objection": "Not looking to convert yet",
                "best_message": "Awareness-led guide or event roundup",
            },
            {
                "persona": "Warm local audience",
                "what_they_want": "A reason to take the next step",
                "objection": "Low urgency",
                "best_message": "Local proof + clear reason to engage",
            },
        ]

    if "public intent" in mode:
        return [
            {
                "persona": "Service shopper",
                "what_they_want": f"A trusted provider for '{phrase}'",
                "objection": "Comparing several options",
                "best_message": "Fast value + proof + easy CTA",
            },
            {
                "persona": "Comparison buyer",
                "what_they_want": "Confidence before contacting anyone",
                "objection": "Trust and price sensitivity",
                "best_message": "Proof-led and low-friction",
            },
        ]

    business = str(row.get("name", "this prospect"))
    business_type = str(row.get("business_type", "local business"))
    return [
        {
            "persona": f"{business_type.title()} owner/operator",
            "what_they_want": "More qualified leads and more consistent visibility",
            "objection": "Skeptical that marketing will work",
            "best_message": "Show missed opportunity and fast-win package",
        },
        {
            "persona": f"{business} decision-maker",
            "what_they_want": "A clear path to more calls, forms, or bookings",
            "objection": "Worried about budget and time",
            "best_message": "Simple offer, simple launch, simple proof",
        },
    ]


def angle_map(row: pd.Series) -> List[Dict[str, str]]:
    mode = str(row.get("search_mode", "")).lower()
    phrase = str(row.get("intent_phrase", row.get("search_keyword", "")))
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))
    offer = str(row.get("recommended_offer", row.get("ad_package_recommendation", "Free consultation")))

    base = [
        {
            "angle": "Pain to solution",
            "message": f"Turn the friction around '{phrase}' into a simple next step with {offer}.",
        },
        {
            "angle": "Outcome / desire",
            "message": f"Show how the customer gets a better outcome faster in {market}.",
        },
        {
            "angle": "Proof / trust",
            "message": "Lead with local credibility, clarity, and an easier decision.",
        },
    ]

    if "relocation" in mode:
        base.append(
            {
                "angle": "Location confidence",
                "message": f"Reduce uncertainty about moving to {market} with a guide, homes list, or neighborhood content.",
            }
        )
    elif "community" in mode:
        base.append(
            {
                "angle": "Local relevance",
                "message": f"Anchor the message in what is happening in {market} right now.",
            }
        )
    else:
        base.append(
            {
                "angle": "Action now",
                "message": "Use a low-friction CTA that gets the prospect to raise a hand quickly.",
            }
        )

    return base


def generate_copy_set(row: pd.Series) -> Dict[str, List[str]]:
    mode = str(row.get("search_mode", "")).lower()
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))
    phrase = str(row.get("intent_phrase", row.get("search_keyword", "")))
    offer = str(row.get("recommended_offer", row.get("ad_package_recommendation", "Free consultation")))
    business_name = str(row.get("name", "this prospect"))
    package = str(row.get("ad_package_recommendation", "Lead Growth Package"))
    target_intent = infer_target_intent(row)

    if "relocation" in mode:
        hooks = [
            f"Moving to {market}? Start here.",
            f"Planning a move to {market}?",
            f"Still comparing where to land in {market}?",
            f"Make your move to {market} easier.",
            f"Researching {market}? Start with the local guide.",
            f"Before you move to {market}, see this first.",
        ]
        headlines = [
            f"Moving to {market}? Get the Guide",
            f"Start Your {market} Move Smarter",
            f"Relocating to {market}? Begin Here",
            f"Explore Homes, Rentals, and Local Insights",
            f"Get a {market} Relocation Plan",
            f"Plan Your Move with Local Confidence",
        ]
        bodies = [
            f"Target intent: {target_intent}. Help future movers take the next step with {offer} and a clear local landing page.",
            f"Use Google Search and Meta to capture people researching {market}. Lead with clarity, not pressure.",
            f"Build trust early with a guide, home list, neighborhood map, or rental plan tied directly to what they are searching.",
        ]
        ctas = ["Get the Guide", "See Local Options", "Start Planning", "Browse Homes"]
    elif "community" in mode:
        hooks = [
            f"See what is happening in {market}.",
            f"Discover more around {market}.",
            f"Want a better local guide for {market}?",
            f"Stay connected to what matters in {market}.",
            f"Make {market} easier to explore.",
            f"Find local opportunities in {market}.",
        ]
        headlines = [
            f"Explore {market} Like a Local",
            f"Your Guide to {market}",
            f"What to Know About {market}",
            f"Find Events, Groups, and Local Highlights",
            f"See More Around {market}",
            f"Start with a Local Guide",
        ]
        bodies = [
            f"Target intent: {target_intent}. This is a softer awareness play, so lead with useful content before asking for a hard conversion.",
            f"Build engagement with a local guide, roundup, or neighborhood content package that feels helpful first.",
            f"Use Meta and remarketing to move people from curiosity to action over time.",
        ]
        ctas = ["Get the Guide", "See Local Highlights", "Learn More", "Explore Now"]
    elif "public intent" in mode:
        hooks = [
            f"{phrase.title()}? Start here.",
            f"Need help with {phrase}?",
            f"Searching for the right option in {market}?",
            f"Make the next step easier in {market}.",
            f"Local demand is already there. Capture it.",
            f"Turn search intent into booked business.",
        ]
        headlines = [
            f"{phrase.title()} in {market}",
            f"Get Better Leads from Local Search",
            f"Capture More High-Intent Searches",
            f"Show Up When Local Buyers Are Looking",
            f"Convert Search Demand into Real Leads",
            f"Build a Smarter Local Search Campaign",
        ]
        bodies = [
            f"Target intent: {target_intent}. Use a high-conviction, local landing page synced to the exact phrase people are already searching.",
            f"Lead with a clear offer, trust signal, and one simple next step so the click does not get wasted.",
            f"Best fit: search-driven campaigns with fast contact options, strong proof, and compressed copy.",
        ]
        ctas = ["Get a Quote", "Call Today", "See Options", "Book Now"]
    else:
        hooks = [
            f"{business_name} looks like a strong fit for growth.",
            f"This prospect likely needs more lead flow.",
            f"Pitch the easiest win first.",
            f"Show the missed opportunity fast.",
            f"Make the next step feel simple.",
            f"Sell the package, not just the tactic.",
        ]
        headlines = [
            f"Growth Plan for {business_name}",
            f"How to Get {business_name} More Leads",
            f"Pitch {package} with a Fast Win",
            f"Turn Visibility into Real Opportunities",
            f"Build a Simpler Lead Engine",
            f"Start with a Low-Friction Offer",
        ]
        bodies = [
            f"Target intent: {target_intent}. This prospect should hear a simple, clear value proposition tied to outcomes and easy activation.",
            f"Lead with what they are missing today, then show how {package} fixes it without heavy lift.",
            f"Use proof, a clear next step, and a short path to visible results.",
        ]
        ctas = ["Book a Call", "See the Plan", "Get Started", "Request Strategy"]

    return {
        "hooks": hooks,
        "headlines": headlines,
        "primary_text": bodies,
        "ctas": ctas,
    }


def landing_page_sync(row: pd.Series) -> Dict[str, str]:
    mode = str(row.get("search_mode", "")).lower()
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))
    phrase = str(row.get("intent_phrase", row.get("search_keyword", "")))
    offer = str(row.get("recommended_offer", row.get("ad_package_recommendation", "Free consultation")))
    target_intent = infer_target_intent(row)

    if "relocation" in mode:
        return {
            "headline": f"Moving to {market}? Start Here",
            "subheadline": f"Target intent: {target_intent}. Use a guide-first page with {offer}, local context, and a low-friction form.",
            "sections": "Hero + relocation guide, local options, neighborhoods / schools / rentals, proof block, CTA form.",
            "cta": "Get the Guide",
            "bridge_note": "Match ad promise to guide or homes/rentals content immediately above the fold.",
        }

    if "community" in mode:
        return {
            "headline": f"Explore More Around {market}",
            "subheadline": f"Target intent: {target_intent}. Keep the page helpful first and conversion second.",
            "sections": "Hero + local guide, highlights/events, useful resources, community proof, soft CTA.",
            "cta": "See Local Highlights",
            "bridge_note": "Do not oversell. Reward curiosity with genuinely useful local content.",
        }

    if "public intent" in mode:
        return {
            "headline": f"{phrase.title()} in {market}",
            "subheadline": f"Target intent: {target_intent}. Sync the landing page to the exact search phrase and remove friction fast.",
            "sections": "Hero + exact phrase match, benefit bullets, trust / proof, service details, CTA strip.",
            "cta": "Get a Quote",
            "bridge_note": "The first line on the page should closely echo the ad headline and keyword intent.",
        }

    return {
        "headline": "Get More Qualified Leads Without Guessing",
        "subheadline": f"Target intent: {target_intent}. Show the prospect a simple package, clear outcome, and easy next step.",
        "sections": "Hero + outcome, quick audit/opportunity, package details, proof, CTA.",
        "cta": "Book Strategy Call",
        "bridge_note": "Keep the page simple and package-led so the rep can pitch it confidently.",
    }


def campaign_plan(row: pd.Series) -> Dict[str, str]:
    mode = str(row.get("search_mode", "")).lower()
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))
    channel = str(row.get("recommended_channel", row.get("channel", "")) or "Google Search")
    offer = str(row.get("recommended_offer", row.get("ad_package_recommendation", "Free consultation")))
    target_intent = infer_target_intent(row)
    stage = infer_audience_stage(row)

    objective = "Lead capture"
    if "community" in mode:
        objective = "Awareness and audience warming"
    elif "public intent" in mode:
        objective = "Demand capture"
    elif "relocation" in mode:
        objective = "Move-intent lead generation"
    elif mode:
        objective = "Prospect activation"

    return {
        "objective": objective,
        "target_intent": target_intent,
        "audience_stage": stage,
        "primary_channel": channel,
        "backup_channel": "Meta + Retargeting" if "Google" in channel else "Google Search",
        "offer": offer,
        "budget_note": "Start with a focused test budget tied to one offer and one primary CTA.",
        "first_test": "Test a direct CTA versus a softer low-friction CTA to see which moves this audience best.",
        "geo_note": f"Keep the campaign tightly anchored to {market} and related market terms.",
    }


def rep_talk_track(row: pd.Series) -> Dict[str, str]:
    name = str(row.get("name", "this prospect"))
    package = str(row.get("ad_package_recommendation", "Lead Growth Package"))
    target_intent = infer_target_intent(row)
    offer = str(row.get("recommended_offer", row.get("ad_package_recommendation", "Free consultation")))
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))

    return {
        "opener": f"We found a clear opportunity around {name} and the target intent signals connected to {market}.",
        "problem_frame": f"Right now the likely gap is that this demand is not being converted as efficiently as it could be. The strongest intent we found was: {target_intent}.",
        "pitch": f"The best entry point is {package}, paired with {offer} and a landing page built around that exact intent.",
        "objection_handle": "The goal is not a huge complicated launch. It is one clear package, one clear offer, and one easier next step that can start producing signal fast.",
        "close": "Would you rather start with the lower-friction guide/offer angle first, or go straight into the direct lead-generation version?",
    }


def client_ready_strategy(row: pd.Series) -> str:
    plan = campaign_plan(row)
    landing = landing_page_sync(row)
    name = str(row.get("name", "this prospect"))
    market = str(row.get("target_market", row.get("area_label", row.get("search_area", ""))))
    package = str(row.get("ad_package_recommendation", "Lead Growth Package"))

    return (
        f"{name} shows a strong opportunity in {market} built around {plan['target_intent']}. "
        f"The recommended activation is {package} using {plan['primary_channel']} as the first channel. "
        f"Lead with {plan['offer']} and bridge the message into a landing page headed '{landing['headline']}'. "
        f"The first testing move should compare a direct CTA against a softer low-friction CTA so the team can learn quickly which version converts this audience best."
    )


def generate_prospect_strategy(row: pd.Series) -> Dict:
    return {
        "target_intent": infer_target_intent(row),
        "offer_diagnosis": offer_diagnosis(row),
        "personas": persona_map(row),
        "angles": angle_map(row),
        "copy_set": generate_copy_set(row),
        "landing_page": landing_page_sync(row),
        "campaign_plan": campaign_plan(row),
        "rep_talk_track": rep_talk_track(row),
        "client_strategy": client_ready_strategy(row),
    }


def render_strategy_card(title: str, body: str):
    st.markdown(
        f"""
        <div class="tv-strategy-card">
            <div class="tv-strategy-title">{title}</div>
            <div class="tv-strategy-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# EXPORT HELPERS
# =========================================================
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

    if is_public_audience_df(df):
        preferred = [
            "name", "intent_phrase", "intent_type", "move_direction", "relocation_type",
            "target_market", "estimated_audience_size", "confidence", "quality_label",
            "recommended_channel", "recommended_offer", "landing_page_angle",
            "pitch_summary", "ad_package_recommendation", "ad_package_price_range", "ad_package_reason"
        ]
        cols = [c for c in preferred if c in df.columns]
        remainder = [c for c in df.columns if c not in cols]
        return df[cols + remainder].copy()

    preferred = [
        "name", "best_contact_name", "business_type", "search_keyword", "source_zip", "address",
        "website", "primary_email", "primary_phone", "rating", "ratings_total",
        "needs_leads_score", "needs_leads_tier", "needs_leads_reason",
        "pitch_opening_line", "pitch_offer", "pitch_cta", "pitch_summary",
        "ad_package_recommendation", "ad_package_price_range", "ad_package_reason"
    ]
    cols = [c for c in preferred if c in df.columns]
    remainder = [c for c in df.columns if c not in cols]
    return df[cols + remainder].copy()


def fallback_crm_export_df(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()

    if is_public_audience_df(df):
        out["audience_name"] = df["name"] if "name" in df.columns else ""
        out["intent_phrase"] = df["intent_phrase"] if "intent_phrase" in df.columns else ""
        out["target_market"] = df["target_market"] if "target_market" in df.columns else ""
        out["recommended_channel"] = df["recommended_channel"] if "recommended_channel" in df.columns else ""
        out["recommended_offer"] = df["recommended_offer"] if "recommended_offer" in df.columns else ""
        out["quality_label"] = df["quality_label"] if "quality_label" in df.columns else ""
        out["estimated_audience_size"] = df["estimated_audience_size"] if "estimated_audience_size" in df.columns else ""
        out["notes"] = df["pitch_summary"] if "pitch_summary" in df.columns else ""
        out["owner"] = user_email
        return out

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


def build_package_zip_fallback(client_df: pd.DataFrame, crm_df: pd.DataFrame, summary_text: str, manifest: dict) -> bytes:
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("client_leads.csv", client_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("crm_import.csv", crm_df.to_csv(index=False).encode("utf-8"))
        zf.writestr("package_summary.txt", summary_text.encode("utf-8"))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    buf.seek(0)
    return buf.read()


def get_package_zip_bytes(client_df: pd.DataFrame, crm_df: pd.DataFrame, summary_text: str, manifest: dict) -> bytes:
    if callable(build_package_zip_bytes):
        try:
            return build_package_zip_bytes(client_df, crm_df, summary_text, manifest)
        except Exception:
            pass
    return build_package_zip_fallback(client_df, crm_df, summary_text, manifest)


# =========================================================
# RESULTS RENDER
# =========================================================
def render_results_card(df: pd.DataFrame, title: str = "Lead Results"):
    df = add_display_columns(df)
    is_public_mode = is_public_audience_df(df)

    if is_public_mode:
        render_section_header(title, "Review modeled intent phrases, audience strength, recommended channels, and offer ideas.")
        estimate_series = pd.to_numeric(df.get("estimated_audience_size", pd.Series([0] * len(df))), errors="coerce").fillna(0)
        strong_count = int((df.get("quality_label", pd.Series([""] * len(df))).astype(str).str.lower() == "strong").sum())
        channel_count = int(df.get("recommended_channel", pd.Series([""] * len(df))).astype(str).replace("", pd.NA).dropna().nunique())
        avg_estimate = int(estimate_series.mean()) if len(estimate_series) else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Intent Phrases", len(df))
        m2.metric("Strong Audiences", strong_count)
        m3.metric("Avg Audience Size", avg_estimate)
        m4.metric("Channels Used", channel_count)

        preferred_cols = [
            "name", "intent_phrase", "intent_type", "move_direction", "relocation_type",
            "target_market", "estimated_audience_size", "confidence", "quality_label",
            "recommended_channel", "recommended_offer", "landing_page_angle",
            "ad_package_recommendation", "ad_package_price_range"
        ]
    else:
        render_section_header(title, "Review, score, and export client-ready lead packages.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Results", len(df))
        m2.metric("With Website", safe_metric_count(df, "website"))
        m3.metric("With Email", safe_metric_count(df, "primary_email"))
        m4.metric("Hot Leads", hot_lead_count(df))

        preferred_cols = [
            "name", "best_contact_name", "primary_email", "primary_phone", "website",
            "address", "business_type", "needs_leads_score", "needs_leads_tier",
            "ad_package_recommendation", "ad_package_price_range", "pitch_summary"
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

tab1, tab2, tab3, tab4 = st.tabs(
    ["Campaign Search", "Client Package Builder", "Expansion Planner", "Prospect Strategy Builder"]
)


# =========================================================
# TAB 1
# =========================================================
with tab1:
    left_col, right_col = st.columns([2.15, 1], gap="large")

    with left_col:
        render_section_header("Location & Keywords", "Set the search area, vertical, and campaign discovery inputs.")

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
            zip_list_text = st.text_area("ZIP LIST", value="66048, 66044, 66086", height=120, key="zip_list_multi")

        radius = st.number_input("RADIUS (miles)", min_value=1, max_value=100, value=10, step=1, key="campaign_radius")
        area_label = st.text_input("CITY / AREA LABEL", value="Leavenworth", key="campaign_area_label")

        search_mode = st.selectbox(
            "Search Mode",
            BUSINESS_SEARCH_MODES + PUBLIC_SEARCH_MODES,
            index=0,
            key="campaign_search_mode",
        )

        label, default_value = default_prompt(search_mode)
        category_or_topic = st.text_input(label, value=default_value, key="campaign_topic_keyword")

        if search_mode in PUBLIC_SEARCH_MODES:
            with st.expander(suggestion_title(search_mode), expanded=False):
                phrases = expand_topic_queries(search_mode, category_or_topic.strip(), zip_code=zip_code.strip(), area_label=area_label.strip())
                if phrases:
                    st.markdown("\n".join([f"- `{phrase}`" for phrase in phrases]))
                else:
                    st.caption("No suggestions yet. Enter a keyword or area.")

            st.info(f"{search_mode} is built for modeled audience planning, messaging, and channel recommendations rather than direct person-level outreach.")

        ad_pack_choice = recommend_frontend_pack(search_mode, category_or_topic.strip())
        run_search = st.button("FIND LEADS", use_container_width=True, key="run_search_main")

    with right_col:
        render_section_header("Search Options", "Google key is stored in app secrets. Reps only need to run searches.")
        use_google = st.checkbox("Use Google API if available", value=True, key="use_google_main")
        use_osm = st.checkbox("Use OpenStreetMap backup", value=False, key="use_osm_main")
        do_enrich = st.checkbox("Find public business contact info", value=True, key="do_enrich_main")
        enrich_limit = st.number_input("Max rows to enrich", min_value=0, max_value=5000, value=100, step=25, key="enrich_limit_main")
        do_score = st.checkbox("Score business leads", value=True, key="do_score_main")
        trim_results = st.checkbox("Trim final results", value=False, key="trim_results_main")
        final_cap = st.selectbox("Final result cap", [100, 250, 500, 1000, 2500, 5000], index=2, key="final_cap_main")
        show_debug = st.checkbox("Show debug counts", value=True, key="show_debug_main")
        public_pages_only = st.checkbox("Public pages only", value=False if search_mode in PUBLIC_SEARCH_MODES else True, key="public_pages_only_main")
        max_pages = st.slider("Public search pages", 1, 10, 6 if search_mode in PUBLIC_SEARCH_MODES else 4, key="max_pages_main")

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
                        rows = discover_businesses(z, float(radius), mode, category_or_topic.strip(), use_google, use_osm)
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
                progress = st.progress(0, text="Building audience signals...")

                for idx, z in enumerate(target_zips):
                    rows = search_public_topics(search_mode, category_or_topic.strip(), z, area_label.strip(), max_pages, use_google, public_pages_only)
                    for row in rows:
                        row["search_mode"] = search_mode
                        row["search_keyword"] = category_or_topic.strip()
                        row["source_zip"] = z
                        row["area_label"] = area_label.strip()
                        row["run_by"] = user_email
                        row["front_end_ad_pack_choice"] = ad_pack_choice
                    all_rows.extend(rows)
                    progress.progress((idx + 1) / len(target_zips), text=f"Audience build {idx + 1}/{len(target_zips)}")

                progress.empty()

            raw_count = len(all_rows)

            if not all_rows:
                st.warning("No results found.")
                if search_mode in PUBLIC_SEARCH_MODES:
                    st.info("No audience signals came back for this run. Try a broader phrase or add more search pages.")
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

                render_results_card(df, title="Audience Results" if search_mode in PUBLIC_SEARCH_MODES else "Lead Results")

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
    render_section_header("Build a Client Package", "Turn current results into client-ready CSV, Excel, CRM, and ZIP exports.")

    if st.session_state.results_df.empty:
        st.info("Run a search first in the Campaign Search tab.")
    else:
        df = sort_by_score_if_present(st.session_state.results_df.copy())
        df = add_display_columns(df)
        meta = st.session_state.last_run_meta or {}
        public_mode = is_public_audience_df(df)

        c1, c2, c3 = st.columns(3)
        with c1:
            package_name = st.text_input("Package Name", value="MWH Audience Package" if public_mode else "MWH Lead Package", key="package_name_input")
        with c2:
            prepared_by = st.text_input("Prepared By", value=user_name or user_email, key="prepared_by_input")
        with c3:
            max_rows_default = max(1, min(250, len(df)))
            max_rows = st.number_input("Max Rows in Package", min_value=1, max_value=5000, value=max_rows_default, step=1, key="package_max_rows")

        if public_mode:
            st.info("This package contains modeled audience signals and campaign-planning recommendations, not direct outreach contacts.")

        st.markdown("### What Package Should You Pitch?")
        default_pack = meta.get("ad_pack_choice", "Google Ads")
        package_options = ["SEO", "Google Ads", "OTT", "Social Media Ads", "Retargeting", "Local SEO + Google Ads", "Full Funnel Package", "Relocation Capture Package"]
        if default_pack not in package_options:
            default_pack = "Google Ads"

        ad_pack_choice = st.selectbox("What ad pack should you offer?", package_options, index=package_options.index(default_pack), help="Choose the package you want reps to pitch in the client package area.", key="tab2_ad_pack_choice")
        render_ad_pack_helper(ad_pack_choice)

        meta["ad_pack_choice"] = ad_pack_choice
        st.session_state.last_run_meta = meta

        package_df = df.head(int(max_rows)).copy()
        client_df = get_client_export_df(package_df)
        crm_df = get_crm_export_df(package_df)
        summary_text = build_summary_text(package_df, package_name=package_name, prepared_by=prepared_by, search_mode=meta.get("search_mode", ""), keyword=meta.get("keyword", ""), area_label=meta.get("area_label", ""))
        manifest = build_manifest(package_name=package_name, prepared_by=prepared_by, row_count=len(package_df), meta=meta)

        st.text_area("Package Summary", value=summary_text, height=220, key="package_summary_text")
        render_results_card(package_df, title="Package Preview")

        client_csv = client_df.to_csv(index=False).encode("utf-8")
        crm_csv = crm_df.to_csv(index=False).encode("utf-8")
        client_excel = get_excel_bytes(client_df)
        zip_bytes = get_package_zip_bytes(client_df, crm_df, summary_text, manifest)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button("Client CSV", data=client_csv, file_name=f"{package_name.lower().replace(' ', '_')}_client.csv", mime="text/csv", use_container_width=True, key="download_client_csv")
        with d2:
            st.download_button("CRM CSV", data=crm_csv, file_name=f"{package_name.lower().replace(' ', '_')}_crm.csv", mime="text/csv", use_container_width=True, key="download_crm_csv")
        with d3:
            st.download_button("Client Excel", data=client_excel, file_name=f"{package_name.lower().replace(' ', '_')}_client.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="download_client_excel")
        with d4:
            st.download_button("Full ZIP Package", data=zip_bytes, file_name=f"{package_name.lower().replace(' ', '_')}_package.zip", mime="application/zip", use_container_width=True, key="download_full_zip")


# =========================================================
# TAB 3
# =========================================================
with tab3:
    render_section_header("Expansion Planner", "Generate public-intent and market-interest phrases to expand discovery coverage.")

    planner_mode = st.selectbox("Planner Mode", PUBLIC_SEARCH_MODES, index=0, key="planner_mode_select")
    planner_topic = st.text_input("Main Keyword", value="roofing company", key="planner_topic")
    planner_zip = st.text_input("ZIP", value="66048", key="planner_zip")
    planner_area = st.text_input("Area Label", value="Leavenworth", key="planner_area")

    phrases = expand_topic_queries(planner_mode, planner_topic.strip(), planner_zip.strip(), planner_area.strip())

    render_section_header(suggestion_title(planner_mode), "Use these to widen discovery without lowering relevance too aggressively.")

    if phrases:
        st.markdown("\n".join([f"- `{phrase}`" for phrase in phrases]))
    else:
        st.info("Enter a keyword and area to generate phrase ideas.")


# =========================================================
# TAB 4 - STRATEGY BUILDER
# =========================================================
with tab4:
    render_section_header(
        "Prospect Strategy Builder",
        "Generate target intent, ad copy, landing page angles, campaign plans, and a client-ready strategy for any selected result.",
    )

    if st.session_state.results_df.empty:
        st.info("Run a search first in the Campaign Search tab to unlock strategy generation.")
    else:
        df = add_display_columns(sort_by_score_if_present(st.session_state.results_df.copy()))
        meta = st.session_state.last_run_meta or {}

        selector_labels = []
        row_lookup = {}
        for idx, row in df.iterrows():
            label = f"{idx + 1}. {row.get('name', 'Untitled')} — {row.get('ad_package_recommendation', row.get('search_mode', 'Strategy'))}"
            selector_labels.append(label)
            row_lookup[label] = row

        selected_label = st.selectbox("Choose a prospect / audience row", selector_labels, key="strategy_row_select")
        selected_row = row_lookup[selected_label]
        strategy = generate_prospect_strategy(selected_row)

        top_a, top_b, top_c, top_d = st.columns(4)
        top_a.metric("Search Mode", str(selected_row.get("search_mode", "")))
        top_b.metric("Package", str(selected_row.get("ad_package_recommendation", "")))
        top_c.metric("Target Intent", strategy["target_intent"])
        top_d.metric("Audience Stage", strategy["campaign_plan"]["audience_stage"].title())

        st.markdown("### Target Intent Snapshot")
        render_strategy_card(
            "Why this row matters",
            f"This row is best treated as **{strategy['target_intent']}**. That should shape the offer, channel, CTA, and landing-page bridge."
        )

        diag = strategy["offer_diagnosis"]
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("Clarity", diag["clarity"].title())
        d2.metric("Outcome", diag["outcome"].title())
        d3.metric("Proof", diag["proof"].title())
        d4.metric("Friction", diag["friction"].title())
        d5.metric("Urgency", diag["urgency"].title())
        st.caption(diag["note"])

        subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs(
            ["Performance Brief", "Ad Copy", "Landing Page", "Campaign Plan", "Client Strategy"]
        )

        with subtab1:
            st.markdown("### Persona and sophistication map")
            for persona in strategy["personas"]:
                render_strategy_card(
                    persona["persona"],
                    f"Wants: {persona['what_they_want']}<br><br>Objection: {persona['objection']}<br><br>Best message: {persona['best_message']}"
                )

            st.markdown("### Angle stack")
            for angle in strategy["angles"]:
                render_strategy_card(angle["angle"], angle["message"])

            st.markdown("### Rep talk track")
            talk = strategy["rep_talk_track"]
            st.write("**Opener:**", talk["opener"])
            st.write("**Problem frame:**", talk["problem_frame"])
            st.write("**Pitch:**", talk["pitch"])
            st.write("**Objection handle:**", talk["objection_handle"])
            st.write("**Close:**", talk["close"])

        with subtab2:
            copy_set = strategy["copy_set"]
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Hooks")
                for item in copy_set["hooks"]:
                    st.markdown(f"- {item}")

                st.markdown("### Headlines")
                for item in copy_set["headlines"]:
                    st.markdown(f"- {item}")

            with c2:
                st.markdown("### Primary text")
                for item in copy_set["primary_text"]:
                    st.markdown(f"- {item}")

                st.markdown("### CTA options")
                for item in copy_set["ctas"]:
                    st.markdown(f"- {item}")

        with subtab3:
            landing = strategy["landing_page"]
            st.write("**Headline:**", landing["headline"])
            st.write("**Subheadline:**", landing["subheadline"])
            st.write("**Recommended sections:**", landing["sections"])
            st.write("**Primary CTA:**", landing["cta"])
            st.write("**Message bridge note:**", landing["bridge_note"])

        with subtab4:
            plan = strategy["campaign_plan"]
            p1, p2 = st.columns(2)
            with p1:
                st.write("**Objective:**", plan["objective"])
                st.write("**Target intent:**", plan["target_intent"])
                st.write("**Audience stage:**", plan["audience_stage"])
                st.write("**Primary channel:**", plan["primary_channel"])
            with p2:
                st.write("**Backup channel:**", plan["backup_channel"])
                st.write("**Offer:**", plan["offer"])
                st.write("**Budget note:**", plan["budget_note"])
                st.write("**Geo note:**", plan["geo_note"])

            render_strategy_card("First test", plan["first_test"])

        with subtab5:
            st.markdown("### Client-ready strategy")
            st.write(strategy["client_strategy"])

            strategy_export = {
                "selected_row": selected_row.to_dict(),
                "generated_at": datetime.now().isoformat(),
                "search_meta": meta,
                "strategy": strategy,
            }
            strategy_json = json.dumps(strategy_export, indent=2)
            strategy_text = (
                f"CLIENT STRATEGY\n\n"
                f"Target Intent: {strategy['target_intent']}\n\n"
                f"{strategy['client_strategy']}\n\n"
                f"Landing Page Headline: {strategy['landing_page']['headline']}\n"
                f"Primary Channel: {strategy['campaign_plan']['primary_channel']}\n"
                f"Offer: {strategy['campaign_plan']['offer']}\n"
            )

            d1, d2 = st.columns(2)
            with d1:
                st.download_button(
                    "Download Strategy JSON",
                    data=strategy_json.encode("utf-8"),
                    file_name="prospect_strategy.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with d2:
                st.download_button(
                    "Download Strategy TXT",
                    data=strategy_text.encode("utf-8"),
                    file_name="prospect_strategy.txt",
                    mime="text/plain",
                    use_container_width=True,
                )


st.markdown("---")
st.caption("Internal Midwest Horizons workspace for public business discovery, enrichment, scoring, export, and prospect strategy generation.")
