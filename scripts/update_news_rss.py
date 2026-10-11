#!/usr/bin/env python3
"""Discover Africa-China article leads from AllAfrica country RSS feeds.

RSS items are metadata leads only. No article bodies are fetched or stored.
Failed feeds never delete old country records; checkpoints are written atomically.
"""
import argparse
import email.utils
import hashlib
import html
import json
import os
import pathlib
import random
import re
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin, urlparse, urlunparse

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / 'data' / 'news.json'
MAP = json.loads((ROOT / 'data' / 'africa_map.json').read_text(encoding='utf-8'))
COUNTRIES = {c['code']: c for c in MAP if not c.get('special')}
# AllAfrica uses distinct editorial category IDs for a few country names.
FEED_SLUGS = {
    'COD': 'congo_kinshasa', 'COG': 'congo_brazzaville',
    'CIV': 'ivorycoast', 'CPV': 'capeverde', 'STP': 'saotomeandprincipe',
    'GNB': 'guineabissau', 'GNQ': 'equatorialguinea',
    'SWZ': 'swaziland', 'SSD': 'southsudan', 'TZA': 'tanzania',
    'BFA': 'burkinafaso', 'CAF': 'centralafricanrepublic',
    'DZA': 'algeria', 'MAR': 'morocco', 'MRT': 'mauritania',
    'NER': 'niger', 'NGA': 'nigeria', 'SEN': 'senegal',
    'ZAF': 'southafrica',
}
CHINA_RE = re.compile(r'(?i)(?<![\w])(?:china|chinese|chine|chinois|chinoise)(?![\w])')
TOPIC_PATTERNS = {
    'diplomacy': r'\b(diplomac|foreign minister|ambassador|bilateral|president|summit|relations diplomatiques|focac|ambassade)\b',
    'trade': r'\b(trad(?:e|ing)|export|import|tariff|customs|commercial|commerce|échange)\b',
    'investment': r'\b(invest|enterprise|company|firm|joint venture|shareholding|acquisition|investissement|entreprise)\b',
    'financing': r'\b(loan|debt|credit|bond|repay|restructur|financ|prêt|dette)\b',
    'projects': r'\b(railway|railroad|rail|port|airport|bridge|highway|infrastructure|barrage|construction|road)\b',
    'resources': r'\b(mining|mine|mineral|cobalt|copper|bauxite|lithium|oil|gas|uranium|gold|petroleum|minerai|pétrole)\b',
    'industry': r'\b(factory|manufactur|industry|industrial|solar|electric vehicle|battery|technology|digital|usine)\b',
    'payments': r'\b(yuan|renminbi|currency|central bank|payment|clearing|swap|banque centrale)\b',
    'security': r'\b(militar|defen[cs]e|army|security|weapon|terror|troops|coup|armée|sécurité)\b',
    'multilateral': r'\b(united nations|african union|brics|un general assembly|multilateral|cooperation forum)\b',
    'society': r'\b(school|student|education|scholarship|culture|university|language|éducation|université)\b',
    'opinion': r'\b(protest|poll|survey|public opinion|demonstrat|backlash|social movement|manifestation|opinion publique)\b',
    'external': r'\b(france|united states|european union|russia|turkey|india|japan|français|européen)\b',
}


def country_slug(iso):
    country = COUNTRIES[iso]
    if iso in FEED_SLUGS:
        return FEED_SLUGS[iso]
    return re.sub(r'[^a-z0-9]+', '', country['en'].casefold())


def feed_url(iso, language):
    host = 'fr.allafrica.com' if language == 'fr' else 'allafrica.com'
    return f'https://{host}/tools/headlines/rdf/{country_slug(iso)}/headlines.rdf'


