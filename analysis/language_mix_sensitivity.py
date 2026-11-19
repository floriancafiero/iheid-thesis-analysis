#!/usr/bin/env python3
"""Stratify NER trends by extraction-language model and standardize composition.
Based solely on existing per-thesis NER and country/organization count data.
"""
from pathlib import Path
import csv,json,zipfile,math
from collections import Counter,defaultdict
import argparse

def load_csv(path):
 with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def export(path,items,cols):
 with open(path,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,cols,extrasaction='ignore');w.writeheader();w.writerows(items)

def main(args):
 meta={r['doc_id']:r for r in load_csv(args.metadata) if r['include']=='1'}
 removed={r['remove'] for r in load_csv(args.duplicate_audit) if r['classification']=='strong_probable_duplicate' and r['remove']}
 if args.dedup:meta={did:r for did,r in meta.items() if did not in removed}
 lng={}
 with zipfile.ZipFile(args.ner) as z:
  name=next(x for x in z.namelist() if x.endswith('.jsonl'))
  for line in z.open(name):
   r=json.loads(line)
   if r['doc_id'] in meta:lng[r['doc_id']]=r['language']
 assert len(lng)==len(meta)
 # NER ORG entity values in source vocabulary are preserved.
 country=defaultdict(int)
 for r in load_csv(args.thesis_country):
  if r['doc_id'] in meta:country[(r['doc_id'],r['country'])]=int(r['direct_mentions'])
 org=defaultdict(int)
 with zipfile.ZipFile(args.systematic) as z:
  name=next(n for n in z.namelist() if n.endswith('document_entity_counts.csv'))
  for r in csv.DictReader(x.decode('utf-8-sig') for x in z.open(name)):
   if r['doc_id'] in meta and r['category'] in ('organization','family') and r['channel']=='direct':
    org[(r['doc_id'],r['entity'])]=int(r['mentions'])
 entities={'country':['United States','France','China','India','Germany','United Kingdom','Soviet Union','Russia'],
           'organization':['ONU','SDN','OMC','Construction européenne (strictement CEE→CE→UE)','Banque mondiale']}
 groups=defaultdict(list)
 for did,r in meta.items():
  if r['institution']!='IHEID' or not 2010<=int(r['year'])<=2026:continue
  decade=int(r['year'])//10*10
  groups[(decade,lng[did])].append(did)
 all_d={dec:[did for (dd,ll),ids in groups.items() if dd==dec for did in ids] for dec in [2010,2020]}
 languages=sorted({l for _,l in groups})
 shares={dec:{l:len(groups[(dec,l)])/len(all_d[dec]) for l in languages} for dec in [2010,2020]}
 detail=[];overall=[]
 for typ,labels in entities.items():
  m=country if typ=='country' else org
  for e in labels:
   r_by={}
   n_by={}
   for dec in [2010,2020]:
    for lang in languages:
     ids=groups[(dec,lang)];n=len(ids)
     hits=sum(m.get((did,e),0)>=5 for did in ids)
     r_by[(dec,lang)]=hits/n if n else None
     n_by[(dec,lang)]=hits
     detail.append(dict(entity_type=typ,entity=e,decade=dec,language=lang,n_theses=n,ner5_n=hits,
                        ner5_pct=round(100*hits/n,2) if n else None,
                        language_share_pct=round(100*shares[dec].get(lang,0),2)))
   total={dec:sum(n_by[(dec,l)] for l in languages)/len(all_d[dec]) for dec in [2010,2020]}
   # Standardize both periods to 2010 language mix (fixing changing composition).
   std={dec:sum(shares[2010][l]*r_by[(dec,l)] for l in languages if r_by[(dec,l)] is not None) for dec in [2010,2020]}
   overall.append(dict(entity_type=typ,entity=e,
                       pct_2010=round(100*total[2010],2),pct_2020_2026=round(100*total[2020],2),
                       raw_change_pp=round(100*(total[2020]-total[2010]),2),
                       pct_2020_2026_fixed_lang2010=round(100*std[2020],2),
                       change_pp_fixed_lang2010=round(100*(std[2020]-std[2010]),2),
                       composition_shift_contribution_pp=round(100*(total[2020]-std[2020]),2)))
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 export(out/'language_model_mix.csv',[
  {'decade':dec,'language':l,'n_theses':len(groups[(dec,l)]),'share_pct':round(100*shares[dec][l],2)}
  for dec in [2010,2020] for l in languages],['decade','language','n_theses','share_pct'])
 export(out/'language_stratified_ner.csv',detail,list(detail[0]))
 export(out/'language_standardized_changes.csv',overall,list(overall[0]))
 print('LANGUAGE COMPOSITION')
 for dec in [2010,2020]:print(dec,len(all_d[dec]),dict((l,round(100*shares[dec][l],2)) for l in languages))
 print('CHANGES')
 for r in overall:print(r)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for x in ['metadata','duplicate-audit','ner','thesis-country','systematic','out']:p.add_argument('--'+x,required=True)
 p.add_argument('--dedup',action='store_true');main(p.parse_args())
