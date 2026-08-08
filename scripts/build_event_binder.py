#!/usr/bin/env python3
"""
Build a client-facing HTML binder from conference roster CSVs.

Why a binder and not a spreadsheet
----------------------------------
A CSV is a file you attach. A binder is a link you send — it opens on a phone,
it looks like you spent money on it, and it gets forwarded to the person who
actually signs. Same data, completely different reception.

Self-contained HTML with the data inlined. No build step, no server, no
dependencies. Drop it on Cloudflare Pages or open it locally.

What it produces
----------------
  index.html      full-bleed photo hero, stat pills, one card per list
  <section>.html  searchable, sortable, filterable table per CSV

Usage
-----
    python -X utf8 -m scripts.build_event_binder \\
        --config data/example-binder.json --outdir dist/example

See README for the config shape.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import date
from pathlib import Path

from scripts.common import read_csv

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?'
         'family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">')

CSS = """
:root{
  --bg:#f2f5fb; --card:#fff; --ink:#0f1e33; --muted:#5a6880; --line:#d6e2f0;
  --blue:#0f5cc0; --blue-soft:#edf4ff;
  --green:#1a7a4e; --green-soft:#e6f7ef;
  --amber:#9a5c00; --amber-soft:#fff6e0;
  --purple:#5a2a8a; --purple-soft:#f2eaff;
  --gray-soft:#f0f2f5;
  --shadow:0 16px 40px rgba(15,30,60,.09); --radius:16px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,Arial,sans-serif;background:var(--bg);
     color:var(--ink);line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 80px}
a{color:var(--blue)}

/* Hero. The photo leads — it is the first thing on the page and it runs the
   full width of the card, with the copy sitting in the darkened lower half. */
