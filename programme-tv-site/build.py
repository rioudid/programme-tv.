#!/usr/bin/env python3
"""Collecte XMLTV -> JSON statique. Aucun abonnement/API/IA requis."""
import gzip, io, json, os, re, sys, unicodedata, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'site' / 'data' / 'guide.json'
CACHE = ROOT / 'cache' / 'enrichissements.json'
SOURCE = os.getenv('XMLTV_URL', 'https://xmltvfr.fr/xmltv/xmltv_fr.xml.gz')
TZ = ZoneInfo('Europe/Paris')
# Numéros de chaînes Orange connus. Les canaux 40/45 varient selon le bouquet.
CHAINS = [(1,'TF1'),(2,'France 2'),(3,'France 3'),(4,'France 4'),(5,'France 5'),(6,'M6'),(7,'Arte'),(8,'LCP'),(9,'W9'),(10,'TMC'),(11,'TFX'),(12,'Gulli'),(17,'CStar'),(18,'T18'),(19,'NOVO19'),(20,'TF1 Séries Films'),(21,"L’Équipe"),(22,'6ter'),(23,'RMC Story'),(24,'RMC Découverte'),(25,'Chérie 25')]
ALIASES = {8:['lcp','assemblee nationale','public senat'], 17:['cstar'],18:['t18'],19:['novo19'],20:['tf1 series films'],21:['lequipe','lequipe 21'],22:['6ter'],23:['rmc story'],24:['rmc decouverte'],25:['cherie 25']}

def norm(s):
    s=unicodedata.normalize('NFKD', s or '').encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+',' ',s).strip()

def dateparse(s):
    # XMLTV dates YYYYMMDDHHMMSS +0100 / YYYYMMDDHHMM +0100
    if not s: return None
    m=re.match(r'^(\d{12}(?:\d{2})?)\s*([+-]\d{4})?',s)
    if not m:return None
    ds,offset=m.groups(); ds=ds.ljust(14,'0'); dt=datetime.strptime(ds,'%Y%m%d%H%M%S')
    if offset:
        sign=1 if offset[0]=='+' else -1
        z=timezone(sign*timedelta(hours=int(offset[1:3]), minutes=int(offset[3:5])))
        dt=dt.replace(tzinfo=z)
    else: dt=dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)

def picklang(node,tag):
    el=node.findall(tag)
    for x in el:
        if x.attrib.get('lang','').lower().startswith('fr') and x.text:return x.text.strip()
    return next((x.text.strip() for x in el if x.text), '')

def load():
    req=urllib.request.Request(SOURCE,headers={'User-Agent':'GuideTVPersonnel/1.0 (lecture ponctuelle XMLTV compresse)','Accept-Encoding':'identity'})
    with urllib.request.urlopen(req, timeout=95) as response:
        data=response.read()
    if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
    return ET.fromstring(data)

def matching(label, num, name):
    n=norm(label); targets=[norm(name)]+ALIASES.get(num,[])
    if n in targets:return 3
    if any(n.startswith(t+' ') or t.startswith(n+' ') for t in targets if len(t)>3):return 2
    return 0

def produce(root):
    available={}
    for ch in root.findall('channel'):
        available[ch.get('id')]=[x.text or '' for x in ch.findall('display-name')]
    mapped={}; details=[]
    for number,name in CHAINS:
        picks=[]
        for cid,labels in available.items():
            score=max((matching(x,number,name) for x in labels),default=0)
            if score:picks.append((score,cid))
        if picks:
            picks.sort(reverse=True);mapped[picks[0][1]]=(number,name)
        else:details.append(name)
    existing={}
    if OUT.exists():
        try:existing=json.loads(OUT.read_text(encoding='utf-8'))
        except Exception:pass
    notes={}
    if CACHE.exists():
        try:notes=json.loads(CACHE.read_text(encoding='utf-8'))
        except Exception:pass
    now=datetime.now(TZ)
    entries=[]
    for p in root.findall('programme'):
        mapped_item=mapped.get(p.get('channel'))
        if not mapped_item:continue
        start=dateparse(p.get('start'));stop=dateparse(p.get('stop'))
        if not start or not stop or stop<=start:continue
        # Programmes de première et deuxième partie de soirée, début >= 20:45
        if not (start.hour >= 20 or start.hour<=2):continue
        if (start.hour==20 and start.minute<45):continue
        if (stop-start).total_seconds() < 45*60:continue
        day=(start-timedelta(days=1)).date() if start.hour<=2 else start.date()
        if day < now.date() or day > now.date()+timedelta(days=6):continue
        title=picklang(p,'title') or 'Programme sans titre'
        description=picklang(p,'desc')
        sub=picklang(p,'sub-title')
        categories=[x.text.strip() for x in p.findall('category') if x.text]
        year=picklang(p,'date')
        if year and not re.fullmatch(r'\d{4}',year):
            hit=re.search(r'\b(?:19|20)\d{2}\b',year);year=hit.group() if hit else ''
        number,name=mapped_item
        identifier=norm(title)
        extra=notes.get(identifier,{})
        entries.append({'date':day.isoformat(),'channel':number,'channel_name':name,'start':start.isoformat(),'stop':stop.isoformat(), 'title':title,'subtitle':sub,'description':description,'categories':categories,'year':year,'allocine_public':extra.get('allocine_public'), 'allocine_press':extra.get('allocine_press'),'tele7_stars':extra.get('tele7_stars'),'allocine_url':extra.get('allocine_url'),'tele7_url':extra.get('tele7_url')})
    # Preserve remaining future cached days only if provider temporarily omits an entry
    if not entries and existing.get('programmes'):
        raise RuntimeError('Aucun programme récupéré : préservation du fichier précédent')
    entries.sort(key=lambda x:(x['date'],x['channel'],x['start']))
    data={'generated_at':now.isoformat(),'source':'XMLTV France','coverage_note':'Jusqu’à 5 jours selon la source','missing_channels':details,'channels':[{'number':n,'name':name} for n,name in CHAINS], 'programmes':entries}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    temp=OUT.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8');temp.replace(OUT)
    print('OK',len(entries),'programmes',len(set(x['channel'] for x in entries)),'chaînes; absentes:',details)

if __name__=='__main__':
    try:produce(load())
    except Exception as exc:
        print('Échec récupération:',exc,file=sys.stderr);sys.exit(1)
