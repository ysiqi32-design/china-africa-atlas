import json
import pathlib
import tempfile
import unittest
from datetime import datetime, timezone

from scripts import update_news_rss as news


class NewsRSSCollectorTests(unittest.TestCase):
    def test_rdf_parser_keeps_source_link_and_only_china_leads(self):
        xml = """<?xml version="1.0"?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
          xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
          <item rdf:about="https://allafrica.com/stories/202610110001.html">
            <title>Senegal and China sign a new trade accord</title>
            <link>https://allafrica.com/stories/202610110001.html</link>
            <dc:date>2026-10-11T10:00:00Z</dc:date>
          </item>
          <item rdf:about="https://allafrica.com/stories/202610110002.html">
            <title>Senegal launches school reform</title>
            <link>https://allafrica.com/stories/202610110002.html</link>
            <dc:date>2026-10-11T09:00:00Z</dc:date>
          </item>
        </rdf:RDF>"""
        rows = news.parse_rss(xml, "SEN", news.feed_url("SEN", "en"), "2026-10-11T11:00:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["url"], "https://allafrica.com/stories/202610110001.html")
        self.assertEqual(rows[0]["country"], "SEN")
        self.assertEqual(rows[0]["verification"], "unverified_discovery")
        self.assertIn("trade", rows[0]["modules"])

    def test_french_feed_and_country_slug(self):
        self.assertIn("fr.allafrica.com", news.feed_url("SEN", "fr"))
        self.assertEqual(news.country_slug("COD"), "congo_kinshasa")

    def test_rfc822_date_is_normalized(self):
        result = news.iso_time("Sun, 11 Oct 2026 10:00:00 GMT")
        self.assertEqual(result, "2026-10-11T10:00:00Z")

    def test_empty_success_preserves_unexpired_old_leads(self):
        old = [{"id": "existing", "detected_at_utc": "2026-10-10T10:00:00Z"}]
        self.assertEqual(news.merge(old, [], "2026-10-11T11:00:00Z"), old)

    def test_atomic_checkpoint_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "data" / "news.json"
            news.atomic_write(path, {"countries": {}, "status": "partial"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["status"], "partial")


if __name__ == "__main__":
    unittest.main()
