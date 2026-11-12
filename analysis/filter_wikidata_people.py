#!/usr/bin/env python3
"""Screen batch-linked Wikidata humans and infer an auditable country.

The intended *heuristic*, requested for the IHEID thesis analysis, excludes
likely bibliographic social-science/humanities academics from the person-based
geography signal even if they might be genuine thesis subjects. It keeps other
people, not just politicians (artists, activists, etc.).

Input: candidate_qids.csv from analysis/wikidata_batch_linker.py. Requires API
connectivity on GitHub Actions. Output: person_country_links.csv + audit.
"""
import argparse
import csv
import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import requests

API = 'https://www.wikidata.org/w/api.php'
UA = 'IHEID-thesis-analysis/1.0 (https://github.com/floriancafiero/iheid-thesis-analysis)'

# Excluding intellectual-occupation *signals*, not only the person's self-label.
# An explicit social scientist / philosopher is excluded even if also a politician,
# following the requested conservative approximation for bibliographic noise.
ACADEMIC = re.compile(r'\b(?:sociolog(?:ist|ue)|econom(?:ist|iste)|philosoph(?:er|e|ical)|'
    r'political scientist|scientist of politics|politologue|political theorist|'
    r'historian|historien|anthropolog(?:ist|ue)|psycholog(?:ist|ue)|'
    r'geographer|geographe|professor|professeur|academic|academique|'
    r'university teacher|university lecturer|universitaire|'
    r'social scientist|researcher|chercheur|scholar|erudit|'
    r'linguist|linguiste|literary critic|literary theorist|'
    r'jurist|legal scholar|legal academic|legal theorist|'
    r'political economist|economiste politique|theologian|theologien)\b', re.I)
# Obvious named reference writers regardless of incomplete P106 metadata.
EXPLICIT_EXCLUDE = {'michel foucault', 'karl marx', 'max weber'}

# Common jurisdiction identifiers (historical states intentionally kept distinct).
COUNTRY_QIDS = {
    'Q142':'France', 'Q30':'United States', 'Q145':'United Kingdom',
    'Q183':'Germany','Q148':'China','Q668':'India','Q155':'Brazil',
    'Q39':'Switzerland','Q38':'Italy','Q29':'Spain','Q17':'Japan',
    'Q159':'Russia','Q15180':'Soviet Union','Q258':'South Africa',
    'Q16':'Canada','Q96':'Mexico','Q43':'Turkey','Q241':'Cuba',
    'Q794':'Iran','Q796':'Iraq','Q801':'Israel','Q858':'Syria',
    'Q408':'Australia','Q34':'Sweden','Q55':'Netherlands',
    'Q20':'Norway','Q33':'Finland','Q31':'Belgium','Q36':'Poland',
    'Q45':'Portugal','Q41':'Greece','Q28':'Hungary','Q40':'Austria',
    'Q232':'Kazakhstan','Q836':'Myanmar','Q869':'Thailand',
    'Q252':'Indonesia','Q928':'Philippines','Q881':'Vietnam',
    'Q974':'Democratic Republic of the Congo','Q822':'Lebanon',
    'Q224':'Croatia','Q403':'Serbia','Q1033':'Nigeria',
    'Q963':'Botswana','Q1049':'Sudan', 'Q843':'Pakistan',
    'Q16957':'East Germany', 'Q713750':'West Germany',
    'Q15180':'Soviet Union', 'Q36704':'Yugoslavia',
}


def normalize(value):
    s = unicodedata.normalize('NFKD',str(value).casefold().replace('’', "'"))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^a-z0-9]+',' ',s).split())


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)


def claim_ids(entity,prop):
    values=set()
    for statement in entity.get('claims',{}).get(prop,[]):
        snak=statement.get('mainsnak',{})
        val=snak.get('datavalue',{}).get('value',{})
        if isinstance(val,dict) and val.get('id'):
            values.add(val['id'])
    return sorted(values)


def label(entity):
    ls=entity.get('labels',{})
    return next((ls[x]['value'] for x in ('en','fr','de','es') if x in ls),'')


class Wikidata:
    def __init__(self,delay=0.7):
        self.delay=delay
        self.session=requests.Session()
        self.session.headers.update({'User-Agent':UA})
        self.cache={}

    def call(self,**params):
        for attempt in range(5):
            try:
                r=self.session.get(API,params={'format':'json','formatversion':2,**params},timeout=45)
                if r.status_code in (429,500,502,503,504):
                    time.sleep(3*(attempt+1));continue
                r.raise_for_status()
                obj=r.json();time.sleep(self.delay)
                if 'error' in obj:raise ValueError(obj['error'])
                return obj
            except (requests.RequestException,ValueError):
                if attempt==4:raise
                time.sleep(3*(attempt+1))
        raise RuntimeError('Wikidata API failed')

    def get(self,ids):
        missing=[q for q in sorted(set(ids)) if q and q not in self.cache]
        for i in range(0,len(missing),40):
            chunk=missing[i:i+40]
            result=self.call(action='wbgetentities',ids='|'.join(chunk),
                props='labels|claims',languages='en|fr|de|es')
            entities=result.get('entities',{})
            if isinstance(entities,list):
                entities={x.get('id'):x for x in entities if x.get('id')}
            for q in chunk:self.cache[q]=entities.get(q,{})
        return {q:self.cache.get(q,{}) for q in ids}


