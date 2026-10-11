import importlib.util,json,pathlib,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('news_script',ROOT/'scripts/update_news.py')
news=importlib.util.module_from_spec(spec);spec.loader.exec_module(news)
class NewsPipelineTests(unittest.TestCase):
 def test_54_queries_and_country_names(self):
  self.assertEqual(len(news.NAMES),54)
  self.assertIn('"Guinea"',news.query_for('GIN'))
  self.assertIn('"Equatorial Guinea"',news.query_for('GNQ'))
  self.assertIn('"DR Congo"',news.query_for('COD'))
 def test_only_safe_urls_and_headline_metadata(self):
  fixture=json.loads((ROOT/'tests/fixtures/gdelt_sample.json').read_text())
  rows=news.parse_articles(fixture['GIN'],'GIN','2026-10-11T01:02:03Z')
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['domain'],'www.reuters.com')
  self.assertEqual(rows[0]['url'],'https://www.reuters.com/world/africa/guinea-china-railway/')
  self.assertEqual(rows[0]['verification'],'unverified_discovery')
  self.assertIn('projects',rows[0]['modules'])
  self.assertNotIn('summary',rows[0])
  self.assertNotIn('body',rows[0])
 def test_dates_are_detection_not_publication(self):
  self.assertEqual(news.date_from_seen('20261009T080000Z'),'2026-10-09T08:00:00Z')
  self.assertIsNone(news.date_from_seen('missing'))
 def test_preserve_good_records_on_partial_error(self):
  fixture=json.loads((ROOT/'tests/fixtures/gdelt_sample.json').read_text())
  fixture['SEN']={'something_else':[]}
  with tempfile.TemporaryDirectory() as tmp:
   dest=pathlib.Path(tmp)/'news.json'
   prior={'countries':{'SEN':[{'id':'keep','title':'Previous verified index metadata','url':'https://example.org/x','detected_at_utc':'2026-10-10T00:00:00Z'}]},'country_status':{}}
   dest.write_text(json.dumps(prior))
   status=news.refresh(dest,['GIN','SEN'],14,35,90,fixture,sleep_seconds=0)
   d=json.loads(dest.read_text())
   self.assertEqual(status,0)
   self.assertEqual(d['country_status']['SEN']['status'],'fetch_failed')
   self.assertEqual(d['countries']['SEN'][0]['id'],'keep')
   self.assertEqual(len(d['countries']['GIN']),1)
 def test_no_overwrite_if_all_queries_fail(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=pathlib.Path(tmp)/'news.json'
   dest.write_text('{"countries":{"GIN":[]}}')
   before=dest.read_bytes()
   self.assertEqual(news.refresh(dest,['GIN'],14,35,90,{'GIN':{'oops':[]}},0),2)
   self.assertEqual(dest.read_bytes(),before)
if __name__=='__main__':unittest.main()
