import importlib.util,json,pathlib,tempfile,unittest
from unittest.mock import patch
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
   self.assertEqual(news.refresh(dest,['GIN'],14,35,90,{'GIN':{'oops':[]}},0),2)
   result=json.loads(dest.read_text())
   self.assertEqual(result['countries']['GIN'],[])
   self.assertEqual(result['country_status']['GIN']['status'],'fetch_failed')
   self.assertEqual(result['batch_success'],0)
class NewsRateLimitTests(unittest.TestCase):
 def test_least_recent_batch_moves_past_rate_limited_country(self):
  all_countries=['AGO','BDI','BEN','BFA','BWA']
  checked={'AGO':{'checked_at_utc':'2026-10-11T10:00:00Z','status':'fetch_failed'},
           'BDI':{'last_success_at_utc':'2026-10-11T10:00:00Z','checked_at_utc':'2026-10-11T10:00:00Z'}}
  self.assertEqual(news.select_batch(all_countries,checked,3),['BEN','BFA','BWA'])
 def test_429_is_not_retried(self):
  class MockResponse:
   status_code=429
   headers={'Retry-After':'120'}
  class MockSession:
   def __init__(self):self.calls=0
   def get(self,*a,**k):self.calls+=1;return MockResponse()
  sess=MockSession()
  with self.assertRaises(news.RateLimitError):news.fetch_country(sess,'GIN',14,35)
  self.assertEqual(sess.calls,1)
 def test_rate_limit_stops_batch_and_keeps_previous_records(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=pathlib.Path(tmp)/'news.json'
   prev={'countries':{'GIN':[{'id':'old-123','detected_at_utc':'2026-10-09T08:00:00Z'}]},'country_status':{}}
   dest.write_text(json.dumps(prev))
   with patch.object(news,'fetch_country',side_effect=news.RateLimitError('HTTP 429')) as request:
    code=news.refresh(dest,['GIN','SEN','MLI'],30,35,90,fixtures=None,sleep_seconds=0)
   self.assertEqual(code,2)
   self.assertEqual(request.call_count,1)
   result=json.loads(dest.read_text())
   self.assertEqual(result['countries']['GIN'][0]['id'],'old-123')
   self.assertEqual(result['status'],'rate_limited')
   self.assertNotIn('SEN',result['country_status'])

if __name__=='__main__':unittest.main()
