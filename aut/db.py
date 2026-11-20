"""SQLite + FTS5 storage for au-art-tracker."""
import json
import pathlib
import sqlite3
from typing import Any

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country TEXT DEFAULT 'Australia',
    category TEXT DEFAULT 'Artist',
    tier TEXT DEFAULT 'standard',
    years TEXT DEFAULT '',
    variant_count INTEGER DEFAULT 1,
    variants_json TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS houses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT DEFAULT 'Unknown',
    website TEXT DEFAULT '',
    domain TEXT DEFAULT '',
    coverage_class TEXT DEFAULT 'B (Own-Site Direct)',
    platform TEXT DEFAULT 'Bespoke / CMS',
    access_route TEXT DEFAULT 'index_diff',
    etag TEXT DEFAULT '',
    last_modified TEXT DEFAULT '',
    consecutive_failures INTEGER DEFAULT 0,
    last_checked_utc TEXT DEFAULT '',
    UNIQUE(domain, name)
);

CREATE TABLE IF NOT EXISTS lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_url TEXT NOT NULL UNIQUE,
    house_name TEXT NOT NULL,
    house_country TEXT DEFAULT '',
    sale_date TEXT DEFAULT 'UNKNOWN',
    title TEXT NOT NULL,
    artist_listed TEXT DEFAULT '',
    description TEXT DEFAULT '',
    medium TEXT DEFAULT '',
    estimate TEXT DEFAULT 'UNKNOWN',
    currency TEXT DEFAULT 'UNKNOWN',
    image_url TEXT DEFAULT '',
    matched_artist TEXT DEFAULT '',
    match_reason TEXT DEFAULT '',
    sleeper_score INTEGER DEFAULT 0,
    first_seen_utc TEXT NOT NULL,
    status TEXT DEFAULT 'NEW'
);

CREATE VIRTUAL TABLE IF NOT EXISTS lots_fts USING fts5(
    title, artist_listed, description, medium, house_name,
    content='lots', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS lots_ai AFTER INSERT ON lots BEGIN
    INSERT INTO lots_fts(rowid, title, artist_listed, description, medium, house_name)
    VALUES (new.id, new.title, new.artist_listed, new.description, new.medium, new.house_name);
END;

CREATE TABLE IF NOT EXISTS fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_utc TEXT NOT NULL,
    house_name TEXT NOT NULL,
    status_code INTEGER DEFAULT 0,
    new_lots INTEGER DEFAULT 0,
    error_msg TEXT DEFAULT ''
);
"""


def get_conn(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: pathlib.Path, artists_json: pathlib.Path, houses_json: pathlib.Path) -> dict[str, int]:
    conn = get_conn(db_path)
    conn.executescript(SCHEMA_SQL)
    artists = json.loads(artists_json.read_text(encoding="utf-8"))
    houses = json.loads(houses_json.read_text(encoding="utf-8"))

    a_count = 0
    for a in artists:
        conn.execute(
            """INSERT OR IGNORE INTO artists(name, country, category, tier, years, variant_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (a["name"], a.get("country", "Australia"), a.get("category", "Artist"),
             a.get("tier", "standard"), a.get("years", ""), a.get("variant_count", 1)),
        )
        a_count += 1

    h_count = 0
    for h in houses:
        conn.execute(
            """INSERT OR IGNORE INTO houses(name, country, website, domain, coverage_class, platform)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (h["name"], h.get("country", "Unknown"), h.get("website", ""),
             h.get("domain", ""), h.get("coverage_class", "B (Own-Site Direct)"),
             h.get("platform", "Bespoke / CMS")),
        )
        h_count += 1

    conn.commit()
    conn.close()
    return {"artists_loaded": a_count, "houses_loaded": h_count}
