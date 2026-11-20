"""Polite HTTP client with robots.txt, ETag caching, and per-domain jitter."""
import random
import time
import urllib.parse
import urllib.robotparser
from typing import Optional
import requests

ROBOTS_UA = "au-art-tracker"
USER_AGENT = "au-art-tracker/2.0 (personal research; polite; +https://github.com/footscray1977-dev)"
_LAST_HIT: dict[str, float] = {}
_ROBOTS_CACHE: dict[str, urllib.robotparser.RobotFileParser] = {}


def can_fetch(url: str, timeout: int = 8) -> bool:
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in _ROBOTS_CACHE:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            resp = requests.get(f"{base}/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=timeout)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                rp.allow_all = True
        except Exception:
            rp.allow_all = True
        _ROBOTS_CACHE[base] = rp
    return _ROBOTS_CACHE[base].can_fetch(ROBOTS_UA, url)


def polite_get(url: str, etag: str = "", min_delay: float = 2.0, max_delay: float = 5.0, timeout: int = 15) -> Optional[requests.Response]:
    if not can_fetch(url):
        return None
    domain = urllib.parse.urlparse(url).netloc.lower()
    elapsed = time.time() - _LAST_HIT.get(domain, 0.0)
    target_delay = random.uniform(min_delay, max_delay)
    if elapsed < target_delay:
        time.sleep(target_delay - elapsed)

    headers = {"User-Agent": USER_AGENT}
    if etag:
        headers["If-None-Match"] = etag

    for attempt in range(3):
        try:
            _LAST_HIT[domain] = time.time()
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code in (429, 503):
                time.sleep(2 ** (attempt + 1))
                continue
            return resp
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None
