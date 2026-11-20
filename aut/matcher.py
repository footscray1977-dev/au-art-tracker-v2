"""Local 3-pass matcher & Sleeper Score engine (Nov 2026 rules: prints IN, bark paintings OUT)."""
import difflib
import re
import unicodedata

try:
    from rapidfuzz import fuzz
    def _token_ratio(a: str, b: str) -> float:
        return fuzz.token_set_ratio(a, b)
except ImportError:
    def _token_ratio(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a, b).ratio() * 100.0

EXCLUDED_RX = re.compile(
    r"\b(bark painting|aboriginal bark|didgeridoo|boomerang|churinga|woomera|"
    r"taschen|franklin mint|lladro|royal doulton|hummel|coin|sovereign|postage stamp)\b",
    re.I,
)

IN_SCOPE_MEDIA_RX = re.compile(
    r"\b(oil|acrylic|tempera|watercolour|watercolor|gouache|pastel|drawing|charcoal|"
    r"pencil|ink|sculpture|bronze|ceramic|pottery|photograph|etching|lithograph|"
    r"screenprint|linocut|woodcut|woodblock|engraving|drypoint|print)\b",
    re.I,
)

SUBJECT_TERMS = [
    "gum tree", "gum trees", "eucalypt", "eucalyptus", "she-oak", "wattle",
    "outback", "billabong", "shearing", "stockman", "drover", "australian",
    "sydney", "melbourne", "tasmania", "hobart", "queensland", "bushland",
]

MISATTRIBUTION_TERMS = [
    "continental", "british school", "english school", "european school",
    "unknown artist", "unidentified", "unsigned", "attributed to",
    "in the manner of", "circle of", "follower of", "school of", "possibly",
]


def normalize(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", ascii_str.lower()).strip()


def score_lot(lot: dict, artists: list[dict]) -> tuple[int, str, str]:
    """Returns (sleeper_score, matched_artist, match_reason)."""
    blob = " ".join([
        lot.get("title", ""),
        lot.get("artist_listed", ""),
        lot.get("description", ""),
        lot.get("medium", ""),
    ])
    if EXCLUDED_RX.search(blob):
        return -100, "", "Excluded item/bark/memorabilia"

    norm_blob = normalize(blob)
    norm_artist_field = normalize(lot.get("artist_listed", "") or lot.get("title", ""))

    score = 0
    reasons = []
    matched_artist = ""

    # Pass 1: Exact or high-confidence fuzzy artist match (+30)
    for a in artists:
        a_norm = normalize(a["name"])
        if not a_norm:
            continue
        if f" {a_norm} " in f" {norm_blob} " or _token_ratio(a_norm, norm_artist_field) >= 88:
            matched_artist = a["name"]
            score += 30
            reasons.append(f"Watchlist match: {matched_artist} (+30)")
            break

    # Pass 2: Surname-only fallback (+15) if no full match
    if not matched_artist:
        for a in artists:
            parts = normalize(a["name"]).split()
            if len(parts) >= 2 and len(parts[-1]) >= 5:
                surname = parts[-1]
                if re.search(rf"\b{re.escape(surname)}\b", norm_artist_field):
                    matched_artist = a["name"]
                    score += 15
                    reasons.append(f"Surname match: {surname} (+15)")
                    break

    # Pass 3: Australian subject terms & Misattribution (+15)
    subj_hits = [t for t in SUBJECT_TERMS if t in norm_blob]
    if len(subj_hits) >= 2:
        score += 15
        reasons.append(f"AU subjects ({', '.join(subj_hits[:3])}) (+15)")
    elif len(subj_hits) == 1:
        score += 8
        reasons.append(f"AU subject ({subj_hits[0]}) (+8)")

    mis_hits = [t for t in MISATTRIBUTION_TERMS if t in norm_blob]
    if mis_hits:
        score += 15
        reasons.append(f"Misattribution cue ({mis_hits[0]}) (+15)")

    # Overseas bonus (+10)
    country = (lot.get("house_country") or "").lower()
    if country and "australia" not in country:
        score += 10
        reasons.append(f"Overseas ({lot.get('house_country')}) (+10)")

    # Medium in scope (+5)
    if IN_SCOPE_MEDIA_RX.search(blob):
        score += 5
        reasons.append("In-scope medium (+5)")

    # Signed cue (+5)
    if re.search(r"\bsigned\b|\bsignature\b", norm_blob):
        score += 5
        reasons.append("Signed/signature noted (+5)")

    # Provenance/exhibition penalty (-5)
    if re.search(r"\bprovenance\b|\bexhibited\b|\bliterature\b|\bcatalogue raisonne\b", norm_blob):
        score -= 5
        reasons.append("Catalogued provenance (-5)")

    return score, matched_artist, "; ".join(reasons)
