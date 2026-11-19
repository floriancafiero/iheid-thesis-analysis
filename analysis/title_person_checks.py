#!/usr/bin/env python3
"""Positive title evidence for candidate Wikidata persons using only existing top-50 NER.
Reject single-token automatic names and generic phrase matches; keep academic QIDs.
Not evidence for all references in a thesis or QID coreference accuracy.
"""
import argparse,csv,re,unicodedata,json,zipfile
from collections import Counter,defaultdict
from pathlib import Path

def norm(s):
 s=unicodedata.normalize('NFKD',str(s).casefold());return ' '.join(re.sub(r'[^a-z0-9]+',' ',''.join(c for c in s if not unicodedata.combining(c))).split())

def rows(path):
 with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

STOP=set('the italian president monsieur madame mister mr mrs prof professor doctor docteur president madam she he this that some state part chapter question being not also person people president prime minister'.split())
PART={'de','du','da','di','der','den','van','von','le','la','del','d','j'}

def admissible(s,label):
 t=norm(s).split()
 if not label or any(x in STOP for x in t): return False
 meaningful=[x for x in t if x not in PART and len(x)>1]
 if len(meaningful)<2:return False
 return sum(x in norm(label).split() for x in meaningful)>=2

def main(a):
 meta={r['doc_id']:r for r in rows(a.metadata) if r['include']=='1'}
 dup=rows(a.duplicates);drop={r['remove'] for r in dup if r['classification']=='strong_probable_duplicate' and r['remove']}
 if a.dedup:meta={k:v for k,v in meta.items() if k not in drop}
 c=rows(a.candidates);scr={r['source_row']:r for r in rows(a.screened)}
 candidates=defaultdict(list)
 for r in c:
  if r['status']=='unique_human_name_candidate' and r['qid'] and admissible(r['surface'],r['person_label']):candidates[norm(r['surface'])].append(r)
 # Intentionally only identify when the SAME surface is in the title and in NER,
 # with a single unique human Wikidata candidate. These are positives to inspect.
 out=[]
 with zipfile.ZipFile(a.ner) as z:
  file=next(s for s in z.namelist() if s.endswith('.jsonl'))
  for line in z.open(file):
   doc=json.loads(line);did=doc['doc_id']
   if did not in meta:continue
   title=meta[did]['title'];tn=' '+norm(title)+' '
   for t in ('PERSON','PER'):
    for form,n in doc['entities_by_type'].get(t,{}).items():
     sf=norm(form)
     if ' '+sf+' ' not in tn:continue
     for r in candidates.get(sf,[]):
      wd=scr.get(r['source_row'],{})
      out.append(dict(doc_id=did,year=meta[did]['year'],institution=meta[did]['institution'],title=title,
                      raw_surface=form,wikidata_label=r['person_label'],qid=r['qid'],mentions=n,
                      screen_status=wd.get('screen_status',''),country_if_screened=wd.get('country',''),
                      status='positive_title_mention_candidate_QID_requires_manual_identity_check'))
 combined={}
 for r in out:
  k=(r['doc_id'],r['qid'])
  if k not in combined:
   combined[k]=dict(r)
  else:
   prev=combined[k]
   prev['mentions']=int(prev['mentions'])+int(r['mentions'])
   prev['raw_surface'] += ' | ' + r['raw_surface']
 out=sorted(combined.values(),key=lambda r:(r['year'],r['institution'],r['title'],r['qid']))
 p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]) if out else ['doc_id']);w.writeheader();w.writerows(out)
 print('TITLE-PERSON',len(out),len(set(x['doc_id'] for x in out)),Counter(x['screen_status'] for x in out))
 for r in out: print(r['year'],r['institution'],r['raw_surface'],r['wikidata_label'],r['qid'],r['screen_status'],'|',r['title'])

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ['metadata','duplicates','candidates','screened','ner','out']:p.add_argument('--'+k,required=True)
 p.add_argument('--dedup',action='store_true');main(p.parse_args())
