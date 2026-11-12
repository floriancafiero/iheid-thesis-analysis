#!/usr/bin/env python3
"""Batch candidate Wikidata linking for PERSON/PER NER.

Usage: python analysis/wikidata_batch_linker.py ranked_wikidata_candidates.csv \
  --limit 450 --out wikidata_candidates.csv

Requires requests and public Wikidata API network access. Search hits are
CANDIDATES, not confirmed people or country assignments. Do not treat P27 or
birthplace as a country studied. Caches every completed lookup to resume.
"""
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
    found=wd.search(surface)
    data=wd.entities(found)
    candidates=[]
    roles=set()
    for qid,entity in data.items():
        claims=entity.get("claims",{})
        if "Q5" not in qids(claims,"P31"):continue
        positions=qids(claims,"P39")
        if not positions:continue
        candidates.append((qid,positions,qids(claims,"P27")))
        roles.update(positions)
    office_entities=wd.entities(sorted(roles))
    answer=[]
    for qid,positions,citizenship in candidates:
        role_titles=[labels(office_entities.get(p,{})) for p in positions]
        # Role filtering, not just politician occupation or country of citizenship.
        positive=[r for r in role_titles if any(w in norm(r) for w in (
            "minister","president","chancellor","ambassador","senator",
            "parliament","premier","king","queen","secretary of state","head of state",
            "head of government","governor","politician","commissar"))]
        positive=[r for r in positive if not any(w in norm(r) for w in (
            "university","european commission","european parliament",
            "united nations","international court","olympic"))]
        if not positive:continue
        office_country_qids=sorted({c for pos in positions for c in qids(office_entities.get(pos,{}).get("claims",{}),"P17")})
        answer.append(dict(qid=qid,role_titles="|".join(positive[:10]),
                           office_country_qids="|".join(office_country_qids),
                           citizenship_qids="|".join(citizenship)))
    if len(answer)==1:
        return {"status":"political_person_candidate",**answer[0],"all_exact_qids":"|".join(found)}
    if len(answer)>1:
        return {"status":"ambiguous_multiple_political_people","all_exact_qids":"|".join(a["qid"] for a in answer)}
    return {"status":"no_unambiguous_political_office","all_exact_qids":"|".join(found)}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("candidates",type=Path)
    a.add_argument("--limit",type=int,default=450)
    a.add_argument("--out",type=Path,default=Path("wikidata_candidates.csv"))
    a.add_argument("--delay",type=float,default=.35)
    args=a.parse_args()
    with args.candidates.open(encoding="utf-8-sig",newline="") as f:
        candidates=list(csv.DictReader(f))[:args.limit]
    fields=["surface","mentions","documents","status","qid","role_titles",
            "office_country_qids","citizenship_qids","all_exact_qids","error"]
    prior={}
    if args.out.exists():
        with args.out.open(encoding="utf8",newline="") as f:
            prior={r["surface"]:r for r in csv.DictReader(f)}
    wd=Wikidata(args.delay)
    results=[]
    for i,r in enumerate(candidates,1):
        known=prior.get(r["surface"])
        if known and known.get("status")!="network_error":
            out=known
        else:
            try:
                out={**r,**evaluate(wd,r["surface"])}
            except requests.RequestException as err:
                out={**r,"status":"network_error","error":str(err)[:200]}
        results.append(out)
        if i%20==0:print(i,"/",len(candidates),out.get("status"),flush=True)
        with args.out.open("w",encoding="utf8",newline="") as f:
            writer=csv.DictWriter(f,fields,extrasaction="ignore")
            writer.writeheader();writer.writerows(results)
    print("Wrote",len(results),"rows. Candidate links must be resolved and geopolitical jurisdictions checked before aggregation.")
if __name__=="__main__":main()
