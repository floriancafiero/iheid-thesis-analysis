#!/usr/bin/env python3
"""Century-scale direct-mention diversity of doctoral NER (1928–2026).
Requires pandas, numpy and scipy; uses refitted doctoral entity scores.
Usage: python analysis/century_diversity.py METADATA_CSV SCORES_CSV DIAGNOSTICS_CSV
"""
import sys
import numpy as np
import pandas as pd
from scipy.special import gammaln

m=pd.read_csv(sys.argv[1],dtype={"doc_id":str})
s=pd.read_csv(sys.argv[2],dtype={"doc_id":str})
d=pd.read_csv(sys.argv[3])
assert m.doc_id.is_unique and len(m)==1730
m["era"]=pd.cut(m.year,[1927,1960,1990,2010,2027],right=False,labels=["1928–1959","1960–1989","1990–2009","2010–2026"])
valid=d[(d.channel=="direct")&(d.status=="separable")]
s=s[s.channel=="direct"].merge(valid[["type","entity","channel"]],on=["type","entity","channel"])
s["strong"]=(s.high_probability>=0.9).astype(int)
def effective(x):
 k=x.sum(0);p=k/k.sum()
 return 1/(p*p).sum() if k.sum()>0 else float("nan")
def rarefy(x,n=100):
 N=len(x);n=min(n,N);k=x.sum(0)
 absent=np.zeros(len(k))
 mask=(N-k)>=n
 absent[mask]=np.exp(gammaln(N-k[mask]+1)-gammaln(N-k[mask]-n+1)-gammaln(N+1)+gammaln(N-n+1))
 return (1-absent).sum()
rows=[];entity_rows=[]
for typ in ["country","organization"]:
 names=sorted(valid.loc[valid.type==typ,"entity"].unique())
 mat=(s[s.type==typ].pivot_table(index="doc_id",columns="entity",values="strong",aggfunc="max",fill_value=0)
      .reindex(index=m.doc_id,columns=names,fill_value=0))
 for era,doc in m.groupby("era",observed=True):
  x=mat.loc[doc.doc_id].to_numpy(dtype=int)
  k=x.sum(0);N=len(x)
  rows.append(dict(type=typ,era=str(era),n=N,n_entities=len(names),
                   expected_entities_per_100=round(float(rarefy(x)),2),
                   effective_simpson=round(float(effective(x)),2),
                   n_documents_any=int((x.sum(1)>0).sum())))
  entity_rows.extend(dict(type=typ,era=str(era),entity=name,strong=int(ki),
                          prevalence_pct=round(100*ki/N,2)) for name,ki in zip(names,k))
pd.DataFrame(rows).to_csv("century_diversity.csv",index=False)
pd.DataFrame(entity_rows).to_csv("century_entity_prevalence.csv",index=False)
print(pd.DataFrame(rows).to_string(index=False))
