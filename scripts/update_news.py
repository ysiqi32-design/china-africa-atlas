#!/usr/bin/env python3
"""Discover recent Africa–China article *leads* using GDELT DOC API.

No crawling full articles; only discovered metadata + source URL. Country and
China keyword matches are NOT verification. Safe, bounded and source-traceable.
Never replace an existing country dataset when its request fails.

Offline tests:
 python scripts/update_news.py --fixture tests/fixtures/gdelt_sample.json --countries GIN,SEN --no-sleep
Live:
 python scripts/update_news.py --days 14
"""
import argparse
import hashlib
import json
import pathlib
import random
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests

ROOT=pathlib.Path(__file__).resolve().parents[1]
TARGET=ROOT/'data'/'news.json'
MAP=json.loads((ROOT/'data'/'africa_map.json').read_text(encoding='utf-8'))
NAMES={c['code']:c['en'] for c in MAP if not c.get('special')}
# Specific aliases avoid the worst GDELT country-name ambiguities.
ALIASES={
 'COD':['"Democratic Republic of the Congo"','"DR Congo"','"DRC"'],
 'COG':['"Republic of the Congo"','"Congo Brazzaville"'],
 'GIN':['"Guinea"','"Guinée"'],
 'GNB':['"Guinea-Bissau"'],
 'GNQ':['"Equatorial Guinea"'],
 'NGA':['"Nigeria"'],
 'NER':['"Niger"'],
 'CIV':['"Ivory Coast"','"Côte d’Ivoire"','"Cote d Ivoire"'],
 'CPV':['"Cape Verde"','"Cabo Verde"'],
 'SWZ':['"Eswatini"','"Swaziland"'],
 'GMB':['"Gambia"'],
 'STP':['"Sao Tome and Principe"','"São Tomé et Príncipe"'],
 'TZA':['"Tanzania"'],
 'BFA':['"Burkina Faso"'],
 'CAF':['"Central African Republic"'],
 'SSD':['"South Sudan"'],
 'ZAF':['"South Africa"'],
 'SEN':['"Senegal"','"Sénégal"'],
 'MLI':['"Mali"'],
}
TOPIC_PATTERNS={
 'diplomacy':r'\b(diplomac|foreign minister|ambassador|bilateral|president|summit|visite officielle|relations diplomatiques|focac|ambassade|state visit)\b',
 'trade':r'\b(trad(?:e|ing)|export|import|tariff|customs|commercial|douane|échange|commerce|trade agreement)\b',
 'investment':r'\b(invest|enterprise|company|firm|joint venture|shareholding|acquisition|investissement|entreprise)\b',
 'financing':r'\b(loan|debt|credit|bond|repay|restructur|financ|prêt|dette|créance)\b',
 'projects':r'\b(railway|railroad|rail|port|airport|bridge|highway|infrastructure|barrage|construction|road|chemin de fer)\b',
 'resources':r'\b(mining|mine|mineral|cobalt|copper|bauxite|lithium|oil|gas|uranium|gold|petroleum|minerai|pétrole)\b',
 'industry':r'\b(factory|manufactur|industry|industrial|solar|electric vehicle|battery|technology|digital|usine|industri)\b',
 'payments':r'\b(yuan|renminbi|currency|central bank|payment|clearing|swap|banque centrale|monnaie)\b',
 'security':r'\b(militar|defen[cs]e|army|security|weapon|terror|troops|coup|armée|sécurit|conflit)\b',
 'multilateral':r'\b(united nations|african union|brics|un general assembly|multilateral|cooperation forum)\b',
 'society':r'\b(school|student|education|scholarship|culture|university|language|éducation|université)\b',
 'opinion':r'\b(protest|poll|survey|public opinion|demonstrat|backlash|social movement|manifestation|opinion publique)\b',
 'external':r'\b(france|united states|european union|russia|turkey|india|japan|français|européen)\b',
}
TRACKING_PREFIXES=('utm_','fbclid','gclid','mc_')


