#!/usr/bin/env python3
"""Data-driven salience on normalized hierarchical document/entity counts.

Requires numpy, scipy and scikit-learn. Example:
python analysis/hierarchical_salience.py analysis/hierarchy_output/document_entities.csv \
 --corpus entities_combined.jsonl.zip --output analysis/hierarchy_salience
All zero-mention documents are retained in prevalence denominators.
"""
import argparse,csv,json,zipfile
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from sklearn.mixture import GaussianMixture

def corpus(path):
    with zipfile.ZipFile(path) as z:
        files=[n for n in z.namelist() if n.endswith('.jsonl') and not n.startswith('__MACOSX')]
        if len(files)!=1:raise ValueError("Expected one JSONL")
        with z.open(files[0]) as f:
            for line in f:
                o=json.loads(line)
                if int(o.get("words_processed") or 0)>0:
                    yield str(o["doc_id"]),int(o["words_processed"])

def score(counts,exposures,gain=10):
    positive=counts>0
    output=np.zeros(len(counts))
    if positive.sum()<30 or len(set(counts[positive]))<4:
        return output,{"status":"insufficient","n_positive":int(positive.sum()),"bic_gain":"","rate_ratio":""}
    avg=max(counts.sum()/exposures.sum(),1e-9)
    def nll(x):
        rate,disp=np.exp(x);r=1/disp;m=rate*exposures
        return -sum(gammaln(counts+r)-gammaln(r)-gammaln(counts+1)+r*np.log(r/(r+m))+counts*np.log(m/(r+m)))
    fit=minimize(nll,[np.log(avg),0],method="L-BFGS-B",bounds=[(-14,14),(-9,9)])
    if not fit.success:
        return output,{"status":"fit_failed","n_positive":int(positive.sum()),"bic_gain":"","rate_ratio":""}
    rate,disp=np.exp(fit.x);prior=1/disp
    logrates=np.log((counts[positive]+prior)/(exposures[positive]+prior/rate)).reshape(-1,1)
    a=GaussianMixture(n_components=1,reg_covar=.025,random_state=21).fit(logrates)
    b=GaussianMixture(n_components=2,reg_covar=.025,random_state=21,n_init=3).fit(logrates)
    means=np.exp(b.means_.ravel());hi=int(np.argmax(means))
    improvement=float(a.bic(logrates)-b.bic(logrates))
    ratio=float(max(means)/min(means))
    status="separable" if improvement>=gain and ratio>=1.5 else "not_separable"
    if status=="separable":output[positive]=b.predict_proba(logrates)[:,hi]
    return output,{"status":status,"n_positive":int(positive.sum()),
                   "bic_gain":round(improvement,2),"rate_ratio":round(ratio,2)}

def save(path,rows,fields):
    with path.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("hierarchy_csv",type=Path)
    p.add_argument("--corpus",required=True,type=Path)
    p.add_argument("--output",type=Path,default=Path("analysis/hierarchy_salience"))
    p.add_argument("--bic-gain",type=float,default=10)
    args=p.parse_args();args.output.mkdir(exist_ok=True,parents=True)
    docs=list(corpus(args.corpus))
    ids=[d for d,w in docs];indices={d:i for i,d in enumerate(ids)}
    exposures=np.array([w/10000 for d,w in docs],float)
    counts=defaultdict(lambda:np.zeros(len(docs)))
    institution={}
    with args.hierarchy_csv.open(encoding="utf8",newline="") as f:
        for row in csv.DictReader(f):
            if row["doc_id"] not in indices:continue
            i=indices[row["doc_id"]];institution[i]=row["institution"]
            kind=row["type"];name=row["entity"]
            # Accept either existing exploratory export or committed compact version.
            direct=int(row.get("mentions_direct",row.get("direct",0)))
            inherited=int(row.get("mentions_inherited",row.get("inherited",0)))
            counts[(kind,name,"direct")][i]+=direct
            counts[(kind,name,"expanded")][i]+=direct+inherited
    panels={"ALL":np.ones(len(docs),bool)}
    for label in sorted(set(institution.values())):
        panels[label]=np.array([institution.get(i,"Unknown")==label for i in range(len(docs))])
    diagnostic=[];summaries=[];document_scores=[]
    for (kind,name,channel),n in sorted(counts.items()):
        prob,diagnosis=score(n,exposures,args.bic_gain)
        diagnostic.append({"type":kind,"entity":name,"channel":channel,**diagnosis})
        for panel,mask in panels.items():
            summaries.append({"panel":panel,"type":kind,"entity":name,"channel":channel,
                "documents":int(mask.sum()),"mentioned":int(((n>0)&mask).sum()),
                "high_80":int(((prob>=.8)&mask).sum()),
                "high_90":int(((prob>=.9)&mask).sum()),
                "high_95":int(((prob>=.95)&mask).sum()),
                "prevalence_high_90_pct":round(100*((prob>=.9)&mask).sum()/mask.sum(),2),
                "status":diagnosis["status"]})
        for i in np.flatnonzero(n>0):
            document_scores.append({"doc_id":ids[i],"institution":institution.get(i,"Unknown"),
                "type":kind,"entity":name,"channel":channel,"mentions":int(n[i]),
                "probability_high":round(float(prob[i]),4)})
    save(args.output/"diagnostics.csv",diagnostic,["type","entity","channel","status","n_positive","bic_gain","rate_ratio"])
    save(args.output/"summary.csv",summaries,["panel","type","entity","channel","documents","mentioned","high_80","high_90","high_95","prevalence_high_90_pct","status"])
    save(args.output/"document_scores.csv",document_scores,["doc_id","institution","type","entity","channel","mentions","probability_high"])
    print(f"{len(docs)} documents, {len(diagnostic)} models, {sum(r['status']=='separable' for r in diagnostic)} separable")

if __name__=="__main__":main()