.hero{position:relative;border-radius:24px;overflow:hidden;margin-bottom:32px;
      box-shadow:var(--shadow);background:linear-gradient(135deg,#091e40,#0e3270 55%,#1549a0)}
.hero .photo{position:absolute;inset:0;background-size:cover;background-position:center 40%}
.hero .scrim{position:absolute;inset:0;background:linear-gradient(180deg,
      rgba(9,30,64,.30) 0%,rgba(9,30,64,.58) 38%,rgba(9,30,64,.88) 72%,rgba(9,30,64,.96) 100%)}
.hero .inner{position:relative;padding:190px 48px 40px;color:#fff}
.hero .kicker{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
      color:#8fc0ff;margin-bottom:12px}
.hero h1{font-size:38px;font-weight:800;letter-spacing:-.02em;line-height:1.12;margin-bottom:10px}
.hero .where{font-size:14px;font-weight:500;color:#c9dcf5;margin-bottom:26px}
.stat-row{display:flex;gap:14px;flex-wrap:wrap}
.sp{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);
    border-radius:12px;padding:12px 18px}
.sp .k{font-size:10px;text-transform:uppercase;letter-spacing:.08em;opacity:.78;margin-bottom:2px}
.sp .v{font-size:22px;font-weight:800}
.hero .credit{position:absolute;right:14px;bottom:10px;color:rgba(255,255,255,.45);font-size:10px}

.intro{font-size:14.5px;color:var(--muted);max-width:830px}
.section-label{display:flex;align-items:center;gap:12px;margin:36px 0 16px;
               padding-bottom:12px;border-bottom:2px solid var(--line)}
.section-label h2{font-size:18px;font-weight:800}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
      padding:22px 24px;box-shadow:0 2px 14px rgba(15,30,60,.07);
      display:flex;flex-direction:column;gap:10px;cursor:pointer;
      transition:box-shadow .15s,transform .15s;text-decoration:none;color:inherit}
.card:hover{box-shadow:0 8px 28px rgba(15,30,60,.14);transform:translateY(-2px)}
.card-top{display:flex;align-items:flex-start;gap:14px}
.card-icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;
           justify-content:center;font-size:19px;flex-shrink:0}
.card-title{font-size:15px;font-weight:800;line-height:1.3}
.card-subtitle{font-size:12px;color:var(--muted);margin-top:3px;font-weight:500}
.card-body{font-size:13px;color:var(--muted);line-height:1.5;flex:1}
.card-footer{display:flex;gap:6px;flex-wrap:wrap;padding-top:8px;border-top:1px solid var(--line)}
.tag{font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;display:inline-block}
.tag-blue{background:var(--blue-soft);color:var(--blue);border:1px solid #c2d8f5}
.tag-green{background:var(--green-soft);color:var(--green);border:1px solid #a8dfc5}
.tag-amber{background:var(--amber-soft);color:var(--amber);border:1px solid #f0cc80}
.tag-purple{background:var(--purple-soft);color:var(--purple);border:1px solid #d0b8f0}
.tag-gray{background:var(--gray-soft);color:#5a6880;border:1px solid #d0d8e8}
.ic-blue{background:var(--blue-soft)} .ic-green{background:var(--green-soft)}
.ic-amber{background:var(--amber-soft)} .ic-purple{background:var(--purple-soft)}

.binder-footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);
   color:var(--muted);font-size:12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}

/* ---- table pages ---- */
.thead-wrap{background:linear-gradient(135deg,#091e40,#0e3270 60%,#1549a0);
            border-radius:16px 16px 0 0;padding:22px 26px;color:#fff}
.thead-wrap h1{font-size:21px;font-weight:800;letter-spacing:-.01em}
.thead-wrap .sub{font-size:12.5px;color:rgba(255,255,255,.78);margin-top:6px;max-width:790px;line-height:1.5}
.back{display:inline-flex;align-items:center;gap:7px;background:#fff;border:1px solid var(--line);
      border-radius:8px;padding:7px 14px;font-size:12.5px;font-weight:700;
      color:var(--blue);text-decoration:none;margin-bottom:16px}
.back:hover{background:var(--blue-soft)}
.dl{background:#fff;color:#0e3270;border-radius:8px;padding:9px 16px;font-size:12px;
    font-weight:700;text-decoration:none;white-space:nowrap}
.dl:hover{background:#e8f0fc}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:var(--card);
     border:1px solid var(--line);border-top:none;padding:14px 22px;position:sticky;top:0;z-index:20}
#q{flex:1;min-width:220px;padding:10px 14px;border:1px solid var(--line);
   border-radius:9px;font-size:13.5px;font-family:inherit;background:#fff}
#q:focus{outline:2px solid var(--blue);outline-offset:-1px}
.toggle{font-size:12px;font-weight:700;color:var(--blue);border:1px solid #c2d8f5;
        background:var(--blue-soft);border-radius:999px;padding:7px 14px;cursor:pointer;font-family:inherit}
.toggle.on{background:var(--blue);color:#fff;border-color:var(--blue)}
.chip{font-size:12px;color:var(--muted)} .chip b{color:var(--ink)}

.tbl{background:var(--card);border:1px solid var(--line);border-top:none;
     border-radius:0 0 16px 16px;overflow:hidden}
/* border-collapse:collapse breaks position:sticky on <th> in Chrome — the
   header renders *underneath* the first rows, which is what the earlier
   version did. separate + border-spacing:0 looks identical and sticks. */
table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px}
th{background:#eef3fa;color:#3c4d66;text-align:left;font-size:10.5px;font-weight:800;
   text-transform:uppercase;letter-spacing:.05em;padding:12px 16px;
   border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap;
   position:sticky;top:var(--barh,60px);z-index:10}
th:hover{background:#e3ebf7}
th .ar{opacity:.4;font-size:9px;margin-left:4px}
td{padding:12px 16px;border-bottom:1px solid #eaf0f8;vertical-align:top}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#f7faff}
td.nm{font-weight:700}
.pill{font-size:10px;font-weight:700;border-radius:999px;padding:3px 9px;
      text-transform:uppercase;letter-spacing:.04em;white-space:nowrap}
.c-confirmed{background:var(--green-soft);color:var(--green);border:1px solid #a8dfc5}
.c-probable{background:var(--amber-soft);color:var(--amber);border:1px solid #f0cc80}
.c-weak{background:var(--gray-soft);color:#5a6880;border:1px solid #d0d8e8}
.empty{color:#b6c0d0}
.note{font-size:11.5px;color:var(--muted);margin-top:16px}

@media(max-width:680px){
  .hero .inner{padding:130px 22px 30px}.hero h1{font-size:26px}
  .cards{grid-template-columns:1fr}.wrap{padding:22px 14px 60px}
  th{position:static}.bar{position:static}
}
"""

TABLE_JS = """
function syncBar(){
  const b=document.querySelector('.bar');
  if(b) document.documentElement.style.setProperty('--barh', b.offsetHeight+'px');
}
syncBar(); window.addEventListener('resize', syncBar);

const rows=[...document.querySelectorAll('tbody tr')];
const q=document.getElementById('q'), cnt=document.getElementById('cnt');
let only=null;
function apply(){
  const t=(q.value||'').trim().toLowerCase();
  let n=0;
  rows.forEach(r=>{
    const okT=!t||r.dataset.hay.includes(t);
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
  document.querySelectorAll('th .ar').forEach(a=>a.textContent='');
  const ar=th.querySelector('.ar'); if(ar) ar.textContent=asc?'\\u25B2':'\\u25BC';
  [...tb.querySelectorAll('tr')].sort((a,b)=>{
    const x=a.children[i].innerText.trim().toLowerCase();
    const y=b.children[i].innerText.trim().toLowerCase();
    if(!x) return 1; if(!y) return -1;
    return asc?x.localeCompare(y):y.localeCompare(x);
  }).forEach(r=>tb.appendChild(r));
}));
"""

PRETTY = {
    "person_name": "Name", "title": "Title", "organization": "Company",
    "linkedin_url": "LinkedIn", "email": "Email", "phone": "Phone",
    "website": "Website", "role_type": "Role", "confidence": "Confidence",
    "event_name": "Event", "segment": "Matched Role", "source": "Source",
    "evidence": "Evidence", "next_action": "Next Action",
}
ACCENTS = ["blue", "green", "amber", "purple"]


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def cell(col: str, val: str) -> str:
    v = (val or "").strip()
    if not v:
        return '<span class="empty">&mdash;</span>'
    if col == "linkedin_url":
        return f'<a href="{esc(v)}" target="_blank" rel="noopener">profile &#8599;</a>'
    if col == "website":
        lab = v.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        return f'<a href="{esc(v)}" target="_blank" rel="noopener">{esc(lab[:32])} &#8599;</a>'
    if col == "email":
        return f'<a href="mailto:{esc(v)}">{esc(v)}</a>'
    if col == "confidence":
        return f'<span class="pill c-{esc(v.lower())}">{esc(v)}</span>'
    if col == "source" and v.startswith("http"):
        return f'<a href="{esc(v)}" target="_blank" rel="noopener">page &#8599;</a>'
    return esc(v[:170])


def build_table_page(section, rows, cfg, outdir) -> dict:
    cols = section.get("columns") or [
        c for c in ["person_name", "title", "organization", "linkedin_url", "email", "confidence"]
        if any((r.get(c) or "").strip() for r in rows)
    ]
    body = []
    for r in rows:
        hay = " ".join(str(r.get(c, "")) for c in cols).lower()
        flags = (f' data-li="{1 if (r.get("linkedin_url") or "").strip() else 0}"'
                 f' data-em="{1 if (r.get("email") or "").strip() else 0}"'
                 f' data-cf="{1 if (r.get("confidence") or "").lower()=="confirmed" else 0}"')
        tds = ""
        for i, c in enumerate(cols):
            klass = ' class="nm"' if i == 0 else ""
            tds += f"<td{klass}>{cell(c, r.get(c, ''))}</td>"
        body.append(f'<tr data-hay="{esc(hay)}"{flags}>{tds}</tr>')

    ths = "".join(
        f'<th>{esc(PRETTY.get(c, c.replace("_", " ").title()))}<span class="ar"></span></th>'
        for c in cols
    )
    n_li = sum(1 for r in rows if (r.get("linkedin_url") or "").strip())
    n_em = sum(1 for r in rows if (r.get("email") or "").strip())
    n_cf = sum(1 for r in rows if (r.get("confidence") or "").lower() == "confirmed")

    toggles = ['<button class="toggle" data-filter="li">Has LinkedIn</button>']
    if n_em:
        toggles.append('<button class="toggle" data-filter="em">Has email</button>')
    toggles.append('<button class="toggle" data-filter="cf">Confirmed only</button>')

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(cfg['title'])} &mdash; {esc(section['label'])}</title>{FONTS}
<style>{CSS}</style></head><body><div class="wrap">
<a class="back" href="index.html">&larr; Back to binder</a>
<div class="thead-wrap">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
    <div><h1>{esc(section['label'])}</h1>
    <div class="sub">{esc(section.get('blurb',''))}</div></div>
    <a class="dl" href="{esc(section['id'])}.csv" download>Download CSV</a>
  </div>
</div>
<div class="bar">
  <input id="q" placeholder="Search&hellip;"/>
  {''.join(toggles)}
  <span class="chip"><b id="cnt">{len(rows)}</b> of {len(rows)}</span>
</div>
<div class="tbl"><table><thead><tr>{ths}</tr></thead><tbody>{''.join(body)}</tbody></table></div>
<div class="note">{len(rows)} rows &middot; {n_cf} confirmed &middot; {n_li} with LinkedIn{f' &middot; {n_em} with email' if n_em else ''}.
Click a column heading to sort.</div>
</div><script>{TABLE_JS}</script></body></html>"""
    (outdir / f"{section['id']}.html").write_text(page, encoding="utf-8")
    return {"rows": len(rows), "linkedin": n_li, "email": n_em, "confirmed": n_cf}


def main() -> int:
    ap = argparse.ArgumentParser(description="Build an HTML prospect binder from roster CSVs")
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    stats, cards = {}, []
    total_rows = 0
    all_orgs: set[str] = set()

    for i, section in enumerate(cfg["sections"]):
        csv_path = Path(section["csv"])
        if not csv_path.exists():
            print(f"  skip {section['id']}: {csv_path} not found")
            continue
        rows = read_csv(csv_path)
        if not rows:
            print(f"  skip {section['id']}: empty")
            continue

        s = build_table_page(section, rows, cfg, outdir)
        shutil.copy(csv_path, outdir / f"{section['id']}.csv")
        stats[section["id"]] = s
        total_rows += s["rows"]
        all_orgs |= {(r.get("organization") or "").strip().lower()
                     for r in rows if (r.get("organization") or "").strip()}

        accent = section.get("accent") or ACCENTS[i % len(ACCENTS)]
        tag_specs = [
            (f"{s['rows']} rows", "gray"),
            (f"{s['confirmed']} confirmed" if s["confirmed"] else "", "green"),
            (f"{s['linkedin']} LinkedIn" if s["linkedin"] else "", "blue"),
            (f"{s['email']} emails" if s["email"] else "", "purple"),
        ]
        tags = "".join(f'<span class="tag tag-{cls}">{esc(t)}</span>'
                       for t, cls in tag_specs if t)
        cards.append(f"""<a class="card" href="{esc(section['id'])}.html">
  <div class="card-top">
    <div class="card-icon ic-{accent}">{section.get('icon', '&#128203;')}</div>
    <div><div class="card-title">{esc(section['label'])}</div>
    <div class="card-subtitle">{s['rows']} records</div></div>
  </div>
  <div class="card-body">{esc(section.get('blurb', ''))}</div>
  <div class="card-footer">{tags}</div></a>""")
        print(f"  {section['id']}: {s['rows']} rows")

    hero_img = cfg.get("hero_image", "")
    photo = (f'<div class="photo" style="background-image:url(\'{esc(hero_img)}\')"></div>'
             if hero_img else "")
    credit = f'<div class="credit">{esc(cfg["hero_credit"])}</div>' if cfg.get("hero_credit") else ""
    where = " &middot; ".join(esc(x) for x in
                             [cfg.get("event_dates"), cfg.get("venue"), cfg.get("city")] if x)

    n_cf = sum(s["confirmed"] for s in stats.values())
    n_li = sum(s["linkedin"] for s in stats.values())
    n_em = sum(s["email"] for s in stats.values())
    pills = [(str(total_rows), "Total records"), (str(len(all_orgs)), "Companies")]
    if n_cf:
        pills.append((str(n_cf), "Confirmed"))
    if n_li:
        pills.append((str(n_li), "LinkedIn"))
    if n_em:
        pills.append((str(n_em), "Emails"))
    pills_html = "".join(
        f'<div class="sp"><div class="k">{esc(l)}</div><div class="v">{esc(v)}</div></div>'
        for v, l in pills
    )

    today = date.today()
    built = f"{today:%B} {today.day}, {today.year}"

    index = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(cfg['title'])} &mdash; {esc(cfg.get('subtitle', 'Prospect Binder'))}</title>{FONTS}
<style>{CSS}</style></head><body><div class="wrap">
<div class="hero">{photo}<div class="scrim"></div><div class="inner">
  <div class="kicker">{esc(cfg.get('subtitle', 'Conference Prospect Binder'))}</div>
  <h1>{esc(cfg['title'])}</h1>
  <div class="where">{where}</div>
  <div class="stat-row">{pills_html}</div>
</div>{credit}</div>
{f'<div class="intro">{esc(cfg["intro"])}</div>' if cfg.get("intro") else ""}
<div class="section-label"><h2>Lists</h2></div>
<div class="cards">{''.join(cards)}</div>
<div class="binder-footer">
  <span>Built {built}{f" for {esc(cfg['owner'])}" if cfg.get("owner") else ""}</span>
  <span>Confidence: <span class="pill c-confirmed">confirmed</span> verified &middot;
  <span class="pill c-probable">probable</span> check first &middot;
  <span class="pill c-weak">weak</span> verify before contacting</span>
</div></div></body></html>"""
    (outdir / "index.html").write_text(index, encoding="utf-8")

    print(f"\n{'=' * 62}")
    print(f"Binder -> {outdir / 'index.html'}")
    print(f"  {total_rows} records &middot; {len(stats)} lists &middot; {len(all_orgs)} companies"
          .replace("&middot;", "·"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
