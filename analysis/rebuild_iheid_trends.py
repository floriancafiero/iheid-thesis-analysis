#!/usr/bin/env python3
"""Reproducible conservative reanalysis of IHEID doctoral country, IO and person NER.

All values are document-level mention proxies, NOT manually validated thesis topics.
Both the manually checked actor registry and stricter exploratory Wikidata links
are exported as separate channels; only checked actors enter the main evidence.
"""
from __future__ import annotations
import argparse
import collections
import csv
import json
import re
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def norm(x):
    x = unicodedata.normalize('NFKD', str(x).casefold().replace('’', "'").replace('‘', "'"))
    x = ''.join(c for c in x if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', x).split())


def csvrows(f):
    with open(f, encoding='utf-8-sig', newline='') as h:
        return list(csv.DictReader(h))


def dumpcsv(out, rows, cols):
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)


def to_int(v):
    try: return int(v)
    except (ValueError, TypeError): return 0


COUNTRY_CANON = {
    'france':'France','royaume uni':'United Kingdom','united kingdom':'United Kingdom',
    'etats unis':'United States','united states':'United States',
    'chine':'China','china':'China','inde':'India','india':'India',
    'irak':'Iraq','iraq':'Iraq','iran':'Iran','israel':'Israel',
    'palestine':'Palestine','bolivie':'Bolivia','bolivia':'Bolivia',
    'bresil':'Brazil','brazil':'Brazil','ghana':'Ghana',
    'rd congo':'DR Congo','democratic republic of the congo':'DR Congo',
    'ukraine':'Ukraine','rda':'East Germany','east germany':'East Germany',
    'allemagne':'Germany','germany':'Germany','urss':'Soviet Union','soviet union':'Soviet Union',
    'cuba':'Cuba','yougoslavie':'Yugoslavia','yugoslavia':'Yugoslavia',
    'turquie':'Turkey','turkey':'Turkey','cambodge':'Cambodia','cambodia':'Cambodia',
    'coree du nord':'North Korea','north korea':'North Korea',
    'afrique du sud':'South Africa','south africa':'South Africa',
    'senegal':'Senegal'
}
def canon_country(s): return COUNTRY_CANON.get(norm(s), str(s).strip())

# Exclusion is a lexical *risk flag*, not a claim that non-listed strings are correct.
BAD_WORDS = set('''are was were will would shall should can could may might did does done
while which where when what who why whose whom the a an and or with without to from
for than that this these those it its they them theirs he she we us you your his her
based rather given however several furthermore thus therefore such other another
part section appendix chapter volume page pages table figure introduction conclusion
results discussion analysis chapter book pdf thesis paper research article reviewer
international national political economic government trade foreign monetary civil
rights conflict security human public legal policy academic introduction republic
at the of by no oui non et des les de du la le une un sur en dans pour comme au aux
as is be have has had not also between among i ii iii iv v vi vii viii ix x
rev roi roi etude
tableau figure theses scholars professor universite university institut institute
'''.split())
PARTICLES=set('de du des van von der den da di del della le la el al ben bin ibn st st.'.split())


def check_multitoken(s, person_label):
    tokens=norm(s).split()
    if len(tokens)<2: return False, 'single_token'
    if any(t in BAD_WORDS and t not in PARTICLES for t in tokens):
        return False,'common_language_token'
    meaningful=[t for t in tokens if t not in PARTICLES and len(t)>=3]
    # Auto-link only plausible complete names (at least two substantive terms).
    # Verified names such as 'de Gaulle' are handled independently by the registry.
    if len(meaningful)<2:
        return False,'incomplete_or_particle_only'
    labels=set(norm(person_label).split())
    # A surname/part of a personal name should literally overlap the recorded label.
    if not any(t in labels and len(t)>=4 for t in meaningful):
        return False,'name_label_mismatch'
    return True,'provisional_multitoken'


