"""Check the data and the built PDF agree.

Usage:
    python check.py                      # uses data/edition-2027.json
    python check.py data/edition-2028.json

Run after build.py. Exits with an error if anything is wrong, so CI goes red.
"""
import csv
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).parent
CONFIG = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "edition-2027.json"
CFG = json.loads(CONFIG.read_text(encoding="utf-8"))
REGIONS = {"Americas", "Europe", "Asia", "Oceania"}
PAGES = 8

errors = []


def norm(text):
    """Keep letters only, lower case and single spaced, so line breaks,
    punctuation and the flag emoji next to each city don't affect matching."""
    return " ".join(re.sub(r"[^a-z]+", " ", text.lower()).split())


# 1. The CSV is complete and consistent
with open(CONFIG.parent / CFG["data_file"], newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 50:
    errors.append(f"expected 50 rows, got {len(rows)}")

names = [r["university"] for r in rows]
dupes = {n for n in names if names.count(n) > 1}
if dupes:
    errors.append(f"duplicate universities: {sorted(dupes)}")

prev_rank, prev_score = 0, 101.0
for i, r in enumerate(rows, start=2):  # line 1 is the header
    for field in ("rank", "university", "city", "country", "country_code", "region", "overall_score", "best_for"):
        if not r.get(field, "").strip():
            errors.append(f"line {i}: {field} is empty")
    rank = int(r["rank"].lstrip("="))
    score = float(r["overall_score"])
    if rank < prev_rank:
        errors.append(f"line {i}: rank {r['rank']} is out of order")
    if score > prev_score:
        errors.append(f"line {i}: score {score} is higher than the row above")
    if not re.fullmatch(r"[A-Z]{2}", r["country_code"]):
        errors.append(f"line {i}: country_code '{r['country_code']}' is not two capital letters")
    if r["region"] not in REGIONS:
        errors.append(f"line {i}: region '{r['region']}' is not one of {sorted(REGIONS)}")
    prev_rank, prev_score = rank, score

# 2. The PDF and slides exist and match the CSV
pdf_path = ROOT / "output" / f"Top-50-Universities-{CFG['edition']}.pdf"
if not pdf_path.exists():
    errors.append(f"{pdf_path.relative_to(ROOT)} is missing, run build.py first")
else:
    reader = PdfReader(pdf_path)
    if len(reader.pages) != PAGES:
        errors.append(f"PDF has {len(reader.pages)} pages, expected {PAGES}")
    raw = " ".join(p.extract_text() or "" for p in reader.pages)
    pdf_text = norm(raw)
    pdf_words = raw.split()
    for r in rows:
        for field in ("university", "best_for"):
            if norm(r[field]) not in pdf_text:
                errors.append(f"{r['university']}: {field} '{r[field]}' not found in the PDF")
        # Scores must be real, copyable text in the PDF, not just look right
        if f"{float(r['overall_score']):.1f}" not in pdf_words:
            errors.append(f"{r['university']}: score {r['overall_score']} is not readable text in the PDF")

for i in range(1, PAGES + 1):
    if not (ROOT / "output" / "slides" / f"slide-{i}.png").exists():
        errors.append(f"output/slides/slide-{i}.png is missing")

if errors:
    print(f"{len(errors)} problem(s) found:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print(f"All good: 50 universities, {PAGES} pages and {PAGES} slides match the data.")
