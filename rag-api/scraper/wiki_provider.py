import json
import sys
from aiofiles import open as aio_open
from bs4 import BeautifulSoup
from base.logger import log
from base.logger import warn
from base.logger import error
from base.request import get_url
from base.json_search import JSONSearch
from base.utils import fix_punctuation_spaces
from scraper.overpass_provider import get_locations_by_admin_level
from scraper.overpass_provider import MEXICO_AREA_CODE
from scraper.overpass_provider import ADMIN_LEVEL_COUNTRY
from scraper.overpass_provider import ADMIN_LEVEL_STATE
from scraper.overpass_provider import ADMIN_LEVEL_CITY

WIKIDATA_REST_URL = 'https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/{id}'
WIKIPEDIA_PAGE_URL = 'https://{lang}.wikipedia.org/wiki/{slug}'
WIKIPEDIA_SEARCH_URL = 'https://{lang}.wikipedia.org/w/index.php?search={term}'

FIXED_WIKI_LOCATIONS = {
  "Q10794738": 'https://es.wikipedia.org/wiki/Municipio_de_Morelos_(Michoac%C3%A1n)'
}

FIXED_WIKIDATA_LOCATIONS = {
  "Q20127021": "Q51120215"
}

async def extract_geo_info(wikidata_id: str, resolve_nested_locations=False):
  # log(f"Extracting geo info on: {wikidata_id}")
  wikidata_id = FIXED_WIKIDATA_LOCATIONS.get(wikidata_id) or wikidata_id
  url = WIKIDATA_REST_URL.format(id=wikidata_id)
  data = await get_url(url, sys.maxsize, 'json')
  json = JSONSearch(data)
  name = json.search('labels.es') or json.search('labels.en')
  aliases_lst = json.search('aliases.es') or []
  coords_lat = json.search('statements.P625[0].value.content.latitude')
  coords_lng = json.search('statements.P625[0].value.content.longitude')
  es_wiki = json.search('sitelinks.eswiki.url')

  # borders
  borders = json.search('statements.P47[*].value.content') or []
  if resolve_nested_locations:
    borders = [await extract_geo_info(border) for border in borders]
    borders = [border['name'] for border in borders]

  # relations
  relations = json.search('statements.P31[*].value.content') or []
  is_city = 'Q515' in relations
  is_country = 'Q6256' in relations
  # state and municipality codes are for Mexico only
  is_state = 'Q15149663' in relations
  is_municipality = 'Q1952852' in relations

  # state
  state = json.search('(statements.P131[*].value.content)[0]')
  if resolve_nested_locations and state:
    state = await extract_geo_info(state)
    state = state['name']

  # country
  country = json.search('(statements.P17[*].value.content)[0]')
  if resolve_nested_locations and country:
    country = await extract_geo_info(country)
    country = country['name']

  # capital city
  capital_city = json.search('(statements.P36[*].value.content)[0]')
  if resolve_nested_locations and capital_city:
    capital_city = await extract_geo_info(capital_city)
    capital_city = capital_city['name']

  # capital of
  capital_of = json.search('(statements.P1376[*].value.content)[0]')
  if resolve_nested_locations and capital_of:
    capital_of = await extract_geo_info(capital_of)
    capital_of = capital_of['name']

  loc_type = ''
  try:
    types = ['country', 'city', 'municipality', 'state']
    type_index = [is_country, is_city, is_municipality, is_state].index(True)
    loc_type = types[type_index]
  except Exception as e:
    loc_type = ''

  return {
    'id': wikidata_id,
    'name': name,
    'aliases': ', '.join(aliases_lst),
    'type': loc_type,
    'state': state,
    'capital_of': capital_of,
    'capital_city': capital_city, # in municipality this is the head of the municipality
    'country': country,
    'borders': ', '.join(borders),
    'lat': coords_lat,
    'lng': coords_lng,
    'eswiki': es_wiki
  }

