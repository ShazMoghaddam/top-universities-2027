"""Build the Top 50 Universities carousel (PDF + Instagram slides) from data/.

Usage:
    python build.py                      # uses data/edition-2027.json
    python build.py data/edition-2028.json
"""
import csv
import collections
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
CONFIG = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "edition-2027.json"
CFG = json.loads(CONFIG.read_text(encoding="utf-8"))
EDITION = CFG["edition"]
OUT = ROOT / "output"
SLIDES = OUT / "slides"
TOTAL = 8

# Region colours, validated for colour-blind separation on the paper background.
REG = {"Americas": "#E4572E", "Europe": "#2F5BEA", "Asia": "#0E9F6E", "Oceania": "#D99520"}
REG_LABEL = {"Americas": "North America", "Europe": "Europe", "Asia": "Asia", "Oceania": "Oceania"}


def flag(code):
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def load_rows():
    with open(CONFIG.parent / CFG["data_file"], newline="", encoding="utf-8") as f:
        rows = []
        for r in csv.DictReader(f):
            r["score"] = float(r["overall_score"])
            r["rank_num"] = int(r["rank"].lstrip("="))
            r["flag"] = flag(r["country_code"])
            rows.append(r)
    assert len(rows) == 50, f"expected 50 rows, got {len(rows)}"
    return rows


ROWS = load_rows()
region_counts = collections.Counter(r["region"] for r in ROWS)
country_counts = collections.Counter(r["country"] for r in ROWS).most_common()
flags = {r["country"]: r["flag"] for r in ROWS}
country_region = {r["country"]: r["region"] for r in ROWS}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..800'
         '&family=Lora:ital@1&display=swap" rel="stylesheet">')