def screen(data,wd):
    """Stage 1: conservative occupation exclusion, no assumptions about text position."""
    relevant=[r for r in data if r.get('status')=='unique_human_name_candidate' and r.get('qid')]
    people=wd.get([r['qid'] for r in relevant])
    occupation_ids={q for person in people.values() for q in claim_ids(person,'P106')}
    offices_ids={q for person in people.values() for q in claim_ids(person,'P39')}
    occupation_objects=wd.get(occupation_ids)
    # P279 immediate parent categories catch specializations beyond a label match.
    parents={q for ent in occupation_objects.values() for q in claim_ids(ent,'P279')}
    parent_objects=wd.get(parents)
    offices=wd.get(offices_ids)
    juris_ids={q for e in offices.values() for p in ('P17','P1001') for q in claim_ids(e,p)}
    juris_ids|={q for e in people.values() for q in claim_ids(e,'P27')}
    countries=wd.get(juris_ids)

    results=[]
    for row in data:
        out={k:row.get(k,'') for k in ('source_row','surface','mentions','documents','status','qid','label','all_human_qids')}
        out.update(screen_status='',occupations='',occupation_qids='',
                   office_qids='',office_country_qids='',citizenship_qids='',
                   country='',country_qid='',country_basis='',country_candidates='',reason='')
        if row.get('status')!='unique_human_name_candidate' or not row.get('qid'):
            out['screen_status']='unmatched_or_ambiguous';out['reason']='identity_not_unique';results.append(out);continue
        person=people.get(row['qid'],{})
        if not person or 'Q5' not in claim_ids(person,'P31'):
            out['screen_status']='unverified_human';out['reason']='no_human_instance';results.append(out);continue
        oids=claim_ids(person,'P106');pids=claim_ids(person,'P39')
        titles=[label(occupation_objects.get(q,{})) for q in oids]
        parent_titles=[label(parent_objects.get(q,{})) for q in sorted({x for q in oids for x in claim_ids(occupation_objects.get(q,{}),'P279')})]
        out['occupations']='|'.join(x for x in titles if x)
        out['occupation_qids']='|'.join(oids)
        out['office_qids']='|'.join(pids)
        if normalize(label(person)) in EXPLICIT_EXCLUDE or normalize(row['surface']) in EXPLICIT_EXCLUDE:
            out['screen_status']='excluded_academic';out['reason']='explicit_reference_filter';results.append(out);continue
        if ACADEMIC.search(' '.join(titles+parent_titles)):
            out['screen_status']='excluded_academic';out['reason']='P106_academic_occupation';results.append(out);continue
        if not oids and not pids:
            out['screen_status']='insufficient_biography';out['reason']='no_occupation_or_office';results.append(out);continue
        # Prefer the political jurisdiction of positions (P39→office P1001/P17)
        office_juris={q for pos in pids for prop in ('P1001','P17') for q in claim_ids(offices.get(pos,{}),prop)}
        citizenship=set(claim_ids(person,'P27'))
        out['office_country_qids']='|'.join(sorted(office_juris))
        out['citizenship_qids']='|'.join(sorted(citizenship))
        # A jurisdiction not recognized as a state is left unresolved, not guessed.
        office_states={q:COUNTRY_QIDS[q] for q in office_juris if q in COUNTRY_QIDS}
        citizens={q:COUNTRY_QIDS[q] for q in citizenship if q in COUNTRY_QIDS}
        # If a person had multiple country jobs / citizenships, retain ambiguity.
        if office_juris:
            source='political_office';eligible=office_states
            unknown=office_juris-set(office_states)
        else:
            source='citizenship_fallback';eligible=citizens
            unknown=citizenship-set(citizens)
        out['country_candidates']='|'.join(f'{q}:{countries.get(q,{}).get("id",q)}:{name}' for q,name in eligible.items())
        if unknown:
            out['screen_status']='unmapped_jurisdiction';out['reason']='unmapped_country_qid';results.append(out);continue
        distinct_names=set(eligible.values())
        if len(distinct_names)!=1:
            out['screen_status']='multiple_or_missing_countries'
            out['reason']='multiple_states' if distinct_names else 'no_country'
            results.append(out);continue
        out['country']=next(iter(distinct_names))
        out['country_qid']='|'.join(sorted(eligible))
        out['country_basis']=source
        out['screen_status']='retained'
        results.append(out)
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('linked_candidates',type=Path)
    parser.add_argument('--out',type=Path,default=Path('results/wikidata/person_country_links.csv'))
    parser.add_argument('--delay',type=float,default=.7)
    args=parser.parse_args()
    rows=read_csv(args.linked_candidates)
    wd=Wikidata(args.delay)
    result=screen(rows,wd)
    fields=['source_row','surface','mentions','documents','status','qid','label','all_human_qids',
            'screen_status','occupations','occupation_qids','office_qids',
            'office_country_qids','citizenship_qids','country','country_qid',
            'country_basis','country_candidates','reason']
    write_csv(args.out,result,fields)
    counts=Counter(r['screen_status'] for r in result)
    print('Input',len(rows),'screened',dict(counts),'saved',args.out)
    print('NOTE: P27 fallback is weaker than office jurisdiction; multi-country cases unresolved.')
if __name__=='__main__':main()