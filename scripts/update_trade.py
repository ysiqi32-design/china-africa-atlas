#!/usr/bin/env python3
"""Safely collect UN Comtrade annual merchandise totals using China's reporter data.

Uses free preview when UN_COMTRADE_KEY is absent; optional API key is passed in header.
Trade uses the SAME reporter (China 156) for X and M to avoid silently mixing
mirror-statistics. Omitted/unavailable records remain missing, never zero.

Run: python scripts/update_trade.py --start 2020 --end 2025
Test: python scripts/update_trade.py --fixture tests/fixtures/comtrade_example.json --start 2024 --end 2024
"""
import argparse,json,os,pathlib,random,sys,time
from datetime import datetime,timezone
import requests
import pycountry
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'trade.json'
COUNTRIES=json.loads((ROOT/'data'/'africa_map.json').read_text(encoding='utf-8'))
CODE_TO_ISO={int(c.numeric):c.alpha_3 for c in pycountry.countries if getattr(c,'numeric',None)}
AFRICA={x['code'] for x in COUNTRIES if not x.get('special')}

def parse_rows(payload,flow,year):
    if not isinstance(payload,dict) or not isinstance(payload.get('data'),list):raise ValueError('UN Comtrade API: invalid data array')
    out={}
    for x in payload['data']:
        iso=CODE_TO_ISO.get(int(x.get('partnerCode',0)))
        if iso not in AFRICA or str(x.get('cmdCode','')).upper() not in ('TOTAL','0'):continue
        if str(x.get('flowCode','')).upper()!=flow:continue
        if str(x.get('period',''))!=str(year):continue
        val=x.get('primaryValue')
        if not isinstance(val,(int,float)) or isinstance(val,bool) or val<0:continue
        # exclude differing trade customs and second partner when provided
        if str(x.get('partner2Code',0)) not in ('0','None',''):continue
        if x.get('customsCode') not in (None,'','C00'):continue
        if x.get('motCode') not in (None,0,'0'):continue
        key='china_exports_usd' if flow=='X' else 'china_imports_usd'
        if iso in out:raise ValueError(f'duplicate China-reported TOTAL record for {iso} {flow} {year}; refusing ambiguous total')
        out[iso]={key:val,'year':year}
    return out

def call(session,flow,year,key=None,attempts=4):
    route='https://comtradeapi.un.org/data/v1/get/C/A/HS' if key else 'https://comtradeapi.un.org/public/v1/preview/C/A/HS'
    params={'reporterCode':156,'period':year,'cmdCode':'TOTAL','flowCode':flow,'partner2Code':0,'customsCode':'C00','motCode':0,'maxRecords':500}
    headers={'User-Agent':'AfricaResearchAtlas/2.0 academic, source-traceable','Accept':'application/json'}
    if key:headers['Ocp-Apim-Subscription-Key']=key
    for n in range(attempts):
        try:
            r=session.get(route,params=params,headers=headers,timeout=45)
            if r.status_code in (429,500,502,503,504):raise RuntimeError('temporary rate/server '+str(r.status_code))
            r.raise_for_status()
            obj=r.json()
            if obj.get('error') or obj.get('errors'):raise RuntimeError('API response error '+str(obj.get('error') or obj.get('errors'))[:180])
            if len(obj.get('data',[]))>=500:raise RuntimeError('preview reached 500-record cap; refusing possibly truncated dataset')
            return parse_rows(obj,flow,year)
        except (requests.RequestException,ValueError,RuntimeError) as e:
            if n==attempts-1:raise
            time.sleep(min(60,4*(2**n))+random.random())

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--start',type=int,default=2020)
    p.add_argument('--end',type=int,default=min(2025,datetime.now(timezone.utc).year))
    p.add_argument('--fixture',help='Offline testing: list of response objects with flow and year keys')
    p.add_argument('--strict',action='store_true',help='Exit error if any request fails (useful CI)')
    a=p.parse_args()
    if a.start>a.end or a.start<2000 or a.end>datetime.now(timezone.utc).year: p.error('Invalid year range')
    prior=json.loads(DATA.read_text(encoding='utf-8')) if DATA.exists() else {'countries':{}}
    countries=prior.get('countries') or {}
    fixtures=json.loads(pathlib.Path(a.fixture).read_text(encoding='utf-8')) if a.fixture else None
    fetched=[];errors=[]
    with requests.Session() as sess:
        for yr in range(a.start,a.end+1):
            for flow in ('X','M'):
                try:
                    if fixtures is None:
                        record=call(sess,flow,yr,os.environ.get('UN_COMTRADE_KEY'))
                        time.sleep(1.3)
                    else:
                        entry=next(x for x in fixtures if x['year']==yr and x['flow']==flow)
                        record=parse_rows(entry['response'],flow,yr)
                    if not record:raise ValueError('zero African-country records: invalid or unavailable API response')
                    for iso,item in record.items():
                        rows={int(x['year']):dict(x) for x in countries.get(iso,[])}
                        rows.setdefault(yr,{'year':yr}).update(item)
                        countries[iso]=sorted(rows.values(),key=lambda x:x['year'],reverse=True)
                    print(yr,flow,len(record),'African countries')
                    fetched.append([yr,flow,len(record)])
                except Exception as e:
                    print('ERROR',yr,flow,type(e).__name__,str(e)[:180],file=sys.stderr)
                    errors.append([yr,flow,str(e)[:180]])
    if not fetched:
        print('No new observations; old data preserved.',file=sys.stderr)
        return 2
    result=dict(prior)
    result.update({'schema_version':2,'dataset':'bilateral_trade_china_reporter','source':'UN Comtrade (China reporter 156)',
    'source_url':'https://comtradeplus.un.org/','reported_by':'CHN','units':'current USD',
    'definition':'X = China reports exports to African partner; M = China reports imports from African partner. These are China-reported values and may differ from partner-reported imports/exports.',
    'updated_at_utc':datetime.now(timezone.utc).isoformat(),'status':'partial' if errors else 'updated',
    'fetched_groups':fetched,'errors':errors,'countries':countries})
    tmp=DATA.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');tmp.replace(DATA)
    print('Saved',DATA,'countries',len(countries),'errors',len(errors))
    return 1 if errors and a.strict else 0
if __name__=='__main__':sys.exit(main())
