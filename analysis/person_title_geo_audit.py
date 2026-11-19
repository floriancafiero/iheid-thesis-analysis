#!/usr/bin/env python3
"""Non-contradictory evidence audit for person nationality/office versus title toponyms."""
import csv,argparse
from collections import Counter,defaultdict
from pathlib import Path

def load(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows,cols):
 with open(p,'w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main(a):
 t=load(a.title_pairs);m=load(a.metadata);p=load(a.person_links)
 titles={r['doc_id']:r['title'] for r in m}
 by_doc=defaultdict(set)
 for r in t:
  if r['entity_type']=='country':by_doc[r['doc_id']].add(r['entity'])
 outputs=[]; counts=Counter()
 for r in p:
  channel=r['country_basis'] if r['link_channel']!='curated_exact' else 'curated_exact'
  labels=by_doc.get(r['doc_id'],set())
  if labels:
   cmp='country_in_title' if r['country'] in labels else 'other_country_in_title'
  else:cmp='no_country_in_title'
  counts[(channel,cmp)]+=1
  if cmp=='other_country_in_title':
   outputs.append({'doc_id':r['doc_id'],'year':r['year'],'institution':r['institution'],
                   'title':titles.get(r['doc_id'],''),'qid':r['qid'],'person':r['name'],
                   'person_country_attribution':r['country'],'country_basis':channel,
                   'title_named_countries':'|'.join(sorted(labels)),
                   'ner_mentions':r['mentions'],
                   'interpretation':'Not a false match proof; could be comparative relations or a theoretical reference'})
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 write(out/'different_country_title_person.csv',outputs,list(outputs[0]) if outputs else ['doc_id'])
 summary=[{'source':channel,'evidence':cmp,'pairs':n} for (channel,cmp),n in sorted(counts.items())]
 write(out/'person_geography_title_cross_tab.csv',summary,['source','evidence','pairs'])
 print(summary)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for s in ['title-pairs','metadata','person-links','out']:p.add_argument('--'+s,required=True)
 main(p.parse_args())