def load_registry(path):
    if str(path).lower().endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            name=next(x for x in z.namelist() if x.endswith('expanded_registry_strict_full_names.csv'))
            with z.open(name) as f:
                registry=list(csv.DictReader(line.decode('utf-8-sig') for line in f))
    else: registry=csvrows(path)
    by_surface={}; aliases=collections.defaultdict(set); by_qid={}
    collisions=[]
    for r in registry:
        qid=r['wikidata_qid']; country=canon_country(r['political_jurisdiction'])
        by_qid[qid]=(r['canonical_name'],country)
        for s in r['accepted_ner_surfaces'].split('|'):
            k=norm(s)
            if not k:continue
            if k in by_surface and by_surface[k]['qid']!=qid:
                collisions.append((k,by_surface[k]['qid'],qid))
            by_surface[k]={'qid':qid,'name':r['canonical_name'],'country':country,
                            'basis':'curated_office','channel':'curated_exact','surface':k}
            aliases[qid].add(k)
    if collisions: raise ValueError('Curated alias collisions: '+str(collisions))
    return by_surface,by_qid,aliases


def identify(candidates, screened, curated):
    by_curated,by_qid,aliases=curated
    candidates_by_row={x['source_row']:x for x in candidates}
    seen=set(); identities={}; audit=[]
    for r in screened:
        n=norm(r['surface']); c=candidates_by_row[r['source_row']]
        if r['source_row'] in seen: raise ValueError('duplicate source_row')
        seen.add(r['source_row'])
        if c['surface']!=r['surface'] or c['qid']!=r['qid']: raise ValueError('screen alignment error')
        obj=None; method='not_used'; reason=''
        if n in by_curated:
            identity=by_curated[n]
            # Curated names are explicitly checked independent of Wikidata's exact-name search;
            # record conflicts instead of making a false silent override.
            if c.get('qid') and c['qid']!=identity['qid']:
                method='curated_conflict';reason='candidate_qid_disagrees'
            else:
                obj=dict(identity)
                method='curated_exact'
        elif r['status']=='unique_human_name_candidate' and r['qid']:
            ok,why=check_multitoken(r['surface'],c['person_label'])
            if ok and r['screen_status']=='retained':
                country=canon_country(r['country'])
                obj={'qid':r['qid'],'name':c['person_label'] or r['surface'],
                     'country':country,'basis':r['country_basis'],
                     'channel':'provisional_full_name','surface':n}
                method='provisional_full_name'
            else:method='held';reason=why if not ok else r['screen_status']
        else:reason=r['status'];method='held'
        if obj: identities[n]=obj
        audit.append({'surface':r['surface'],'qid':r['qid'],
                      'candidate_label':c['person_label'],'source_status':r['screen_status'],
                      'action':method,'reason':reason,'mentions_inventory':c['mentions'],
                      'country':obj['country'] if obj else '',
                      'basis':obj['basis'] if obj else ''})
    # If curated name is an exact acceptable alias absent or rejected by Wiki match,
    # it is still usable (after independent manual registry verification).
    for n,obj in by_curated.items():
        if n not in identities:
            identities[n]=dict(obj)
            audit.append({'surface':n,'qid':obj['qid'],'candidate_label':obj['name'],
                         'source_status':'curated_without_exact_wikidata_candidate',
                         'action':'curated_exact','reason':'independent_curated_registry',
                         'mentions_inventory':'','country':obj['country'],'basis':obj['basis']})
    # A QID may occur in automatically linked rows that are single-token surnames.
    # Those can only strengthen an explicitly curated identity INSIDE A THESIS
    # where a curated full name of the same QID is also present.
    surnames={}
    for r in screened:
        n=norm(r['surface'])
        if len(n.split())!=1 or r['status']!='unique_human_name_candidate': continue
        qid=r['qid']
        if qid in by_qid and n not in BAD_WORDS and n and len(n)>=4:
            surnames[n]=qid
    return identities,audit,surnames,by_qid


def read_ner(path):
    if str(path).endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if n.endswith('.jsonl')]
            if len(names)!=1:raise ValueError('Expected one JSONL in NER ZIP')
            with z.open(names[0]) as f:
                for line in f:yield json.loads(line)
    else:
        with open(path,encoding='utf8') as f:
            for line in f:yield json.loads(line)


