#!/usr/bin/env python3
"""au-art-tracker v2 — Daily 3am AEST & Manual On-Demand Overseas Sleeper Hunter."""
import argparse
import datetime
import pathlib
from aut.db import get_conn, init_db
from aut.adapters import fetch_house_lots
from aut.matcher import score_lot
from aut.digest import build_digest

ROOT = pathlib.Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "tracker.db"
ARTISTS_JSON = ROOT / "data" / "artists_master.json"
HOUSES_JSON = ROOT / "data" / "houses_master.json"
REPORT_PATH = ROOT / "reports" / "latest.html"


def run_sweep(limit: int = 50, house_filter: str = "") -> None:
    conn = get_conn(DB_PATH)
    artists = [dict(r) for r in conn.execute("SELECT * FROM artists").fetchall()]
    if house_filter:
        houses = [dict(r) for r in conn.execute(
            "SELECT * FROM houses WHERE lower(name) LIKE ? LIMIT ?", (f"%{house_filter.lower()}%", limit)
        ).fetchall()]
    else:
        houses = [dict(r) for r in conn.execute(
            """SELECT * FROM houses WHERE coverage_class LIKE 'B%'
               ORDER BY CASE WHEN coverage_class LIKE 'B-Priority%' THEN 0 ELSE 1 END, id LIMIT ?""",
            (limit,),
        ).fetchall()]

    now_utc = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    new_hits = 0
    for h in houses:
        lots, code, err = fetch_house_lots(h)
        inserted = 0
        for lot in lots:
            sc, m_artist, reason = score_lot(lot, artists)
            if sc > 0:
                cur = conn.execute(
                    """INSERT OR IGNORE INTO lots
                       (lot_url, house_name, house_country, sale_date, title, artist_listed,
                        description, medium, estimate, currency, matched_artist, match_reason, sleeper_score, first_seen_utc)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (lot["lot_url"], lot["house_name"], lot["house_country"], lot["sale_date"],
                     lot["title"], lot["artist_listed"], lot["description"], lot["medium"],
                     lot["estimate"], lot["currency"], m_artist, reason, sc, now_utc),
                )
                if cur.rowcount > 0:
                    inserted += 1
                    new_hits += 1
        conn.execute(
            "INSERT INTO fetch_log(run_utc, house_name, status_code, new_lots, error_msg) VALUES (?, ?, ?, ?, ?)",
            (now_utc, h["name"], code, inserted, err),
        )
    conn.commit()
    build_digest(conn, REPORT_PATH)
    conn.close()
    print(f"Sweep complete: checked {len(houses)} houses, {new_hits} new sleeper hits -> {REPORT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Australian Art Overseas Sleeper Tracker")
    parser.add_argument("--init-db", action="store_true", help="Initialize SQLite FTS5 DB from master JSONs")
    parser.add_argument("--sweep", action="store_true", help="Run polite Class-B sweep")
    parser.add_argument("--limit", type=int, default=50, help="Max houses to fetch")
    parser.add_argument("--house", type=str, default="", help="Filter by single house name")
    parser.add_argument("--report-only", action="store_true", help="Regenerate HTML digest from local DB")
    args = parser.parse_args()

    if args.init_db:
        res = init_db(DB_PATH, ARTISTS_JSON, HOUSES_JSON)
        print(f"Initialized DB: {res}")
    elif args.report_only:
        conn = get_conn(DB_PATH)
        out = build_digest(conn, REPORT_PATH)
        conn.close()
        print(f"Digest written to {out}")
    elif args.sweep or args.house:
        run_sweep(limit=args.limit, house_filter=args.house)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
