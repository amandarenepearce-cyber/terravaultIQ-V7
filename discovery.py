import time
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import requests
import streamlit as st


HEADERS = {"User-Agent": "TerraVaultIQ/1.0"}

BUSINESS_PRESETS = {
    "roofing": "roofers",
    "roofers": "roofers",
    "cleaners": "cleaning companies",
    "cleaning": "cleaning companies",
    "house cleaners": "house cleaning service",
    "cleaning companies": "cleaning companies",
    "med spa": "med spas",
    "med spas": "med spas",
    "lawn care": "lawn care",
    "landscape lighting": "landscape lighting",
    "holiday lighting installer": "holiday lighting installer",
    "christmas light installation": "christmas light installation",
    "mortgage lenders": "mortgage lenders",
    "credit unions": "credit unions",
    "loan officers": "loan officers",
    "contractors": "contractors",
    "real estate": "real estate agents",
    "salons": "hair salons",
    "dentists": "dentists",
    "property managers": "property management",
    "apartments": "apartments",
    "plumbers": "plumbers",
    "electricians": "electricians",
    "painters": "painters",
    "restaurants": "restaurants",
}

PUBLIC_TOPIC_PRESETS = {
    "public intent search": [
        "{keyword}",
        "{keyword} near me",
        "best {keyword} {area}",
        "{keyword} services {area}",
        "top rated {keyword} {area}",
        "affordable {keyword} {area}",
    ],
    "relocation finder": [
        "moving to {area}",
        "relocation to {area}",
        "homes for sale {area}",
        "apartments in {area}",
        "utilities in {area}",
        "schools in {area}",
        "{keyword} {area}",
    ],
    "community interest finder": [
        "{keyword} {area}",
        "events in {area}",
        "things to do in {area}",
        "community groups in {area}",
        "local organizations in {area}",
        "volunteer opportunities in {area}",
    ],
}


def normalize_keyword(keyword: str) -> str:
    raw = str(keyword or "").strip().lower()
    return BUSINESS_PRESETS.get(raw, raw)


def geocode_google(api_key: str, place: str) -> Tuple[float, float, str]:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": place, "key": api_key}
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Google Geocoding error: {data.get('status', 'unknown')}")

    result = data["results"][0]
    loc = result["geometry"]["location"]
    return loc["lat"], loc["lng"], result["formatted_address"]