def audit_title_duplicates(meta):
    group=collections.defaultdict(list)
    for m in meta.values():
        group[(m['institution'],int(m['year']),norm(m['title']))].append(m)
    pairs=[]; drop=set()
    for (inst,year,title),members in group.items():
        if len(members)!=2:continue
        a,b=members
        id_a,id_b=a['doc_id'],b['doc_id']
        words_a,words_b=to_int(a['words_processed']),to_int(b['words_processed'])
        ratio=min(words_a,words_b)/max(words_a,words_b) if min(words_a,words_b) else 0
        is_numeric_a=bool(re.fullmatch(r'\d+',id_a))
        is_numeric_b=bool(re.fullmatch(r'\d+',id_b))
        source_overlap=is_numeric_a!=is_numeric_b
        # Never deduplicate two records solely because of a generic title.
        # A second independent signal is near-identical extracted word count.
        # Keep the dedicated PDF text (numeric ID) in detected OCR/PDF overlap.
        strong=inst=='IHEID' and source_overlap and ratio>=.995
        remove=id_b if strong and is_numeric_a else id_a if strong and is_numeric_b else ''
        keep=id_a if strong and is_numeric_a else id_b if strong and is_numeric_b else ''
        if remove:drop.add(remove)
        pairs.append({'institution':inst,'year':year,'title':a['title'],
                      'doc_a':id_a,'doc_b':id_b,'words_a':words_a,'words_b':words_b,
                      'word_ratio':round(ratio,5),'source_overlap':int(source_overlap),
                      'classification':'strong_probable_duplicate' if strong else 'unresolved_title_collision',
                      'keep':keep,'remove':remove})
    return pairs,drop


