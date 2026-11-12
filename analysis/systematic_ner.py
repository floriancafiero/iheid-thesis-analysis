#!/usr/bin/env python3
"""Reproducible, auditable NER surface inventory and hierarchical resolution.

Every (NER label, normalized surface) gets a status: canonical, child_place,
ambiguous, noisy, candidate, unresolved. No silent fuzzy autocorrections.
Country and organization direct/parent counts are distinct, historical names retained.
"""
import ast,csv,json,re,unicodedata,zipfile,argparse
from collections import Counter,defaultdict
from pathlib import Path
from rapidfuzz import process,fuzz

HERE=Path(__file__).resolve().parent

def norm(s):
 s=unicodedata.normalize('NFKD',s.casefold().replace('’',"'").replace('‐','-'))
 s=''.join(c for c in s if not unicodedata.combining(c))
 return ' '.join(re.sub(r'[^a-z0-9]+',' ',s).split())

def get_constant(path,key):
 tree=ast.parse(Path(path).read_text(encoding='utf8'))
 for node in tree.body:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in node.targets):
   return ast.literal_eval(node.value)
 raise ValueError(f'Cannot find {key}: {path}')

def put(out,rows,fields):
 with open(out,'w',encoding='utf8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def run(inputzip,metadata,out,dictionary_path):
 out.mkdir(exist_ok=True,parents=True)
 dicts=json.loads(dictionary_path.read_text(encoding='utf8'))
 countries=dicts['countries']
 places=dicts['places']
 orgs=dicts['organizations']
 # Supplement specific organizations omitted from original international-organization shortlist.
 orgs.update({
 'European Parliament':{'strong':['parlement europeen','european parliament'],'broad':[]},
 'European Commission':{'strong':['commission europeenne','european commission'],'broad':[]},
 'European Council':{'strong':['conseil europeen','european council'],'broad':[]},
 'CICR':{'strong':['cicr','icrc','comite international de la croix rouge','international committee of the red cross'],'broad':[]},
 'CIJ':{'strong':['cij','icj','cour internationale de justice','international court of justice'],'broad':[]},
 'CPJI':{'strong':['cpji','pcij','cour permanente de justice internationale','permanent court of international justice'],'broad':[]},
 'UNESCO':{'strong':['unesco','united nations educational scientific and cultural organization'],'broad':[]},
 'FAO':{'strong':['fao','food and agriculture organization'],'broad':[]},
 'PNUD':{'strong':['pnud','undp','united nations development programme','programme des nations unies pour le developpement'],'broad':[]},
 'OCDE':{'strong':['ocde','oecd','organisation de cooperation et de developpement economiques','organisation for economic co operation and development'],'broad':[]},
 'OTAN':{'strong':['otan','nato','l otan','north atlantic treaty organization'],'broad':[]},
 'ASEAN':{'strong':['asean','association of southeast asian nations'],'broad':[]},
 'CNUCED':{'strong':['cnuced','unctad','conference des nations unies sur le commerce et le developpement','united nations conference on trade and development'],'broad':[]},
 'OPEP':{'strong':['opec','opep','organization of the petroleum exporting countries','organisation des pays exportateurs de petrole'],'broad':[]},
 'TPIY':{'strong':['icty','tpiy','international criminal tribunal for the former yugoslavia','tribunal penal international pour l ex yougoslavie'],'broad':[]},
 'UNRWA':{'strong':['unrwa','united nations relief and works agency'],'broad':[]},
 'CEDAW':{'strong':['cedaw','committee on the elimination of discrimination against women'],'broad':[]},
 'CPI':{'strong':['international criminal court','cour penale internationale','cpi','icc'],'broad':[]},
 'CEDH':{'strong':['cour europeenne des droits de l homme','european court of human rights','echr'],'broad':[]},
 'Cour de justice UE':{'strong':['cour de justice de l union europeenne','court of justice of the european union','cjue','cjeu'],'broad':[]},
 'OLP':{'strong':['olp','plo','organisation de liberation de la palestine','palestine liberation organization'],'broad':[]},
 'FARC':{'strong':['farc','fuerzas armadas revolucionarias de colombia'],'broad':[]},
 'OEA':{'strong':['oea','oas','organization of american states','organisation des etats americains'],'broad':[]},
 'Union africaine':{'strong':['union africaine','african union'],'broad':['au']},
 'Assemblée générale ONU':{'strong':['assemblee generale des nations unies','un general assembly','united nations general assembly','the united nations general assembly'],'broad':['general assembly','the general assembly','assemblee generale']},
 'Conseil de sécurité ONU':{'strong':['conseil de securite des nations unies','un security council','united nations security council','the un security council'],'broad':['conseil de securite','the security council','security council']},
 })
 families={
 'Construction européenne':['CEE/EEC','CE/EC','UE/EU','European Parliament','European Commission','European Council'],
 'Construction européenne (strictement CEE→CE→UE)':['CEE/EEC','CE/EC','UE/EU'],
 'Gouvernance commerciale':['GATT','OMC'],
 'Sécurité coopérative européenne':['CSCE','OSCE'],
 'Système ONU':['ONU','HCR','UNICEF','OMS','OIT','UNESCO','FAO','PNUD','UNRWA','CNUCED','Assemblée générale ONU','Conseil de sécurité ONU'],
 'Juridictions internationales':['CIJ','CPJI','CPI','TPIY','CEDH','Cour de justice UE'],
 }
 # Note: families are analytic sums, never canonicalization synonyms or successor identity.
 countries_alias=defaultdict(set);place_alias=defaultdict(set);org_alias=defaultdict(set);broad_alias=defaultdict(set)
 for entity,pipe in countries.items():
  for x in [entity]+pipe.split('|'):countries_alias[norm(x)].add(entity)
 for country,pipe in places.items():
  for x in pipe.split('|'):place_alias[norm(x)].add(country)
 for entity,v in orgs.items():
  for x in v['strong']:org_alias[norm(x)].add(entity)
  for x in v['broad']:broad_alias[norm(x)].add(entity)
 # Ambiguous initials and high false-positive generic surfaces are never automatically linked.
 short_ambig={norm(x) for x in ['un','ec','eu','ce','us','us.','who','bit','ua','oc','bm','un doc','the eu','union','cee','eec']}
 # 'CEE' and 'EEC' in ORG may be accepted as lexical strong (unlike MISC),
 # while no MISC short acronym is silently admitted unless unusually diagnostic.
 allow_short_org={norm(x) for x in ['sdn','onu','fmi','imf','gatt','omc','wto','cee','eec','cicr','icrc','unhcr','hcr','unicef','unesco','osce','csce','nato','otan','ilo','oit','fao','hrw','wef','oecd','ocde','icj','cij','cpji','pcij','asean','unctad','cnuced','opec','opep','icty','unrwa','cedaw','farc','olp','plo','oea','oas','cpi','icc','tpiY']}
 noise={norm(x) for x in ['c’','l’','n’','qu’','ibid','cit','op.cit','op cit','op','etc','this','the','there','they','one','two','first','however','et al','see also','p','pp','ed','eds','doc','no','however','cour','commission','committee','conseil','l’organisation','court','convention','states','state']}

 def status(typ,raw):
  k=norm(raw)
  if not k or len(k)<2 or k in noise or k.isdigit():return ('noisy','','','')
  org=org_alias.get(k,set()) if typ in {'ORG','MISC','EVENT','LOC','GPE','PERSON','PER'} else set()
  country=countries_alias.get(k,set()) if typ in {'LOC','GPE','MISC','NORP','ORG'} else set()
  place=place_alias.get(k,set()) if typ in {'LOC','GPE','MISC'} else set()
  if len(org)>1 or len(country)>1 or len(place)>1:return ('ambiguous','','','collision')
  if org:
   e=next(iter(org))
   if k in short_ambig and k not in {'cee','eec'}:return ('ambiguous','','','ambiguous acronym')
   if len(k)<=4 and typ!='ORG' and k not in {'wef','wto','omc','sdn','onu','fmi','imf','nato','otan','icrc','cicr','unhcr','unicef','unesco','hcr','ilo','oit','oecd','ocde','farc','olp','plo','gatt','osce','csce','asean','unrwa','opec','icty','cedaw'}:return ('ambiguous','','','short acronym outside ORG label')
   if typ in {'LOC','GPE','PERSON','PER'} and len(k)<8:return ('ambiguous','','','short organization outside org type')
   return ('canonical','organization',e,'direct')
  if country and not place:
   if typ=='ORG' and len(k)<6:return ('ambiguous','','','short country string in ORG')
   return ('canonical','country',next(iter(country)),'direct')
  if place and not country:
   return ('child_place','country',next(iter(place)),'inherited')
  if country and place:return ('ambiguous','','','country/place collision')
  if k in broad_alias:return ('ambiguous','','','broad historical acronym')
  if typ in {'ORG','MISC','EVENT'}:
   # Fuzzy matches are suggestions only, and must be confirmed before aggregation.
   if len(k)>7 and not re.search(r'\b(university press|journal|review|journal of|publisher)\b',k):
    match=process.extractOne(k,list(org_alias),scorer=fuzz.ratio,score_cutoff=91)
    if match and abs(len(k)-len(match[0]))<=4:
     cand=org_alias[match[0]]
     if len(cand)==1:return ('candidate','organization',next(iter(cand)),f'fuzzy:{match[1]:.1f}')
  return ('unresolved','','','')

 inventory=Counter();all_docs=[]
 with zipfile.ZipFile(inputzip) as z:
  filenames=[x for x in z.namelist() if x.endswith('.jsonl') and not x.startswith('__MACOSX')]
  assert len(filenames)==1
  with z.open(filenames[0]) as f:
   for ln in f:
    d=json.loads(ln);all_docs.append(d)
    for typ,vals in d.get('entities_by_type',{}).items():
     for raw,num in vals.items():inventory[(typ,raw)]+=int(num)
 print('inventory distinct type×surface',len(inventory),'total',sum(inventory.values()),flush=True)
 # Match once per unique surface and NER type, preserving every original spelling.
 resolved={};variants=[];states=Counter();counts=Counter()
 for (typ,raw),n in inventory.items():
  s,category,entity,reason=status(typ,raw)
  resolved[(typ,raw)]=(s,category,entity)
  states[s]+=1;counts[s]+=n
  variants.append(dict(ner_type=typ,raw=raw,normalized=norm(raw),normalized_surface_id=f'surface:{typ}:{norm(raw)}',mentions=n,status=s,category=category,canonical_entity=entity,relation=reason))
 variants.sort(key=lambda x:(-x['mentions'],x['ner_type'],x['raw']))
 put(out/'all_surface_inventory.csv',variants,list(variants[0]))
 # All unresolved and ambiguous high-frequency candidates for review; every row is in full inventory.
 put(out/'review_priority.csv',[x for x in variants if x['status'] in {'ambiguous','candidate','unresolved'} and (x['ner_type'] in {'ORG','MISC','LOC','GPE'} or x['mentions']>=100)][:5000],list(variants[0]))
 md={r['doc_id']:r for r in csv.DictReader(open(metadata,encoding='utf8'))}
 rows=[];long=[];coverage=Counter();anachronisms=[]
 # Mentions predating the formal creation of a named organization are separated
 # instead of silently shaping early historical time series.
 founded={'SDN':1920,'ONU':1945,'CEE/EEC':1958,'CE/EC':1967,'UE/EU':1993,
          'GATT':1948,'OMC':1995,'OSCE':1995,'CSCE':1975,'WEF':1971,
          'UNICEF':1946,'UNESCO':1945,'OMS':1948,'PNUD':1965,'HCR':1950,
          'CPI':2002,'TPIY':1993,'CEDAW':1982,'UNRWA':1949,'OPEP':1960,
          'Union africaine':2002,'OCDE':1961,'ASEAN':1967,'OTAN':1949}
 
 for doc in all_docs:
  did=doc['doc_id'];dcounts=Counter();m=md.get(did,{})
  for typ,vals in doc['entities_by_type'].items():
   for raw,n in vals.items():
    s,cat,entity=resolved[(typ,raw)];n=int(n)
    coverage[(typ,s)]+=n
    if s in {'canonical','child_place'}:
     chan='direct' if s=='canonical' else 'inherited'
     dcounts[(cat,entity,chan)]+=n
  # Family counts use no double counting of canonical entity aliases; families sum distinct entities.
  year=int(m.get('year') or 0)
  for (cat,entity,chan),num in list(dcounts.items()):
   if cat=='organization' and entity in founded and year and year<founded[entity] and num:
    anachronisms.append(dict(doc_id=did,year=year,entity=entity,mentions=num,reason=f'predates founding {founded[entity]}'))
    del dcounts[(cat,entity,chan)]
  for family,members in families.items():dcounts[('family',family,'direct')]=sum(dcounts[('organization',member,'direct')] for member in members)
  for (cat,entity,chan),n in dcounts.items():
   if n:
    long.append(dict(doc_id=did,year=m.get('year',''),institution=m.get('institution',''),category=cat,entity=entity,channel=chan,mentions=n,words=doc.get('words_processed',0)))
 rows_fields=['doc_id','year','institution','category','entity','channel','mentions','words']
 put(out/'document_entity_counts.csv',long,rows_fields)
 put(out/'date_anomalies.csv',anachronisms,['doc_id','year','entity','mentions','reason'])
 put(out/'coverage_by_label.csv',[dict(ner_type=t,status=s,mentions=n) for (t,s),n in sorted(coverage.items())],['ner_type','status','mentions'])
 # entity registry with explicit parent/continuity; separate legal names, avoid retrospective conflation
 registry=[]
 for e in countries:registry.append(dict(id=f'country:{norm(e).replace(" ","_")}',name=e,category='country',parent='',relation='',valid_from='',valid_to=''))
 for e in orgs:
  parent='|'.join(f for f,children in families.items() if e in children)
  founded={'SDN':1920,'ONU':1945,'CEE/EEC':1958,'CE/EC':1967,'UE/EU':1993,'GATT':1948,'OMC':1995,'CSCE':1975,'OSCE':1995}
  registry.append(dict(id=f'organization:{norm(e).replace(" ","_")}',name=e,category='organization',parent=parent,relation='analytical_membership',valid_from=founded.get(e,''),valid_to={'SDN':1946,'GATT':1994,'CEE/EEC':1993,'CE/EC':2009,'CSCE':1994}.get(e,'')))
 for country,terms in places.items():
  for term in terms.split('|'):
   registry.append(dict(id=f'place:{norm(term).replace(" ","_")}',name=term,category='place',parent=country,relation='located_in',valid_from='',valid_to=''))
 for fam in families:registry.append(dict(id=f'family:{norm(fam).replace(" ","_")}',name=fam,category='family',parent='',relation='analytical_family',valid_from='',valid_to=''))
 put(out/'entity_registry.csv',registry,list(registry[0]))
 # Institution-specific decade summaries and annual rolling panel, never join institutes across mergers.
 group=defaultdict(list)
 for x in long:
  if x['channel']!='direct' or x['category'] not in {'organization','family'}:continue
  group[(x['institution'],x['entity'],x['year'])].append(x)
 document_instyear=defaultdict(list)
 for d in all_docs:
  m=md.get(d['doc_id'],{})
  if m and m.get('year'):
   document_instyear[(m['institution'],int(m['year']))].append(d['doc_id'])
 entities=[e for e in orgs]+list(families)
 docmetrics=defaultdict(int)
 for x in long:
  if x['category'] in {'organization','family'} and x['channel']=='direct':docmetrics[(x['doc_id'],x['entity'])]=x['mentions']
 panels=[]
 for inst in ['HEI','IUED','IHEID']:
  years=[y for (i,y) in document_instyear if i==inst]
  if not years:continue
  for y in range(min(years),max(years)+1):
   for width in (5,9,15):
    ids=[did for (i,yr),li in document_instyear.items() if i==inst and abs(yr-y)<=width//2 for did in li]
    if not ids:continue
    for e in entities:
     val=[docmetrics[(did,e)] for did in ids]
     panels.append(dict(institution=inst,year=y,window=width,entity=e,documents=len(ids),
       pct_any=round(100*sum(x>0 for x in val)/len(ids),3),
       pct_3plus=round(100*sum(x>=3 for x in val)/len(ids),3),
       pct_5plus=round(100*sum(x>=5 for x in val)/len(ids),3),
       pct_10plus=round(100*sum(x>=10 for x in val)/len(ids),3)))
 put(out/'rolling_by_institute.csv',panels,list(panels[0]))
 report={'documents':len(all_docs),'total_ner_mentions':sum(inventory.values()),'distinct_type_surface':len(inventory),
         'distinct_status_counts':dict(states),'mention_status_counts':dict(counts),
         'resolved_organization_occurrences':sum(x['mentions'] for x in long if x['category']=='organization'),
         'resolved_country_occurrences_direct':sum(x['mentions'] for x in long if x['category']=='country' and x['channel']=='direct'),
         'resolved_country_occurrences_inherited':sum(x['mentions'] for x in long if x['category']=='country' and x['channel']=='inherited'),
         'anomalous_organization_mentions_excluded':sum(x['mentions'] for x in anachronisms),
         'organizations':{e:sum(x['mentions'] for x in long if x['category']=='organization' and x['entity']==e) for e in orgs}}
 (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps(report,ensure_ascii=False,indent=2)[:4200],flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ner',type=Path,default=Path('/mnt/data/iheid_catalog_recovery/doctoral_ner_recovered.jsonl.zip'))
 p.add_argument('--metadata',type=Path,default=Path('/mnt/data/iheid_catalog_recovery/doctoral_metadata_recovered.csv'))
 p.add_argument('--output',type=Path,default=Path('/mnt/data/iheid_revision/systematic'))
 p.add_argument('--dictionary',type=Path,default=HERE/'systematic_ner_dictionaries.json')
 args=p.parse_args();run(args.ner,args.metadata,args.output,args.dictionary)