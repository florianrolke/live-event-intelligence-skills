#!/usr/bin/env python3
"""
Build a client-facing HTML binder from conference roster CSVs.

Why a binder and not a spreadsheet
----------------------------------
A CSV is a file you send. A binder is a link you send — it opens on a phone,
it looks like you spent money on it, and it gets forwarded to the person who
actually signs. Same data, completely different reception.

It is one self-contained HTML file with the data inlined. No build step, no
server, no dependencies. Drop it on Cloudflare Pages, Netlify, or just open it
locally. There is nothing to break.

What it produces
----------------
  index.html      hero with a photo of the host city, stat tiles, section cards
  <section>.html  one searchable, sortable, filterable table per CSV

Usage
-----
    python -X utf8 -m scripts.build_event_binder \\
        --config data/example-binder.json \\
        --outdir dist/example

Config shape (everything optional except title and sections):

    {
      "title": "Example Conference 2026",
      "subtitle": "Prospect Binder",
      "owner": "Your Name",
      "event_dates": "September 22-24, 2026",
      "venue": "Some Convention Center",
      "city": "Nashville, TN",
      "hero_image": "assets/hero.jpg",
      "hero_credit": "Photo: Someone, CC BY 4.0",
      "intro": "One line on what this is.",
      "sections": [
        {
          "id": "speakers",
          "label": "Speakers",
          "icon": "🎤",
          "csv": "data/example-speakers.csv",
          "blurb": "Everyone on stage. Best opener in the building.",
          "columns": ["person_name", "title", "organization", "linkedin_url"]
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import date
from pathlib import Path

from scripts.common import read_csv

# Same visual language as the other client binders: Cinzel display serif over
# Lato, cream paper, navy, one gold accent. Deliberately not a dashboard.
CSS = """
:root{--barh:66px;--brand:#1b3a5c;--dark:#0f2640;--accent:#c5985e;--cream:#f9f7f3;
      --line:#e7e2d9;--ink:#0f1e33;--muted:#5a6880;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--cream);color:var(--ink);font-family:'Lato',Inter,Arial,sans-serif;line-height:1.55}
.wrap{max-width:1280px;margin:0 auto;padding:26px 20px 70px}
h1{font-family:'Cinzel',Georgia,serif;font-weight:500;letter-spacing:.04em;color:var(--brand)}
h2{font-family:'Cinzel',Georgia,serif;font-weight:500;font-size:19px;color:var(--brand);
   letter-spacing:.03em;margin:34px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}
a{color:var(--brand)}
.lead{color:var(--muted);font-size:14px;margin:8px 0 20px}
.hero{position:relative;overflow:hidden;border-radius:12px;margin-bottom:26px;
      background:linear-gradient(135deg,var(--dark) 0%,var(--brand) 60%,#24507c 100%)}
.hero .bg{position:absolute;inset:0;background-size:cover;background-position:center;opacity:.34}
.hero .veil{position:absolute;inset:0;background:linear-gradient(120deg,rgba(15,38,64,.93),rgba(27,58,92,.62))}
.hero .inner{position:relative;padding:52px 44px}
.hero h1{color:#fff;font-size:31px;margin-bottom:10px}
.hero .sub{color:var(--accent);font-family:'Overpass',sans-serif;font-size:12px;font-weight:600;
           letter-spacing:.16em;text-transform:uppercase;margin-bottom:16px}
.hero .meta{color:#dbe4f0;font-size:14px}
.hero .credit{position:absolute;right:12px;bottom:8px;color:rgba(255,255,255,.5);font-size:10px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:22px 0 8px}
.tile{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px}
.tile .n{font-family:'Cinzel',Georgia,serif;font-size:28px;color:var(--brand);line-height:1}
.tile .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.09em;margin-top:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:22px;
      display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-2px);box-shadow:0 10px 26px rgba(15,38,64,.10)}
.card .ic{font-size:22px;margin-bottom:10px}
.card h3{font-family:'Cinzel',Georgia,serif;font-weight:500;font-size:17px;color:var(--brand);margin-bottom:7px}
.card p{font-size:13px;color:var(--muted);flex:1;margin-bottom:15px}
.card .go{font-family:'Overpass',sans-serif;font-size:11px;font-weight:600;letter-spacing:.1em;
          text-transform:uppercase;color:var(--accent);text-decoration:none}
.tag{display:inline-block;font-size:10px;letter-spacing:.07em;text-transform:uppercase;
     background:#f0f3f8;color:#38485f;border-radius:4px;padding:3px 8px;margin-right:5px}
.bar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:16px;
     position:sticky;top:0;background:var(--cream);padding:14px 0;z-index:6}
#q{flex:1;min-width:230px;padding:11px 15px;border:1px solid var(--line);border-radius:6px;font-size:14px;background:#fff}
.toggle{font-size:12px;font-weight:700;color:var(--brand);border:1px solid var(--line);
        background:#fff;border-radius:6px;padding:9px 14px;cursor:pointer}
.toggle.on{background:var(--brand);color:#fff;border-color:var(--brand)}
.chip{font-size:12px;color:var(--muted)} .chip b{color:var(--brand)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);
      border-radius:8px;overflow:hidden;font-size:12.5px}
th{background:#f0f3f8;color:#38485f;text-align:left;font-size:11px;text-transform:uppercase;
   letter-spacing:.04em;padding:11px 10px;border-bottom:1px solid var(--line);cursor:pointer;
   position:sticky;top:var(--barh);z-index:4;white-space:nowrap;box-shadow:0 1px 0 var(--line)}
th:hover{background:#e6ebf3}
td{padding:11px 10px;border-bottom:1px solid #eef1f5;vertical-align:top}
tr:hover td{background:#fcfaf6}
.pill{font-size:10px;border-radius:4px;padding:2px 7px;text-transform:uppercase;letter-spacing:.05em;font-weight:700}
.c-confirmed{background:#e3f2e8;color:#1f6b3a}
.c-probable{background:#fdf3e0;color:#8a5a12}
.c-weak{background:#f3f0ec;color:#7a6f62}
.back{font-family:'Overpass',sans-serif;font-size:11px;font-weight:600;letter-spacing:.1em;
      text-transform:uppercase;color:var(--muted);text-decoration:none}
.dl{background:var(--accent);color:#fff;border:none;border-radius:6px;padding:10px 16px;
    font-family:'Overpass',sans-serif;font-size:11px;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;cursor:pointer;text-decoration:none;display:inline-block}
.dl:hover{background:#d4ab73}
.foot{margin-top:40px;padding-top:18px;border-top:1px solid var(--line);font-size:11.5px;color:var(--muted)}
@media(max-width:680px){.hero .inner{padding:34px 22px}.hero h1{font-size:23px}
  .wrap{padding:20px 14px 60px}th{position:static}}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600'
         '&family=Lato:wght@300;400;700&family=Overpass:wght@400;600&display=swap" rel="stylesheet">')

TABLE_JS = """
function syncBarHeight(){
  const bar=document.querySelector('.bar');
  if(bar) document.documentElement.style.setProperty('--barh', bar.offsetHeight+'px');
}
syncBarHeight();
window.addEventListener('resize', syncBarHeight);
const rows=[...document.querySelectorAll('tbody tr')];
const q=document.getElementById('q'),cnt=document.getElementById('cnt');
let only=null;
function apply(){
  const t=(q.value||'').toLowerCase();
  let n=0;
  rows.forEach(r=>{
    const hay=r.dataset.hay, okT=!t||hay.includes(t);
    const okF=!only||r.dataset[only]==='1';
    const show=okT&&okF; r.style.display=show?'':'none'; if(show)n++;
  });
  cnt.textContent=n;
}
q.addEventListener('input',apply);
document.querySelectorAll('.toggle').forEach(b=>b.addEventListener('click',()=>{
  const f=b.dataset.filter;
  if(only===f){only=null;b.classList.remove('on');}
  else{document.querySelectorAll('.toggle').forEach(x=>x.classList.remove('on'));
       only=f;b.classList.add('on');}
  apply();
}));
document.querySelectorAll('th').forEach((th,i)=>th.addEventListener('click',()=>{
  const tb=th.closest('table').querySelector('tbody');
  const asc=th.dataset.asc!=='1'; th.dataset.asc=asc?'1':'0';
  [...tb.querySelectorAll('tr')].sort((a,b)=>{
    const x=a.children[i].innerText.trim().toLowerCase();
    const y=b.children[i].innerText.trim().toLowerCase();
    return asc?x.localeCompare(y):y.localeCompare(x);
  }).forEach(r=>tb.appendChild(r));
}));
"""

PRETTY = {
    "person_name": "Name", "title": "Title", "organization": "Company",
    "linkedin_url": "LinkedIn", "email": "Email", "phone": "Phone",
    "website": "Website", "role_type": "Role", "confidence": "Confidence",
    "event_name": "Event", "segment": "Searched Role", "source": "Source",
    "evidence": "Evidence", "next_action": "Next Action",
}


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def cell(col: str, val: str) -> str:
    """Render one cell — links become links, confidence becomes a pill."""
    v = (val or "").strip()
    if not v:
        return '<span style="color:#c3c9d4">—</span>'
    if col == "linkedin_url":
        return f'<a href="{esc(v)}" target="_blank" rel="noopener">profile ↗</a>'
    if col == "website":
        label = v.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        return f'<a href="{esc(v)}" target="_blank" rel="noopener">{esc(label[:34])} ↗</a>'
    if col == "email":
        return f'<a href="mailto:{esc(v)}">{esc(v)}</a>'
    if col == "confidence":
        return f'<span class="pill c-{esc(v.lower())}">{esc(v)}</span>'
    if col == "source":
        return f'<a href="{esc(v)}" target="_blank" rel="noopener">page ↗</a>' if v.startswith("http") else esc(v)
    return esc(v[:180])


def build_table_page(section: dict, rows: list[dict], cfg: dict, outdir: Path) -> dict:
    cols = section.get("columns") or [
        c for c in ["person_name", "title", "organization", "linkedin_url", "email", "confidence"]
        if any((r.get(c) or "").strip() for r in rows)
    ]
    body = []
    for r in rows:
        hay = " ".join(str(r.get(c, "")) for c in cols).lower()
        flags = (
            f' data-li="{1 if (r.get("linkedin_url") or "").strip() else 0}"'
            f' data-em="{1 if (r.get("email") or "").strip() else 0}"'
            f' data-cf="{1 if (r.get("confidence") or "").lower() == "confirmed" else 0}"'
        )
        tds = "".join(f"<td>{cell(c, r.get(c, ''))}</td>" for c in cols)
        body.append(f'<tr data-hay="{esc(hay)}"{flags}>{tds}</tr>')

    ths = "".join(f"<th>{esc(PRETTY.get(c, c.replace('_', ' ').title()))}</th>" for c in cols)
    n_li = sum(1 for r in rows if (r.get("linkedin_url") or "").strip())
    n_em = sum(1 for r in rows if (r.get("email") or "").strip())
    n_cf = sum(1 for r in rows if (r.get("confidence") or "").lower() == "confirmed")

    csv_name = f"{section['id']}.csv"
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(cfg['title'])} — {esc(section['label'])}</title>{FONTS}
<style>{CSS}</style></head><body><div class="wrap">
<a class="back" href="index.html">&larr; Back to binder</a>
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-top:12px">
  <div><h1 style="font-size:23px">{esc(section['label'])}</h1>
  <div class="lead">{esc(section.get('blurb',''))}</div></div>
  <a class="dl" href="{esc(csv_name)}" download>Download CSV</a>
</div>
<div class="bar">
  <input id="q" placeholder="Search names, titles, companies…"/>
  <button class="toggle" data-filter="li">Has LinkedIn</button>
  <button class="toggle" data-filter="em">Has email</button>
  <button class="toggle" data-filter="cf">Confirmed only</button>
  <span class="chip"><b id="cnt">{len(rows)}</b> of {len(rows)} shown</span>
</div>
<table><thead><tr>{ths}</tr></thead><tbody>{''.join(body)}</tbody></table>
<div class="foot">{len(rows)} rows · {n_cf} confirmed · {n_li} with LinkedIn · {n_em} with email.
Click any column heading to sort.</div>
</div><script>{TABLE_JS}</script></body></html>"""
    (outdir / f"{section['id']}.html").write_text(page, encoding="utf-8")
    return {"rows": len(rows), "linkedin": n_li, "email": n_em, "confirmed": n_cf}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an HTML prospect binder from roster CSVs")
    ap.add_argument("--config", required=True, help="Binder config JSON")
    ap.add_argument("--outdir", required=True, help="Where to write the binder")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    stats, cards = {}, []
    total_rows = total_orgs = 0
    all_orgs: set[str] = set()

    for section in cfg["sections"]:
        csv_path = Path(section["csv"])
        if not csv_path.exists():
            print(f"  skipping {section['id']}: {csv_path} not found")
            continue
        rows = read_csv(csv_path)
        if not rows:
            print(f"  skipping {section['id']}: no rows")
            continue
        s = build_table_page(section, rows, cfg, outdir)
        shutil.copy(csv_path, outdir / f"{section['id']}.csv")
        stats[section["id"]] = s
        total_rows += s["rows"]
        all_orgs |= {(r.get("organization") or "").strip().lower()
                     for r in rows if (r.get("organization") or "").strip()}
        tags = "".join(
            f'<span class="tag">{t}</span>' for t in [
                f"{s['rows']} rows",
                f"{s['confirmed']} confirmed" if s["confirmed"] else "",
                f"{s['linkedin']} LinkedIn" if s["linkedin"] else "",
            ] if t
        )
        cards.append(f"""<a class="card" href="{esc(section['id'])}.html" style="text-decoration:none">
  <div class="ic">{esc(section.get('icon','📋'))}</div>
  <h3>{esc(section['label'])}</h3>
  <p>{esc(section.get('blurb',''))}</p>
  <div style="margin-bottom:12px">{tags}</div>
  <span class="go">Open list →</span></a>""")
        print(f"  {section['id']}: {s['rows']} rows")

    total_orgs = len(all_orgs)
    hero_img = cfg.get("hero_image", "")
    bg = f'<div class="bg" style="background-image:url(\'{esc(hero_img)}\')"></div>' if hero_img else ""
    credit = f'<div class="credit">{esc(cfg["hero_credit"])}</div>' if cfg.get("hero_credit") else ""

    tiles = [
        (total_rows, "Total records"),
        (total_orgs, "Companies"),
        (sum(s["confirmed"] for s in stats.values()), "Confirmed"),
        (sum(s["linkedin"] for s in stats.values()), "LinkedIn profiles"),
    ]
    tiles_html = "".join(
        f'<div class="tile"><div class="n">{n}</div><div class="l">{esc(l)}</div></div>'
        for n, l in tiles
    )
    meta_bits = " · ".join(x for x in [cfg.get("event_dates"), cfg.get("venue"), cfg.get("city")] if x)

    # %-d is glibc-only and raises on Windows; build the date portably.
    today = date.today()
    built_on = f"{today:%B} {today.day}, {today.year}"

    index = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(cfg['title'])} — {esc(cfg.get('subtitle','Prospect Binder'))}</title>{FONTS}
<style>{CSS}</style></head><body><div class="wrap">
<div class="hero">{bg}<div class="veil"></div><div class="inner">
  <div class="sub">{esc(cfg.get('subtitle','Prospect Binder'))}</div>
  <h1>{esc(cfg['title'])}</h1>
  <div class="meta">{esc(meta_bits)}</div>
</div>{credit}</div>
{f'<div class="lead">{esc(cfg["intro"])}</div>' if cfg.get("intro") else ""}
<div class="tiles">{tiles_html}</div>
<h2>Lists</h2>
<div class="cards">{''.join(cards)}</div>
<div class="foot">
  Built {built_on}{f" for {esc(cfg['owner'])}" if cfg.get("owner") else ""}.
  Every row links back to the page it came from — check the Source column.<br>
  Confidence: <span class="pill c-confirmed">confirmed</span> verified ·
  <span class="pill c-probable">probable</span> likely, check first ·
  <span class="pill c-weak">weak</span> verify before contacting.
</div></div></body></html>"""
    (outdir / "index.html").write_text(index, encoding="utf-8")

    print(f"\n{'='*62}")
    print(f"Binder -> {outdir / 'index.html'}")
    print(f"  {total_rows} records across {len(stats)} lists, {total_orgs} companies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
