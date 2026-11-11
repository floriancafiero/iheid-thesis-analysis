#!/usr/bin/env python3
"""Document-level entity salience for IHEID NER exports.

Usage:
  python analysis/document_salience.py entities_combined.jsonl.zip
  python analysis/document_salience.py entities_combined.jsonl.zip --metadata metadata.csv

Optional metadata.csv columns: doc_id, year, institution, degree.
No years or degree types are inferred from document IDs.
"""
import argparse
import csv
import json
import math
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

# Deliberately conservative aliases: ambiguous OCR strings (e.g. "us",
# "etat", "states") are excluded rather than incorrectly mapped.
ALIASES = {
    "France": ["france", "la france"],
    "United States": ["united states", "the united states", "etats-unis", "etats unis", "etats-unis d'amerique", "usa", "u.s.a.", "etats unis d amerique"],
    "China": ["chine", "la chine", "china", "the people's republic of china", "republique populaire de chine", "prc"],
    "Switzerland": ["suisse", "switzerland", "schweiz", "la suisse"],
    "Germany": ["allemagne", "germany", "deutschland", "rfa", "rda"],
    "United Kingdom": ["royaume-uni", "united kingdom", "great britain", "grande-bretagne"],
    "Russia": ["russie", "russia", "russian federation", "federation de russie"],
    "USSR": ["urss", "ussr", "soviet union", "union sovietique"],
    "India": ["inde", "india", "l'inde"],
    "Brazil": ["bresil", "brazil", "brasil"],
    "Japan": ["japon", "japan"],
    "Turkey": ["turquie", "turkey", "turkiye"],
    "Israel": ["israel"],
    "Iran": ["iran"],
    "Italy": ["italie", "italy", "italia"],
    "Canada": ["canada"],
    "Mexico": ["mexique", "mexico"],
    "Cameroon": ["cameroun", "cameroon"],
    "Mali": ["mali"],
    "Senegal": ["senegal"],
    "Burkina Faso": ["burkina faso", "haute-volta", "upper volta"],
    "Madagascar": ["madagascar"],
    "Vietnam": ["vietnam", "viet nam"],
    "Indonesia": ["indonesie", "indonesia"],
    "Ukraine": ["ukraine"],
    "Colombia": ["colombie", "colombia"],
    "South Africa": ["afrique du sud", "south africa"],
}
ORGANIZATIONS = {
    "United Nations": ["onu", "united nations", "organisation des nations unies", "nations unies", "un"],
    "League of Nations": ["societe des nations", "league of nations", "sdn"],
    "World Bank": ["banque mondiale", "world bank"],
    "IMF": ["fmi", "imf", "international monetary fund", "fonds monetaire international"],
    "WTO": ["omc", "wto", "world trade organization", "organisation mondiale du commerce"],
    "WHO": ["oms", "who", "world health organization", "organisation mondiale de la sante"],
    "ILO": ["oit", "ilo", "international labour organization", "organisation internationale du travail", "bureau international du travail"],
    "UNESCO": ["unesco"],
    "UNICEF": ["unicef"],
    "European Union": ["union europeenne", "european union"],
    "European Commission": ["commission europeenne", "european commission"],
    "OECD": ["ocde", "oecd", "organisation de cooperation et de developpement economiques"],
    "ICRC": ["cicr", "icrc", "comite international de la croix rouge", "international committee of the red cross"],
}
def norm(s):
    s = unicodedata.normalize("NFKD", s.lower().strip())
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c)))

COUNTRY_LOOKUP = {norm(alias): label for label, aliases in ALIASES.items() for alias in aliases}
ORG_LOOKUP = {norm(alias): label for label, aliases in ORGANIZATIONS.items() for alias in aliases}
def input_records(path):
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            members = [n for n in z.namelist() if n.endswith(".jsonl") and not n.startswith("__MACOSX")]
            if len(members) != 1:
                raise ValueError("Expected exactly one JSONL in ZIP")
            with z.open(members[0]) as stream:
                for line in stream:
                    yield json.loads(line)
    else:
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                yield json.loads(line)

