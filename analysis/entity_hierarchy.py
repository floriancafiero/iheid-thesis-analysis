#!/usr/bin/env python3
"""Hierarchical NER normalizer for entities_combined.jsonl.zip (stdlib only).

Run: python analysis/entity_hierarchy.py entities_combined.jsonl.zip
Results: analysis/hierarchy_output/*.csv
Direct country mentions and inherited mentions from cities are NEVER conflated.
"""
import csv
import json
import re
import sys
import zipfile
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

COUNTRY = {
"China":"china|chine|la chine|république populaire de chine|people's republic of china",
"Switzerland":"switzerland|suisse|la suisse|schweiz",
"France":"france|la france",
"United States":"united states|the united states|états-unis|etats unis|usa",
"United Kingdom":"united kingdom|the united kingdom|royaume-uni|grande-bretagne|great britain|britain",
"Germany":"germany|allemagne|deutschland|rfa|rda",
"Russia":"russia|russie|russian federation",
"Soviet Union":"ussr|urss|soviet union|the soviet union|union soviétique",
"India":"india|inde","Japan":"japan|japon","Italy":"italy|italie|italia",
"Brazil":"brazil|brésil|brasil","Canada":"canada",
"Iran":"iran","Israel":"israel|israël","Turkey":"turkey|turquie|türkiye",
"Mexico":"mexico|mexique","Egypt":"egypt|égypte","South Africa":"south africa|afrique du sud",
"Spain":"spain|espagne","Belgium":"belgium|belgique",
"Netherlands":"netherlands|pays-bas","Poland":"poland|pologne",
"Ukraine":"ukraine","Austria":"austria|autriche",
"Indonesia":"indonesia|indonésie","Vietnam":"vietnam|viet nam",
"Pakistan":"pakistan","Bangladesh":"bangladesh",
"Saudi Arabia":"saudi arabia|arabie saoudite","Syria":"syria|syrie",
"Iraq":"iraq|irak","Lebanon":"lebanon|liban","Palestine":"palestine",
"Afghanistan":"afghanistan","Thailand":"thailand|thaïlande",
"Senegal":"senegal|sénégal","Mali":"mali","Cameroon":"cameroon|cameroun",
"Burkina Faso":"burkina faso|haute-volta|upper volta",
"Morocco":"morocco|maroc","Algeria":"algeria|algérie",
"Tunisia":"tunisia|tunisie","Nigeria":"nigeria","Kenya":"kenya",
"DR Congo":"drc|rdc|zaïre|zaire|république démocratique du congo",
"Argentina":"argentina|argentine","Chile":"chile|chili",
"Colombia":"colombia|colombie","Peru":"peru|pérou",
"Australia":"australia|australie","New Zealand":"new zealand|nouvelle zélande",
}
PLACE = {
"China":"shanghai|beijing|pékin|peking|tianjin|shenzhen|guangzhou|nanjing|wuhan|chengdu|guangdong|sichuan",
"Switzerland":"vaud|canton de vaud|genève|geneva|lausanne|zurich|bern|berne|basel|bâle|fribourg|neuchâtel|valais|lucerne|nyon",
"France":"paris|lyon|marseille|bordeaux|toulouse|lille|strasbourg|nantes|montpellier|grenoble|rennes",
"United States":"new york|los angeles|chicago|boston|san francisco|california|californie|texas|florida|philadelphia|seattle",
"United Kingdom":"london|londres|manchester|birmingham|oxford|cambridge|edinburgh|glasgow|england|angleterre",
"Germany":"berlin|munich|hamburg|frankfurt|francfort|bonn|cologne|leipzig|dresden",
"Russia":"moscow|moscou|saint petersburg|saint pétersbourg|siberia|sibérie",
"India":"delhi|new delhi|mumbai|bombay|kolkata|calcutta|chennai|bangalore",
"Japan":"tokyo|osaka|kyoto|hiroshima",
"Brazil":"rio de janeiro|sao paulo|são paulo|brasilia|recife",
"Italy":"rome|roma|milan|milano|turin|torino|naples|florence|venice|venise",
"Belgium":"brussels|bruxelles|anvers",
"Netherlands":"amsterdam|rotterdam|the hague|la haye",
"Turkey":"istanbul|ankara|izmir",
"Egypt":"cairo|le caire|alexandria|alexandrie",
"Senegal":"dakar|thies|casamance",
"Mali":"bamako|tombouctou|timbuktu|mopti",
"Burkina Faso":"ouagadougou|ouahigouya|yatenga|ganzourgou|kouritenga|oubritenga",
"Cameroon":"yaoundé|douala|garoua",
"South Africa":"johannesburg|cape town|le cap|pretoria|durban",
"DR Congo":"kinshasa|lubumbashi|goma|bukavu",
"Argentina":"buenos aires",
"Mexico":"mexico city|ciudad de mexico|chiapas|oaxaca",
"Chile":"santiago de chile|santiago du chili|valparaiso",
"Indonesia":"jakarta|bali|java",
"Vietnam":"hanoi|saigon|ho chi minh city",
"Thailand":"bangkok",
"Australia":"sydney|melbourne|canberra",
"Canada":"ottawa|toronto|montreal|montréal|vancouver|quebec|québec",
}
ORGANIZATION = {
"World Economic Forum":("wef|world economic forum|forum économique mondial","Global forums"),
"United Nations":("onu|l'onu|nations unies|united nations|the united nations|organisation des nations unies","UN system"),
"UNICEF":("unicef","UN system"),
"UNHCR":("unhcr|hcr|haut commissariat des nations unies pour les réfugiés","UN system"),
"UNESCO":("unesco","UN system"),
"WHO":("oms|world health organization|organisation mondiale de la santé","UN system"),
"ILO":("oit|international labour organization|organisation internationale du travail|bureau international du travail","UN system"),
"FAO":("fao|food and agriculture organization","UN system"),
"UNDP":("pnud|undp","UN system"),
"UN Security Council":("conseil de sécurité|the security council|un security council","UN system"),
"UN General Assembly":("general assembly|assemblée générale des nations unies","UN system"),
"League of Nations":("sdn|société des nations|league of nations","Historical institutions"),
"World Bank":("banque mondiale|world bank|the world bank|ibrd","Financial institutions"),
"IMF":("fmi|imf|international monetary fund|fonds monétaire international","Financial institutions"),
"WTO":("omc|wto|world trade organization|organisation mondiale du commerce","Trade institutions"),
"GATT":("gatt|general agreement on tariffs and trade","Trade institutions"),
"EU":("union européenne|l'union européenne|european union|the european union","European integration"),
"EEC":("cee|communauté économique européenne|european economic community","European integration"),
"European Commission":("commission européenne|european commission","European integration"),
"European Parliament":("parlement européen|european parliament","European integration"),
"NATO":("nato|otan|l'otan|north atlantic treaty organization","Security alliances"),
"OSCE":("osce","Security institutions"),
"OECD":("oecd|ocde","Economic cooperation"),
"ASEAN":("asean","Regional organizations"),
"ICRC":("cicr|icrc|comité international de la croix rouge|international committee of the red cross","Humanitarian organizations"),
"Amnesty International":("amnesty international","Human rights NGOs"),
"Human Rights Watch":("human rights watch|hrw","Human rights NGOs"),
"Médecins Sans Frontières":("médecins sans frontières|doctors without borders|msf","Humanitarian NGOs"),
"Greenpeace":("greenpeace","Environmental NGOs"),
"Oxfam":("oxfam","Development NGOs"),
}
CONTINENT = {
"Europe":"Switzerland|France|United Kingdom|Germany|Russia|Soviet Union|Italy|Spain|Belgium|Netherlands|Poland|Ukraine|Austria",
"Asia":"China|India|Japan|Iran|Israel|Turkey|Indonesia|Vietnam|Pakistan|Bangladesh|Saudi Arabia|Syria|Iraq|Lebanon|Palestine|Afghanistan|Thailand",
"Africa":"Egypt|South Africa|Senegal|Mali|Cameroon|Burkina Faso|Morocco|Algeria|Tunisia|Nigeria|Kenya|DR Congo",
"North America":"United States|Canada|Mexico",
"South America":"Brazil|Argentina|Chile|Colombia|Peru",
"Oceania":"Australia|New Zealand",
}
def norm(s):
    s=unicodedata.normalize("NFKD",str(s).casefold().replace("’","'"))
    s="".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",re.sub(r"[-‐‑–—'.,()]"," ",s)).strip()

def aliases(spec):
    lookup={}
    for entity,terms in spec.items():
        for term in [entity]+terms.split("|"):
            k=norm(term)
            if k in lookup and lookup[k]!=entity:
                raise ValueError("Alias collision: "+k)
            lookup[k]=entity
    return lookup

C,P,O=aliases(COUNTRY),aliases(PLACE),aliases({k:v[0] for k,v in ORGANIZATION.items()})
REGION={k:region for region,terms in CONTINENT.items() for k in terms.split("|")}

def records(path):
    if path.suffix==".zip":
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if n.endswith(".jsonl") and not n.startswith("__MACOSX")]
            if len(names)!=1: raise ValueError("Provide one JSONL")
            with z.open(names[0]) as f:
                for line in f: yield json.loads(line)
    else:
        with path.open(encoding="utf8") as f:
            for line in f: yield json.loads(line)

