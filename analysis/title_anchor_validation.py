#!/usr/bin/env python3
"""Validate and triangulate top-50 IHEID doctoral NER from catalogue titles only.

Title exact toponyms/organization names are positive *title evidence*, never a complete
subject classification.  Documents not naming an entity in their title remain unknown.
No API, full texts or new NER required. All input paths explicit and provenance logged.
"""
import argparse,csv,json,math,re,unicodedata,zipfile
from collections import Counter,defaultdict
from pathlib import Path

# Conservative EXACT toponyms; deliberately excludes standalone US/UK, America,
# bare EU/UN/EC, generic 'Soviet' and adjectives such as 'French'.
COUNTRIES={
'United States':['united states','etats unis','etats-unis','estados unidos','vereinigte staaten','usa','u s a'],
'France':['france','francia','frankreich'],
'China':['china','chine','chine populaire','chinas'],
'India':['india','inde','bharat'],
'Germany':['germany','allemagne','alemania','deutschland'],
'United Kingdom':['united kingdom','royaume uni','royaume-uni','reino unido','grossbritannien','great britain'],
'Russia':['russia','russie','rusia','russland'],
'Soviet Union':['soviet union','union sovietique','unione sovietica','urss','ussr','udssr','urssr'],
'Switzerland':['switzerland','suisse','schweiz','suiza'],
'Brazil':['brazil','bresil','brasil'],
'Japan':['japan','japon','japao'],
'Italy':['italy','italie','italia'],
'Spain':['spain','espagne','espana','spanien'],
'Turkey':['turkey','turquie','turkiye','turkei'],
'Israel':['israel'],
'Palestine':['palestine','palestina','palastina'],
'Ukraine':['ukraine','ucrania'],
'Iran':['iran'],
'Iraq':['iraq','irak'],
'Cuba':['cuba'],
'Vietnam':['vietnam','viet nam'],
'South Africa':['south africa','afrique du sud','sudafrica'],
'North Korea':['north korea','coree du nord'],
'South Korea':['south korea','coree du sud'],
'Mexico':['mexico','mexique','mexiko'],
'Argentina':['argentina','argentine','argentinien'],
'Colombia':['colombia','colombie'],
'Chile':['chile','chili'],
'Peru':['peru','perou'],
'Bolivia':['bolivia','bolivie'],
'Ghana':['ghana'],
'Nigeria':['nigeria'],
'Senegal':['senegal'],
'Egypt':['egypt','egypte','egipto','agypten'],
'Libya':['libya','libye','libia'],
'Morocco':['morocco','maroc','marruecos','marokko'],
'Algeria':['algeria','algerie','argelia'],
'Tunisia':['tunisia','tunisie','tunez'],
'Ethiopia':['ethiopia','ethiopie','etiopia'],
'Kenya':['kenya'],
'Uganda':['uganda','ouganda'],
'DR Congo':['democratic republic of congo','democratic republic of the congo','republique democratique du congo','rd congo','r d congo'],
'Zaire':['zaire'],
'Yugoslavia':['yugoslavia','yougoslavie','jugoslawien'],
'East Germany':['east germany','allemagne de l est','rda','ddr'],
'West Germany':['west germany','allemagne de l ouest','rfa','frg'],
'Cambodia':['cambodia','cambodge','camboya'],
'Pakistan':['pakistan'],
'Bangladesh':['bangladesh'],
'Indonesia':['indonesia','indonesie'],
'Philippines':['philippines','filipinas'],
'Lebanon':['lebanon','liban','libano'],
'Syria':['syria','syrie','siria'],
'Jordan':['jordan','jordanie','jordania'],
'Saudi Arabia':['saudi arabia','arabie saoudite','arabia saudita'],
'Afghanistan':['afghanistan'],
}
# Organization labels are kept historically separate where meaningful.
# Keys correspond to title concepts; NER labels below resolve canonical IDs.
ORG_NER_LABELS={'CEE':'CEE/EEC','CE':'CE/EC','UE':'UE/EU'}
ORGANIZATIONS={
'SDN':['league of nations','societe des nations','sdn','volkerbund'],
'ONU':['united nations','nations unies','onu','organizacion de las naciones unidas'],
'CEE':['european economic community','communaute economique europeenne','comunidad economica europea','cee','eec'],
'CE':['european community','communaute europeenne','comunidad europea'],
'UE':['european union','union europeenne','union europea','europaische union'],
'GATT':['general agreement on tariffs and trade','gatt'],
'OMC':['world trade organization','organisation mondiale du commerce','organizacion mundial del comercio','wto','omc'],
'FMI':['international monetary fund','fonds monetaire international','fondo monetario internacional','imf','fmi'],
'Banque mondiale':['world bank','banque mondiale','banco mundial'],
'ASEAN':['asean','association of southeast asian nations'],
'OMS':['world health organization','organisation mondiale de la sante','organizacion mundial de la salud','oms'],
}

