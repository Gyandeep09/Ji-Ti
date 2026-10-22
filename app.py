import os
import math
import time
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from exa_py import Exa
from ddgs import DDGS
from flask import Flask, render_template, request

load_dotenv()

exa = Exa(os.getenv('EXA_API_KEY'))
app = Flask(__name__)


def clean_title(title):
    if not title:
        return '(no title)'
    title = title.split('.tiktok-')[0].strip()
    return title or '(no title)'


def short(text):
    text = ' '.join((text or '').split())
    if len(text) > 220:
        return text[:220] + '...'
    return text


def make_snippet(highlights):
    if not highlights:
        return ''
    return short(highlights[0].replace('#', ' '))


def domain_of(url):
    return urlparse(url or '').netloc.replace('www.', '')


def youtube_id(url):
    parsed = urlparse(url or '')
    if 'youtube.com' in parsed.netloc:
        return parse_qs(parsed.query).get('v', [None])[0]
    if 'youtu.be' in parsed.netloc:
        return parsed.path.lstrip('/') or None
    return None


def search_exa(query):
    response = exa.search(query, num_results=30, contents={'highlights': True})
    results = []
    for item in response.results:
        results.append({
            'title': clean_title(item.title),
            'url': item.url,
            'domain': domain_of(item.url),
            'image': getattr(item, 'image', None),
            'author': getattr(item, 'author', None),
            'date': (getattr(item, 'published_date', None) or '')[:10],
            'snippet': make_snippet(getattr(item, 'highlights', None)),
            'video_id': None,
        })
    return results


def free_search(kind, query, count):
    try:
        return getattr(DDGS(), kind)(query, max_results=count)
    except Exception as problem:
        if 'no results' in str(problem).lower():
            return []
        raise Exception(
            'The free ' + kind + ' search is not responding right now. '
            'DuckDuckGo may be limiting requests, so wait a minute and try again. '
            'Details: ' + str(problem)
        )


def search_images(query):
    results = []
    for item in free_search('images', query, 40):
        picture = item.get('thumbnail') or item.get('image')
        if not picture:
            continue
        page_url = item.get('url') or picture
        results.append({
            'title': clean_title(item.get('title')),
            'url': page_url,
            'domain': domain_of(page_url),
            'image': picture,
            'author': item.get('source'),
            'date': '',
            'snippet': '',
            'video_id': None,
        })
    return results


def search_videos(query):
    results = []
    for item in free_search('videos', query, 30):
        link = item.get('content')
        if not link:
            continue
        thumbs = item.get('images') or {}
        picture = None
        if isinstance(thumbs, dict):
            picture = thumbs.get('large') or thumbs.get('medium') or thumbs.get('small')
        results.append({
            'title': clean_title(item.get('title')),
            'url': link,
            'domain': domain_of(link),
            'image': picture,
            'author': item.get('uploader') or item.get('publisher'),
            'date': (item.get('published') or '')[:10],
            'snippet': short(item.get('description')),
            'video_id': youtube_id(link),
        })
    return results


def search_news(query):
    results = []
    for item in free_search('news', query, 30):
        link = item.get('url')
        if not link:
            continue
        results.append({
            'title': clean_title(item.get('title')),
            'url': link,
            'domain': domain_of(link),
            'image': item.get('image'),
            'author': item.get('source'),
            'date': (item.get('date') or '')[:10],
            'snippet': short(item.get('body')),
            'video_id': None,
        })
    return results


def run_search(query, tab):
    if tab == 'images':
        return search_images(query)
    if tab == 'videos':
        return search_videos(query)
    if tab == 'news':
        return search_news(query)
    return search_exa(query)


PAGE_SIZE = {'all': 10, 'images': 12, 'videos': 6, 'news': 10}
CACHE = {}
CACHE_SECONDS = 15 * 60


def get_results(query, tab):
    key = (query.lower(), tab)
    saved = CACHE.get(key)
    if saved and time.time() - saved[0] < CACHE_SECONDS:
        return saved[1]
    results = run_search(query, tab)
    if len(CACHE) > 50:
        CACHE.clear()
    CACHE[key] = (time.time(), results)
    return results


@app.route('/')
def home():
    query = request.args.get('q', '').strip()
    tab = request.args.get('tab', 'all')
    if tab not in PAGE_SIZE:
        tab = 'all'
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1

    results = []
    pages = 1
    has_more = False
    error = None

    if query:
        try:
            everything = get_results(query, tab)
            size = PAGE_SIZE[tab]
            pages = max(1, math.ceil(len(everything) / size))
            page = min(page, pages)
            start = (page - 1) * size
            results = everything[start:start + size]
            has_more = page < pages
        except Exception as problem:
            error = str(problem)

    return render_template(
        'index.html', query=query, tab=tab, results=results,
        error=error, page=page, pages=pages, has_more=has_more,
    )


if __name__ == '__main__':
    app.run(debug=True)