def iso_time(raw):
    if not raw:
        return None
    raw = html.unescape(str(raw)).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(raw)
        except (TypeError, ValueError, OverflowError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def local_name(tag):
    return tag.rsplit('}', 1)[-1].lower()


def node_text(node):
    if node is None:
        return ''
    return html.unescape(' '.join(''.join(node.itertext()).split()))


def parse_rss(xml_text, iso, feed, now_iso):
    root = ET.fromstring(xml_text)
    found, seen = [], set()
    for item in root.iter():
        if local_name(item.tag) not in ('item', 'entry'):
            continue
        values = {local_name(child.tag): child for child in list(item)}
        title = node_text(values.get('title'))
        summary = node_text(values.get('description') or values.get('summary') or values.get('content'))
        link_node = values.get('link')
        link = (link_node.attrib.get('href') if link_node is not None else None) or node_text(link_node)
        link = urljoin(feed, link.strip())
        raw_date = next((node_text(values[k]) for k in ('pubdate', 'date', 'issued', 'published', 'updated') if k in values), '')
        published = iso_time(raw_date)
        parsed = urlparse(link)
        if not title or len(title) > 360 or not published or parsed.scheme not in ('http', 'https') or not parsed.hostname:
            continue
        if not CHINA_RE.search(title + ' ' + summary):
            continue
        key = hashlib.sha256((iso + '\n' + link).encode('utf-8')).hexdigest()[:20]
        if key in seen:
            continue
        seen.add(key)
        text = title + ' ' + summary
        modules = [name for name, pattern in TOPIC_PATTERNS.items() if re.search(pattern, text, re.I)] or ['general']
        publisher = node_text(values.get('publisher') or values.get('source'))[:120]
        found.append({
            'id': key, 'country': iso, 'title': title, 'url': link,
            'domain': parsed.hostname.lower(), 'publisher': publisher,
            'detected_at_utc': published, 'first_seen_at_utc': now_iso,
            'language': 'fr' if 'fr.allafrica.com' in feed else 'en',
            'source_index': 'AllAfrica RSS', 'source_feed': feed,
            'verification': 'unverified_discovery', 'relevance': 'headline_keyword_match',
            'modules': modules,
        })
    return sorted(found, key=lambda x: x['detected_at_utc'], reverse=True)


def fetch_feed(session, iso, language, timeout=30):
    url = feed_url(iso, language)
    response = session.get(url, timeout=timeout, headers={
        'User-Agent': 'ChinaAfricaResearchAtlas/4.2 (+https://ysiqi32-design.github.io/china-africa-atlas/; RSS headline indexing)'
    })
    if response.status_code == 429:
        raise RuntimeError(f'HTTP 429 from AllAfrica RSS ({language})')
    response.raise_for_status()
    if not response.content.strip():
        raise ValueError(f'Empty AllAfrica RSS response ({language})')
    return parse_rss(response.content.decode(response.encoding or 'utf-8', errors='replace'), iso, url, datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))


def select_batch(countries, status, size):
    def rank(iso):
        row = status.get(iso) or {}
        return (row.get('last_success_at_utc') or '', row.get('checked_at_utc') or '', iso)
    return sorted(countries, key=rank)[:size]


def merge(old, new, now_iso, retention_days=90, cap=45):
    cutoff = datetime.fromisoformat(now_iso.replace('Z', '+00:00')) - timedelta(days=retention_days)
    by_id = {x['id']: x for x in old if isinstance(x, dict) and x.get('id')}
    for row in new:
        if row['id'] in by_id:
            row['first_seen_at_utc'] = by_id[row['id']].get('first_seen_at_utc', now_iso)
        by_id[row['id']] = row
    valid = []
    for row in by_id.values():
        try:
            if datetime.fromisoformat(row['detected_at_utc'].replace('Z', '+00:00')) >= cutoff:
                valid.append(row)
        except (ValueError, TypeError, KeyError):
            continue
    return sorted(valid, key=lambda x: x['detected_at_utc'], reverse=True)[:cap]


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.write('\n')
            out.flush()
        pathlib.Path(temp_name).replace(path)
    finally:
        pathlib.Path(temp_name).unlink(missing_ok=True)