def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--metadata", type=Path, help="CSV with doc_id,year,institution,degree")
    p.add_argument("--out", type=Path, default=Path("analysis/output"))
    p.add_argument("--min-mentions", type=int, default=5)
    p.add_argument("--min-per-10k", type=float, default=2.0)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    meta = {}
    if args.metadata:
        with args.metadata.open(encoding="utf-8-sig", newline="") as f:
            meta = {r["doc_id"]: r for r in csv.DictReader(f)}
    docs = []
    for x in input_records(args.input):
        did = str(x["doc_id"])
        words = int(x.get("words_processed") or 0)
        if words <= 0:
            continue
        row = meta.get(did, {})
        prefix = did.split("_", 1)[0]
        institution = row.get("institution") or (prefix if prefix in ("HEI", "IUED", "IHEID") else "Unmapped")
        year_str = str(row.get("year") or "").strip()
        year = int(year_str) if year_str.isdigit() else None
        degree = row.get("degree") or "Unknown"
        counts = Counter()
        # Labels are used from relevant location / organization types ONLY.
        for ner_type, named in x.get("entities_by_type", {}).items():
            if ner_type in ("LOC", "GPE"):
                lookup, group = COUNTRY_LOOKUP, "country"
            elif ner_type == "ORG":
                lookup, group = ORG_LOOKUP, "organization"
            else:
                continue
            for mention, n in named.items():
                label = lookup.get(norm(mention))
                if label:
                    counts[(group, label)] += int(n)
        docs.append(dict(doc_id=did, institution=institution, degree=degree,
                         year=year, decade=year // 10 * 10 if year else None,
                         words=words, counts=counts))
    # Individual document metrics, suitable for inspecting outliers.
    details = []
    for d in docs:
        for (kind, name), n in d["counts"].items():
            rate = n * 10000 / d["words"]
            details.append(dict(doc_id=d["doc_id"], institution=d["institution"],
                                degree=d["degree"], year=d["year"] or "",
                                entity_type=kind, entity=name, mentions=n,
                                words=d["words"], per_10k=round(rate, 3),
                                significant=int(n >= args.min_mentions and rate >= args.min_per_10k)))
    write_csv(args.out / "document_entities.csv", details,
              ["doc_id", "institution", "degree", "year", "entity_type", "entity",
               "mentions", "words", "per_10k", "significant"])
    # Separate overall and institution-level panels; add decades only with year metadata.
    panels = [("all", "All documents", docs)]
    for institution in sorted(set(d["institution"] for d in docs)):
        panels.append(("institution", institution, [d for d in docs if d["institution"] == institution]))
    if any(d["year"] for d in docs):
        for decade in sorted(set(d["decade"] for d in docs if d["decade"] is not None)):
            panels.append(("decade", str(decade), [d for d in docs if d["decade"] == decade]))
    all_entities = sorted(set(k for d in docs for k in d["counts"]))
    rows = []
    overall_counts = Counter()
    for d in docs:
        for e, n in d["counts"].items():
            if n >= args.min_mentions and n * 10000 / d["words"] >= args.min_per_10k:
                overall_counts[e] += 1
    for group, panel, group_docs in panels:
        total_words = sum(d["words"] for d in group_docs)
        for kind, name in all_entities:
            mentioned = sum(d["counts"].get((kind, name), 0) > 0 for d in group_docs)
            significant = sum((n := d["counts"].get((kind, name), 0)) >= args.min_mentions
                              and n * 10000 / d["words"] >= args.min_per_10k for d in group_docs)
            count = sum(d["counts"].get((kind, name), 0) for d in group_docs)
            prevalence = significant / len(group_docs) if group_docs else 0
            global_prev = overall_counts[(kind, name)] / len(docs) if docs else 0
            # Ratio has a small smoothing term to avoid infinite scores.
            specificity = math.log2((prevalence + 0.005) / (global_prev + 0.005))
            rows.append(dict(group=group, panel=panel, entity_type=kind, entity=name,
                             documents=len(group_docs), words=total_words, documents_any=mentioned,
                             documents_significant=significant, prevalence_pct=round(prevalence * 100, 2),
                             mentions=count, per_100k_words=round(count * 100000 / total_words, 2) if total_words else 0,
                             specificity_log2=round(specificity, 3)))
    write_csv(args.out / "summary.csv", rows,
              ["group", "panel", "entity_type", "entity", "documents", "words", "documents_any",
               "documents_significant", "prevalence_pct", "mentions", "per_100k_words", "specificity_log2"])
    print(f"{len(docs):,} documents; {len(details):,} nonzero document-entity pairs; {len(rows):,} summary rows")
    print(f"Output: {args.out}")
    print("Historical decade comparison needs --metadata with document-level years.")
    print("Unmapped institution rows must NOT be merged into HEI/IUED/IHEID by guesswork.")

if __name__ == "__main__":
    main()
