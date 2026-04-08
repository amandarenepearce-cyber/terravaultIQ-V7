import math
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

CATEGORY_VARIANTS = {
    "roofers": ["roofers", "roofing contractor", "roofing company"],
    "cleaning companies": ["cleaning companies", "house cleaning service", "maid service"],
    "med spas": ["med spas", "medical spa"],
    "mortgage lenders": ["mortgage lenders", "home loan lender", "loan officer"],
    "credit unions": ["credit unions", "bank"],
    "contractors": ["contractors", "general contractor", "home remodeling contractor"],
    "real estate agents": ["real estate agents", "realtor", "real estate broker"],
    "property management": ["property management", "property manager"],
    "apartments": ["apartments", "apartment complex", "rental community"],
    "plumbers": ["plumbers", "plumbing company"],
    "electricians": ["electricians", "electrical contractor"],
    "painters": ["painters", "painting contractor"],
    "restaurants": ["restaurants", "restaurant"],
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


def nearby_search(
    api_key: str,
    keyword: str,
    lat: float,
    lng: float,
    radius_m: int,
    max_pages: int = 3,
) -> List[dict]:
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    results = []
    next_page_token = None

    for _ in range(max_pages):
        params = {
            "location": f"{lat},{lng}",
            "radius": radius_m,
            "keyword": keyword,
            "key": api_key,
        }
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
            raise ValueError(f"Google Nearby Search error: {status}")

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


def keyword_variants(keyword: str) -> List[str]:
    base = normalize_keyword(keyword)
    variants = [base]

    if base in CATEGORY_VARIANTS:
        variants.extend(CATEGORY_VARIANTS[base])

    raw = str(keyword or "").strip().lower()
    if raw and raw != base:
        variants.append(raw)

    return dedupe_strings(variants)


def meters_to_lat_delta(meters: float) -> float:
    return meters / 111320.0


def meters_to_lng_delta(meters: float, lat: float) -> float:
    cos_lat = math.cos(math.radians(lat))
    cos_lat = max(cos_lat, 0.2)
    return meters / (111320.0 * cos_lat)


def build_search_grid(lat: float, lng: float, radius_m: int) -> List[Tuple[float, float]]:
    """
    Create a grid of search points so the app can exceed the ~60-result ceiling
    of a single Places query. Wider radii get more tiles.
    """
    if radius_m <= 8000:
        return [(lat, lng)]

    step_m = min(12000, max(4000, radius_m / 3))
    lat_step = meters_to_lat_delta(step_m)
    lng_step = meters_to_lng_delta(step_m, lat)

    layers = max(1, min(4, int(radius_m / step_m)))
    points = []

    for x in range(-layers, layers + 1):
        for y in range(-layers, layers + 1):
            points.append((lat + x * lat_step, lng + y * lng_step))

    return points


def discover_businesses(
    zip_code: str,
    radius: float,
    mode: str,
    keyword: str,
    use_google: bool,
    use_osm: bool,
) -> List[Dict]:
    api_key = st.secrets.get("GOOGLE_API_KEY", "").strip()

    if not use_google:
        return []

    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in app secrets.")

    area = zip_code.strip()
    radius_m = int(float(radius) * 1609.34)

    lat, lng, formatted_area = geocode_google(api_key, area)
    grid_points = build_search_grid(lat, lng, radius_m)

    all_items = []
    for variant in keyword_variants(keyword):
        for point_lat, point_lng in grid_points:
            try:
                items = nearby_search(
                    api_key=api_key,
                    keyword=variant,
                    lat=point_lat,
                    lng=point_lng,
                    radius_m=min(radius_m, 25000),
                    max_pages=3,
                )
                all_items.extend(items)
            except Exception:
                continue

    rows = []
    for item in dedupe_rows([
        {
            "name": item.get("name", ""),
            "address": item.get("vicinity", "") or item.get("formatted_address", ""),
            "website": "",
            "url": "",
            "title": item.get("name", ""),
            "place_id": item.get("place_id", ""),
            "_raw": item,
        }
        for item in all_items
    ]):
        place_id = item.get("place_id", "")
        raw_item = item.get("_raw", {})
        details = get_place_details(api_key, place_id) if place_id else {}

        normalized_keyword = normalize_keyword(keyword)

        rows.append({
            "name": details.get("name") or raw_item.get("name", ""),
            "business_type": normalized_keyword,
            "search_keyword": normalized_keyword,
            "search_area": formatted_area,
            "address": details.get("formatted_address") or raw_item.get("vicinity", "") or raw_item.get("formatted_address", ""),
            "website": details.get("website", ""),
            "url": details.get("website", ""),
            "phone": details.get("formatted_phone_number") or details.get("international_phone_number", ""),
            "rating": details.get("rating", raw_item.get("rating", "")),
            "ratings_total": details.get("user_ratings_total", raw_item.get("user_ratings_total", "")),
            "google_maps_url": details.get("url", ""),
            "place_id": place_id,
            "types": ", ".join(details.get("types", raw_item.get("types", []))),
            "title": details.get("name") or raw_item.get("name", ""),
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
            f"homes for sale in {area}".strip(),
            f"apartments in {area}".strip(),
            f"cost of living in {area}".strip(),
            f"best neighborhoods in {area}".strip(),
            f"schools in {area}".strip(),
            f"utilities in {area}".strip(),
        ]
        if base:
            phrases.extend([
                f"{base} {area}".strip(),
                f"{base} near {area}".strip(),
            ])

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


def _estimate_audience_size(search_mode: str, intent_phrase: str, area: str) -> int:
    phrase = str(intent_phrase or "").lower()
    mode = str(search_mode or "").lower()
    area_bonus = min(max(len(str(area or "").strip()) * 12, 0), 240)

    score = 180
    if "relocation" in mode:
        score += 450
    if "moving to" in phrase or "moving from" in phrase:
        score += 650
    if "homes for sale" in phrase or "apartments" in phrase:
        score += 500
    if "realtor" in phrase or "real estate" in phrase:
        score += 350
    if "cost of living" in phrase or "neighborhood" in phrase or "schools" in phrase:
        score += 220
    if "near me" in phrase or "best " in phrase:
        score += 110

    estimate = score + area_bonus
    return int(round(estimate / 25.0) * 25)


def _quality_label(estimate: int) -> str:
    if estimate >= 1400:
        return "strong"
    if estimate >= 700:
        return "fair"
    return "weak"


def _confidence_label(search_mode: str, intent_phrase: str) -> str:
    phrase = str(intent_phrase or "").lower()
    if "moving to" in phrase or "moving from" in phrase or "relocation" in phrase:
        return "high"
    if "homes for sale" in phrase or "apartments" in phrase or "realtor" in phrase:
        return "medium"
    return "medium" if str(search_mode or "").lower() == "relocation interest finder" else "low"


def _move_direction(intent_phrase: str) -> str:
    phrase = str(intent_phrase or "").lower()
    if "moving to" in phrase or "relocation to" in phrase:
        return "into"
    if "moving from" in phrase or "relocation from" in phrase:
        return "out_of"
    return "both"


def _relocation_type(intent_phrase: str, keyword: str) -> str:
    text = f"{intent_phrase} {keyword}".lower()
    if "pcs" in text or "military" in text or "fort" in text:
        return "military"
    if "retire" in text or "retirement" in text:
        return "retirement"
    if "job" in text or "work" in text or "corporate" in text:
        return "corporate"
    if "apartment" in text or "rent" in text:
        return "renter"
    if "home" in text or "realtor" in text or "sale" in text:
        return "buyer"
    return "general"


def _recommended_channel(search_mode: str, intent_phrase: str) -> str:
    phrase = str(intent_phrase or "").lower()
    mode = str(search_mode or "").lower()

    if mode == "relocation interest finder":
        if "moving to" in phrase or "homes for sale" in phrase or "apartments" in phrase:
            return "Google Search"
        if "schools" in phrase or "neighborhood" in phrase or "cost of living" in phrase:
            return "Meta + Retargeting"
        return "Google Search + Meta"

    if mode == "community interest finder":
        return "Meta"
    return "Google Search"


def _recommended_offer(search_mode: str, intent_phrase: str) -> str:
    phrase = str(intent_phrase or "").lower()
    mode = str(search_mode or "").lower()

    if mode == "relocation interest finder":
        if "homes for sale" in phrase:
            return "New resident home list"
        if "apartments" in phrase:
            return "Rental guide"
        if "schools" in phrase:
            return "School district guide"
        if "cost of living" in phrase:
            return "Cost of living guide"
        if "neighborhood" in phrase:
            return "Neighborhood map"
        return "Free relocation guide"

    if mode == "community interest finder":
        return "Local guide"
    return "Free estimate"


def _landing_page_angle(search_mode: str, intent_phrase: str, area: str) -> str:
    phrase = str(intent_phrase or "").lower()
    area = str(area or "").strip()

    if str(search_mode or "").lower() == "relocation interest finder":
        if "homes for sale" in phrase:
            return f"Moving to {area}? Browse local homes."
        if "apartments" in phrase:
            return f"Relocating to {area}? Start with rentals."
        if "schools" in phrase:
            return f"Thinking about {area}? Compare school options."
        if "cost of living" in phrase:
            return f"See what it really costs to live in {area}."
        if "neighborhood" in phrase:
            return f"Find the best neighborhoods in {area}."
        return f"Moving to {area}? Start with a relocation guide."

    return f"Find trusted options in {area}."


def _build_public_intent_row(search_mode: str, query: str, area: str, base_keyword: str) -> Dict:
    estimate = _estimate_audience_size(search_mode, query, area)
    quality = _quality_label(estimate)
    confidence = _confidence_label(search_mode, query)

    return {
        "name": query.title(),
        "business_type": search_mode,
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
        "types": search_mode,
        "title": query.title(),
        "snippet": f"Modeled audience signal for {area}. Use this phrase for campaign planning and audience targeting.",
        "domain": "",
        "score": estimate,
        "intent_phrase": query,
        "intent_type": "local_service_intent",
        "move_direction": "",
        "relocation_type": "",
        "target_market": area,
        "estimated_audience_size": estimate,
        "confidence": confidence,
        "quality_label": quality,
        "recommended_channel": _recommended_channel(search_mode, query),
        "recommended_offer": _recommended_offer(search_mode, query),
        "landing_page_angle": _landing_page_angle(search_mode, query, area),
        "pitch_opening_line": f"People in and around {area} are likely searching phrases like '{query}'.",
        "pitch_offer": f"Recommended offer: {_recommended_offer(search_mode, query)} via {_recommended_channel(search_mode, query)}.",
        "pitch_cta": f"Build a landing page and ad group around '{query}' for {area}.",
        "pitch_reason": f"Modeled {quality} demand based on search-intent phrasing.",
        "pitch_angle": base_keyword or query,
        "needs_leads_score": estimate,
        "needs_leads_tier": "Hot" if quality == "strong" else "Warm" if quality == "fair" else "Cold",
        "needs_leads_reason": f"Audience estimate {estimate} with {confidence} confidence.",
    }


def _build_relocation_row(query: str, area: str, base_keyword: str) -> Dict:
    estimate = _estimate_audience_size("relocation interest finder", query, area)
    quality = _quality_label(estimate)
    confidence = _confidence_label("relocation interest finder", query)
    move_direction = _move_direction(query)
    relocation_type = _relocation_type(query, base_keyword)

    offer = _recommended_offer("relocation interest finder", query)
    channel = _recommended_channel("relocation interest finder", query)
    landing_page = _landing_page_angle("relocation interest finder", query, area)

    return {
        "name": query.title(),
        "business_type": "Relocation Interest Audience",
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
        "types": "relocation audience",
        "title": query.title(),
        "snippet": f"Modeled relocation-intent audience for {area}. Best used for ads, landing pages, and retargeting rather than direct outreach.",
        "domain": "",
        "score": estimate,
        "intent_phrase": query,
        "intent_type": "relocation_intent",
        "move_direction": move_direction,
        "relocation_type": relocation_type,
        "target_market": area,
        "estimated_audience_size": estimate,
        "confidence": confidence,
        "quality_label": quality,
        "recommended_channel": channel,
        "recommended_offer": offer,
        "landing_page_angle": landing_page,
        "pitch_opening_line": f"People showing relocation interest toward {area} may respond to '{query}'.",
        "pitch_offer": f"Best next move: run {channel} with a '{offer}' offer.",
        "pitch_cta": f"Use a destination page: {landing_page}",
        "pitch_reason": f"Relocation audience modeled as {quality} quality with {confidence} confidence.",
        "pitch_angle": "relocation",
        "needs_leads_score": estimate,
        "needs_leads_tier": "Hot" if quality == "strong" else "Warm" if quality == "fair" else "Cold",
        "needs_leads_reason": f"Audience estimate {estimate}; move_direction={move_direction}; relocation_type={relocation_type}.",
        "audience_name": f"{area} Relocation Intent Audience",
        "market_region": area,
        "channel": channel,
        "audience_type": "privacy_safe_modeled_audience",
        "warning_status": "under_100" if estimate < 100 else "ok",
    }


def _build_community_row(query: str, area: str, base_keyword: str) -> Dict:
    estimate = _estimate_audience_size("community interest finder", query, area)
    quality = _quality_label(estimate)
    confidence = _confidence_label("community interest finder", query)

    return {
        "name": query.title(),
        "business_type": "Community Interest Audience",
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
        "types": "community audience",
        "title": query.title(),
        "snippet": f"Modeled community-interest audience for {area}. Good for awareness and local engagement campaigns.",
        "domain": "",
        "score": estimate,
        "intent_phrase": query,
        "intent_type": "community_interest",
        "move_direction": "",
        "relocation_type": "",
        "target_market": area,
        "estimated_audience_size": estimate,
        "confidence": confidence,
        "quality_label": quality,
        "recommended_channel": "Meta",
        "recommended_offer": "Local guide",
        "landing_page_angle": f"See what is happening in {area}.",
        "pitch_opening_line": f"People interested in {area} may engage with '{query}'.",
        "pitch_offer": "Lead with a local guide or event roundup.",
        "pitch_cta": f"Build an awareness campaign around '{query}'.",
        "pitch_reason": f"Modeled {quality} community-interest demand.",
        "pitch_angle": base_keyword or query,
        "needs_leads_score": estimate,
        "needs_leads_tier": "Hot" if quality == "strong" else "Warm" if quality == "fair" else "Cold",
        "needs_leads_reason": f"Audience estimate {estimate} with {confidence} confidence.",
    }


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
    base_keyword = str(keyword or "").strip()

    queries = expand_topic_queries(
        mode,
        base_keyword,
        zip_code=zip_code,
        area_label=area,
    )

    limit = max(1, min(int(max_pages or 4), 10))
    selected_queries = queries[:limit]

    rows = []
    for query in selected_queries:
        mode_lower = mode.lower()
        if mode_lower == "relocation interest finder":
            rows.append(_build_relocation_row(query, area, base_keyword))
        elif mode_lower == "community interest finder":
            rows.append(_build_community_row(query, area, base_keyword))
        else:
            rows.append(_build_public_intent_row(mode, query, area, base_keyword))

    return dedupe_rows(rows)
