#!/usr/bin/env python3
"""Aggregate Wikidata-filtered NER persons into doctoral country signals.

This is a deliberately approximate, *biographical* geography measure. Academic
P106 professions have been excluded upstream. With count-only NER, it does not
resolve bibliography vs thesis body. Historical entities remain distinct.

Example:
python analysis/aggregate_person_countries.py \
 --ner doctoral_ner_recovered.jsonl.zip \
 --metadata doctoral_metadata_recovered.csv \
 --country-ner document_entity_counts.csv \
 --people results/wikidata/people*.csv \
 --verified analysis/verified_actor_registry.csv --out results/person_geography
"""
import argparse,csv,json,math,re,unicodedata,zipfile
from collections import Counter,defaultdict
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import PowerNorm

FR_TO_CANONICAL={
'france':'France','royaume uni':'United Kingdom','etats unis':'United States',
'chine':'China','inde':'India','allemagne':'Germany','russie':'Russia',
'urss':'Soviet Union','suisse':'Switzerland','bresil':'Brazil','irak':'Iraq',
'iran':'Iran','israel':'Israel','palestine':'Palestine','bolivie':'Bolivia',
'ghana':'Ghana','rd congo':'DR Congo','turquie':'Turkey','afrique du sud':'South Africa',
'yougoslavie':'Yugoslavia','cuba':'Cuba','cambodge':'Cambodia','coree du nord':'North Korea',
'senegal':'Senegal','rda':'East Germany','japon':'Japan','italie':'Italy',
'royaume uni':'United Kingdom','etats unis':'United States',
}
EXPLICIT_IGNORE={'michel foucault','karl marx','max weber'}

def normalize(x):
    x=unicodedata.normalize('NFKD',str(x).casefold().replace('’',"'"))
    return ' '.join(re.sub(r'[^a-z0-9]+',' ',''.join(ch for ch in x if not unicodedata.combining(ch))).split())

