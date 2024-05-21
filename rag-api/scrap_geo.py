import json
import sys
import time
from bs4 import BeautifulSoup
from base.logger import log
from base.request import get_url

API_URL = 'https://overpass-api.de/api/interpreter'
WIKIDATA_PAGE_URL = 'https://www.wikidata.org/wiki/{id}'
WIKIPEDIA_PAGE_URL = 'https://{lang}.wikipedia.org/wiki/{slug}'
WIKIPEDIA_SEARCH_URL = 'https://{lang}.wikipedia.org/w/index.php?search={term}'

"""
  Get Countries with area codes:
  https://overpass-turbo.eu/#

  [out:csv(::id, "name:es", "wikipedia")];
  area["admin_level"="2"][boundary=administrative][type!=multilinestring];
  out;
"""

ADMIN_LEVEL_COUNTRY = 2
ADMIN_LEVEL_STATE = 4
ADMIN_LEVEL_CITY = 6

async def get_locations(code_id: int, admin_level: int):
  """ Uses overpass api to get locations from a given area code and admin level. """
  data = f"""
    [out:json];
    area({code_id})->.searchArea;
    rel["boundary"="administrative"]["admin_level"={admin_level}](area.searchArea);
    out tags;
  """
  req_url = f"{API_URL}?data={data}"
  content = await get_url(req_url, sys.maxsize, 'json')
  # parse json
  data = json.loads(content)
  elements = []
  for element in data['elements']:
    tags = element.get('tags', {})
    name = tags.get('name', '')
    wikidata = tags.get('wikidata', '')
    wikipedia = tags.get('wikipedia', '')
    # removes es:, en:, etc prefix
    slug = wikipedia.split(':')[-1].replace(' ', '_')
    lang = wikipedia.split(':')[0]
    # if slug contains commas invalidate the whole slug
    if ',' in slug:
      slug = ''
    elements.append({
      'name': name,
      'wikidata': wikidata,
      'wikipedia': wikipedia,
      'slug': slug,
      'lang': lang
    })
  return elements

async def find_wiki_page(name, wikimedia_id: str, lang):
  """ Finds a wikipedia page from a wikidata id by augmenting the search with the state and country """
  wikimedia_url = WIKIDATA_PAGE_URL.format(id=wikimedia_id)
  wikimedia_page = await get_url(wikimedia_url, sys.maxsize, 'html')
  soup = BeautifulSoup(wikimedia_page, 'html.parser')
  state = soup.select_one('#P131 a[title^=Q]').getText()
  country = soup.select_one('#P17 a[title^=Q]').getText()
  if not state or not country:
    return None
  if (lang == ''):
    lang = 'es'

  query = f'{name} {state} {country}'.replace(' ', '+')
  wiki_search_url = WIKIPEDIA_SEARCH_URL.format(lang=lang, term=query)
  wikipedia_page = await get_url(wiki_search_url, sys.maxsize, 'html')
  soup = BeautifulSoup(wikipedia_page, 'html.parser')
  anchor = soup.select_one('.mw-search-results a')
  if not anchor:
    return None
  page_slug = anchor.get('href').replace('/wiki/', '')
  return WIKIPEDIA_PAGE_URL.format(lang=lang, slug=page_slug)

async def get_wiki_pages():
  countries = await get_locations(3600114686, ADMIN_LEVEL_COUNTRY)
  states = await get_locations(3600114686, ADMIN_LEVEL_STATE)
  cities = await get_locations(3600114686, ADMIN_LEVEL_CITY)
  # merge all locations
  locations = countries + states + cities
  # deduplicate from name key
  entries = []
  for loc in locations:
    if not loc['wikipedia'] or not loc['slug']:
      log(f"Finding wiki page from: {loc} because it doesn't have wikipedia link.")
      wikipedia_url = await find_wiki_page(loc['name'], loc['wikidata'], loc['lang'])
      if not wikipedia_url:
        log(f"Couldn't find wiki page from: {loc}")
        continue
    else:
      wikipedia_url = WIKIPEDIA_PAGE_URL.format(lang=loc['lang'], slug=loc['slug'])
    if (wikipedia_url is not None):
      page = await get_url(wikipedia_url, sys.maxsize, 'html')
      entries.append(page)
    # time.sleep(1)
  return entries


async def scrape_entries(entries):
  for entry in entries:
    soup = BeautifulSoup(entry, 'html.parser')
    log(soup.title.string)


if __name__ == "__main__":
  import asyncio
  loop = asyncio.get_event_loop()
  loop.run_until_complete(get_locations(3600114686, 2))