def normalize(s):
    s=unicodedata.normalize('NFKD',str(s).casefold())
    s=''.join(c for c in s if not unicodedata.combining(c))
    return ' '.join(re.sub('[^a-z0-9]+',' ',s).split())

def read_csv(p):
    with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(p,rows,fields):
    with open(p,'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

def title_matches(title, lexicon):
    t=' '+normalize(title)+' '
    result={}
    for k,variants in lexicon.items():
        matches=[v for v in variants if ' '+normalize(v)+' ' in t]
        if matches:result[k]=sorted(matches,key=lambda s:-len(s))[0]
    return result

def wilson(x,n,z=1.96):
    if not n:return (0.,0.)
    p=x/n; a=z*z;d=1+a/n
    mid=(p+a/(2*n))/d; rad=z*math.sqrt((p*(1-p)+a/(4*n))/n)/d
    return round(100*(mid-rad),2),round(100*(mid+rad),2)

def main(args):
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    source=read_csv(args.metadata)
    source={r['doc_id']:r for r in source if r['include']=='1'}
    dups=read_csv(args.duplicate_audit)
    dropped={r['remove'] for r in dups if r['classification']=='strong_probable_duplicate' and r['remove']}
    if args.dedup_strong: source={did:r for did,r in source.items() if did not in dropped}
    n_by=Counter((r['institution'],int(r['year'])//10*10) for r in source.values())
    direct_country={}
    for r in read_csv(args.thesis_country):
        if r['doc_id'] in source:
            direct_country[(r['doc_id'],r['country'])]=int(r['direct_mentions'])
    # Use ORIGINAL systematic entity counts for organization evidence, not group estimates.
    org_doc={}
    with zipfile.ZipFile(args.systematic) as z:
        member=next(n for n in z.namelist() if n.endswith('document_entity_counts.csv'))
        with z.open(member) as f:
            reader=csv.DictReader((line.decode('utf-8-sig') for line in f))
            for r in reader:
                if r['doc_id'] in source and r['channel']=='direct' and r['category'] in ('organization','family'):
                    org_doc[(r['doc_id'],r['entity'])]=max(org_doc.get((r['doc_id'],r['entity']),0),int(float(r['mentions'])))
    records=[]
    for did,r in sorted(source.items()):
        year=int(r['year']);inst=r['institution'];dec=year//10*10
        for typ,lex in [('country',COUNTRIES),('organization',ORGANIZATIONS)]:
            matches=title_matches(r['title'],lex)
            for e,term in matches.items():
                if typ=='country':n=direct_country.get((did,e),0)
                else:n=org_doc.get((did,ORG_NER_LABELS.get(e,e)),0)
                records.append({'doc_id':did,'year':year,'decade':dec,'institution':inst,'title':r['title'],
                                'entity_type':typ,'entity':e,'title_keyword':term,
                                'ner_direct_mentions':n,'ner_direct_3':int(n>=3),'ner_direct_5':int(n>=5),
                                'ner_direct_10':int(n>=10),'source':'catalogue_title_exact_phrase',
                                'title_evidence':'explicit_name_in_title_not_proven_main_subject'})
    title_country={(r['doc_id'],r['entity']) for r in records if r['entity_type']=='country'}
    title_org={(r['doc_id'],r['entity']) for r in records if r['entity_type']=='organization'}
    # All eligible entity/doc pairs, not just title-positive: enables precision-type
    # diagnostics of how often high-frequency NER has an explicit title anchor.
    compare=[]
    for typ,lex in [('country',COUNTRIES),('organization',ORGANIZATIONS)]:
        pairs=title_country if typ=='country' else title_org
        if typ=='country':nermap=direct_country
        else:nermap=org_doc
        for inst,dec in sorted(n_by):
            ids={k for k,v in source.items() if v['institution']==inst and int(v['year'])//10*10==dec}
            for label in lex:
                t={did for did,l in pairs if l==label and did in ids}
                nerlabel=ORG_NER_LABELS.get(label,label) if typ=='organization' else label
                ng3={did for did in ids if nermap.get((did,nerlabel),0)>=3}
                ng5={did for did in ids if nermap.get((did,nerlabel),0)>=5}
                ng10={did for did in ids if nermap.get((did,nerlabel),0)>=10}
                t_and5=t&ng5
                lo,hi=wilson(len(t),len(ids))
                compare.append({'institution':inst,'decade':dec,'n_theses':len(ids),'entity_type':typ,'entity':label,
                                'explicit_title_n':len(t),'explicit_title_pct':round(100*len(t)/len(ids),2),
                                'explicit_title_ci95_low':lo,'explicit_title_ci95_high':hi,
                                'ner_direct3_n':len(ng3),'ner_direct5_n':len(ng5),'ner_direct10_n':len(ng10),
                                'title_and_ner5_n':len(t_and5),'title_without_ner5_n':len(t-ng5),
                                'ner5_without_title_n':len(ng5-t),
                                'pct_ner5_given_title':round(100*len(t_and5)/len(t),2) if t else '',
                                'pct_title_given_ner5':round(100*len(t_and5)/len(ng5),2) if ng5 else ''})
    # One tab per title-positive pair, with no guesses about citation locations.
    write_csv(out/'title_evidence_doc_entity.csv',records,['doc_id','year','decade','institution','title','entity_type','entity','title_keyword','ner_direct_mentions','ner_direct_3','ner_direct_5','ner_direct_10','source','title_evidence'])
    write_csv(out/'title_ner_triangulation_decade.csv',compare,list(compare[0]))
    covered=Counter(r['entity_type'] for r in records)
    nposit=Counter(r['entity_type'] for r in records if r['ner_direct_5'])
    miss=Counter(r['entity_type'] for r in records if not r['ner_direct_5'])
    nner={k:sum(v>=5 for (did,e),v in (direct_country if k=='country' else org_doc).items()) for k in ('country','organization')}
    report={'doc_count':len(source),'historical_duplicate_records_dropped':len(dropped) if args.dedup_strong else 0,
            'documents_with_title_country':len({r['doc_id'] for r in records if r['entity_type']=='country'}),
            'documents_with_title_organization':len({r['doc_id'] for r in records if r['entity_type']=='organization'}),
            'title_entity_pairs':dict(covered),'title_entity_pairs_ner_direct5':dict(nposit),
            'title_entity_pairs_below_ner_direct5':dict(miss),
            'agreement_title_ner5_pct':{k:round(100*nposit[k]/covered[k],2) if covered[k] else None for k in covered},
            'warning':['Title lexicon is selective and positive-only; negative is unknown, not non-topic.',
                       'NER top-50 truncated; a title entity absent from top-50 is not an error by definition.',
                       'NER counts from heterogeneous multilingual models and historical OCR.',
                       'The 109 probable duplicate exclusions are sensitivity analysis, not proven text identity.',
                       'Do not interpret citizenship-based Wikidata geography as thesis focus.',
                       'Wilson intervals quantify sampling uncertainty conditional on this corpus, not measurement bias.']}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--metadata',required=True)
    p.add_argument('--duplicate-audit',required=True)
    p.add_argument('--thesis-country',required=True)
    p.add_argument('--systematic',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--dedup-strong',action='store_true')
    main(p.parse_args())
