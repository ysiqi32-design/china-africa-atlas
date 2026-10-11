import importlib.util,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
TRADESPEC=importlib.util.spec_from_file_location('update_trade',ROOT/'scripts/update_trade.py')
trade=importlib.util.module_from_spec(TRADESPEC);TRADESPEC.loader.exec_module(trade)
class DataIntegrityTests(unittest.TestCase):
 def test_country_coverage(self):
  data=json.loads((ROOT/'data/africa_map.json').read_text())
  self.assertEqual(len([x for x in data if not x.get('special')]),54)
 def test_source_link_for_every_record(self):
  records=json.loads((ROOT/'data/records.json').read_text())['records']
  self.assertTrue(records)
  self.assertTrue(all(r['source_url'].startswith('https://') and r['country'] in trade.AFRICA for r in records))
 def test_normalize_china_reporter_totals(self):
  iso=324
  example={'data':[{'partnerCode':iso,'flowCode':'X','cmdCode':'TOTAL','period':2024,'primaryValue':123456,'partner2Code':0,'customsCode':'C00','motCode':0}]}
  self.assertEqual(trade.parse_rows(example,'X',2024)['GIN']['china_exports_usd'],123456)
 def test_missing_not_zero(self):
  self.assertEqual(trade.parse_rows({'data':[]},'X',2024),{})
 def test_deny_ambiguous_duplicate(self):
  x={'partnerCode':324,'flowCode':'X','cmdCode':'TOTAL','period':2024,'primaryValue':1,'partner2Code':0,'customsCode':'C00','motCode':0}
  with self.assertRaises(ValueError):trade.parse_rows({'data':[x,x]},'X',2024)
 def test_data_files_parse(self):
  for f in (ROOT/'data').glob('*.json'):json.loads(f.read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
