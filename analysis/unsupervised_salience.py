#!/usr/bin/env python3
"""Unsupervised, entity-specific significant prevalence.

Input: entities_combined.jsonl.zip. No document labels or manual annotation.
For each entity: fit an empirical-Bayes gamma-Poisson count model to all
documents, then a one- versus two-component Gaussian mixture to the
log posterior-mean rates among documents where the entity occurs.
Only classify when the 2-component model improves BIC by at least 10.
Output includes sensitivity to the posterior-probability criterion.
"""
import argparse
import csv
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from sklearn.mixture import GaussianMixture

from document_salience import (
    COUNTRY_LOOKUP, ORG_LOOKUP, input_records, norm
)

def log_nb(counts, means, alpha):
    r = 1.0 / alpha
    return (gammaln(counts + r) - gammaln(r) - gammaln(counts + 1)
            + r * np.log(r / (r + means))
            + counts * np.log(means / (r + means)))

def classify(counts, exposures, min_delta_bic=10, seed=42):
    """Return posterior probability of high-rate regime for each document."""
    counts = np.asarray(counts, dtype=float)
    exposures = np.asarray(exposures, dtype=float)  # units of 10,000 words
    positive = counts > 0
    post = np.zeros(len(counts))
    if positive.sum() < 30 or np.unique(counts[positive]).size < 4:
        return post, None
    rate = max(counts.sum() / exposures.sum(), 1e-6)

    def neg_ll(params):
        mean = np.exp(params[0]) * exposures
        alpha = np.exp(params[1])
        return -np.sum(log_nb(counts, mean, alpha))

    fit = minimize(neg_ll, [np.log(rate), 0.0], method="L-BFGS-B",
                   bounds=[(-14, 14), (-9, 9)])
    if not fit.success:
        return post, None
    baseline, alpha = np.exp(fit.x)
    # Gamma-Poisson conjugate posterior rate; the shrinkage is learned
    # from corpus variability rather than fixed to a number of pseudo-words.
    shape = 1.0 / alpha
    posterior_rate = (counts + shape) / (exposures + shape / baseline)
    x = np.log(posterior_rate[positive]).reshape(-1, 1)
    one = GaussianMixture(n_components=1, reg_covar=.025,
                          random_state=seed).fit(x)
    two = GaussianMixture(n_components=2, reg_covar=.025,
                          n_init=5, random_state=seed).fit(x)
    delta = float(one.bic(x) - two.bic(x))
    means = np.exp(two.means_.ravel())
    higher = int(np.argmax(means))
    lower = 1 - higher
    # A real distinction must also have appreciably different means.
    separation = float(means[higher] / means[lower])
    diagnostic = {
        "n_mentioned": int(positive.sum()),
        "delta_bic": round(delta, 2),
        "low_rate_per_10k": round(float(means[lower]), 3),
        "high_rate_per_10k": round(float(means[higher]), 3),
        "rate_ratio": round(separation, 2),
        "status": "separable" if delta >= min_delta_bic and separation >= 1.5
                  else "not_separable"
    }
    if diagnostic["status"] == "separable":
        post[positive] = two.predict_proba(x)[:, higher]
    return post, diagnostic

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, default=Path("analysis/output"))
    p.add_argument("--metadata", type=Path, help="Optional CSV: doc_id,year,institution,degree")
    p.add_argument("--bic-gain", type=float, default=10.)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    metadata = {}
    if args.metadata:
        with args.metadata.open(encoding="utf-8-sig", newline="") as f:
            metadata = {r["doc_id"]: r for r in csv.DictReader(f)}
    docs = []
    entities = {}
    for label, lookup in (("country", COUNTRY_LOOKUP), ("organization", ORG_LOOKUP)):
        for name in set(lookup.values()):
            entities[(label, name)] = {}
    for d in input_records(args.input):
        words = int(d.get("words_processed") or 0)
        if not words:
            continue
        ident = str(d["doc_id"])
        aliases_by_doc = {}
        for typ, names in d.get("entities_by_type", {}).items():
            if typ in ("LOC", "GPE"):
                lookup, category = COUNTRY_LOOKUP, "country"
            elif typ == "ORG":
                lookup, category = ORG_LOOKUP, "organization"
            else:
                continue
            for mention, count in names.items():
                entity = lookup.get(norm(mention))
                if entity:
                    key = (category, entity)
                    aliases_by_doc[key] = aliases_by_doc.get(key, 0) + int(count)
        row = metadata.get(ident, {})
        prefix = ident.split("_")[0]
        docs.append({"id": ident, "words": words,
                     "institution": row.get("institution") or (
                         prefix if prefix in {"HEI", "IUED", "IHEID"} else "Unmapped"),
                     "year": row.get("year", ""), "degree": row.get("degree", ""),
                     "counts": aliases_by_doc})
    exposure = np.array([d["words"] / 10000.0 for d in docs])
    document_rows, entity_rows = [], []
    for category, name in sorted(entities):
        key = (category, name)
        counts = np.array([d["counts"].get(key, 0) for d in docs])
        posterior, diag = classify(counts, exposure, args.bic_gain)
        if diag is None:
            continue
        entity_rows.append({
            "entity_type": category, "entity": name, **diag,
            "n_high_80pct": int(sum(posterior >= .8)),
            "n_high_90pct": int(sum(posterior >= .9)),
            "n_high_95pct": int(sum(posterior >= .95)),
            "total_documents": len(docs)
        })
        for i in np.where(counts > 0)[0]:
            document_rows.append({
                "doc_id": docs[i]["id"], "institution": docs[i]["institution"],
                "degree": docs[i]["degree"], "year": docs[i]["year"],
                "entity_type": category, "entity": name,
                "count": int(counts[i]), "words": docs[i]["words"],
                "rate_per_10k": round(float(counts[i] / exposure[i]), 3),
                "high_regime_probability": round(float(posterior[i]), 4),
                "high_90pct": int(posterior[i] >= .9),
                "model_status": diag["status"]
            })
    def export(name, data):
        if data:
            with (args.out / name).open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                w.writeheader()
                w.writerows(data)
    export("unsupervised_document_salience.csv", document_rows)
    export("unsupervised_entity_diagnostics.csv", entity_rows)
    print(f"{len(docs)} documents, {len(entity_rows)} fitted entities")
    for r in entity_rows:
        if r["entity"] in {"France", "China", "United States", "World Bank", "United Nations"}:
            print(r)

if __name__ == "__main__":
    main()