async def find_wiki_page(query: str, lang: str):
  """ Finds a wikipedia page from a wikidata id by augmenting the search with the state and country """
  wiki_search_url = WIKIPEDIA_SEARCH_URL.format(lang=lang, term=query)
  wikipedia_page = await get_url(wiki_search_url, sys.maxsize, 'html')
  soup = BeautifulSoup(wikipedia_page, 'html.parser')
  anchor = soup.select_one('.mw-search-results a')
  if not anchor:
    return None
  page_slug = anchor.get('href').replace('/wiki/', '')
  return WIKIPEDIA_PAGE_URL.format(lang=lang, slug=page_slug)

async def get_from_fixed_locations(wikidata_id: str):
  # read file from fixed_locations.json
  try:
    async with aio_open('scraper/fixed_locations.json', 'r', encoding='utf-8') as f:
      data = json.loads(await f.read())
      # find data array for entry with id === wikidata_id
      entry = next((entry for entry in data if entry['id'] == wikidata_id), None)
      return entry
  except Exception as e:
    error(f"Error reading fixed locations: {e}")
    return None

async def get_wiki_pages():
  countries = await get_locations_by_admin_level(MEXICO_AREA_CODE, ADMIN_LEVEL_COUNTRY)
  states = await get_locations_by_admin_level(MEXICO_AREA_CODE, ADMIN_LEVEL_STATE)
  cities = await get_locations_by_admin_level(MEXICO_AREA_CODE, ADMIN_LEVEL_CITY)
  # merge all locations
  locations = countries + states + cities
  locations = locations[0:2600]
  log(f"Locations count: {len(locations)}")
  # deduplicate from name key
  entries = []
  for loc in locations:
    geo_info = await extract_geo_info(loc['wikidata'], True)
    wikipedia_url = geo_info['eswiki'] or FIXED_WIKI_LOCATIONS.get(loc['wikidata'])
    if not wikipedia_url:
      wiki_query = [loc['name'], geo_info['state'], geo_info['country'], f"intitle:{loc['name']}"]
      wiki_query = ' '.join([q for q in wiki_query if q])
      wiki_query = wiki_query.replace(' ', '+')
      wikipedia_url = await find_wiki_page(wiki_query, 'es')
      warn(f"Alternative wiki page used: {wikipedia_url} from: {loc['name']}.")
      log(f"\t> Search query augmented with {geo_info['name']}, {geo_info['state']} from Wikidata: {geo_info['id']}")
      log(f"\t> Search URL: {WIKIPEDIA_SEARCH_URL.format(lang='es', term=wiki_query)}")
      if not wikipedia_url:
        warn(f"Couldn't find wiki page from: {loc}")

    if (wikipedia_url is not None):
      page = await get_url(wikipedia_url, sys.maxsize, 'html')
      entries.append({ 'scrape': True, 'url': wikipedia_url, 'contents': page, 'geo_info': geo_info })
    else:
      log(f"Trying to get data from local fixed locations for: {loc['name']}")
      fixed_loc = await get_from_fixed_locations(loc['wikidata'])
      if fixed_loc:
        log(f"Fixed location found: {loc['name']}")
        entries.append({ 'scrape': False, 'url': fixed_loc['url'], 'contents': fixed_loc['description'], 'geo_info': geo_info })
      else:
        error(f"Couldn't find wiki page from: {loc}")
  return entries

async def scrape_wiki_pages(pages):
  result = []
  for page in pages:
    if page['scrape']:
      log(f"Scraping page: {page['url']}")
      soup = BeautifulSoup(page['contents'], 'html.parser')
      description = soup.select_one('.mw-body-content .mw-parser-output > .infobox ~ p:not(.mw-empty-elt)')
      if not description:
        description = soup.select_one('.mw-body-content .mw-parser-output > p')
      # remove elements with class .not-here
      for el in description.select('.autonumber, sup, small'):
        el.decompose()
      # remove empty parentheses
      description = description.getText().replace('()', '')
      # generic punctuation fixes
      description = fix_punctuation_spaces(description)
      result.append({
        'url': page['url'],
        'title': soup.select_one('h1').getText(),
        'description': description,
        'geo_info': page['geo_info'],
      })
    else:
      result.append({
        'url': page['url'],
        'title': page['geo_info']['name'],
        'description': page['contents'],
        'geo_info': page['geo_info'],
      })
  return result

if __name__ == "__main__":
  pass