CSS = """
@page { size: 1080px 1350px; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --paper:#F5F2EB; --ink:#14161B; --muted:#6A6E77; --rule:#DFD9CC; --soft:#ECE7DC; }
body { font-family: 'Inter', sans-serif; color: var(--ink); -webkit-font-smoothing: antialiased; }
.page { width:1080px; height:1350px; position:relative; overflow:hidden; page-break-after:always; background:var(--paper); }
.disp { font-family:'Inter Display','Inter',sans-serif; }
.serif { font-family:'Lora',serif; font-style:italic; font-weight:400; }
.flag { font-family:'Noto Color Emoji','Apple Color Emoji','Segoe UI Emoji',sans-serif; }
.num { font-variant-numeric: tabular-nums; font-feature-settings:'tnum','ss01'; }
a { color: inherit; text-decoration: none; }

/* cover */
.cover { background:#111318; color:#F5F2EB; padding:84px 80px; display:flex; flex-direction:column; }
.cover .eyebrow { font-size:20px; letter-spacing:.18em; text-transform:uppercase; color:#A9ADB6; font-weight:500; }
.cover .eyebrow b { color:#F5F2EB; font-weight:600; }
.cover .big { font-size:300px; line-height:.82; font-weight:800; letter-spacing:-.05em; margin-top:84px; white-space:nowrap; }
.cover .big span { margin-left:18px; color:transparent; -webkit-text-stroke:3px #F5F2EB; }
.cover h1 { font-size:76px; font-weight:700; letter-spacing:-.03em; line-height:1.02; margin-top:30px; }
.cover h1 .serif { font-weight:400; color:#C9CCD3; }
.cover .lede { font-size:25px; line-height:1.45; color:#B9BDC6; margin-top:28px; max-width:820px; }
.podium { display:grid; grid-template-columns:1fr 1fr 1.4fr; gap:16px; margin-top:52px; }
.pod { border-top:1.5px solid #3A3E47; padding-top:18px; }
.pod .pr { font-size:44px; font-weight:800; letter-spacing:-.03em; }
.pod .pn { font-size:24px; font-weight:600; margin-top:6px; }
.pod .pl { font-size:18px; color:#A9ADB6; margin-top:4px; }
.split { margin-top:auto; margin-bottom:126px; }
.split .bar { display:flex; height:22px; border-radius:11px; overflow:hidden; gap:4px; }
.split .bar div { height:100%; }
.split .keys { display:flex; gap:34px; margin-top:20px; font-size:20px; color:#C9CCD3; }
.split .keys i { display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:9px; vertical-align:1px; }
.split .keys b { color:#F5F2EB; font-weight:600; margin-right:4px; }
.jump { position:absolute; left:80px; right:80px; bottom:84px; display:flex; justify-content:space-between; align-items:flex-end; }
.chips { display:flex; gap:12px; }
.chips a { font-size:19px; font-weight:600; padding:13px 20px; border:1.5px solid #3A3E47; border-radius:40px; color:#E6E3DC; }
.swipe { font-size:20px; font-weight:600; letter-spacing:.06em; text-transform:uppercase; color:#F5F2EB; display:flex; align-items:center; gap:14px; }
.swipe svg { width:46px; height:22px; }

/* shared top bar + byline */
.list, .ins, .charts { padding:62px 64px 0; }
.top { display:flex; justify-content:space-between; align-items:flex-start; }
.top .eyebrow { font-size:17px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); font-weight:600; }
.top .right { display:flex; align-items:center; gap:18px; }
.top .pg { font-size:17px; font-weight:600; color:var(--muted); padding-left:18px; border-left:1.5px solid var(--rule); }
.by { font-size:16px; color:var(--muted); display:flex; align-items:center; gap:10px; }
.by b { color:var(--ink); font-weight:600; }
.by a { color:var(--ink); font-weight:600; border-bottom:1.5px solid #2F5BEA; }
.by .dot { width:4px; height:4px; border-radius:50%; background:#B9B3A6; }
.cover .by { margin-top:34px; font-size:19px; color:#A9ADB6; gap:12px; }
.cover .by b, .cover .by a { color:#F5F2EB; }
.cover .by a { border-bottom-color:#5B7CF0; }
.cover .by .dot { background:#4A4E57; }

/* list pages */
.head { display:flex; align-items:flex-end; justify-content:space-between; margin-top:20px; padding-bottom:22px; border-bottom:2px solid var(--ink); }
.head h2 { font-size:96px; font-weight:800; letter-spacing:-.045em; line-height:.9; }
.legend { display:flex; gap:20px; font-size:16px; color:var(--muted); padding-bottom:10px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:7px; vertical-align:1px; }
.row { display:grid; grid-template-columns:112px minmax(0,1fr) 120px; column-gap:16px; align-items:center; height:104px; border-bottom:1px solid var(--rule); position:relative; }
.row .rk { font-size:50px; font-weight:800; letter-spacing:-.04em; display:flex; align-items:baseline; }
.row .rk small { font-size:30px; font-weight:600; color:var(--muted); margin-right:2px; letter-spacing:0; }
.row .nm { font-size:25px; font-weight:700; letter-spacing:-.015em; line-height:1.15; }
.row .meta { margin-top:5px; font-size:16.5px; color:var(--muted); display:flex; align-items:center; gap:8px; white-space:nowrap; }
.row .meta .flag { font-size:18px; }
.row .st { margin-top:4px; font-size:17.5px; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.row .st em { font-style:normal; color:var(--muted); font-weight:500; font-size:13px; letter-spacing:.12em; text-transform:uppercase; margin-right:10px; }
.row .tick { position:absolute; left:-64px; top:24px; bottom:24px; width:6px; border-radius:0 4px 4px 0; }
.row .sc { text-align:right; }
.row .sc b { font-size:28px; font-weight:700; letter-spacing:-.02em; display:block; }
.row .sc span { font-size:13px; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); font-weight:600; }
.row .sc .meter { height:5px; background:var(--soft); border-radius:3px; margin-top:8px; overflow:hidden; }
.row .sc .meter div { height:100%; background:var(--ink); border-radius:3px; }
.foot { position:absolute; left:64px; right:64px; bottom:40px; display:flex; justify-content:space-between; font-size:15px; color:var(--muted); }
.foot b { color:var(--ink); font-weight:600; }

/* charts page */
.charts h2, .ins h2 { font-size:80px; font-weight:800; letter-spacing:-.04em; line-height:.98; margin-top:20px; }
.charts h2 .serif, .ins h2 .serif { color:var(--muted); }
.chart { margin-top:34px; background:#FFFFFF; border:1px solid var(--rule); border-radius:22px; padding:26px 28px 18px; }
.chart h3 { font-size:26px; font-weight:700; letter-spacing:-.015em; }
.chart p { font-size:17.5px; color:#4A4D55; margin-top:6px; line-height:1.4; }
.chart svg { display:block; margin-top:10px; }
.chart svg text { font-family:'Inter',sans-serif; }

/* insights page */
.cards { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:40px; }
.card { background:#FFFFFF; border:1px solid var(--rule); border-radius:22px; padding:26px 28px; }
.card .v { font-size:64px; font-weight:800; letter-spacing:-.045em; line-height:1; }
.card .v small { font-size:28px; color:var(--muted); font-weight:600; letter-spacing:-.01em; }
.card p { font-size:19px; line-height:1.4; color:#3D4048; margin-top:12px; }
.countries { margin-top:40px; }
.countries h3 { font-size:17px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); font-weight:600; margin-bottom:14px; }
.crow { display:grid; grid-template-columns:250px 1fr 44px; align-items:center; height:36px; font-size:18px; }
.crow .cn { display:flex; gap:10px; align-items:center; font-weight:500; }
.crow .track { height:12px; }
.crow .track div { height:100%; border-radius:0 6px 6px 0; }
.crow .n { text-align:right; font-weight:700; }
.src { position:absolute; left:64px; right:64px; bottom:40px; border-top:2px solid var(--ink); padding-top:20px; font-size:15.5px; line-height:1.5; color:var(--muted); display:grid; grid-template-columns:1.35fr 1fr; gap:36px; }
.src b { color:var(--ink); font-weight:600; }
.src a { color:var(--ink); font-weight:600; border-bottom:1.5px solid #2F5BEA; }
"""

