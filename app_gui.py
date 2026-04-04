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
# FIX WHITE-ON-WHITE DROPDOWNS / INPUTS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
    }

    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }

    div[role="listbox"] {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
    }

    div[role="option"] {
        background-color: #111827 !important;
        color: #ffffff !important;
    }

    div[role="option"]:hover {
        background-color: #1f2937 !important;
        color: #ffffff !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #374151 !important;
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
        "Public Intent Search": ("TOPIC / KEYWORD", "need a roofer"),
        "Relocation Interest Finder": ("TARGET AREA", "moving to chicago"),
        "Community Interest Finder": ("COMMUNITY / INTEREST", "small business owners"),
    }
    return defaults.get(search_mode, ("KEYWORD", "roofing"))


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

    # -----------------------------
    # Best contact name
    # -----------------------------
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

    # -----------------------------
    # Pitch summary
    # -----------------------------
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

    # -----------------------------
    # Ad package recommendation
    # -----------------------------
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
            zip_code = st.text_input("ZIP CODE", value="66048")
            zip_list_text = ""
        else:
            zip_code = ""
            zip_list_text = st.text_area("ZIP LIST", value="66048, 66044, 66086", height=120)

        radius = st.number_input("RADIUS (miles)", min_value=1, max_value=100, value=10, step=1)
        area_label = st.text_input("CITY / AREA LABEL", value="Leavenworth")

        search_mode = st.selectbox(
            "Search Mode",
            [
                "Marketing Prospect Finder",
                "Custom Business Search",
                "Public Intent Search",
                "Relocation Interest Finder",
                "Community Interest Finder",
            ],
            index=0,
        )

        label, default_value = default_prompt(search_mode)
        category_or_topic = st.text_input(label, value=default_value)

        if search_mode in ["Public Intent Search", "Relocation Interest Finder", "Community Interest Finder"]:
            with st.expander("Suggested public search phrases"):
                for phrase in expand_topic_queries(
                    search_mode,
                    category_or_topic.strip(),
                    zip_code=zip_code.strip(),
                    area_label=area_label.strip(),
                ):
                    st.code(phrase, language=None)

        run_search = st.button("FIND LEADS", use_container_width=True)

    with right_col:
        render_section_header(
            "Search Options",
            "Google key is stored in app secrets. Reps only need to run searches.",
        )

        use_google = st.checkbox("Use Google API if available", value=True)
        use_osm = st.checkbox("Use OpenStreetMap backup", value=False)
        do_enrich = st.checkbox("Find public business contact info", value=True)
        enrich_limit = st.number_input("Max rows to enrich", min_value=0, max_value=5000, value=100, step=25)
        do_score = st.checkbox("Score business leads", value=True)
        trim_results = st.checkbox("Trim final results", value=False)
        final_cap = st.selectbox("Final result cap", [100, 250, 500, 1000, 2500, 5000], index=2)
        show_debug = st.checkbox("Show debug counts", value=True)

        public_pages_only = st.checkbox("Public pages only", value=True)
        max_pages = st.slider("Public search pages", 1, 10, 4)

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

            if search_mode in ["Marketing Prospect Finder", "Custom Business Search"]:
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

                    all_rows.extend(rows)
                    progress.progress((idx + 1) / len(target_zips), text=f"Public search {idx + 1}/{len(target_zips)}")

                progress.empty()

            raw_count = len(all_rows)

            if not all_rows:
                st.warning("No results found.")
                if search_mode in ["Public Intent Search", "Relocation Interest Finder", "Community Interest Finder"]:
                    st.info(
                        "This usually means the issue is inside search_public_topics(...) or the query is too narrow. "
                        "Try increasing Public search pages, turning off Public pages only, or testing a broader phrase like "
                        "'moving', 'relocation', or 'interstate movers'."
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
                    )
                with d2:
                    st.download_button(
                        "Download Search Results Excel",
                        data=excel_bytes,
                        file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
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
            package_name = st.text_input("Package Name", value="MWH Lead Package")
        with c2:
            prepared_by = st.text_input("Prepared By", value=user_name or user_email)
        with c3:
            max_rows = st.number_input("Max Leads in Package", min_value=10, max_value=5000, value=min(250, len(df)), step=10)

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

        st.text_area("Package Summary", value=summary_text, height=220)
        render_results_card(package_df, title="Package Preview")

        client_csv = client_df.to_csv(index=False).encode("utf-8")
        crm_csv = crm_df.to_csv(index=False).encode("utf-8")
        client_excel = get_excel_bytes(client_df)
        zip_bytes = get_package_zip_bytes(client_df, crm_df, summary_text, manifest)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button("Client CSV", data=client_csv, file_name=f"{package_name.lower().replace(' ', '_')}_client.csv", mime="text/csv", use_container_width=True)
        with d2:
            st.download_button("CRM CSV", data=crm_csv, file_name=f"{package_name.lower().replace(' ', '_')}_crm.csv", mime="text/csv", use_container_width=True)
        with d3:
            st.download_button("Client Excel", data=client_excel, file_name=f"{package_name.lower().replace(' ', '_')}_client.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with d4:
            st.download_button("Full ZIP Package", data=zip_bytes, file_name=f"{package_name.lower().replace(' ', '_')}_package.zip", mime="application/zip", use_container_width=True)


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
        [
            "Public Intent Search",
            "Relocation Interest Finder",
            "Community Interest Finder",
        ],
        index=0,
    )
    planner_topic = st.text_input("Main Keyword", value="need a roofer")
    planner_zip = st.text_input("ZIP", value="66048")
    planner_area = st.text_input("Area Label", value="Leavenworth")

    phrases = expand_topic_queries(
        planner_mode,
        planner_topic.strip(),
        planner_zip.strip(),
        planner_area.strip(),
    )

    render_section_header(
        "Suggested Search Phrases",
        "Use these to widen discovery without lowering relevance too aggressively.",
    )

    for phrase in phrases:
        st.code(phrase, language=None)


st.markdown("---")
st.caption("Internal Midwest Horizons workspace for public business discovery, enrichment, scoring, and export.")