def places_search(api_key: str, query: str, lat: float, lng: float, radius_m: int, max_pages: int = 3) -> List[dict]:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []
    next_page_token = None

    for _ in range(max_pages):
        params = {"query": query, "location": f"{lat},{lng}", "radius": radius_m, "key": api_key}
        if next_page_token:
            time.sleep(2.5)
            params = {"pagetoken": next_page_token, "key": api_key}

        r = requests.get(url, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        status = data.get("status")

        if status not in ("OK", "ZERO_RESULTS"):
            if status == "INVALID_REQUEST" and next_page_token:
                continue
            raise ValueError(f"Google Places error: {status}")

        results.extend(data.get("results", []))
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

    return results


def get_place_details(api_key: str, place_id: str) -> dict:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    fields = ",".join([
        "name",
        "website",
        "formatted_phone_number",
        "international_phone_number",
        "formatted_address",
        "url",
        "rating",
        "user_ratings_total",
        "types",
    ])
    params = {"place_id": place_id, "fields": fields, "key": api_key}
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "OK":
        return {}
    return data.get("result", {})


def dedupe_rows(rows: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for row in rows:
        key = (
            str(row.get("name", "")).strip().lower(),
            str(row.get("address", "")).strip().lower(),
            str(row.get("website", "")).strip().lower(),
            str(row.get("url", "")).strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def dedupe_strings(values: List[str]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        v = str(value or "").strip()
        if not v:
            continue
        k = v.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(v)
    return out


def split_keyword_phrases(keyword: str) -> List[str]:
    raw = str(keyword or "").strip()
    if not raw:
        return []

    if "," in raw:
        return dedupe_strings([part.strip() for part in raw.split(",")])

    # If user pasted a long roofing-style phrase blob, split to useful variants
    lower = raw.lower()
    known_chunks = [
        "roof repair",
        "roofing contractor",
        "roof replacement",
        "roofing company",
        "emergency roof repair",
        "roofer",
        "moving company",
        "local movers",
        "interstate movers",
        "relocation services",
        "community events",
        "things to do",
        "local organizations",
        "volunteer opportunities",
    ]

    found = [chunk for chunk in known_chunks if chunk in lower]
    if found:
        return dedupe_strings(found)

    return [raw]


def discover_businesses(zip_code: str, radius: float, mode: str, keyword: str, use_google: bool, use_osm: bool) -> List[Dict]:
    api_key = st.secrets.get("GOOGLE_API_KEY", "").strip()

    if not use_google:
        return []

    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in app secrets.")

    search_keyword = normalize_keyword(keyword)
    area = zip_code.strip()
    radius_m = int(float(radius) * 1609.34)

    lat, lng, formatted_area = geocode_google(api_key, area)
    query = f"{search_keyword} in {formatted_area}"
    search_results = places_search(api_key, query, lat, lng, radius_m)

    rows = []
    for item in search_results:
        place_id = item.get("place_id", "")
        details = get_place_details(api_key, place_id) if place_id else {}

        rows.append({
            "name": details.get("name") or item.get("name", ""),
            "business_type": search_keyword,
            "search_keyword": search_keyword,
            "search_area": formatted_area,
            "address": details.get("formatted_address") or item.get("formatted_address", ""),
            "website": details.get("website", ""),
            "phone": details.get("formatted_phone_number") or details.get("international_phone_number", ""),
            "rating": details.get("rating", item.get("rating", "")),
            "ratings_total": details.get("user_ratings_total", item.get("user_ratings_total", "")),
            "google_maps_url": details.get("url", ""),
            "place_id": place_id,
            "types": ", ".join(details.get("types", item.get("types", []))),
        })

    return dedupe_rows(rows)


def get_cse_credentials() -> Tuple[str, str]:
    api_key = st.secrets.get("GOOGLE_CSE_API_KEY", "").strip()
    cx = st.secrets.get("GOOGLE_CSE_CX", "").strip()
    return api_key, cx


def google_cse_search(api_key: str, cx: str, query: str, start: int = 1, num: int = 10) -> List[Dict]:
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "start": start,
        "num": min(max(num, 1), 10),
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("items", [])


def is_public_page(url: str) -> bool:
    lowered = str(url or "").lower()
    if not lowered.startswith(("http://", "https://")):
        return False

    blocked_tokens = [
        "/wp-admin",
        "/cart",
        "/checkout",
        "/my-account",
        "/account",
        "/login",
        "/signin",
        "/sign-in",
        "/register",
        "/portal",
        "/dashboard",
        "/privacy",
        "/terms",
        "/feed",
        ".pdf",
    ]
    return not any(token in lowered for token in blocked_tokens)


def domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def score_public_result(title: str, snippet: str, query: str, area_label: str) -> int:
    score = 0
    haystack = f"{title} {snippet}".lower()
    q = str(query or "").lower().strip()
    area = str(area_label or "").lower().strip()

    for token in q.split():
        if token and token in haystack:
            score += 3

    if q and q in haystack:
        score += 8

    if area and area in haystack:
        score += 4

    return score


def normalize_public_row(item: Dict, phrase: str, search_mode: str, area_label: str) -> Dict:
    url = item.get("link", "")
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    pagemap = item.get("pagemap", {}) or {}
    metatags = (pagemap.get("metatags") or [{}])[0] if isinstance(pagemap.get("metatags"), list) else {}
    site_name = metatags.get("og:site_name", "") if isinstance(metatags, dict) else ""

    return {
        "name": title or site_name or domain_from_url(url),
        "business_type": search_mode,
        "search_keyword": phrase,
        "search_area": area_label,
        "address": "",
        "website": url,
        "url": url,
        "phone": "",
        "rating": "",
        "ratings_total": "",
        "google_maps_url": "",
        "place_id": "",
        "types": search_mode,
        "title": title,
        "snippet": snippet,
        "domain": domain_from_url(url),
        "score": score_public_result(title, snippet, phrase, area_label),
    }


def expand_topic_queries(search_mode: str, keyword: str, zip_code: str = "", area_label: str = "") -> List[str]:
    mode = str(search_mode or "").strip().lower()
    area = str(area_label or zip_code or "").strip()
    phrases = split_keyword_phrases(keyword)

    templates = PUBLIC_TOPIC_PRESETS.get(mode, PUBLIC_TOPIC_PRESETS["public intent search"])
    queries = []

    for phrase in phrases:
        for template in templates:
            queries.append(template.format(keyword=phrase, area=area).strip())

    if not queries:
        base = str(keyword or "").strip()
        queries = [
            f"{base} near me",
            f"best {base} {area}".strip(),
            f"{base} services {area}".strip(),
            f"top rated {base} {area}".strip(),
            f"affordable {base} {area}".strip(),
        ]

    return dedupe_strings([q for q in queries if q.strip()])


def search_public_topics(
    search_mode: str,
    keyword: str,
    zip_code: str,
    area_label: str,
    max_pages: int,
    use_google: bool,
    public_pages_only: bool,
) -> List[Dict]:
    if not use_google:
        return []

    api_key, cx = get_cse_credentials()
    if not api_key or not cx:
        raise ValueError("Missing GOOGLE_CSE_API_KEY or GOOGLE_CSE_CX in app secrets.")

    area = str(area_label or zip_code or "").strip()
    queries = expand_topic_queries(search_mode, keyword, zip_code=zip_code, area_label=area)

    # max_pages in UI is treated as search breadth control, not literal Google pagination pages
    max_queries = max(1, min(int(max_pages or 4), len(queries)))
    queries_to_run = queries[:max_queries]

    rows = []
    for query in queries_to_run:
        items = google_cse_search(api_key, cx, query, start=1, num=10)

        for item in items:
            row = normalize_public_row(item, query, search_mode, area)

            if public_pages_only and not is_public_page(row.get("url", "")):
                continue

            rows.append(row)

    rows = dedupe_rows(rows)
    rows.sort(key=lambda r: (r.get("score", 0), r.get("name", "")), reverse=True)
    return rows