ARROW = ('<svg viewBox="0 0 46 22" fill="none" stroke="#F5F2EB" stroke-width="2.4" stroke-linecap="round" '
         'stroke-linejoin="round"><path d="M2 11h40M33 3l9 8-9 8"/></svg>')


def span(i):
    c = ROWS[i * 10:(i + 1) * 10]
    return f"{c[0]['rank_num']}–{c[-1]['rank_num']}"


def byline():
    site = CFG["website"]
    return (f'<div class="by"><b>{CFG["author"]}</b><span class="dot"></span>{CFG["location"]}'
            f'<span class="dot"></span><a href="{site}">{site.split("//")[-1]}</a></div>')


def top(n):
    return (f'<div class="top"><div class="eyebrow">Top 50 universities · {EDITION}</div>'
            f'<div class="right">{byline()}<div class="pg num">{n} / {TOTAL}</div></div></div>')


def legend():
    return '<div class="legend">' + "".join(
        f'<span><i style="background:{REG[r]}"></i>{REG_LABEL[r]}</span>' for r in REG) + '</div>'


def cover():
    bar = "".join(f'<div style="flex:{region_counts[r]};background:{REG[r]}"></div>' for r in REG if region_counts[r])
    keys = "".join(f'<span><i style="background:{REG[r]}"></i><b>{region_counts[r]}</b>{REG_LABEL[r]}</span>'
                   for r in REG if region_counts[r])
    chips = "".join(f'<a href="#p{i + 2}">{span(i)}</a>' for i in range(5)) + '<a href="#p7">Charts</a>'
    # Podium: group tied entries under one rank.
    groups = collections.OrderedDict()
    for r in ROWS:
        if r["rank_num"] <= 3:
            groups.setdefault(r["rank"], []).append(r)
    short = {"Massachusetts Institute of Technology": "MIT"}
    pod = "".join(
        f'<div class="pod"><div class="pr disp num">{rk}</div>'
        f'<div class="pn">{" & ".join(short.get(u["university"], u["university"].replace("University of ", "").replace(" University", "")) for u in us)}</div>'
        f'<div class="pl">{us[0]["country"]}</div></div>' for rk, us in groups.items())
    return f'''<section class="page cover" id="p1">
  <div class="eyebrow"><b>{EDITION} Edition</b> &nbsp;·&nbsp; Times Higher Education data</div>
  <div class="big disp">TOP<span>50</span></div>
  <h1 class="disp">Universities in the world, <span class="serif">and what each does best</span></h1>
  <p class="lede">{CFG["lede"]}</p>
  <div class="podium">{pod}</div>
  <div class="split"><div class="bar">{bar}</div><div class="keys">{keys}</div>{byline()}</div>
  <div class="jump"><div class="chips">{chips}</div><div class="swipe">Swipe {ARROW}</div></div>
</section>'''