def csvrows(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def canonical(country):
    return FR_TO_CANONICAL.get(normalize(country),country.strip())

def registry(people_files,verified):
    """One surface -> one QID, or excluded on conflict. Verified actors override API."""
    registry=[]
    for file in people_files:
        for r in csvrows(file):
            if r.get('screen_status')!='retained' or not r.get('qid') or not r.get('country'):continue
            country=canonical(r['country'])
            if normalize(r.get('label','')) in EXPLICIT_IGNORE:continue
            registry.append(dict(surface=normalize(r['surface']),qid=r['qid'],
                name=r.get('label',''),country=country,
                basis=r.get('country_basis') or 'unspecified',source='wikidata_screened'))
    if verified:
        for r in csvrows(verified):
            c=canonical(r['political_jurisdiction'])
            if not c or c in ('None','Unknown'):continue
            if normalize(r.get('canonical_name','')) in EXPLICIT_IGNORE:continue
            for s in r.get('accepted_ner_surfaces','').split('|'):
                if normalize(s):
                    registry.append(dict(surface=normalize(s),qid=r['wikidata_qid'],
                        name=r['canonical_name'],country=c,basis='verified_office',source='verified_registry'))
    # Existing curated registry should take precedence over Wikidata, while
    # two contradictory Wikidata automatic candidates invalidate a surface.
    by_surface=defaultdict(list)
    for r in registry:by_surface[r['surface']].append(r)
    valid={};conflicts=[]
    for surface,rr in by_surface.items():
        verified_rows=[r for r in rr if r['source']=='verified_registry']
        pool=verified_rows if verified_rows else rr
        ident={(r['qid'],r['country']) for r in pool}
        if len(ident)!=1:
            conflicts.append(dict(surface=surface,alternatives='|'.join(sorted(f'{q}:{c}' for q,c in ident))))
            continue
        valid[surface]=pool[0]
    return valid,conflicts

def document_records(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        files=[x for x in z.namelist() if x.endswith('.jsonl')]
        if len(files)!=1:raise ValueError('Expected exactly one jsonl file')
        with z.open(files[0]) as fh:
            for line in fh:yield json.loads(line)

def aggregate(args):
    meta={r['doc_id']:r for r in csvrows(args.metadata) if r.get('include','1')=='1'}
    print('Doctoral metadata:',len(meta))
    people,conflicts=registry(args.people,args.verified)
    print('Accepted raw surfaces:',len(people),'conflicts',len(conflicts))
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(conflicts,columns=['surface','alternatives']).to_csv(out/'surface_conflicts.csv',index=False)
    direct=Counter()
    if args.country_ner:
        for r in csvrows(args.country_ner):
            if r.get('category')=='country' and r.get('channel')=='direct' and r['doc_id'] in meta:
                direct[(r['doc_id'],canonical(r['entity']))]+=int(float(r['mentions']))
    individuals=[];summaries=[];used=set()
    for doc in document_records(args.ner):
        did=doc['doc_id']
        if did not in meta:continue
        m=meta[did]
        qid_count=Counter();qid_detail={};qid_surfaces=defaultdict(set)
        for typ in ('PER','PERSON'):
            for surface,n in doc.get('entities_by_type',{}).get(typ,{}).items():
                norm=normalize(surface)
                info=people.get(norm)
                if not info:continue
                key=info['qid'];qid_count[key]+=int(n)
                qid_detail[key]=info;qid_surfaces[key].add(norm);used.add(norm)
        by_country=defaultdict(list)
        for qid,num in qid_count.items():
            info=qid_detail[qid]
            by_country[info['country']].append((qid,num,info))
            individuals.append(dict(doc_id=did,year=int(m['year']),institution=m['institution'],
                qid=qid,canonical_name=info['name'],country=info['country'],mentions=num,
                basis=info['basis'],source=info['source']))
        for country,entries in by_country.items():
            count=sum(n for _,n,_ in entries)
            n_distinct=len(entries)
            title=normalize(m.get('title',''))
            title_hit=sum(1 for qid,_,info in entries if any(
                len(surface)>=6 and (' '+surface+' ') in (' '+title+' ')
                for surface in qid_surfaces[qid]))
            office_count=sum(1 for _,_,info in entries if info['basis'] in ('political_office','verified_office'))
            # Conservative default: 2 distinct people and >=5 cumulative mentions.
            strong=count>=5 and (n_distinct>=2 or title_hit>0)
            summaries.append(dict(doc_id=did,year=int(m['year']),institution=m['institution'],
                country=country,people_mentions=count,distinct_people=n_distinct,
                political_office_people=office_count,person_named_in_title=title_hit,
                score=round(sum(math.log1p(n) for _,n,_ in entries),3),
                mentions_country_direct=direct[(did,country)],
                direct5=int(direct[(did,country)]>=5),
                bio5=int(count>=5),bio_strong=int(strong),
                concordant=int(strong and direct[(did,country)]>=5)))
    # Keep the full direct-country baseline, including country-only thesis pairs.
    observed={(r['doc_id'],r['country']) for r in summaries}
    for (did,country),n in direct.items():
        if (did,country) in observed:continue
        m=meta[did]
        summaries.append(dict(doc_id=did,year=int(m['year']),institution=m['institution'],
            country=country,people_mentions=0,distinct_people=0,
            political_office_people=0,person_named_in_title=0,score=0.0,
            mentions_country_direct=n,direct5=int(n>=5),bio5=0,bio_strong=0,concordant=0))
    pd.DataFrame(individuals,columns=['doc_id','year','institution','qid','canonical_name',
        'country','mentions','basis','source']).to_csv(out/'person_doc_counts.csv',index=False)
    df=pd.DataFrame(summaries,columns=['doc_id','year','institution','country','people_mentions','distinct_people',
        'political_office_people','person_named_in_title','score','mentions_country_direct',
        'direct5','bio5','bio_strong','concordant'])
    df.to_csv(out/'doc_country_scores.csv',index=False)
    audit={'metadata_theses':len(meta),'theses_with_recognized_people':len(set(x['doc_id'] for x in individuals)),
        'surfaces_accepted':len(people),'surfaces_encountered':len(used),
        'distinct_people_qids':len(set(x['qid'] for x in individuals)),
        'person_mentions':sum(x['mentions'] for x in individuals),
        'doc_country_rows':len(summaries),'bio_strong_doc_country':int(df.bio_strong.sum()) if len(df) else 0,
        'concordant_strong':int(df.concordant.sum()) if len(df) else 0,
        'direct_country_doc_pairs_5plus':int(df.direct5.sum()) if len(df) else 0,
        'warning':'Count-only NER; academic occupation exclusion is approximate, not a bibliography section classifier'}
    (out/'report.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    years=[]
    for inst in ('HEI','IUED','IHEID'):
        docs=[m for m in meta.values() if m['institution']==inst]
        if not docs:continue
        lo=min(int(x['year']) for x in docs);hi=max(int(x['year']) for x in docs)
        width={'HEI':9,'IUED':15,'IHEID':5}[inst]
        docs_by_year=Counter(int(x['year']) for x in docs)
        g=df[df.institution==inst]
        countries=sorted(set(g.country))
        for y in range(lo,hi+1):
            half=width//2
            ndocs=sum(n for yy,n in docs_by_year.items() if y-half<=yy<=y+half)
            if not ndocs:continue
            subs=g[g.year.between(y-half,y+half)]
            for c in countries:
                z=subs[subs.country==c]
                years.append(dict(institution=inst,year=y,window=width,country=c,n_docs=ndocs,
                    pct_direct5=round(100*z.direct5.sum()/ndocs,3),
                    pct_bio5=round(100*z.bio5.sum()/ndocs,3),
                    pct_bio_strong=round(100*z.bio_strong.sum()/ndocs,3),
                    pct_concordant=round(100*z.concordant.sum()/ndocs,3)))
    yearly=pd.DataFrame(years)
    yearly.to_csv(out/'rolling_country_by_institute.csv',index=False)
    for inst in ('HEI','IHEID'):
        z=yearly[yearly.institution==inst]
        top=df[df.institution==inst].groupby('country')['bio_strong'].sum().nlargest(15).index
        top=[x for x in top if x in z.country.values]
        if not top:continue
        p=z[z.country.isin(top)].pivot(index='country',columns='year',values='pct_bio_strong').reindex(top)
        vals=p.to_numpy(float)
        fig,ax=plt.subplots(figsize=(12,6.2))
        vmax=max(1.,float(np.nanpercentile(vals,95)))
        im=ax.imshow(vals,aspect='auto',cmap='cividis',norm=PowerNorm(gamma=.55,vmin=0,vmax=vmax))
        ticks=list(range(0,len(p.columns),5))
        ax.set_xticks(ticks,[p.columns[i] for i in ticks],rotation=45,ha='right')
        ax.set_yticks(range(len(top)),top)
        ax.set_title(f'{inst} — pays signalés par ≥2 personnalités / ou une dans le titre')
        cb=fig.colorbar(im,ax=ax);cb.set_label('Part des thèses (%) ; fenêtre mobile')
        fig.tight_layout();fig.savefig(out/f'heatmap_{inst}.png',dpi=190,bbox_inches='tight');plt.close(fig)
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--ner',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--country-ner',type=Path)
    p.add_argument('--people',type=Path,nargs='*',default=[])
    p.add_argument('--verified',type=Path)
    p.add_argument('--out',type=Path,default=Path('results/person_geography'))
    a=p.parse_args()
    if not a.people and not a.verified:p.error('Provide --people and/or --verified')
    aggregate(a)