def refresh(target, selected, all_codes, batch_size, fixture=None, delay=8):
    prior = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    if not isinstance(prior, dict):
        raise ValueError('Existing news.json must be a JSON object; refusing to overwrite it')
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    items = dict(prior.get('countries') or {})
    statuses = dict(prior.get('country_status') or {})
    errors, successful, attempted = {}, [], 0
    session = requests.Session()
    for index, iso in enumerate(selected, 1):
        attempted += 1
        language_ok, rows, language_errors = 0, [], []
        for language in ('en', 'fr'):
            try:
                if fixture is not None:
                    xml_text = fixture.get(iso, {}).get(language)
                    if not xml_text:
                        raise ValueError(f'Missing {language} RSS fixture')
                    batch = parse_rss(xml_text, iso, feed_url(iso, language), now)
                else:
                    batch = fetch_feed(session, iso, language)
                rows.extend(batch)
                language_ok += 1
            except Exception as exc:
                language_errors.append(f'{language}: {str(exc)[:180]}')
                if '429' in str(exc):
                    break
            if fixture is None and language == 'en' and delay:
                time.sleep(delay)
        if language_ok:
            items[iso] = merge(items.get(iso, []), rows, now)
            status = 'ok' if not language_errors else 'partial'
            statuses[iso] = {
                **(statuses.get(iso) or {}), 'checked_at_utc': now,
                'last_success_at_utc': now, 'status': status,
                'matched_recently': len(rows), 'stored_records': len(items[iso]),
                'feeds_succeeded': language_ok, 'feeds_expected': 2,
            }
            successful.append(iso)
            print(f'[{index}/{len(selected)}] {iso}: {len(rows)} China-related leads; {language_ok}/2 feeds', flush=True)
        else:
            message = '; '.join(language_errors) or 'No RSS feeds succeeded'
            errors[iso] = message
            statuses[iso] = {
                **(statuses.get(iso) or {}), 'checked_at_utc': now,
                'status': 'fetch_failed', 'error': message,
                'stored_records': len(items.get(iso, [])),
            }
            print(f'[{index}/{len(selected)}] {iso}: FAILED {message}', file=sys.stderr, flush=True)
            if '429' in message:
                print('RSS source rate limit: stopping this batch; prior data remains intact.', file=sys.stderr, flush=True)
                break
        if fixture is None and delay and index < len(selected):
            time.sleep(delay)
    db = dict(prior)
    db.update({
        'schema_version': 2, 'dataset': 'africa_china_news_discovery',
        'provider': 'AllAfrica country RSS feeds',
        'provider_url': 'https://allafrica.com/misc/tools/rss.html',
        'status': 'partial' if errors else 'ok', 'checked_at_utc': now,
        'last_success_at_utc': now if successful else prior.get('last_success_at_utc'),
        'lookback_days': 30, 'retention_days': 90, 'country_status': statuses,
        'countries': items, 'errors': errors, 'batch_attempted': attempted,
        'batch_success': len(successful), 'batch_total': len(selected),
        'methodology': 'Daily rotating country batches from English and French AllAfrica RSS feeds. Headlines and source links are discovery leads; keyword matches are not verified facts. RSS category coverage can vary by country and publisher.',
        'notice': '新闻标题依 AllAfrica RSS 条款标注并链接原文；仅供研究发现，所有线索待核验。各国时间表示最近一次成功读取该国英/法 RSS 分类源。',
    })
    atomic_write(target, db)
    print(f'Saved checkpoint: {len(successful)}/{attempted} countries succeeded; {sum(len(v) for v in items.values())} leads retained.', flush=True)
    return 0 if successful else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--delay', type=int, default=8)
    parser.add_argument('--fixture', help='JSON object containing ISO3 -> en/fr RSS XML strings')
    parser.add_argument('--output', type=pathlib.Path, default=TARGET)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 12 or not 0 <= args.delay <= 60:
        parser.error('batch-size must be 1..12 and delay 0..60 seconds')
    all_codes = list(COUNTRIES)
    prior = json.loads(args.output.read_text(encoding='utf-8')) if args.output.exists() else {}
    state = prior.get('country_status') or {}
    selected = all_codes if args.fixture else select_batch(all_codes, state, args.batch_size)
    fixture = json.loads(pathlib.Path(args.fixture).read_text(encoding='utf-8')) if args.fixture else None
    print(f"Country batch: {', '.join(selected)}; {len(selected)} of {len(all_codes)} countries", flush=True)
    return refresh(args.output, selected, all_codes, args.batch_size, fixture, args.delay)


if __name__ == '__main__':
    sys.exit(main())
