#!/usr/bin/env python3
"""Audit the actual NER inventory coverage; counts are per-type TOP 50, not full NER.

Usage: python analysis/audit_ner_top50.py doctoral_ner_recovered.jsonl.zip
"""
import csv
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


TYPES = ('PER', 'PERSON', 'GPE', 'LOC', 'ORG', 'NORP')


def audit(path):
    frequencies = defaultdict(Counter)
    document_count = 0
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith('.jsonl')]
        if len(names) != 1:
            raise ValueError("Expect a single JSONL in the ZIP")
        with archive.open(names[0]) as stream:
            for line in stream:
                doc = json.loads(line)
                document_count += 1
                by_type = doc.get('entities_by_type', {})
                for tag in TYPES:
                    if tag not in by_type:
                        continue
                    n = len(by_type[tag])
                    if n > 50:
                        raise ValueError(f"Unexpected >50 entities for {doc['doc_id']}, {tag}")
                    frequencies[tag][n] += 1
    results = []
    for tag in TYPES:
        freq = frequencies[tag]
        observed = sum(freq.values())
        at_cap = freq[50]
        results.append({
            'entity_type':tag,
            'documents_type_present':observed,
            'documents_at_cap_50':at_cap,
            'percent_at_cap':round(100*at_cap/observed, 2) if observed else 0,
            'maximum_surface_forms':max(freq) if freq else 0
        })
    return document_count, results


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: audit_ner_top50.py doctoral_ner_recovered.jsonl.zip")
    docs, result = audit(Path(sys.argv[1]))
    print(f'Documents: {docs}')
    w = csv.DictWriter(sys.stdout, fieldnames=list(result[0]))
    w.writeheader()
    w.writerows(result)
    print("WARNING: Presence/absence and exhaustiveness cannot be inferred from TOP 50.",file=sys.stderr)


if __name__ == '__main__':
    main()
