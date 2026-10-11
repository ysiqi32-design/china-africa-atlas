#!/usr/bin/env python3
"""Review-first CSV ingestion for any topical dataset (FDI, loans, survey, arms, etc.).

CSV columns: country,indicator,label,year,value,unit,source_name,source_url,status
Empty value denotes unavailable, not zero. For numerical observations status must
be verified and include an attributable source. --commit required for writing.
"""
import argparse,csv,json,pathlib,math
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
ALLOWED={'investment','financing','engineering','resources','industry','payments','security','multilateral','society','surveys','external','diplomacy'}
COUNTRIES={d['code'] for d in json.loads((ROOT/'data/africa_map.json').read_text(encoding='utf-8')) if not d.get('special')}

def main():
    a=argparse.ArgumentParser();a.add_argument('dataset',choices=sorted(ALLOWED));a.add_argument('file');a.add_argument('--commit',action='store_true');x=a.parse_args()
    rows=[]
    with open(x.file,encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        required={'country','indicator','label','year','value','unit','source_name','source_url','status'}
        if not required.issubset(reader.fieldnames or []):raise ValueError('Missing CSV columns: '+','.join(sorted(required-set(reader.fieldnames or []))))
        for idx,row in enumerate(reader,start=2):
            iso=row['country'].strip().upper()
            if iso not in COUNTRIES:raise ValueError(f'row {idx}: invalid ISO3 country')
            y=int(row['year']);now=datetime.now(timezone.utc).year
            if y<1950 or y>now:raise ValueError(f'row {idx}: year out of range')
            if not row['indicator'].strip() or not row['label'].strip():raise ValueError(f'row {idx}: indicator/label required')
            val=row['value'].strip()
            if val:
                val=float(val)
                if not math.isfinite(val):raise ValueError(f'row {idx}: nonfinite number')
                if row['status'].strip()!='verified':raise ValueError(f'row {idx}: numerical value needs verified status')
                if not row['source_url'].startswith('https://'):raise ValueError(f'row {idx}: numerical value requires https source')
            else: val=None
            rows.append((iso,dict(indicator=row['indicator'].strip(),label=row['label'].strip(),year=y,value=val,unit=row['unit'].strip(),source_name=row['source_name'].strip(),source_url=row['source_url'].strip(),status=row['status'].strip())))
    path=ROOT/'data'/f'{x.dataset}.json';obj=json.loads(path.read_text(encoding='utf-8'));countries=obj.get('countries') or {}
    for iso,row in rows:
        existing=[v for v in countries.get(iso,[]) if not(v.get('indicator')==row['indicator'] and v.get('year')==row['year'])]
        existing.append(row)
        countries[iso]=sorted(existing,key=lambda r:(r.get('indicator',''),-int(r.get('year',0))))
    if x.commit:
        obj.update({'countries':countries,'status':'partial','updated_at_utc':datetime.now(timezone.utc).isoformat()})
        path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(('Imported' if x.commit else 'Validated without writing'),len(rows),'rows',x.dataset,'countries',len(countries))
if __name__=='__main__':main()
