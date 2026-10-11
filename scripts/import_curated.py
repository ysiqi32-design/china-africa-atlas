#!/usr/bin/env python3
"""Import verified manually reviewed rows from CSV into records.json.
Columns: id,country,modules,type,date,title,summary,verification,source_name,source_url
Modules separated by ;. Default is dry-run and does not alter files.
"""
import argparse,csv,json,pathlib,re
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
VALID={x['code'] for x in json.loads((ROOT/'data'/'africa_map.json').read_text()) if not x.get('special')}
VALID_MODS={'base','diplomacy','trade','investment','financing','projects','resources','industry','payments','security','multilateral','society','opinion','external'}
def main():
 p=argparse.ArgumentParser();p.add_argument('csv_file');p.add_argument('--commit',action='store_true');a=p.parse_args()
 rows=[]
 with open(a.csv_file,encoding='utf-8-sig',newline='') as f:
  for n,x in enumerate(csv.DictReader(f),start=2):
   iso=x['country'].strip().upper();mods=[s.strip() for s in x['modules'].split(';') if s.strip()]
   if iso not in VALID or not mods or any(m not in VALID_MODS for m in mods):raise ValueError(f'row {n}: invalid country/module')
   if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',x['date']):raise ValueError(f'row {n}: expected YYYY-MM-DD')
   if not x['source_url'].startswith('https://'):raise ValueError(f'row {n}: evidence requires https source')
   for field in ('id','title','summary','source_name','verification'):
    if not x[field].strip():raise ValueError(f'row {n}: empty {field}')
   rows.append({**{k:v.strip() for k,v in x.items() if v},'country':iso,'modules':mods,'observed_at':datetime.now(timezone.utc).strftime('%Y-%m-%d')})
 target=ROOT/'data'/'records.json';doc=json.loads(target.read_text(encoding='utf-8'))
 prior={r['id']:r for r in doc['records']}
 for x in rows:prior[x['id']]=x
 if a.commit:
  doc['records']=sorted(prior.values(),key=lambda x:(x['country'],x['date'],x['id']))
  doc['updated_at_utc']=datetime.now(timezone.utc).isoformat()
  target.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(('Imported' if a.commit else 'Validated (dry-run only)'),len(rows),'rows; database total',len(prior))
if __name__=='__main__':main()