def safe_url(raw):
    try:
        p=urlparse(str(raw).strip())
        if p.scheme not in ('https','http') or not p.hostname or p.username or p.password:
            return None
        if p.hostname in ('localhost','127.0.0.1') or p.hostname.endswith('.local'):
            return None
        query=urlencode([(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True)
                         if not (k.lower().startswith(TRACKING_PREFIXES) or k.lower() in TRACKING_PREFIXES)])
        return urlunparse((p.scheme,p.netloc.lower(),p.path or '/',p.params,query,''))
    except (TypeError, ValueError):return None


def date_from_seen(value):
    text=str(value or '').strip()
    # seendate means GDELT detected this entry, NOT necessarily the publication date.
    for pattern in ('%Y%m%dT%H%M%SZ','%Y%m%d%H%M%S','%Y-%m-%dT%H:%M:%SZ','%Y-%m-%d'):
        try:return datetime.strptime(text,pattern).replace(tzinfo=timezone.utc).isoformat().replace('+00:00','Z')
        except ValueError:pass
    return None


def topics_for(title):
    text=title.casefold()
    return [topic for topic,pat in TOPIC_PATTERNS.items() if re.search(pat,text,flags=re.I)] or ['general']


def query_for(iso):
    labels=ALIASES.get(iso)
    if not labels:
        plain=NAMES[iso].replace('“','').replace('”','').strip()
        labels=['"'+plain.replace('"','')+'"']
    # query positives reflect only keyword co-mention, not editorial verification.
    needle=labels[0] if len(labels)==1 else '('+' OR '.join(labels[:3])+')'
    return '(China OR Chinese OR Chine OR chinois) '+needle


def parse_articles(payload,iso,now_iso):
    if not isinstance(payload,dict) or not isinstance(payload.get('articles'),list):
        raise ValueError('GDELT returned no JSON articles list')
    results=[];seen=set()
    for item in payload['articles']:
        if not isinstance(item,dict):continue
        link=safe_url(item.get('url'))
        title=str(item.get('title') or '').strip()
        detected=date_from_seen(item.get('seendate'))
        if not link or len(title)<8 or len(title)>360 or not detected:continue
        key=hashlib.sha256((iso+'\n'+link).encode('utf8')).hexdigest()[:20]
        if key in seen:continue
        seen.add(key)
        host=urlparse(link).hostname or ''
        results.append({'id':key,'country':iso,'title':title,'url':link,
                        'domain':host,'detected_at_utc':detected,
                        'first_seen_at_utc':now_iso,
                        'language':str(item.get('language') or '未标注')[:42],
                        'source_country':str(item.get('sourcecountry') or '')[:64],
                        'modules':topics_for(title),
                        'verification':'unverified_discovery',
                        'source_index':'GDELT DOC 2.0',
                        'relevance':'keyword_search_unconfirmed'})
    return sorted(results,key=lambda x:x['detected_at_utc'],reverse=True)


def fetch_country(session,iso,days,maxrecords,retries=3):
    params={'query':query_for(iso),'mode':'artlist','format':'json',
            'timespan':f'{days}d','maxrecords':maxrecords,'sort':'datedesc'}
    last=None
    for n in range(retries):
        try:
            res=session.get('https://api.gdeltproject.org/api/v2/doc/doc',params=params,timeout=40,
                    headers={'User-Agent':'ChinaAfricaResearchAtlas/4.0 (research article discovery)'})
            if res.status_code in (429,500,502,503,504):raise RuntimeError('retryable HTTP '+str(res.status_code))
            res.raise_for_status()
            payload=res.json()
            if isinstance(payload,dict) and (payload.get('error') or payload.get('errors')):
                raise ValueError(str(payload.get('error') or payload.get('errors'))[:200])
            return payload
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last=exc
            if n+1<retries:time.sleep(4*(n+1)+random.random())
    raise RuntimeError(str(last))


