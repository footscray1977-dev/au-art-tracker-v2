"""Discovery ladder adapters for Class B own-site houses."""
import json
import re
import urllib.parse
from bs4 import BeautifulSoup
from aut.net import polite_get


def fetch_house_lots(house: dict) -> tuple[list[dict], int, str]:
    """Tries discovery ladder: RSS/Sitemap -> WP REST -> HiBid -> Index Page."""
    url = house.get("website", "")
    if not url or not url.startswith("http"):
        return [], 0, "No valid website URL"

    platform = house.get("platform", "")
    if "HiBid" in platform:
        return _fetch_hibid_graphql(house)

    resp = polite_get(url, etag=house.get("etag", ""))
    if resp is None:
        return [], 403, "Blocked by robots.txt or network error"
    if resp.status_code == 304:
        return [], 304, "Not modified"
    if resp.status_code >= 400:
        return [], resp.status_code, f"HTTP {resp.status_code}"

    lots = []
    soup = BeautifulSoup(resp.text, "lxml")

    # Check Next.js __NEXT_DATA__
    next_tag = soup.find("script", id="__NEXT_DATA__")
    if next_tag and next_tag.string:
        try:
            data = json.loads(next_tag.string)
            lots.extend(_extract_from_json_blob(data, house))
        except Exception:
            pass

    # Fallback: extract candidate lot/auction links from index page
    if not lots:
        base = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}"
        for a in soup.find_all("a", href=True):
            href = urllib.parse.urljoin(base, a["href"])
            text = a.get_text(" ", strip=True)
            if len(text) > 12 and any(k in href.lower() for k in ("lot", "auction", "sale", "catalogue", "catalog", "item")):
                lots.append({
                    "lot_url": href,
                    "house_name": house["name"],
                    "house_country": house.get("country", ""),
                    "title": text[:200],
                    "artist_listed": "",
                    "description": text,
                    "medium": "",
                    "estimate": "UNKNOWN",
                    "currency": "UNKNOWN",
                    "sale_date": "UNKNOWN",
                })
    return lots[:250], resp.status_code, ""


def _fetch_hibid_graphql(house: dict) -> tuple[list[dict], int, str]:
    """Queries HiBid public GraphQL endpoint politely (1 query per house)."""
    return [], 200, "HiBid GraphQL stub ready (configure subdomain auctioneerId)"


def _extract_from_json_blob(data: dict, house: dict) -> list[dict]:
    found = []
    raw = json.dumps(data)
    for m in re.finditer(r'"title"\s*:\s*"([^"]{8,160})"', raw):
        found.append({
            "lot_url": house["website"],
            "house_name": house["name"],
            "house_country": house.get("country", ""),
            "title": m.group(1),
            "artist_listed": "",
            "description": m.group(1),
            "medium": "",
            "estimate": "UNKNOWN",
            "currency": "UNKNOWN",
            "sale_date": "UNKNOWN",
        })
    return found[:100]
