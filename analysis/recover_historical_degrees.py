#!/usr/bin/env python3
"""Recover historical doctoral status from extracted ALTO catalog metadata.

Usage: python analysis/recover_historical_degrees.py catalog_extracted.csv thesis_metadata.csv entities_combined.jsonl.zip output/
Catalog extraction from the original XLSX: see downloadable analysis archive.
"""
import csv, json, zipfile, re, sys
from collections import Counter, defaultdict
from pathlib import Path

catalog_file, metadata_file, jsonl_zip, destination = sys.argv[1:]
out = Path(destination); out.mkdir(exist_ok=True, parents=True)

def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

catalog = {r["Nom livrable"]: r for r in read(catalog_file)}
metadata = defaultdict(list)
for r in read(metadata_file):
    metadata[r["doc_id"]].append(r)

def classify(text):
    text = text.casefold()
    thesis = bool(re.search(r"\bth[eè]se\b|\bheith\s*\d+\b", text))
    diploma = bool(re.search(r"\bdipl[oô]me\b|\bheidi\s*\d+\b", text))
    return "conflict" if thesis and diploma else "thesis" if thesis else "diploma" if diploma else "unknown"

audit=[]; stats=Counter(); counts=Counter()
with zipfile.ZipFile(jsonl_zip) as z, zipfile.ZipFile(out / "doctoral_ner_recovered.jsonl.zip", "w", zipfile.ZIP_DEFLATED) as target:
    names=[x for x in z.namelist() if x.endswith(".jsonl") and not x.startswith("__MACOSX")]
    if len(names)!=1:raise ValueError("Expected exactly one JSONL")
    with z.open(names[0]) as src, target.open("doctoral_ner_recovered.jsonl", "w") as dest:
        for line in src:
            doc=json.loads(line);doc_id=str(doc["doc_id"])
            candidates=sorted(metadata.get(doc_id, []),key=lambda x:bool(x.get("year","").strip()),reverse=True)
            m=candidates[0] if candidates else {}
            c=catalog.get(doc_id, {})
            year=int(m["year"]) if m.get("year","").isdigit() else None
            status=classify(c.get("Contenu",""))
            include=(year is not None and year>=1927 and
                     (status=="thesis" or (status=="unknown" and m.get("thesis_type")=="PhD")))
            if status=="conflict":include=False
            label="include" if include else status if status!="unknown" else "unverified"
            audit.append({"doc_id":doc_id,"year":year or "","institution":m.get("institution",""),
                          "previous_type":m.get("thesis_type",""),"catalog_class":status,
                          "catalog_content":c.get("Contenu",""),"decision":label,"include":int(include)})
            stats[label]+=1
            if include:
                dest.write(line)
                counts[(year//10*10,m.get("institution",""))]+=1

def export(name, data, keys):
    with open(out/name,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(data)

export("degree_audit.csv",audit,list(audit[0]))
export("doctoral_metadata.csv",[r for r in audit if r["include"]],list(audit[0]))
export("doctoral_counts_by_decade.csv",[
    {"decade":dec,"institution":inst,"doctorates":v}
    for (dec,inst),v in sorted(counts.items())],["decade","institution","doctorates"])
print(dict(stats))