def combine(old,new,now_iso,retention_days,max_per_country=45):
    threshold=datetime.fromisoformat(now_iso.replace('Z','+00:00'))-timedelta(days=retention_days)
    found={x['id']:x for x in old if isinstance(x,dict) and x.get('id')}
    for rec in new:
        if rec['id'] in found:
            rec['first_seen_at_utc']=found[rec['id']].get('first_seen_at_utc',now_iso)
        found[rec['id']]=rec
    valid=[]
    for rec in found.values():
        try:
            d=datetime.fromisoformat(rec['detected_at_utc'].replace('Z','+00:00'))
            if d >= threshold:valid.append(rec)
        except (ValueError,TypeError,KeyError):pass
    return sorted(valid,key=lambda x:x['detected_at_utc'],reverse=True)[:max_per_country]


def refresh(target,countries,days,maxrecords,retention_days,fixtures=None,sleep_seconds=1.6):
    prior=json.loads(target.read_text(encoding='utf8')) if target.exists() else {}
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    db=dict(prior)
    items=dict(prior.get('countries') or {})
    country_status=dict(prior.get('country_status') or {})
    failures={};success=[]
    with requests.Session() as sess:
        for iso in countries:
            try:
                payload=(fixtures[iso] if fixtures is not None else fetch_country(sess,iso,days,maxrecords))
                new=parse_articles(payload,iso,now)
                items[iso]=combine(items.get(iso,[]),new,now,retention_days)
                country_status[iso]={'checked_at_utc':now,'last_success_at_utc':now,
                                     'matched_recently':len(new),'stored_records':len(items[iso]),'status':'ok'}
                success.append(iso)
                print(f'[{len(success)+len(failures)}/{len(countries)}] {iso}: {len(new)} leads',flush=True)
            except Exception as exc:
                failures[iso]=str(exc)[:240]
                old=country_status.get(iso,{})
                country_status[iso]={**old,'checked_at_utc':now,'status':'fetch_failed',
                                     'error':failures[iso], 'stored_records':len(items.get(iso,[]))}
                print(f'[{len(success)+len(failures)}/{len(countries)}] {iso}: FAILED {str(exc)[:120]}',file=sys.stderr,flush=True)
            if fixtures is None and sleep_seconds:time.sleep(sleep_seconds)
    # Never destroy last good output when the entire remote service fails.
    if not success:
        print('No successful country queries: prior verified snapshot retained',file=sys.stderr)
        return 2
    db.update({'schema_version':1,'dataset':'africa_china_news_discovery','provider':'GDELT DOC 2.0 / Article List',
               'provider_url':'https://api.gdeltproject.org/api/v2/doc/doc',
               'checked_at_utc':now,'last_success_at_utc':now,'lookback_days':days,'retention_days':retention_days,
               'status':'partial' if failures else 'ok','country_status':country_status,'countries':items,'errors':failures,
               'methodology':'Automated GDELT article-metadata search by country and China terms. Matches and topic tags do not verify claims. Detection date may differ from article publication. Only title, link, domain, language and dates are stored.',
               'notice':'所有自动搜集内容均为待核验线索，非已核实事实；请阅读原文、核查事件日期并交叉验证。'})
    target.write_text(json.dumps(db,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Saved',target,'updated countries',len(success),'errors',len(failures),'articles',sum(map(len,items.values())))
    return 0


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--countries',help='ISO3 list comma-separated; default all 54')
    parser.add_argument('--days',type=int,default=14)
    parser.add_argument('--maxrecords',type=int,default=35)
    parser.add_argument('--retention-days',type=int,default=90)
    parser.add_argument('--fixture',help='JSON dictionary of ISO3 -> GDELT API fixture response')
    parser.add_argument('--no-sleep',action='store_true')
    parser.add_argument('--output',type=pathlib.Path,default=TARGET)
    args=parser.parse_args()
    if not 1<=args.days<=90 or not 1<=args.maxrecords<=200 or not 14<=args.retention_days<=365:
        parser.error('Invalid days / records / retention limits')
    selected=(args.countries.split(',') if args.countries else list(NAMES))
    if not selected or any(x not in NAMES for x in selected):parser.error('Unknown ISO3 country')
    fixtures=json.loads(pathlib.Path(args.fixture).read_text(encoding='utf8')) if args.fixture else None
    return refresh(args.output,selected,args.days,args.maxrecords,args.retention_days,fixtures,0 if args.no_sleep else 1.6)

if __name__=='__main__':sys.exit(main())
