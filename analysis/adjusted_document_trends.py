#!/usr/bin/env python3
"""Exploratory association of IHEID cohort with NER mention presence.
Adjusts for extraction language and number of processed words; no causal claim.
Use same corpus and label dictionaries as previous descriptive series.
"""
import argparse,csv,json,zipfile,math
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

def load(path):
 with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def run(a):
 meta={r['doc_id']:r for r in load(a.metadata) if r['include']=='1'}
 drop={r['remove'] for r in load(a.duplicate_audit) if r['classification']=='strong_probable_duplicate' and r['remove']}
 meta={did:r for did,r in meta.items() if (a.keep_probable_duplicates or did not in drop) and r['institution']=='IHEID' and int(r['year'])>=2010}
 # All years in this scope map to 2010s or incomplete 2020s.
 langs={}
 with zipfile.ZipFile(a.ner) as z:
  n=next(q for q in z.namelist() if q.endswith('.jsonl'))
  for line in z.open(n):
   obj=json.loads(line)
   if obj['doc_id'] in meta: langs[obj['doc_id']]=obj['language']
 assert len(langs)==len(meta)
 country=defaultdict(int)
 for r in load(a.country_doc):
  if r['doc_id'] in meta:country[(r['doc_id'],r['country'])]=int(r['direct_mentions'])
 org=defaultdict(int)
 with zipfile.ZipFile(a.systematic) as z:
  path=next(x for x in z.namelist() if x.endswith('document_entity_counts.csv'))
  for row in csv.DictReader(line.decode('utf-8-sig') for line in z.open(path)):
   if row['doc_id'] in meta and row['category'] in ('family','organization') and row['channel']=='direct':
    org[(row['doc_id'],row['entity'])]=int(row['mentions'])
 docs=[]
 for did,r in meta.items():
  words=int(r['words_processed']); docs.append({'doc_id':did,'cohort2020':int(r['year'])>=2020,'year':int(r['year']),
                                               'language':langs[did],'log_words':math.log(max(100,words)),
                                               'words':words})
 frame=pd.DataFrame(docs).sort_values('doc_id').reset_index(drop=True)
 X=pd.DataFrame({'const':np.ones(len(frame)),'period2020':frame.cohort2020.astype(int).values,
                 'lang_en':(frame.language=='en').astype(int).values,
                 'lang_de':(frame.language=='de').astype(int).values,
                 'log_words':frame.log_words.to_numpy()-frame.log_words.median()})
 first=(frame.cohort2020==0)
 out=[]
 for typ,entity in [('country','United States'),('country','France'),('country','China'),('country','India'),
                    ('country','Germany'),('organization','ONU'),('organization','Construction européenne (strictement CEE→CE→UE)'),
                    ('organization','OMC'),('organization','Banque mondiale')]:
  m=country if typ=='country' else org
  y=pd.Series([int(m.get((did,entity),0)>=5) for did in frame.doc_id])
  fit=sm.GLM(y,X,family=sm.families.Binomial()).fit(cov_type='HC1')
  logor=float(fit.params['period2020']); se=float(fit.bse['period2020'])
  Xbase=X.loc[first].copy();Xfuture=Xbase.copy();Xbase['period2020']=0;Xfuture['period2020']=1
  pred0=float(fit.predict(Xbase).mean());pred1=float(fit.predict(Xfuture).mean())
  actual10=100*y[first].mean();actual20=100*y[~first].mean()
  out.append({'entity_type':typ,'entity':entity,'n_2010':sum(first),'n_2020_2026':sum(~first),
              'observed_pct_2010':round(actual10,2),'observed_pct_2020_2026':round(actual20,2),
              'observed_delta_pp':round(actual20-actual10,2),
              'gcomp_adjusted_pct_2010':round(100*pred0,2),'gcomp_adjusted_pct_2020_2026':round(100*pred1,2),
              'adjusted_delta_pp':round(100*(pred1-pred0),2),
              'cohort_odds_ratio':round(math.exp(logor),3),
              'odds_ratio_ci_low':round(math.exp(logor-1.96*se),3),
              'odds_ratio_ci_high':round(math.exp(logor+1.96*se),3),
              'exploratory_p':round(float(fit.pvalues['period2020']),4)})
 output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
 pd.DataFrame(out).to_csv(output,index=False)
 desc=frame.groupby('cohort2020').agg(n=('doc_id','size'),median_words=('words','median'),mean_words=('words','mean')).reset_index()
 desc.to_csv(output.with_name('cohort_word_counts.csv'),index=False)
 print('TEXT LENGTHS\n',desc.to_string(index=False))
 print('ESTIMATES\n',pd.DataFrame(out).to_string(index=False))

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--keep-probable-duplicates',action='store_true')
 for x in ['metadata','duplicate-audit','ner','country-doc','systematic','out']:p.add_argument('--'+x,required=True)
 run(p.parse_args())