def build(args):
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    metadata={r['doc_id']:r for r in csvrows(args.metadata) if r['include']=='1' and 1927 <= to_int(r['year'])<=2026}
    if len(metadata)!=1730:raise ValueError(f'Expected corrected input of 1,730 doctoral records; got {len(metadata)}')
    duplicate_audit,drop=audit_title_duplicates(metadata)
    dumpcsv(out/'duplicate_audit.csv',duplicate_audit,
            ['institution','year','title','doc_a','doc_b','words_a','words_b','word_ratio',
             'source_overlap','classification','keep','remove'])
    if args.dedup_strong:
        metadata={did:m for did,m in metadata.items() if did not in drop}

    cand=csvrows(args.candidates);links=csvrows(args.screened)
    identities,audit,surnames,by_qid=identify(cand,links,load_registry(args.curated))
    audit_cols=['surface','qid','candidate_label','source_status','action','reason','mentions_inventory','country','basis']
    dumpcsv(out/'identity_audit.csv',audit,audit_cols)
    orgcounts=collections.Counter();direct=collections.Counter();country_words={};
    for r in csvrows(args.entity_counts):
        did=r['doc_id'];
        if did not in metadata or r['channel']!='direct':continue
        if r['category']=='country':direct[(did,canon_country(r['entity']))]+=to_int(r['mentions'])
        elif r['category'] in ('organization','family'):
            orgcounts[(did,r['entity'])]+=to_int(r['mentions'])
    per_person=collections.Counter();per_person_primary=collections.Counter()
    per_person_expanded=collections.Counter(); person_meta={}
    diag=collections.Counter(); exact_present=set()
    raw_doc_forms={}
    for d in read_ner(args.ner):
        did=d['doc_id'];
        if did not in metadata:continue
        dform=collections.Counter()
        for t in ('PER','PERSON'):
            for sf,n in d.get('entities_by_type',{}).get(t,{}).items():
                dform[norm(sf)]+=to_int(n)
        raw_doc_forms[did]=dform
        by_qid_doc=collections.Counter(); curated_qids=set()
        for sf,n in dform.items():
            data=identities.get(sf)
            if not data:continue
            qid=data['qid'];
            by_qid_doc[qid]+=n
            if qid in by_qid:
                person_meta[qid]=dict(qid=qid,name=by_qid[qid][0],country=by_qid[qid][1],basis='curated_office',channel='curated_exact')
            else:
                person_meta[qid]=data
            if data['channel']=='curated_exact':
                per_person_primary[(did,qid)]+=n
                curated_qids.add(qid)
            else:
                diag['provisional_mentions']+=n
        for qid in curated_qids:exact_present.add((did,qid))
        for qid,n in by_qid_doc.items():per_person[(did,qid)]+=n
    # Add the surname-only sensitivity only to documents already containing a
    # verified complete-name/alias for the SAME QID. This is not main analysis.
    for did,forms in raw_doc_forms.items():
        for sf,n in forms.items():
            qid=surnames.get(sf)
            if not qid or (did,qid) not in exact_present: continue
            person_meta[qid]=dict(qid=qid,name=by_qid[qid][0],country=by_qid[qid][1],
                                  basis='curated_office',channel='curated_exact')
            per_person_expanded[(did,qid)]+=n
    # Diagnostic: the three levels are separate, never automatically merged for headline.
    docs=list(metadata)
    perdocrows=[]
    for (did,qid),n in per_person.items():
        p=person_meta[qid];m=metadata[did]
        perdocrows.append({'doc_id':did,'year':int(m['year']),'institution':m['institution'],
                           'qid':qid,'name':p['name'],'country':p['country'],'mentions':n,
                           'link_channel':'curated_exact' if per_person_primary[(did,qid)] else 'provisional_full_name',
                           'country_basis':p['basis'],
                           'curated_exact_mentions':per_person_primary[(did,qid)],
                           'curated_surname_cooccurrence_extra':per_person_expanded[(did,qid)],
                           'meets_5':int(n>=5)})
    person_cols=['doc_id','year','institution','qid','name','country','mentions','link_channel',
                 'country_basis','curated_exact_mentions','curated_surname_cooccurrence_extra','meets_5']
    dumpcsv(out/'person_doc_links.csv',perdocrows,person_cols)
    # Country actor inference uses only curated exact names. One QID/person per thesis.
    country_people=collections.defaultdict(list)
    provisional_office=collections.defaultdict(list)
    provisional_citizen=collections.defaultdict(list)
    for (did,qid),n in per_person.items():
        if per_person_primary[(did,qid)]:continue
        p=person_meta[qid]
        entry=(qid,n,p['name'])
        if p['basis']=='political_office':provisional_office[(did,p['country'])].append(entry)
        else:provisional_citizen[(did,p['country'])].append(entry)
    for (did,qid),n in per_person_primary.items():
        if n:
            country_people[(did,person_meta[qid]['country'])].append((qid,n,person_meta[qid]['name']))
    allkeys=set(direct)|set(country_people)|set(provisional_office)|set(provisional_citizen)
    geography=[]
    for (did,country) in sorted(allkeys):
        m=metadata[did]; pairs=country_people.get((did,country),[])
        n_actors=len({qid for qid,_,_ in pairs})
        mentions=sum(n for _,n,_ in pairs)
        dirn=direct[(did,country)]
        pr_office=provisional_office.get((did,country),[])
        pr_citizen=provisional_citizen.get((did,country),[])
        geography.append({'doc_id':did,'year':int(m['year']),'institution':m['institution'],
                          'country':country,'direct_mentions':dirn,'direct3':int(dirn>=3),
                          'direct5':int(dirn>=5),'direct10':int(dirn>=10),
                          'direct_rate_per_10k':round(10000*dirn/max(1,to_int(m['words_processed'])),3),
                          'direct5_density2':int(dirn>=5 and dirn*10000/max(1,to_int(m['words_processed']))>=2),
                          'curated_actor_mentions':mentions,'curated_actor_qids':n_actors,
                          'actor5':int(mentions>=5),'actor_strong':int(mentions>=5 and n_actors>=2),
                          'concordant':int(dirn>=5 and mentions>=5 and n_actors>=2),
                          'provisional_office_actor_qids':len(set(q for q,_,_ in pr_office)),
                          'provisional_office_mentions':sum(n for _,n,_ in pr_office),
                          'provisional_citizen_actor_qids':len(set(q for q,_,_ in pr_citizen)),
                          'provisional_citizen_mentions':sum(n for _,n,_ in pr_citizen)})
    geo_cols=['doc_id','year','institution','country','direct_mentions','direct3','direct5','direct10',
              'direct_rate_per_10k','direct5_density2',
              'curated_actor_mentions','curated_actor_qids','actor5','actor_strong','concordant',
              'provisional_office_actor_qids','provisional_office_mentions',
              'provisional_citizen_actor_qids','provisional_citizen_mentions']
    dumpcsv(out/'thesis_country_evidence.csv',geography,geo_cols)
    # Rebuild document decade comparisons for consistent denominators.
    keys=collections.Counter((m['institution'],int(m['year'])//10*10) for m in metadata.values())
    by_g=collections.defaultdict(list)
    for r in geography:by_g[(r['institution'],r['year']//10*10,r['country'])].append(r)
    country_decades=[]
    for (inst,dec),n_docs in sorted(keys.items()):
        countries=sorted({k[2] for k in by_g if k[0]==inst and k[1]==dec})
        for country in countries:
            rr=by_g[(inst,dec,country)]
            country_decades.append({'institution':inst,'decade':dec,'n_theses':n_docs,'country':country,
                                    'direct3_n':sum(x['direct3'] for x in rr),
                                    'direct3_pct':round(100*sum(x['direct3'] for x in rr)/n_docs,2),
                                    'direct5_n':sum(x['direct5'] for x in rr),
                                    'direct5_pct':round(100*sum(x['direct5'] for x in rr)/n_docs,2),
                                    'direct10_n':sum(x['direct10'] for x in rr),
                                    'direct10_pct':round(100*sum(x['direct10'] for x in rr)/n_docs,2),
                                    'direct5_density2_n':sum(x['direct5_density2'] for x in rr),
                                    'direct5_density2_pct':round(100*sum(x['direct5_density2'] for x in rr)/n_docs,2),
                                    'actor_strong_n':sum(x['actor_strong'] for x in rr),
                                    'actor_strong_pct':round(100*sum(x['actor_strong'] for x in rr)/n_docs,2),
                                    'concordant_n':sum(x['concordant'] for x in rr),
                                    'provisional_office5_n':sum(x['provisional_office_mentions']>=5 for x in rr),
                                    'provisional_citizen5_n':sum(x['provisional_citizen_mentions']>=5 for x in rr)})
    dumpcsv(out/'country_decade_by_institute.csv',country_decades,
            ['institution','decade','n_theses','country','direct3_n','direct3_pct','direct5_n','direct5_pct',
             'direct10_n','direct10_pct','direct5_density2_n','direct5_density2_pct','actor_strong_n','actor_strong_pct','concordant_n',
             'provisional_office5_n','provisional_citizen5_n'])
    # Organization and family decade prevalence with n >= 5 *direct* NER mentions.
    by_org=collections.defaultdict(set)
    all_orgs=set()
    for (did,org),n in orgcounts.items():
        all_orgs.add(org)
        for cutoff in (3,5,10):
            if n>=cutoff:by_org[(metadata[did]['institution'],int(metadata[did]['year'])//10*10,org,cutoff)].add(did)
    org_decades=[]
    for (inst,dec),count in sorted(keys.items()):
        for org in sorted(all_orgs):
            vals={cutoff:len(by_org.get((inst,dec,org,cutoff),set())) for cutoff in (3,5,10)}
            org_decades.append({'institution':inst,'decade':dec,'n_theses':count,'organization':org,
                                **{f'direct{cutoff}_n':n for cutoff,n in vals.items()},
                                **{f'direct{cutoff}_pct':round(n/count*100,2) for cutoff,n in vals.items()}})
    dumpcsv(out/'organizations_decade_by_institute.csv',org_decades,
            ['institution','decade','n_theses','organization','direct3_n','direct5_n','direct10_n',
             'direct3_pct','direct5_pct','direct10_pct'])
    # People by decade: denominator is all PhDs from that institute+decade.
    by_p=collections.defaultdict(set)
    for (did,qid),n in per_person_primary.items():
        if n>=5:by_p[(metadata[did]['institution'],int(metadata[did]['year'])//10*10,qid)].add(did)
    people_decades=[]
    for (inst,dec),count in sorted(keys.items()):
        for qid,(name,country) in by_qid.items():
            k=len(by_p.get((inst,dec,qid),set()))
            if k:
                people_decades.append({'institution':inst,'decade':dec,'n_theses':count,
                                       'name':name,'qid':qid,'country':country,
                                       'curated_5_n':k,'curated_5_pct':round(k/count*100,2)})
    dumpcsv(out/'people_decade_by_institute.csv',people_decades,
            ['institution','decade','n_theses','name','qid','country','curated_5_n','curated_5_pct'])
    # Year-centered windows for major countries and institutions.
    rolling=[]
    for inst,width in [('HEI',9),('IHEID',5),('IUED',15)]:
        mm=[m for m in metadata.values() if m['institution']==inst]
        years=range(min(int(m['year']) for m in mm),max(int(m['year']) for m in mm)+1)
        top=collections.Counter({c:sum(r['direct5'] for r in geography if r['institution']==inst and r['country']==c)
                                 for c in set(r['country'] for r in geography)})
        country_set=[x for x,_ in top.most_common(16)]
        for yr in years:
            docids={did for did,m in metadata.items() if m['institution']==inst and abs(int(m['year'])-yr)<=width//2}
            n=len(docids)
            if not n:continue
            for country in country_set:
                rows=[r for r in geography if r['doc_id'] in docids and r['country']==country]
                rolling.append({'institution':inst,'year':yr,'window_years':width,'n_theses':n,
                                'country':country,
                                'direct5_pct':round(100*sum(r['direct5'] for r in rows)/n,2),
                                'actor_strong_pct':round(100*sum(r['actor_strong'] for r in rows)/n,2),
                                'concordant_pct':round(100*sum(r['concordant'] for r in rows)/n,2)})
    dumpcsv(out/'country_rolling_by_institute.csv',rolling,
            ['institution','year','window_years','n_theses','country','direct5_pct','actor_strong_pct','concordant_pct'])
    n_curated_qids=len({q for _,q in per_person_primary})
    n_provisional=len({q for (did,q) in per_person if (did,q) not in per_person_primary})
    reported={'doctoral_documents':len(metadata),
              'doctoral_counts':dict(collections.Counter(m['institution'] for m in metadata.values())),
              'dedup_strong_mode':bool(args.dedup_strong),
              'same_title_year_institution_pairs':len(duplicate_audit),
              'strong_probable_duplicates':len(drop),
              'probable_duplicate_records_removed':len(drop) if args.dedup_strong else 0,
              'inventory_people':len(cand),
              'identity_actions':dict(collections.Counter(r['action'] for r in audit)),
              'unique_corpus_qids_curated':n_curated_qids,
              'unique_corpus_qids_provisional':n_provisional,
              'curated_person_doc_pairs':len(per_person_primary),
              'curated_surname_doc_pairs_reinforcement_only':len(per_person_expanded),
              'curated_actor_geo_5plus_country_doc_pairs':sum(r['actor5'] for r in geography),
              'curated_actor_strong_country_doc_pairs':sum(r['actor_strong'] for r in geography),
              'concordant_country_doc_pairs':sum(r['concordant'] for r in geography),
              'direct_country_5plus_country_doc_pairs':sum(r['direct5'] for r in geography),
              'direct_country_5plus_density2_country_doc_pairs':sum(r['direct5_density2'] for r in geography),
              'provisional_office_5plus_doc_country_pairs':sum(r['provisional_office_mentions']>=5 for r in geography),
              'provisional_citizen_5plus_doc_country_pairs':sum(r['provisional_citizen_mentions']>=5 for r in geography),
              'distinct_country_labels':len({r['country'] for r in geography}),
              'distinct_organization_labels':len(all_orgs),
              'limitations':['Counts cannot distinguish citations, body and bibliography.',
                 'Curated registry only covers 61 people and underestimates historical actors.',
                 'Automated multi-token matches remain provisional and are not used in headline geography.',
                 'Weak citizenship fallback does not establish a thesis topic.',
                 'Period and institution are confounded. IUED doctoral n=23.']}
    (out/'summary.json').write_text(json.dumps(reported,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    draw_figures(out,rolling,org_decades,people_decades,country_decades,keys)
    print(json.dumps(reported,indent=2,ensure_ascii=False))


def draw_figures(out,rolling,orgrows,perrows,countryrows,keys):
    plt.rcParams.update({'font.size':9,'figure.dpi':120})
    # 1. Direct country signals: no inferred citizenship included.
    major=['United States','France','China','India','Germany','United Kingdom','Soviet Union','Russia']
    fig,axes=plt.subplots(2,1,figsize=(11,8),sharey=True)
    for ax,inst in zip(axes,['HEI','IHEID']):
        rs=[r for r in rolling if r['institution']==inst]
        for c in major:
            pts=[r for r in rs if r['country']==c and r['n_theses']>=10]
            if pts:ax.plot([r['year'] for r in pts],[r['direct5_pct'] for r in pts],label=c,linewidth=1.6)
        ax.set_title(f'{inst} — pays cités directement ≥5 fois (fenêtre {9 if inst=="HEI" else 5} ans)')
        ax.set_ylabel('% de doctorats');ax.grid(alpha=.2)
        ax.legend(ncol=4,fontsize=8,loc='upper right')
    fig.tight_layout();fig.savefig(out/'01_pays_mentions_directes.png',dpi=180,bbox_inches='tight');plt.close(fig)
    # 2. IOs and political integration: separately by institute, don't splice 2008.
    available=set(r['organization'] for r in orgrows)
    wanted=['SDN','ONU','Construction européenne (strictement CEE→CE→UE)','GATT','OMC','FMI','Banque mondiale']
    series=[c for c in wanted if c in available]
    if not series:series=sorted(available)[:6]
    fig,axs=plt.subplots(2,1,figsize=(11,7),sharey=True)
    for ax,inst in zip(axs,['HEI','IHEID']):
        for org in series:
            rows=[r for r in orgrows if r['institution']==inst and r['organization']==org and r['n_theses']>=10]
            if rows:
                ax.plot([r['decade'] for r in rows],[r['direct5_pct'] for r in rows],marker='o',label=org)
        ax.set_title(inst+' — organisations citées directement ≥5 fois (par décennie)')
        ax.set_ylabel('% de doctorats');ax.grid(alpha=.2)
        ax.legend(ncol=4,fontsize=8,loc='upper right')
    fig.tight_layout();fig.savefig(out/'02_organisations_par_decennie.png',dpi=180,bbox_inches='tight');plt.close(fig)
    # 3. Matched and direct country evidence: non-comparable proxies, show side by side.
    filt=['France','United States','China','United Kingdom','Germany','India','Israel','Soviet Union','Iraq','Iran']
    agg=collections.defaultdict(lambda:[0,0,0,0])
    for r in countryrows:
        if r['country'] not in filt: continue
        k=(r['institution'],r['country']);arr=agg[k]
        arr[0]+=r['direct5_n'];arr[1]+=r['actor_strong_n'];arr[2]+=r['concordant_n'];arr[3]+=r['n_theses'] if False else 0
    fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
    for ax,inst in zip(axes,['HEI','IHEID']):
        cc=[agg[(inst,c)] for c in filt]; y=np.arange(len(filt))
        ax.barh(y-.18,[v[0] for v in cc],height=.35,label='Mention directe ≥5')
        ax.barh(y+.18,[v[1] for v in cc],height=.35,label='≥2 personnalités vérifiées et ≥5 mentions')
        ax.set_yticks(y,filt);ax.invert_yaxis();ax.set_title(inst)
        ax.set_xlabel('Couples thèse–pays');ax.grid(alpha=.2,axis='x');ax.legend(fontsize=8)
    fig.suptitle('Mentions géographiques et signal biographique (registres non équivalents)')
    fig.tight_layout();fig.savefig(out/'03_pays_acteurs_verifies.png',dpi=180,bbox_inches='tight');plt.close(fig)
    # 4. Person prominence, scaled by thesis volume, independently by institution.
    fig,axs=plt.subplots(2,1,figsize=(11,8),sharey=True)
    for ax,inst in zip(axs,['HEI','IHEID']):
        rr=[r for r in perrows if r['institution']==inst]
        n_by_person=collections.Counter()
        for r in rr:n_by_person[(r['name'],r['qid'])]+=r['curated_5_n']
        top=[qid for (name,qid),num in n_by_person.most_common(7)]
        years=sorted({r['decade'] for r in rr if r['n_theses']>=10})
        for qid in top:
            pp={r['decade']:r for r in rr if r['qid']==qid}
            name=next((r['name'] for r in rr if r['qid']==qid),qid)
            ys=[pp[d]['curated_5_pct'] if d in pp else 0 for d in years]
            ax.plot(years,ys,marker='o',label=name,linewidth=1.6)
        ax.set_title(inst+' — noms complets vérifiés ≥5 fois (par décennie)')
        ax.set_ylabel('% de doctorats');ax.grid(alpha=.2);ax.legend(ncol=3,fontsize=8,loc='upper right')
    fig.suptitle('Personnalités du registre contrôlé — signal sous-estimé (les patronymes seuls sont exclus)')
    fig.tight_layout();fig.savefig(out/'04_personnalites_verifiees.png',dpi=180,bbox_inches='tight');plt.close(fig)



if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--ner',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--entity-counts',type=Path,required=True)
    p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--screened',type=Path,required=True)
    p.add_argument('--curated',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dedup-strong',action='store_true',help='Sensitivity: remove only near-identical cross-source IHEID records')
    build(p.parse_args())
