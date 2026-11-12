#!/usr/bin/env python3
"""Wikidata name-to-human candidate linker. No profession exclusions or automatic thesis subject assignments. The source NER lacks citation and bibliography positions."""
import argparse, csv, json, re, time, unicodedata
from pathlib import Path
import requests

BASE = "https://www.wikidata.org/w/api.php"
UA = "IHEID-historical-research/0.4 (https://github.com/floriancafiero/iheid-thesis-analysis)"

def norm(s):
    s=unicodedata.normalize("NFKD",str(s).casefold().replace("’","'"))
    return " ".join(re.sub("[^a-z0-9]+"," ","".join(c for c in s if not unicodedata.combining(c))).split())

def qids(claims,key):
    result=set()
    for statement in claims.get(key,[]):
        v=statement.get("mainsnak",{}).get("datavalue",{}).get("value",{})
        if isinstance(v,dict) and v.get("id"): result.add(v["id"])
    return sorted(result)

def labels(item):
    x=item.get("labels",{})
    return next((x[l]["value"] for l in ("en","fr","de") if l in x),"")

class Wikidata:
    def __init__(self,delay):
        self.session=requests.Session()
        self.session.headers["User-Agent"]=UA
        self.delay=delay
    def call(self,**params):
        for attempt in range(4):
            try:
                r=self.session.get(BASE,params={"format":"json",**params},timeout=30)
                if r.status_code in (429,500,502,503,504):
                    time.sleep(3*(attempt+1));continue
                r.raise_for_status()
                time.sleep(self.delay)
                return r.json()
            except requests.RequestException:
                if attempt==3:raise
                time.sleep(2*(attempt+1))
        raise RuntimeError("Wikidata request failed")
    def search(self,name):
        found=set()
        for lang in ("en","fr","de"):
            j=self.call(action="wbsearchentities",search=name,language=lang,limit=10,type="item")
            for r in j.get("search",[]):
                if norm(r.get("label",""))==norm(name) or norm(r.get("match",{}).get("text",""))==norm(name):
                    found.add(r["id"])
            if found:break
        return sorted(found)
    def entities(self,ids):
        result={}
        for i in range(0,len(ids),40):
            j=self.call(action="wbgetentities",ids="|".join(ids[i:i+40]),
                        props="claims|labels|descriptions",languages="en|fr|de")
            result.update(j.get("entities",{}))
        return result

def evaluate(wd,surface):
    """QID identification only. Never infer studied subject or country."""
    found=wd.search(surface)
    data=wd.entities(found)
    people=[]
    for qid,entity in data.items():
        cs=entity.get("claims",{})
        if "Q5" not in qids(cs,"P31"):continue
        people.append(dict(qid=qid,person_label=labels(entity),
            occupation_qids="|".join(qids(cs,"P106")),
            position_qids="|".join(qids(cs,"P39")),
            citizenship_qids="|".join(qids(cs,"P27"))))
    if len(people)==1:
        return {"status":"unique_human_name_candidate",**people[0],
                "all_human_qids":people[0]["qid"]}
    if len(people)>1:
        return {"status":"ambiguous_multiple_human_qids",
                "all_human_qids":"|".join(p["qid"] for p in people)}
    return {"status":"no_exact_human_match","all_human_qids":""}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("candidates",type=Path)
    p.add_argument("--start",type=int,default=0,
                   help="Zero-based row offset in entire inventory")
    p.add_argument("--batch-size",type=int,default=100,
                   help="Operational batch size, never a scientific cutoff")
    p.add_argument("--out",type=Path,default=Path("wikidata_candidates.csv"))
    p.add_argument("--delay",type=float,default=.7)
    args=p.parse_args()
    if args.start<0 or args.batch_size<1:raise ValueError("Invalid range")
    with args.candidates.open(encoding="utf-8-sig",newline="") as f:
        candidates=list(csv.DictReader(f))
    selected=candidates[args.start:args.start+args.batch_size]
    if not selected:raise ValueError(f"Empty batch at {args.start}; total {len(candidates)}")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    fields=["source_row","surface","mentions","documents","queue","priority_score",
            "title_doc_count","theses_with_5plus","max_mentions_in_one_thesis",
            "status","qid","person_label","occupation_qids","position_qids",
            "citizenship_qids","all_human_qids","error"]
    prior={}
    if args.out.exists():
        with args.out.open(encoding="utf8",newline="") as f:
            prior={r["source_row"]:r for r in csv.DictReader(f)}
    wd=Wikidata(args.delay)
    rows=[]
    for offset,r in enumerate(selected,args.start):
        key=str(offset)
        if key in prior and prior[key].get("status")!="network_error":
            output=prior[key]
        else:
            try:
                output={"source_row":key,**r,**evaluate(wd,r["surface"])}
            except (requests.RequestException,ValueError,RuntimeError) as exc:
                output={"source_row":key,**r,"status":"network_error","error":str(exc)[:200]}
        rows.append(output)
        if (offset-args.start+1)%20==0:
            print(f"Rows {args.start}..{offset} / {len(candidates)} : {output.get('status')}",flush=True)
        with args.out.open("w",encoding="utf8",newline="") as f:
            writer=csv.DictWriter(f,fields,extrasaction="ignore")
            writer.writeheader();writer.writerows(rows)
    print(f"{len(rows)} name candidates processed, offset {args.start}, total {len(candidates)}")
    print("These are identity candidates ONLY; subject vs bibliography cannot be inferred from NER counts.")

if __name__=="__main__":main()
