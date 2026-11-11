#!/usr/bin/env python3
"""Filter analysis corpus to dated PhDs in or after 1927.

python analysis/filter_doctorates.py thesis_metadata.csv entities_combined.jsonl.zip \
 --hierarchy analysis/hierarchy_output/document_entities.csv
"""
import argparse,csv,json,zipfile
from collections import Counter,defaultdict
from pathlib import Path

def csvout(path,rows,columns):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)

def metadata(path):
    records=defaultdict(list)
    with path.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            records[row["doc_id"]].append(row)
    out={}
    for did,rows in records.items():
        dated=[r for r in rows if r["year"].strip()]
        if len({(r["year"],r["thesis_type"],r["institution"]) for r in dated})>1:
            raise ValueError(f"Conflicting metadata: {did}")
        if len({(r["thesis_type"],r["institution"]) for r in rows})>1:
            raise ValueError(f"Conflicting document type: {did}")
        out[did]=dated[0] if dated else rows[0]
    return out

def source(path):
    with zipfile.ZipFile(path) as z:
        files=[n for n in z.namelist() if n.endswith(".jsonl") and not n.startswith("__MACOSX")]
        if len(files)!=1:raise ValueError("Expected one JSONL in input ZIP")
        with z.open(files[0]) as f:
            for line in f:yield json.loads(line)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("metadata",type=Path)
    p.add_argument("entities_zip",type=Path)
    p.add_argument("--hierarchy",type=Path)
    p.add_argument("--out",type=Path,default=Path("analysis/doctoral_output"))
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    catalog=metadata(a.metadata)
    keep={};excluded=[];seen=set();counts=Counter()
    with zipfile.ZipFile(a.out/"doctoral_entities_1927plus.jsonl.zip","w",zipfile.ZIP_DEFLATED) as z:
        with z.open("doctoral_entities_1927plus.jsonl","w") as f:
            for doc in source(a.entities_zip):
                did=str(doc["doc_id"])
                if did in seen:raise ValueError(f"Repeated JSONL doc_id: {did}")
                seen.add(did);row=catalog.get(did)
                if row is None:reason="metadata_missing"
                elif row["thesis_type"]!="PhD":reason="not_doctorate"
                elif not row["year"].strip():reason="year_missing"
                else:
                    try:year=int(row["year"])
                    except ValueError:reason="year_invalid"
                    else:reason="before_1927" if year<1927 else None
                if reason:
                    counts[reason]+=1;excluded.append({"doc_id":did,"reason":reason});continue
                keep[did]=row
                f.write((json.dumps(doc,ensure_ascii=False)+"\n").encode("utf-8"))
    fields=["doc_id","author","title","year","thesis_type","institution","has_text"]
    csvout(a.out/"doctoral_metadata_1927plus.csv",[keep[k] for k in sorted(keep)],fields)
    csvout(a.out/"excluded_document_ids.csv",excluded,["doc_id","reason"])
    decades=Counter((int(r["year"])//10*10,r["institution"]) for r in keep.values())
    csvout(a.out/"doctoral_counts_by_decade.csv",
           [{"decade":dec,"institution":inst,"documents":n} for (dec,inst),n in sorted(decades.items())],
           ["decade","institution","documents"])
    if a.hierarchy:
        with a.hierarchy.open(encoding="utf-8-sig",newline="") as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;rows=[]
            for r in reader:
                if r["doc_id"] in keep:
                    md=keep[r["doc_id"]]
                    r.update(institution=md["institution"],year=md["year"],degree="PhD")
                    rows.append(r)
        csvout(a.out/"doctoral_hierarchy_1927plus.csv",rows,fields)
    report={"total_ner_documents":len(seen),"included_doctorates":len(keep),
            "exclusions":dict(counts),
            "by_institution":dict(Counter(r["institution"] for r in keep.values()))}
    (a.out/"filter_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