def write(path,columns,rows):
    with path.open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,columns);w.writeheader();w.writerows(rows)

def main():
    if len(sys.argv)<2: raise SystemExit("Usage: python analysis/entity_hierarchy.py input.jsonl.zip [output-dir]")
    src=Path(sys.argv[1]);out=Path(sys.argv[2] if len(sys.argv)>2 else "analysis/hierarchy_output")
    out.mkdir(exist_ok=True,parents=True)
    docs=[];variant=Counter();missing=Counter()
    for item in records(src):
        count=Counter()
        for kind,entries in item.get("entities_by_type",{}).items():
            for raw,n in entries.items():
                s=norm(raw);result=None
                if s in O and s not in {"who"} and (kind in {"ORG","MISC","EVENT"} or len(s)>=5):
                    result=("organization",O[s],"direct")
                elif kind in {"LOC","GPE","MISC"}:
                    if s in C:result=("country",C[s],"direct")
                    elif s in P:result=("country",P[s],"inherited")
                if result:
                    count[result]+=n
                    variant[(*result,raw)]+=n
                elif kind in {"LOC","GPE","ORG"}: missing[(kind,raw)]+=n
        id=str(item["doc_id"])
        prefix=id.split("_")[0]
        institution=prefix if prefix in {"HEI","IUED","IHEID"} else "Unknown"
        docs.append((id,institution,int(item.get("words_processed") or 0),count))
    details=[];groups=Counter();words=Counter();stats=defaultdict(Counter);families=defaultdict(lambda:{"docs":set(),"direct":0,"inherited":0})
    for id,inst,w,counts in docs:
        for panel in ("ALL",inst):
            groups[panel]+=1;words[panel]+=w
        pairs={(typ,name) for typ,name,_ in counts}
        for typ,name in pairs:
            a=counts[(typ,name,"direct")];b=counts[(typ,name,"inherited")]
            details.append(dict(doc_id=id,institution=inst,type=typ,entity=name,direct=a,inherited=b,expanded=a+b,words=w))
            family=(REGION.get(name) if typ=="country" else ORGANIZATION[name][1])
            for panel in ("ALL",inst):
                s=stats[(panel,typ,name)]
                s["direct"]+=a;s["inherited"]+=b;s["docs_direct"]+=bool(a);s["docs_expanded"]+=1
                if family:
                    f=families[(panel,"continent" if typ=="country" else "organization_family",family)]
                    f["docs"].add(id);f["direct"]+=a;f["inherited"]+=b
    summary=[]
    for (panel,typ,name),s in stats.items():
        summary.append(dict(panel=panel,type=typ,entity=name,
            parent=REGION.get(name,"") if typ=="country" else ORGANIZATION[name][1],
            documents=groups[panel],direct=s["direct"],inherited=s["inherited"],
            docs_direct=s["docs_direct"],docs_expanded=s["docs_expanded"],
            pct_direct=round(100*s["docs_direct"]/groups[panel],2),
            pct_expanded=round(100*s["docs_expanded"]/groups[panel],2),
            per_100k_direct=round(1e5*s["direct"]/words[panel],2) if words[panel] else 0))
    family_rows=[]
    for (panel,typ,name),d in families.items():
        family_rows.append(dict(panel=panel,type=typ,family=name,documents=groups[panel],
            docs=len(d["docs"]),prevalence_pct=round(100*len(d["docs"])/groups[panel],2),
            direct=d["direct"],inherited=d["inherited"]))
    write(out/"document_entities.csv",["doc_id","institution","type","entity","direct","inherited","expanded","words"],details)
    write(out/"entity_summary.csv",["panel","type","entity","parent","documents","direct","inherited","docs_direct","docs_expanded","pct_direct","pct_expanded","per_100k_direct"],summary)
    write(out/"families.csv",["panel","type","family","documents","docs","prevalence_pct","direct","inherited"],family_rows)
    write(out/"matched_variants.csv",["type","entity","relation","variant","mentions"],
          [dict(type=t,entity=e,relation=r,variant=v,mentions=n) for (t,e,r,v),n in variant.most_common()])
    write(out/"unresolved_top500.csv",["type","raw","mentions"],
          [dict(type=t,raw=v,mentions=n) for (t,v),n in missing.most_common(500)])
    print(f"{len(docs)} documents, {len(details)} normalized document-entity pairs, {len(variant)} mapped variants")
if __name__=="__main__":
    main()
