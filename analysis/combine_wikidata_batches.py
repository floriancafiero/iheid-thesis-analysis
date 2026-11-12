#!/usr/bin/env python3
"""Merge exhaustive Wikidata shards with row-coverage and identity audits.

A successful final CSV is produced only if every original PER/PERSON surface
has exactly one candidate row and one screened row and no network errors.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def merge(source, folder, out):
    original = read_csv(source)
    expected = len(original)
    candidates = {}
    people = {}
    parts = sorted(folder.glob('*/candidate_qids.csv'))
    if not parts:
        raise ValueError(f'No shard artifacts found in {folder}')
    for path in parts:
        related = path.parent / 'person_country_links.csv'
        if not related.is_file():
            raise ValueError(f'Missing person-country filter output in {path.parent.name}')
        for candidate in read_csv(path):
            rowid = int(candidate['source_row'])
            if rowid in candidates:
                raise ValueError(f'Duplicate candidate row {rowid}')
            if not (0 <= rowid < expected):
                raise ValueError(f'Out-of-range candidate row {rowid}')
            if candidate['surface'] != original[rowid]['surface']:
                raise ValueError(f'Source misalignment at row {rowid}')
            candidates[rowid] = candidate
        for person in read_csv(related):
            rowid = int(person['source_row'])
            if rowid in people:
                raise ValueError(f'Duplicate screened row {rowid}')
            people[rowid] = person
    expected_set = set(range(expected))
    if set(candidates) != expected_set:
        missing = sorted(expected_set - set(candidates))
        raise ValueError(f'Missing {len(missing)} identity rows: {missing[:12]}')
    if set(people) != expected_set:
        missing = sorted(expected_set - set(people))
        raise ValueError(f'Missing {len(missing)} screened rows: {missing[:12]}')
    all_candidates = [candidates[i] for i in range(expected)]
    all_people = [people[i] for i in range(expected)]
    statuses = Counter(x['status'] for x in all_candidates)
    screened = Counter(x['screen_status'] for x in all_people)
    if statuses.get('network_error', 0):
        raise ValueError(f"Unresolved network_error rows: {statuses['network_error']}")
    if any(x['qid'] and x['status'] != 'unique_human_name_candidate'
           for x in all_candidates):
        raise ValueError('A non-unique candidate has an assigned QID')
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / 'candidate_qids.csv', all_candidates, list(all_candidates[0]))
    write_csv(out / 'person_country_links.csv', all_people, list(all_people[0]))
    report = {
        'candidate_rows': expected,
        'shards_found': len(parts),
        'source_inventory_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'identity_statuses': dict(statuses),
        'screen_statuses': dict(screened),
        'human_unique_qids': len({x['qid'] for x in all_candidates if x['status'] == 'unique_human_name_candidate'}),
        'people_with_country': len({x['qid'] for x in all_people if x['screen_status'] == 'retained' and x['country']}),
        'method': 'Exact-name Wikidata matching; academic-occupation heuristic; public-office jurisdiction before citizenship fallback',
        'warning': 'Bibliography positions are missing in the count-only NER; person-based geography is approximate.'
    }
    (out / 'coverage_report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--folder', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    merge(a.source, a.folder, a.out)

if __name__ == '__main__':
    main()
