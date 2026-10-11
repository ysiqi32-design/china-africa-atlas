"""Generate embedded African country map geometry from Natural Earth 1:110m.
This source is public domain. No external data downloads necessary.
"""
import json
from pathlib import Path
import geopandas as gpd
from babel import Locale
from shapely.geometry import MultiPolygon, Polygon

ROOT=Path(__file__).resolve().parents[1]
SHAPE='/opt/pyvenv/lib/python3.13/site-packages/pyogrio/tests/fixtures/naturalearth_lowres/naturalearth_lowres.shp'
DF=gpd.read_file(SHAPE)
zh=Locale.parse('zh_CN').territories
# WB country codes vs ISO3 compatibility
codes={'SWZ':'SZ','COD':'CD','COG':'CG','CIV':'CI','CAF':'CF','SSD':'SS','ZAF':'ZA','TZA':'TZ','GNB':'GW','GNQ':'GQ','SLE':'SL','BFA':'BF','MRT':'MR','ESH':'EH'}
iso2_fallback={
 'AGO':'AO','BDI':'BI','BEN':'BJ','BWA':'BW','DZA':'DZ','EGY':'EG','ERI':'ER','ETH':'ET','GAB':'GA','GHA':'GH','GIN':'GN','GMB':'GM',
 'KEN':'KE','LBR':'LR','LBY':'LY','LSO':'LS','MAR':'MA','MDG':'MG','MLI':'ML','MOZ':'MZ','MWI':'MW','NAM':'NA','NER':'NE','NGA':'NG','RWA':'RW',
 'SDN':'SD','SEN':'SN','SOM':'SO','TCD':'TD','TGO':'TG','TUN':'TN','UGA':'UG','ZMB':'ZM','ZWE':'ZW','CMR':'CM','DJI':'DJ',
 'CPV':'CV','STP':'ST','SYC':'SC','COM':'KM','MUS':'MU'
}
iso2={**iso2_fallback,**codes}
overrides={'COD':'刚果（金）','COG':'刚果（布）','CAF':'中非共和国','GNQ':'赤道几内亚','BFA':'布基纳法索','SWZ':'埃斯瓦蒂尼','SSD':'南苏丹','GMB':'冈比亚','CPV':'佛得角','STP':'圣多美和普林西比','SYC':'塞舌尔','MUS':'毛里求斯','COM':'科摩罗','ESH':'西撒哈拉（地位有争议）','SOM':'索马里','CIV':'科特迪瓦'}
# French-speaking countries: historical/current use, including multi-lingual, not strict French official status.
francophone=set('DZA MAR TUN MRT SEN MLI NER TCD BFA BEN TGO CIV GIN GNB GAB CMR CAF COG COD DJI RWA BDI MDG COM SYC MUS GNQ'.split())
regional={
 '北非':'DZA MAR TUN LBY EGY',
 '西非':'MRT SEN MLI NER BFA BEN TGO CIV GIN GNB GMB GHA NGA LBR SLE CPV',
 '中非':'TCD CAF CMR GAB GNQ COG COD STP',
 '东非':'ETH ERI DJI SOM SDN SSD UGA KEN TZA RWA BDI SYC COM MUS',
 '南部非洲':'AGO ZMB MWI MOZ MDG ZWE BWA NAM ZAF LSO SWZ',
}
regionof={a:r for r,ns in regional.items() for a in ns.split()}
# metadata for island points by coordinates
islands={'CPV':('Cabo Verde',-23.55,15.4),'STP':('São Tomé and Príncipe',6.6,0.2),'SYC':('Seychelles',55.45,-4.65),'COM':('Comoros',43.35,-11.8),'MUS':('Mauritius',57.55,-20.25)}
# Country English name overrides
eng_overrides={'COD':'DR Congo','COG':'Republic of Congo','CIV':'Côte d’Ivoire','SWZ':'Eswatini','SSD':'South Sudan','CAF':'Central African Republic','GNQ':'Equatorial Guinea','CPV':'Cabo Verde','STP':'São Tomé and Príncipe'}

def xy(lon,lat):
 return round(50+(lon+26)*8.12,2),round(33+(38-lat)*9.3,2)

def ringpath(coords):
 a=[]
 for i,(lon,lat) in enumerate(coords):
  x,y=xy(lon,lat); a.append(('M' if i==0 else 'L')+f'{x} {y}')
 return ' '.join(a)+' Z'

def geompath(geo):
 if isinstance(geo,Polygon): polys=[geo]
 else: polys=list(geo.geoms) if isinstance(geo,MultiPolygon) else []
 paths=[]
 for p in polys:
  # skip micro-polys: markers cover them
  if p.area<.008:continue
  q=p.simplify(0.055,preserve_topology=True)
  paths.append(ringpath(q.exterior.coords))
  for hole in q.interiors:paths.append(ringpath(hole.coords))
 return ' '.join(paths)

entries=[]
for _,r in DF[DF.continent=='Africa'].iterrows():
 code=r.iso_a3
 if code=='-99':
  # the Somalia/Somaliland geometry is visually separate, but both route to Somalia country profile
  code='SOM'
 if code=='ESH':
  entries.append({'code':'ESH','zh':overrides['ESH'],'en':'Western Sahara · disputed','path':geompath(r.geometry),'special':True})
  continue
 entries.append({'code':code,'zh':overrides.get(code,zh.get(iso2.get(code,''),r['name'])),'en':eng_overrides.get(code,r['name']),'path':geompath(r.geometry),'francophone':code in francophone,'region':regionof.get(code,'其他')})
for code,(name,lon,lat) in islands.items():
 x,y=xy(lon,lat)
 entries.append({'code':code,'zh':overrides.get(code,zh.get(iso2.get(code,''),name)),'en':name,'point':[x,y],'francophone':code in francophone,'region':regionof.get(code,'其他')})
# merge duplicate Somalia polygons
som=[a for a in entries if a['code']=='SOM']; entries=[a for a in entries if a['code']!='SOM'];
if som:
 merged=som[0].copy();merged['path']=' '.join(x['path'] for x in som);entries.append(merged)
entries=sorted(entries,key=lambda x:x['code'])
print('All:',len(entries),'UN African states:',len([a for a in entries if not a.get('special')]))
assert len([a for a in entries if not a.get('special')])==54
(ROOT/'data'/'africa_map.json').write_text(json.dumps(entries,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
