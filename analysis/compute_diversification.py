#!/usr/bin/env python3
"""Diversification on a dated doctoral NER population, direct salience only.
Requires pandas, numpy, scipy and scikit-learn.
python analysis/compute_diversification.py --metadata doctoral_metadata_1927plus.csv --scores document_scores.csv --diagnostics diagnostics.csv
"""
import argparse
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import gammaln
def rarefy(M,n=100):
    N=len(M);n=min(n,N);k=M.sum(0);ok=N-k>=n
    absence=np.zeros(len(k))
    absence[ok]=np.exp(gammaln(N-k[ok]+1)-gammaln(N-k[ok]-n+1)-gammaln(N+1)+gammaln(N-n+1))
    return float((1-absence).sum())
def effective(M):
    k=M.sum(0)
    if k.sum()==0:return np.nan
    p=k/k.sum();return float(1/(p*p).sum())
def main():
    p=argparse.ArgumentParser()
    for key in ('metadata','scores','diagnostics'):p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--out',type=Path,default=Path('analysis/diversification_output'))
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    m=pd.read_csv(a.metadata,dtype={'doc_id':str})
    assert m.doc_id.is_unique and m.thesis_type.eq('PhD').all() and m.year.ge(1927).all()
    m['decade']=m.year//10*10
    s=pd.read_csv(a.scores,dtype={'doc_id':str});d=pd.read_csv(a.diagnostics)
    assert s.doc_id.isin(m.doc_id).all()
    rows=[];entities=[];sensitivity=[];tests=[];rng=np.random.default_rng(20261111)
    for typ in ('country','organization'):
        allowed=sorted(d[(d.type==typ)&(d.channel=='direct')&(d.status=='separable')].entity.unique())
        ss=s[(s.type==typ)&(s.channel=='direct')&s.entity.isin(allowed)]
        mats={}
        for cutoff in (.8,.9,.95):
            pv=ss.assign(flag=(ss.high_probability>=cutoff).astype(int)).pivot_table(index='doc_id',columns='entity',values='flag',aggfunc='max',fill_value=0).reindex(index=m.doc_id,columns=allowed,fill_value=0)
            for decade,group in m.groupby('decade'):
                M=pv.loc[group.doc_id].to_numpy(dtype=int);k=M.sum(0);N=len(M)
                sensitivity.append(dict(type=typ,decade=decade,cutoff=cutoff,effective=round(effective(M),3),documents_any_strong=int((M.sum(1)>0).sum()),documents=N))
                if cutoff!=.9:continue
                mats[decade]=M
                # Bootstrap percentiles are diagnostics, not calibrated CIs.
                bs=[M[rng.integers(N,size=N)] for _ in range(500)]
                rows.append(dict(type=typ,decade=decade,documents=N,eligible_entities=len(allowed),strong_entity_doc_pairs=int(k.sum()),documents_any_strong=int((M.sum(1)>0).sum()),observed_richness=int((k>0).sum()),rarefied_100=round(rarefy(M),2),rarefied_bootstrap_p025=round(np.quantile([rarefy(z) for z in bs],.025),2),rarefied_bootstrap_p975=round(np.quantile([rarefy(z) for z in bs],.975),2),effective_simpson=round(effective(M),2),effective_bootstrap_p025=round(np.quantile([effective(z) for z in bs],.025),2),effective_bootstrap_p975=round(np.quantile([effective(z) for z in bs],.975),2)))
                entities += [dict(type=typ,decade=decade,entity=e,doctorates=N,strong=int(n),prevalence_pct=round(100*n/N,2)) for e,n in zip(allowed,k)]
        A,B=mats[1990],mats[2010];obs=effective(B)-effective(A);joint=np.concatenate([A,B]);n=len(A)
        null=[]
        for _ in range(3000):
            ix=rng.permutation(len(joint));null.append(effective(joint[ix[n:]])-effective(joint[ix[:n]]))
        tests.append(dict(type=typ,comparison='2010s minus 1990s',difference=round(obs,3),permutation_p_two_sided=round((1+sum(abs(v)>=abs(obs) for v in null))/(len(null)+1),4)))
    pd.DataFrame(rows).to_csv(a.out/'diversification_by_decade.csv',index=False)
    pd.DataFrame(entities).to_csv(a.out/'entity_decade_prevalence.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(a.out/'sensitivity_80_90_95.csv',index=False)
    pd.DataFrame(tests).to_csv(a.out/'permutation_diagnostic.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