def row(u):
    loc = u["city"] if u["city"] == u["country"] else f'{u["city"]}, {u["country"]}'
    eq = '<small>=</small>' if u["rank"].startswith("=") else ''
    pct = max(0, (u["score"] - 70) / 30 * 100)
    return f'''<div class="row"><div class="tick" style="background:{REG[u["region"]]}"></div>
  <div class="rk disp num">{eq}{u["rank_num"]}</div>
  <div><div class="nm">{u["university"]}</div>
    <div class="meta"><span class="flag">{u["flag"]}</span>{loc}</div>
    <div class="st"><em>Best for</em>{u["best_for"]}</div></div>
  <div class="sc num"><b>{u["score"]:.1f}</b><span>Score</span><div class="meter"><div style="width:{pct:.0f}%"></div></div></div>
</div>'''


def list_page(i):
    rows = "".join(row(u) for u in ROWS[i * 10:(i + 1) * 10])
    return f'''<section class="page list" id="p{i + 2}">
  {top(i + 2)}
  <div class="head"><h2 class="disp num">{span(i)}</h2>{legend()}</div>
  {rows}
  <div class="foot"><span>Score = THE overall score out of 100 · “=” means tied</span><span><b>Best for</b> = the fields each university is best known for</span></div>
</section>'''


def score_chart():
    """Dot plot: every university's overall score, in rank order, coloured by region."""
    W, H = 894, 400
    L, R, T, B = 52, 18, 26, 44
    lo, hi = 72, 100
    n = len(ROWS)
    x = lambda i: L + i * (W - L - R) / (n - 1)
    y = lambda s: T + (hi - s) / (hi - lo) * (H - T - B)
    grid = "".join(
        f'<line x1="{L}" x2="{W - R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#ECE7DC" stroke-width="1"/>'
        f'<text x="{L - 12}" y="{y(v) + 5:.1f}" text-anchor="end" font-size="15" fill="#6A6E77">{v}</text>'
        for v in range(75, hi + 1, 5))
    xt = "".join(
        f'<text x="{x(i):.1f}" y="{H - 14}" text-anchor="middle" font-size="15" fill="#6A6E77">{ROWS[i]["rank"]}</text>'
        for i in (0, 9, 19, 29, 39, 49))
    dots = "".join(
        f'<circle cx="{x(i):.1f}" cy="{y(u["score"]):.1f}" r="6.5" fill="{REG[u["region"]]}" stroke="#FFFFFF" stroke-width="2"/>'
        for i, u in enumerate(ROWS))
    first, last = ROWS[0], ROWS[-1]
    top10 = ROWS[9]
    ann = (
        f'<text x="{x(0) - 6:.1f}" y="{y(first["score"]) - 14:.1f}" font-size="15" font-weight="600" fill="#14161B">'
        f'{first["university"].replace("University of ", "")} {first["score"]:.1f}</text>'
        f'<text x="{x(n - 1) + 6:.1f}" y="{y(last["score"]) + 30:.1f}" text-anchor="end" font-size="15" font-weight="600" fill="#14161B">'
        f'{last["university"].replace("Delft University of Technology", "TU Delft")} {last["score"]:.1f}</text>'
        f'<line x1="{x(0):.1f}" x2="{x(9):.1f}" y1="{y(top10["score"]) + 16:.1f}" y2="{y(top10["score"]) + 16:.1f}" stroke="#14161B" stroke-width="1.5"/>'
        f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{y(top10["score"]) + 10:.1f}" y2="{y(top10["score"]) + 16:.1f}" stroke="#14161B" stroke-width="1.5"/>'
        f'<line x1="{x(9):.1f}" x2="{x(9):.1f}" y1="{y(top10["score"]) + 10:.1f}" y2="{y(top10["score"]) + 16:.1f}" stroke="#14161B" stroke-width="1.5"/>'
        f'<text x="{x(0):.1f}" y="{y(top10["score"]) + 38:.1f}" font-size="15" fill="#4A4D55">Top 10 within {first["score"] - top10["score"]:.1f} pts</text>')
    axis = f'<text x="{(L + W - R) / 2:.0f}" y="{H}" text-anchor="middle" font-size="14" fill="#6A6E77">Rank</text>'
    gap = first["score"] - last["score"]
    return f'''<div class="chart"><h3>How close the scores are</h3>
  <p>Every top 50 university by overall score. Just {gap:.1f} points separate 1st from 50th.</p>
  <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Overall scores in rank order">{grid}{xt}{axis}{ann}{dots}</svg></div>'''


