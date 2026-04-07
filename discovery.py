import time
from typing import Dict, List, Tuple

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
            str(row.get("title", "")).strip().lower(),
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
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def split_keyword_phrases(keyword: str) -> List[str]:
    raw = str(keyword or "").strip()
    if not raw:
        return []

    if "," in raw:
        return dedupe_strings([part.strip() for part in raw.split(",")])

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
            "url": details.get("website", ""),
            "phone": details.get("formatted_phone_number") or details.get("international_phone_number", ""),
            "rating": details.get("rating", item.get("rating", "")),
            "ratings_total": details.get("user_ratings_total", item.get("user_ratings_total", "")),
            "google_maps_url": details.get("url", ""),
            "place_id": place_id,
            "types": ", ".join(details.get("types", item.get("types", []))),
            "title": details.get("name") or item.get("name", ""),
            "snippet": "",
            "domain": "",
            "score": "",
        })

    return dedupe_rows(rows)


def expand_topic_queries(search_mode: str, keyword: str, zip_code: str = "", area_label: str = "") -> List[str]:
    mode = str(search_mode or "").strip().lower()
    area = str(area_label or zip_code or "").strip()
    base = str(keyword or "").strip()

    if not base:
        if mode == "public intent search":
            base = "roofing company"
        elif mode == "relocation interest finder":
            base = "moving to town"
        elif mode == "community interest finder":
            base = "community events"
        else:
            base = "local services"

    extra_phrases = split_keyword_phrases(base)

    if mode == "public intent search":
        phrases = []
        for phrase in extra_phrases:
            phrases.extend([
                phrase,
                f"{phrase} near me",
                f"{phrase} {area}".strip(),
                f"best {phrase} {area}".strip(),
                f"{phrase} services {area}".strip(),
            ])

    elif mode == "relocation interest finder":
        phrases = [
            f"moving to {area}".strip(),
            f"relocation to {area}".strip(),
            f"homes for sale {area}".strip(),
            f"apartments in {area}".strip(),
            f"utilities in {area}".strip(),
            f"schools in {area}".strip(),
        ]
        if base:
            phrases.append(f"{base} {area}".strip())

    elif mode == "community interest finder":
        phrases = [
            f"events in {area}".strip(),
            f"things to do in {area}".strip(),
            f"community groups in {area}".strip(),
            f"local organizations in {area}".strip(),
            f"volunteer opportunities in {area}".strip(),
        ]
        if base:
            phrases.append(f"{base} {area}".strip())

    else:
        phrases = [base, f"{base} {area}".strip()]

    return dedupe_strings([p for p in phrases if p.strip()])


def search_public_topics(
    search_mode: str,
    keyword: str,
    zip_code: str,
    area_label: str,
    max_pages: int,
    use_google: bool,
    public_pages_only: bool,
) -> List[Dict]:
    area = str(area_label or zip_code or "").strip()
    mode = str(search_mode or "").strip()

    queries = expand_topic_queries(
        mode,
        keyword,
        zip_code=zip_code,
        area_label=area,
    )

    limit = max(1, min(int(max_pages or 4), 10))

    rows = []
    for i, query in enumerate(queries[:limit], start=1):
        rows.append({
            "name": f"{mode} {i}",
            "business_type": mode,
            "search_keyword": query,
            "search_area": area,
            "address": area,
            "website": "",
            "url": "",
            "phone": "",
            "rating": "",
            "ratings_total": "",
            "google_maps_url": "",
            "place_id": "",
            "types": mode,
            "title": query.title(),
            "snippet": f"Suggested {mode.lower()} topic for {area}.",
            "domain": "",
            "score": 1,
        })

    return dedupe_rows(rows)