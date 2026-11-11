#!/usr/bin/env python3
"""Summarize PhD-only NER salience by decade and institution.

Required files are generated locally from the user's input datasets:
  analysis/filter_doctorates.py
  analysis/entity_hierarchy.py (or previously exported hierarchy CSV)
  analysis/hierarchical_salience.py (re-fit on filtered doctoral corpus)
Usage:
python analysis/doctoral_trends.py \
 --metadata analysis/doctoral_output/doctoral_metadata_1927plus.csv \
 --scores analysis/hierarchy_salience/document_scores.csv \
 --diagnostics analysis/hierarchy_salience/diagnostics.csv \
 --output analysis/doctoral_trends_output
"""
import argparse
from pathlib import Path
import pandas as pd

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--metadata",required=True,type=Path)
    p.add_argument("--scores",required=True,type=Path)
    p.add_argument("--diagnostics",required=True,type=Path)
    p.add_argument("--output",default=Path("analysis/doctoral_trends_output"),type=Path)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    meta=pd.read_csv(a.metadata,dtype={"doc_id":str})
    assert meta.doc_id.is_unique and meta.thesis_type.eq("PhD").all() and meta.year.ge(1927).all()
    meta["decade"]=meta.year.floordiv(10).mul(10)
    scores=pd.read_csv(a.scores,dtype={"doc_id":str})
    diags=pd.read_csv(a.diagnostics)
    assert scores.doc_id.isin(meta.doc_id).all()
    assert not scores.duplicated(["doc_id","type","entity","channel"]).any()
    score=scores.merge(meta[["doc_id","institution","decade"]],on="doc_id",validate="many_to_one",suffixes=("_source",""))
    eligible=diags.loc[diags.status=="separable",["type","entity","channel"]]
    score=score.merge(eligible,on=["type","entity","channel"])
    rows=[]
    panels=[("ALL",meta)]
    panels += [(str(d),sub) for d,sub in meta.groupby("decade")]
    panels += [(str(i),sub) for i,sub in meta.groupby("institution")]
    panels += [(str(i)+":"+str(d),sub) for (i,d),sub in meta.groupby(["institution","decade"])]
    prob_col="high_probability" if "high_probability" in score else "probability_high"
    for label,documents in panels:
        data=score.loc[score.doc_id.isin(documents.doc_id)]
        sums=data.groupby(["type","entity","channel"]).agg(
            mentioned=("doc_id","nunique"),
            high_80=(prob_col,lambda x:int((x>=.8).sum())),
            high_90=(prob_col,lambda x:int((x>=.9).sum())),
            high_95=(prob_col,lambda x:int((x>=.95).sum()))).reset_index()
        combined=eligible.merge(sums,on=["type","entity","channel"],how="left").fillna(0)
        for r in combined.to_dict("records"):
            n=len(documents)
            rows.append(dict(panel=label,documents=n,type=r["type"],entity=r["entity"],
                channel=r["channel"],mentioned=int(r["mentioned"]),
                high_80=int(r["high_80"]),high_90=int(r["high_90"]),high_95=int(r["high_95"]),
                prevalence_pct=round(100*r["high_90"]/n,2)))
    pd.DataFrame(rows).to_csv(a.output/"salience_by_period_institution.csv",index=False)
    meta.groupby(["decade","institution"]).size().rename("doctorates").reset_index().to_csv(
        a.output/"doctoral_counts_by_decade.csv",index=False)
    print(f"{len(meta)} dated doctorates, {len(eligible)} separable entity/channel models")
if __name__=="__main__":main()