def band_chart():
    """Stacked bars: how many universities from each region sit in each rank band."""
    bands = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 50)]
    W, rowh, gap = 894, 44, 14
    L, R = 96, 0
    unit = (W - L - R) / 11  # widest band holds 11 (ties)
    out = []
    for bi, (a, b) in enumerate(bands):
        yy = bi * (rowh + gap)
        members = [u for u in ROWS if a <= u["rank_num"] <= b]
        c = collections.Counter(u["region"] for u in members)
        out.append(f'<text x="0" y="{yy + rowh / 2 + 6:.0f}" font-size="17" font-weight="600" fill="#14161B">{a}–{b}</text>')
        xx = L
        for r in REG:
            if not c[r]:
                continue
            w = c[r] * unit
            out.append(f'<rect x="{xx:.1f}" y="{yy}" width="{w - 2:.1f}" height="{rowh}" rx="4" fill="{REG[r]}"/>')
            if w > 30:
                out.append(f'<text x="{xx + 14:.1f}" y="{yy + rowh / 2 + 6:.0f}" font-size="17" font-weight="700" fill="#FFFFFF">{c[r]}</text>')
            xx += w
    H = len(bands) * (rowh + gap)
    asia_first = min(u["rank_num"] for u in ROWS if u["region"] == "Asia")
    return f'''<div class="chart"><h3>Who sits where in the ranking</h3>
  <p>Universities per region in each band of ten ranks (ties can push a band above ten). Asia’s first entry is at {asia_first}.</p>
  <div style="margin:12px 0 16px">{legend()}</div>
  <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Region mix by rank band">{"".join(out)}</svg></div>'''


def charts_page():
    return f'''<section class="page charts" id="p7">
  {top(7)}
  <h2 class="disp">The top 50 <span class="serif">in charts</span></h2>
  {score_chart()}
  {band_chart()}
  <div class="foot"><span>Data: THE World University Rankings {EDITION}</span><span>Colours show region</span></div>
</section>'''


def insights():
    mx = country_counts[0][1]
    crows = "".join(
        f'<div class="crow"><div class="cn"><span class="flag">{flags[c]}</span>{c}</div>'
        f'<div class="track"><div style="width:{n / mx * 100:.1f}%;background:{REG[country_region[c]]}"></div></div>'
        f'<div class="n num">{n}</div></div>' for c, n in country_counts)
    cards = "".join(
        f'<div class="card"><div class="v disp num">{c["value"]}<small>{c["unit"]}</small></div><p>{c["text"]}</p></div>'
        for c in CFG["insights"])
    site = CFG["website"]
    return f'''<section class="page ins" id="p8">
  {top(8)}
  <h2 class="disp">What the {EDITION} list <span class="serif">tells us</span></h2>
  <div class="cards">{cards}</div>
  <div class="countries"><h3>Top 50 by country or territory</h3>{crows}</div>
  <div class="src">
    <div><b>Source:</b> {CFG["source"]}</div>
    <div><b>Best for</b> is a short guide to each university’s best known fields, not an official THE subject ranking.<br><br><b>Compiled by {CFG["author"]}, {CFG["location"]}</b><br><a href="{site}">{site.split("//")[-1]}</a></div>
  </div>
</section>'''


def main():
    OUT.mkdir(exist_ok=True)
    SLIDES.mkdir(exist_ok=True)
    html = (f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head><body>'
            + cover() + "".join(list_page(i) for i in range(5)) + charts_page() + insights() + '</body></html>')
    html_path = OUT / f"top50-{EDITION}.html"
    html_path.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        try:
            page.goto(html_path.as_uri(), wait_until="networkidle", timeout=15000)
        except Exception:
            pass  # offline: falls back to locally installed fonts
        page.evaluate("document.fonts.ready")
        pdf = OUT / f"Top-50-Universities-{EDITION}.pdf"
        page.pdf(path=str(pdf), width="1080px", height="1350px", print_background=True)
        for i in range(TOTAL):
            page.locator(f"#p{i + 1}").screenshot(path=str(SLIDES / f"slide-{i + 1}.png"))
        clipped = page.evaluate(
            "() => [...document.querySelectorAll('.st,.nm')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)")
        browser.close()
    if clipped:
        print("Warning, text cut off:", clipped)
    print(f"Built {pdf.relative_to(ROOT)} and {TOTAL} slides in {SLIDES.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
