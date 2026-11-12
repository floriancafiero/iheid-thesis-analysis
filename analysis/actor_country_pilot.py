#!/usr/bin/env python3
"""Geographic signal from verified political-person Wikidata QIDs; stdlib only.

Usage: python analysis/actor_country_pilot.py --zip doctoral_ner_recovered.jsonl.zip --metadata doctoral_metadata_recovered.csv --countries document_entity_counts.csv --registry analysis/verified_actor_registry.csv --out comparison.csv

Country attribution is by a documented political jurisdiction, never by nationality alone.
This is a small positive-evidence pilot, not full automatic entity linking.
"""
import argparse,csv,zipfile,json,re,unicodedata
from pathlib import Path
from collections import Counter,defaultdict
JURISDICTION={"France":"France","Royaume-Uni":"United Kingdom","États-Unis":"United States","Chine":"China","Inde":"India","Irak":"Iraq","Palestine":"Palestine","Iran":"Iran","Israël":"Israel","Bolivie":"Bolivia","Brésil":"Brazil","Ghana":"Ghana","RD Congo":"DR Congo","Ukraine":"Ukraine","Allemagne":"Germany","URSS":"Soviet Union","RDA":None,"Russie":"Russia","Cuba":"Cuba","Yougoslavie":None,"Turquie":"Turkey","Cambodge":"Cambodia","Afrique du Sud":"South Africa","Corée du Nord":"North Korea","Sénégal":"Senegal"}
def norm(s):
 s=unicodedata.normalize("NFKD",s.lower().replace("’","'"))
 return " ".join(re.sub("[^a-z0-9]+"," ","".join(c for c in s if not unicodedata.combining(c))).split())
def read(path):
 with open(path,encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def records(path):
 with zipfile.ZipFile(path) as z:
  names=[x for x in z.namelist() if x.endswith(".jsonl") and not x.startswith("__MACOSX")]
  if len(names)!=1:raise ValueError("Expected one JSONL in archive")
  with z.open(names[0]) as f:
   for line in f:yield json.loads(line)
def main():
 p=argparse.ArgumentParser()
 for k in ["zip","metadata","countries","registry","out"]:p.add_argument("--"+k,required=True)
 a=p.parse_args()
 reg=read(a.registry);lookup={};byqid={r["wikidata_qid"]:r for r in reg}
 for r in reg:
  for name in r["accepted_ner_surfaces"].split("|"):
   n=norm(name)
   if n in lookup and lookup[n]!=r["wikidata_qid"]:raise ValueError("Alias collision: "+name)
   lookup[n]=r["wikidata_qid"]
 meta={r["doc_id"]:r for r in read(a.metadata) if r.get("include")=="1"}
 geo=Counter()
 for r in read(a.countries):
  if r["category"]=="country" and r["channel"]=="direct":geo[(r["doc_id"],r["entity"])]+=int(r["mentions"])
 evidence={}
 for d in records(a.zip):
  did=str(d["doc_id"])
  if did not in meta:continue
  ctr=Counter()
  for typ in ("PER","PERSON"):
   for name,n in d.get("entities_by_type",{}).get(typ,{}).items():
    qid=lookup.get(norm(name))
    if qid:ctr[qid]+=int(n)
  c=defaultdict(Counter)
  for qid,n in ctr.items():c[byqid[qid]["political_jurisdiction"]][qid]+=n
  evidence[did]=c
 rows=[]
 for juris,country in JURISDICTION.items():
  if not country:continue
  actor=multi=joint=only=direct=0
  for did in meta:
   counts=evidence.get(did,{}).get(juris,{})
   total=sum(counts.values());strong=total>=5; geo5=geo[(did,country)]>=5
   actor+=strong;multi+=strong and len(counts)>=2;direct+=geo5
   joint+=strong and geo5;only+=strong and not geo5
  rows.append(dict(jurisdiction=juris,n_curated=sum(r["political_jurisdiction"]==juris for r in reg),
    n_phd=len(meta),geography_ge5=direct,actors_ge5=actor,actors_2distinct_ge5=multi,concordant=joint,actors_only=only))
 with open(a.out,"w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print("PhDs",len(meta),"verified people",len(reg),"actor/country positive pairs",sum(r["actors_ge5"] for r in rows),
 "concordant",sum(r["concordant"] for r in rows))
if __name__=="__main__":main()
