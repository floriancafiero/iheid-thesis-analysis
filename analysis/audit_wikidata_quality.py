#!/usr/bin/env python3
"""Quality audit for exhaustive IHEID Wikidata links (not a subject classifier).

From GitHub Actions' combined Wikidata artifact:
    python analysis/audit_wikidata_quality.py --artifact wikidata-results.zip --out results/wikidata/quality

Or provide both --candidates candidate_qids.csv and
--screened person_country_links.csv. No network calls or external dependencies.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path


def load_csv(path: str | None, artifact: zipfile.ZipFile | None, member: str):
    if path:
        with open(path, encoding='utf-8-sig', newline='') as fh:
            return list(csv.DictReader(fh))
    assert artifact is not None
    with artifact.open(member) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig', newline='')))


def positive_int(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def token_count(surface):
    # Unicode-safe; hyphens and apostrophes separate tokens.
    return len(re.findall(r'[^\W_]+', surface, flags=re.UNICODE))


def is_high_risk_single_token(row):
    return token_count(row['surface']) <= 1


def audit(candidates, screened, top_n=100):
    # The Action verifies row coverage, but also verify the join independently.
    by_id = {}
    for row in screened:
        key = row['source_row']
        if key in by_id:
            raise ValueError(f'Duplicate screen source_row {key}')
        by_id[key] = row
    if len(candidates) != len(screened):
        raise ValueError('Candidate and screened row counts differ')
    if {r['source_row'] for r in candidates} != set(by_id):
        raise ValueError('Candidates and screened source_row sets differ')
    joined = []
    for candidate in candidates:
        screen = by_id[candidate['source_row']]
        if screen['surface'] != candidate['surface'] or screen['qid'] != candidate['qid']:
            raise ValueError('Candidate/screen misalignment at source_row ' + candidate['source_row'])
        row = {**candidate, **screen}
        row['mentions_n'] = positive_int(candidate.get('mentions'))
        row['documents_n'] = positive_int(candidate.get('documents'))
        row['title_n'] = positive_int(candidate.get('title_doc_count'))
        joined.append(row)

    id_status = Counter(r['status'] for r in joined)
    screens = Counter(r['screen_status'] for r in joined)
    retained = [r for r in joined if r['screen_status'] == 'retained']
    excluded = [r for r in joined if r['screen_status'] == 'excluded_academic']
    unmapped = [r for r in joined if r['screen_status'] == 'unmapped_jurisdiction']
    single = [r for r in retained if is_high_risk_single_token(r)]
    academic_offices = [r for r in excluded if r.get('office_qids')]
    country_bases = Counter(r['country_basis'] for r in retained)
    retained_mentions = sum(r['mentions_n'] for r in retained)
    single_mentions = sum(r['mentions_n'] for r in single)
    report = {
        'total_forms': len(joined),
        'identity_statuses': dict(id_status),
        'screen_statuses': dict(screens),
        'unique_identity_forms': id_status['unique_human_name_candidate'],
        'retained_forms': len(retained),
        'retained_unique_qids': len({r['qid'] for r in retained}),
        'retained_mention_sum': retained_mentions,
        'high_risk_unreviewed_single_token': {
            'forms': len(single),
            'share_retained_forms': round(len(single) / len(retained), 4) if retained else None,
            'mentions': single_mentions,
            'share_retained_mentions': round(single_mentions / retained_mentions, 4) if retained_mentions else None,
            'note': 'Risk bucket, not proven errors; a single surname may identify a real actor.'
        },
        'excluded_academic_with_offices': len(academic_offices),
        'unmapped_jurisdiction_forms': len(unmapped),
        'retained_country_basis': dict(country_bases),
        'limitations': [
            'Unique Wikidata name matching does not establish contextual identity.',
            'Count-only NER cannot distinguish bibliographic citations from subjects.',
            'Many country links derive from citizenship, not political jurisdiction.',
            'Academic filters exclude some political figures with academic occupations.',
            'Historical states and multiple jurisdictions must not be silently merged.'
        ]
    }
    problems = []

    def record(r, issue, priority):
        problems.append({
            'issue': issue, 'source_row': r['source_row'], 'surface': r['surface'],
            'qid': r['qid'], 'wikidata_label': r.get('person_label', ''),
            'status': r['screen_status'], 'mentions': r['mentions_n'],
            'documents': r['documents_n'], 'title_doc_count': r['title_n'],
            'country': r.get('country', ''), 'country_basis': r.get('country_basis', ''),
            'has_office': int(bool(r.get('office_qids', ''))),
            'country_candidates': r.get('country_candidates', ''),
            'priority': priority, 'manual_decision': '', 'review_note': ''
        })

    for r in single:
        record(r, 'single_token_retained', r['mentions_n'] + 50 * r['title_n'])
    for r in academic_offices:
        record(r, 'academic_exclusion_with_office', r['mentions_n'] + 50 * r['title_n'])
    for r in unmapped:
        if r.get('office_qids') or r['title_n']:
            record(r, 'unmapped_jurisdiction_actor', r['mentions_n'] + 50 * r['title_n'])
    # Multi-token exact matches can still be headings, publishers or references.
    for r in retained:
        if not is_high_risk_single_token(r):
            record(r, 'multi_token_retained_sample', r['mentions_n'] + 50 * r['title_n'])

    order = [
        'academic_exclusion_with_office', 'unmapped_jurisdiction_actor',
        'single_token_retained', 'multi_token_retained_sample'
    ]
    selected = []
    issue_totals = Counter(r['issue'] for r in problems)
    for issue in order:
        subset = sorted((r for r in problems if r['issue'] == issue),
                        key=lambda r: (-r['priority'], -r['documents'], r['surface']))
        selected.extend(subset[:top_n])
    report['review_issue_totals'] = dict(issue_totals)
    report['review_export_rows'] = len(selected)
    return report, selected


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--artifact', type=Path)
    p.add_argument('--candidates', type=Path)
    p.add_argument('--screened', type=Path)
    p.add_argument('--out', type=Path, default=Path('results/wikidata/quality'))
    p.add_argument('--top-per-issue', type=int, default=100)
    args = p.parse_args()
    if not args.artifact and not (args.candidates and args.screened):
        p.error('Provide --artifact or both --candidates and --screened')
    archive = zipfile.ZipFile(args.artifact) if args.artifact else None
    try:
        candidates = load_csv(str(args.candidates) if args.candidates else None, archive, 'candidate_qids.csv')
        screened = load_csv(str(args.screened) if args.screened else None, archive, 'person_country_links.csv')
    finally:
        if archive:
            archive.close()
    report, review = audit(candidates, screened, args.top_per_issue)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fields = [
        'issue', 'source_row', 'surface', 'qid', 'wikidata_label', 'status',
        'mentions', 'documents', 'title_doc_count', 'country', 'country_basis',
        'has_office', 'country_candidates', 'priority', 'manual_decision', 'review_note'
    ]
    with (args.out / 'manual_review_queue.csv').open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
