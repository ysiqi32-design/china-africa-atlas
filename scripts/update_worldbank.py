#!/usr/bin/env python3
"""Generate latest official WDI statistics snapshot for 54 African countries.
Run: pip install requests; python scripts/update_worldbank.py
Requires internet; for automation run in GitHub Actions. Never inserts synthetic figures.
"""
import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
ROOT=pathlib.Path(__file__).resolve().parents[1]
map_data=json.loads((ROOT/'data'/'africa_map.json').read_text(encoding='utf8'))
countries=[x['code'] for x in map_data if not x.get('special')]
INDICATORS=['SP.POP.TOTL','NY.GDP.MKTP.CD','NY.GDP.PCAP.CD','NY.GDP.MKTP.KD.ZG',
'FP.CPI.TOTL.ZG','SL.UEM.TOTL.ZS','SP.POP.0014.TO.ZS','SE.SEC.ENRR',
'NV.IND.MANF.ZS','NV.AGR.TOTL.ZS','NV.SRV.TOTL.ZS','NE.TRD.GNFS.ZS',
'BX.KLT.DINV.CD.WD','GC.DOD.TOTL.GD.ZS','EG.ELC.ACCS.ZS','IT.NET.USER.ZS']

def load(iso):
    url=f'https://api.worldbank.org/v2/country/{iso}/indicator/{";".join(INDICATORS)}'
    params={'source':2,'format':'json','mrnev':12,'per_page':600}
    last=''
    for attempt in range(4):
        try:
            response=requests.get(url,params=params,timeout=26,headers={'User-Agent':'AfricaAtlasResearch/1.0 (WDI academic dashboard)'})
            response.raise_for_status()
            result=response.json()
            if not isinstance(result,list) or len(result)<2 or not isinstance(result[1],list):
                raise ValueError('API returned no indicator array')
            payload={}
            for d in result[1]:
                key=d.get('indicator',{}).get('id');value=d.get('value');year=d.get('date','')
                if key not in INDICATORS or not isinstance(value,(int,float)) or not str(year).isdigit():continue
                payload.setdefault(key,[]).append({'year':int(year),'value':value})
            for key,rows in payload.items():
                latest={r['year']:r for r in rows};payload[key]=[latest[y] for y in sorted(latest,reverse=True)][:15]
            if not payload:raise ValueError('No non-null latest observations')
            return iso,payload,None
        except Exception as e:
            last=str(e)
            time.sleep(2*(attempt+1))
    return iso,None,last

def main():
    print(f'Fetching World Bank WDI latest data: {len(countries)} countries; {len(INDICATORS)} indicators')
    data={};errors={}
    with ThreadPoolExecutor(max_workers=4) as ex:
        future=[ex.submit(load,iso) for iso in countries]
        for f in as_completed(future):
            iso,record,error=f.result()
            if record:data[iso]=record
            else:errors[iso]=error
            print(f'[{len(data)+len(errors)}/{len(countries)}] {iso}: {"OK" if record else error}',flush=True)
    if len(data)<45:
        print(f'ERROR: only {len(data)}/54 successful; refusing to overwrite good snapshot',file=sys.stderr)
        sys.exit(2)
    path=ROOT/'data'/'worldbank_snapshot.json'
    if errors and path.exists():
        try:
            prior=json.loads(path.read_text(encoding='utf8')).get('countries',{})
            for key in errors:
                if key in prior:data[key]=prior[key]
        except (OSError,json.JSONDecodeError):pass
    result={'source':'World Bank World Development Indicators API v2',
            'source_url':'https://api.worldbank.org/v2/',
            'refreshed_at_utc':datetime.now(timezone.utc).isoformat(),
            'note':'This is the API retrieval date, not the statistical reference year; each value includes a year.',
            'failed_countries':list(errors),'countries':data}
    path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    print(f'Saved snapshot {path}; {len(data)} countries; {len(errors)} failures')
if __name__=='__main__':main()
