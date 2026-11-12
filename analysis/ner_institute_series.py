#!/usr/bin/env python3
"""Recalculate institute-separated historical NER, with tracked organizational aliases.

Run: python analysis/ner_institute_series.py doctoral_ner_recovered.jsonl.zip doctoral_metadata_recovered.csv
"""
import argparse,csv,json,re,unicodedata,zipfile
from collections import Counter
from pathlib import Path

ALIAS={
"SDN":"société des nations|societe des nations|la société des nations|league of nations|the league of nations|sdn|s.d.n.|völkerbund|völkerbundes|der völkerbund|the “ league of nations",
"ONU":"nations unies|les nations unies|organisation des nations unies|l’organisation des nations unies|united nations|the united nations|onu|l’onu",
"CEE/EEC":"cee|eec|communauté économique européenne|european economic community|the european economic community",
"CE/EC":"communauté européenne|european community|the european community|european communities|the european communities|communautés européennes",
"UE/EU":"union européenne|l’union européenne|european union|the european union|the eu|europäische union",
"GATT":"gatt|general agreement on tariffs and trade|accord général sur les tarifs douaniers et le commerce",
"OMC":"omc|wto|world trade organization|world trade organisation|organisation mondiale du commerce",
"Banque mondiale":"banque mondiale|world bank|the world bank|international bank for reconstruction and development|ibrd",
"FMI":"fmi|imf|fonds monétaire international|international monetary fund",
"HCR":"hcr|unhcr|un hcr|united nations high commissioner for refugees|haut commissariat des nations unies pour les réfugiés",
"WEF":"wef|world economic forum|forum économique mondial",
"CSCE":"csce|conference on security and cooperation in europe",
"OSCE":"osce|organisation pour la sécurité et la coopération en europe"
}
FAMILIES={"Construction européenne":["CEE/EEC","CE/EC","UE/EU"],
 "Gouvernance commerciale":["GATT","OMC"],"Dialogue sécuritaire européen":["CSCE","OSCE"]}
def norm(s):
 s=unicodedata.normalize("NFKD",s.casefold().replace("’","'"))
 s="".join(c for c in s if not unicodedata.combining(c))
 return " ".join(re.sub(r"[^a-z0-9]+"," ",s).split())
lookup={}
for entity,names in ALIAS.items():
 for name in names.split("|"):
  k=norm(name)
  if k in lookup and lookup[k]!=entity:raise ValueError(f"Collision: {k}")
  lookup[k]=entity
def write(path,rows,fields):
 with path.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser()
 p.add_argument("input_zip",type=Path);p.add_argument("metadata",type=Path)
 p.add_argument("--output",type=Path,default=Path("analysis/institute_series"))
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 with a.metadata.open(encoding="utf-8-sig",newline="") as f:
  metadata={row["doc_id"]:row for row in csv.DictReader(f)}
 docs=[];aud=Counter()
 with zipfile.ZipFile(a.input_zip) as z:
  names=[n for n in z.namelist() if n.endswith(".jsonl") and not n.startswith("__MACOSX")]
  if len(names)!=1:raise ValueError("Expected one JSONL")
  with z.open(names[0]) as f:
   for line in f:
    item=json.loads(line);did=str(item["doc_id"])
    if did not in metadata:continue
    m=metadata[did];year=int(m["year"]);inst=m["institution"]
    if year<1927 or inst not in ("HEI","IUED","IHEID"):continue
    counts=Counter()
    for typ,entities in item["entities_by_type"].items():
     if typ not in ("ORG","MISC"):continue
     for name,n in entities.items():
      k=norm(name);entity=lookup.get(k)
      if entity is None:continue
      # Avoid short acronyms in MISC (potential OCR noise).
      if len(k)<=3 and typ!="ORG":continue
      counts[entity]+=int(n);aud[(entity,typ,name)]+=int(n)
    for family,members in FAMILIES.items():
     counts[family]=sum(counts[key] for key in members)
    row={"doc_id":did,"institution":inst,"year":year,
         "words":int(item.get("words_processed",0))}
    row.update({k:counts[k] for k in list(ALIAS)+list(FAMILIES)})
    docs.append(row)
 if not docs:raise ValueError("No matching doctorates")
 entities=list(ALIAS)+list(FAMILIES)
 write(a.output/"document_counts.csv",docs,["doc_id","institution","year","words"]+entities)
 write(a.output/"alias_audit.csv",
  [{"entity":e,"ner_type":t,"variant":v,"mentions":n}
   for (e,t,v),n in aud.most_common()],["entity","ner_type","variant","mentions"])
 panel=[]
 for inst in ("HEI","IUED","IHEID"):
  subset=[r for r in docs if r["institution"]==inst]
  if not subset:continue
  for y in range(min(r["year"] for r in subset),max(r["year"] for r in subset)+1):
   for width in (5,9,15):
    sample=[r for r in subset if abs(r["year"]-y)<=width//2]
    if not sample:continue
    words=sum(r["words"] for r in sample)
    for name in entities:
     vals=[r[name] for r in sample];n=len(vals)
     panel.append({"institution":inst,"year":y,"window":width,"entity":name,
         "documents":n,"pct_any":round(100*sum(v>0 for v in vals)/n,3),
         "pct_3plus":round(100*sum(v>=3 for v in vals)/n,3),
         "pct_5plus":round(100*sum(v>=5 for v in vals)/n,3),
         "pct_10plus":round(100*sum(v>=10 for v in vals)/n,3),
         "per_100k_words":round(1e5*sum(vals)/words,3) if words else 0})
 write(a.output/"rolling_by_institute.csv",panel,list(panel[0]))
 print(f"{len(docs)} doctorates; {len(panel)} institute-specific rolling measurements")
if __name__=="__main__":main()
