"""Generates the Top-10 / Top-30 local HTML Sleeper Digest (works via file://)."""
import datetime
import html
import pathlib
import sqlite3


def build_digest(conn: sqlite3.Connection, out_path: pathlib.Path, limit: int = 30) -> pathlib.Path:
    rows = conn.execute(
        """SELECT * FROM lots WHERE sleeper_score > 0
           ORDER BY sleeper_score DESC, first_seen_utc DESC LIMIT ?""",
        (limit,),
    ).fetchall()

    now_aest = (datetime.datetime.utcnow() + datetime.timedelta(hours=10)).strftime("%Y-%m-%d %H:%M AEST")
    cards = []
    for idx, r in enumerate(rows, 1):
        badge = "TOP 10 — LOOK FIRST" if idx <= 10 else "SHORTLIST (11–30)"
        cards.append(f"""
        <tr>
          <td><strong>#{idx}</strong><br><small>{badge}</small></td>
          <td><strong>{r['sleeper_score']}</strong></td>
          <td><a href="{html.escape(r['lot_url'])}" target="_blank">{html.escape(r['title'])}</a><br>
              <small>{html.escape(r['match_reason'])}</small></td>
          <td>{html.escape(r['house_name'])} ({html.escape(r['house_country'])})</td>
          <td>{html.escape(r['estimate'])}</td>
          <td>{html.escape(r['sale_date'])}</td>
        </tr>""")

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Michael's Art Tracker — Overseas Sleeper Digest</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#F7F5F0;color:#1C1B18;margin:40px;}}
h1{{margin-bottom:4px;}} .meta{{color:#666;margin-bottom:24px;}}
table{{width:100%;border-collapse:collapse;background:#fff;}}
th,td{{padding:12px 14px;border-bottom:1px solid #E5E0D5;text-align:left;vertical-align:top;}}
th{{background:#1C1B18;color:#FAF7F2;font-size:12px;text-transform:uppercase;letter-spacing:.05em;}}
a{{color:#1B4D3E;font-weight:600;text-decoration:none;}} a:hover{{text-decoration:underline;}}
</style></head><body>
<h1>Michael's Art Tracker — Overseas Sleeper Digest</h1>
<div class="meta">Generated {now_aest} · Top {len(rows)} ranked lots</div>
<table>
<thead><tr><th>Rank</th><th>Score</th><th>Lot &amp; Match Reason</th><th>House</th><th>Estimate</th><th>Sale Date</th></tr></thead>
<tbody>{"".join(cards) if cards else '<tr><td colspan="6">No scored lots yet. Run <code>python3 tracker.py --sweep</code> to fetch Class B houses.</td></tr>'}</tbody>
</table></body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8")
    return out_path
