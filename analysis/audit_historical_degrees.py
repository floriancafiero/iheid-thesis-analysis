#!/usr/bin/env python3
"""Audit degree labels for historical IHEID thesis records.

Run: python analysis/audit_historical_degrees.py thesis_metadata.csv entities_combined.jsonl.zip
Produces an audit of 1927–1989 documents, and a *conservative* doctoral subset.
Optional --evidence CSV (doc_id,degree_verified,evidence_url,evidence_note).
Do not reclassify 'Master/Other' as master or doctorate automatically.
"""
import argparse,csv,json,zipfile
from collections import defaultdict,Counter
from pathlib import Path
def readcsv(p):
    with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def writecsv(path,rows,fields):
    with path.open("w",encoding="utf8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        writer.writeheader();writer.writerows(rows)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("metadata",type=Path)
    p.add_argument("jsonzip",type=Path)
    p.add_argument("--evidence",type=Path,default=Path(__file__).with_name("historical_degree_evidence.csv"))
    p.add_argument("--out",type=Path,default=Path("analysis/historical_degree_audit"))
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    cat=defaultdict(list)
    for r in readcsv(a.metadata):cat[r["doc_id"]].append(r)
    evidence={r["doc_id"]:r for r in readcsv(a.evidence)} if a.evidence.exists() else {}
    documents={}
    with zipfile.ZipFile(a.jsonzip) as z:
        matches=[n for n in z.namelist() if n.endswith(".jsonl") and not n.startswith("__MACOSX")]
        if len(matches)!=1:raise ValueError("Expected one JSONL")
        with z.open(matches[0]) as f:
            for line in f:
                d=json.loads(line);key=str(d["doc_id"])
                if key in documents:raise ValueError(f"Duplicate {key}")
                documents[key]=d
    records=[]
    for did,d in documents.items():
        rows=cat.get(did,[])
        rows=sorted(rows,key=lambda r:bool(r.get("year")),reverse=True)
        r=rows[0] if rows else {}
        year=int(r["year"]) if r.get("year","").isdigit() else None
        ev=evidence.get(did,{})
        verified=ev.get("degree_verified","").lower()
        if verified=="phd":status="verified_phd"
        elif verified in ("diploma","master","other_non_phd"):status="verified_non_phd"
        elif year is None:status="unknown_year"
        elif year<1927:status="before_1927"
        elif r.get("thesis_type")=="PhD":status="catalog_phd"
        else:status="degree_unverified"
        records.append(dict(doc_id=did,year=year or "",title=r.get("title",""),
                            institution=r.get("institution",""),
                            catalog_type=r.get("thesis_type",""),
                            words_processed=d.get("words_processed",""),
                            status=status,degree_verified=verified,
                            evidence_url=ev.get("evidence_url",""),
                            evidence_note=ev.get("evidence_note",""),
                            metadata_rows=len(rows),
                            metadata_year_conflict=int(len({x["year"] for x in rows if x["year"]})>1)))
    records.sort(key=lambda x:(int(x["year"]) if x["year"] else 9999,x["doc_id"]))
    fields=list(records[0])
    writecsv(a.out/"degree_audit_all_ner.csv",records,fields)
    old=[r for r in records if r["year"] and 1927<=int(r["year"])<1990]
    writecsv(a.out/"degree_audit_1927_1989.csv",old,fields)
    selected={r["doc_id"] for r in records if r["year"] and int(r["year"])>=1927
              and r["status"] in {"verified_phd","catalog_phd"}}
    writecsv(a.out/"doctoral_metadata_revised.csv",
             [r for r in records if r["doc_id"] in selected],fields)
    with zipfile.ZipFile(a.out/"doctoral_entities_revised.jsonl.zip","w",zipfile.ZIP_DEFLATED) as z:
        with z.open("doctoral_entities_revised.jsonl","w") as f:
            for k,d in documents.items():
                if k in selected:f.write((json.dumps(d,ensure_ascii=False)+"\n").encode("utf8"))
    print("Historical",len(old),Counter(x["status"] for x in old))
    print("Conservative PhD subset",len(selected))
if __name__=="__main__":main()
