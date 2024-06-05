import sys
from operator import le
from string import Template
from base.json_parse import try_parse_json
from base.logger import log
from base.logger import debug
from base.logger import error
from base.logger import warn
from providers.nominatim_provider import search_location
from providers.nominatim_provider import search_location_params
from providers.nominatim_provider import search_location_details
from base.json_search import JSONSearch
from entities.article_location import ArticleLocation
from base.fuzzy_search import FuzzySearch
from providers.overpass_provider import PLACE_TYPE_STATE
from providers.overpass_provider import PLACE_TYPE_CITY
from providers.overpass_provider import PLACE_TYPE_BOROUGH
from providers.overpass_provider import PLACE_TYPE_TOWN
from providers.overpass_provider import PLACE_TYPE_VILLAGE
from providers.overpass_provider import PLACE_TYPE_HAMLET
from location_mapper import get_locations_map
from base.utils import str_in_text

from gliner import GLiNER

MIN_LOCATION_RANK = 4
MAX_LOCATION_RANK = 20
Cached_Model = None

def build_prompt(title, content, country='México'):
  debug('Building Prompt')
  debug(f'\t Title: {title}')
  debug(f'\t Content: {content}')
  t = Template("""
      ```
      Titulo: $title
      Contenido: $content
      ```
      Del articulo arriba:
      - Extrae las entidades geograficas de $country.
      - Omite colonias, nombres propios, nombres de universidades, empresas, etc.

      Respuesta solo en formato JSON valido:
      ```
      [
        { "ciudad": "Ciudad 1", "municipio": "Municipio o comunidad o localidad", "estado": "Estado 1"},
        { "ciudad": "Ciudad 2", "municipio": "Municipio o comunidad o localidad", "estado": "Estado 2"}
        ...
      ]
      ```

  """)
  return t.substitute(title=title, content=content, country=country)


async def extract_related_locations(location: ArticleLocation):
  query_params = []
  query_params.append({ 'country': location.country, 'state': location.state, 'city': location.city })
  query_params.append({ 'country': location.country, 'state': location.state, 'city': location.town })
  query_params.append({ 'country': location.country, 'state': location.state, 'county': location.county })
  query_params.append({ 'country': location.country, 'state': location.state })
  query_params.append({ 'country': location.country })
  # remove items that have empty values in any of the keys
  query_params = [params for params in query_params if all(params.values())]
  debug(f'Query Params: {query_params}')
  result = []
  for params in query_params:
    try:
      related_loc = await search_location_params(params)
      details_loc = await search_location_details(related_loc.search('place_id'))
      # https://nominatim.org/release-docs/latest/customize/Ranking/#address-rank
      fmt_exp = "address[?(rank_address >= `{rank_from}` && rank_address <= `{rank_to}` && isaddress == `true`)].localname | [0]"
      defaults = {
        'country': details_loc.search(fmt_exp.format(rank_from=4, rank_to=4)),
        'state': details_loc.search(fmt_exp.format(rank_from=5, rank_to=9)),
        'county': details_loc.search(fmt_exp.format(rank_from=10, rank_to=12)),
        'city': details_loc.search(fmt_exp.format(rank_from=13, rank_to=16)),
        'town': details_loc.search(fmt_exp.format(rank_from=17, rank_to=21)),
      }
      debug(f'Defaults: {defaults}')
      geo_loc = await geo_location_from_results(related_loc, default_fields=defaults)
      result.append(geo_loc)
    except Exception as e:
      error('Error extracting parent locations', e)
  return result

async def geo_location_from_results(results: JSONSearch, default_fields = {}):
  try:
    place_id = results.search('place_id')
    details = await search_location_details(place_id)
    return ArticleLocation({
      'place_id': place_id,
      'osm_type': results.search('osm_type'),
      'osm_id': results.search('osm_id'),
      'country': results.search('address.country') or default_fields.get('country', None),
      'city': results.search('address.city') or default_fields.get('city', None),
      'state': results.search('address.state') or default_fields.get('state', None),
      'state_district': results.search('address.state_district'),
      'borough': results.search('address.borough'),
      'village': results.search('address.village'),
      'county': results.search('address.county') or default_fields.get('county', None),
      'town': results.search('address.town') or default_fields.get('town', None),
      'rank_address': details.search('rank_address'),
      'lat': results.search('lat'),
      'lon': results.search('lon'),
    })
  except Exception as e:
    error('Error mapping location', e)
    return None

async def is_valid_identity(name: str):
  name = name.lower().strip()
  if not name:
    return False
  results = await search_location(name)
  # parse int from string or None type
  rank = int(results.search('place_rank') or sys.maxsize)
  if not results.empty and rank <= MAX_LOCATION_RANK:
    return True

def comma_join(values):
  return ', '.join([v for v in values if v])

def deduplicate_locations(locations):
  unique_locations = []
  for location in locations:
    if not any(loc.id == location.id for loc in unique_locations):
      unique_locations.append(location)
  return unique_locations

def filter_locations_between_rank(locations: list[ArticleLocation], rank_from: int, rank_to: int):
  """
      Both LLM and Nominatim are not perfect with high rank locations (such as streets or new neighbourhoods).
      Maybe in the future we can increase the range.
  """
  return [location for location in locations if location.rank_address >= rank_from and location.rank_address <= rank_to]

def get_gliner_model():
  global Cached_Model
  if not Cached_Model:
    Cached_Model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
    Cached_Model.eval()
  return Cached_Model

def extract_locations_from_ner(response_str):
  locations = []
  model = get_gliner_model()
  labels = ["Estado", "Municipio", "Ciudad"]
  entities = model.predict_entities(response_str, labels, threshold=0.4)
  for entity in entities:
    # NER will somethings put the type of location in the text. We ignore it.
    if (entity['text'].lower() in ['municipio', 'ciudad', 'estado']):
      continue
    if str_in_text(entity['text'], response_str) > 0:
      locations.append({ entity["label"]: entity["text"] })
    else:
      warn(f"Ignoring NER label/value: {entity['label']}:\"{entity['text']}\" not found in text")
  log(f"Extracted Locations from NER: {locations}")
  return locations

async def tag_locations(arr: list[str]) -> dict:
  # deduplicate arr
  arr = list(set(arr))
  result = []
  for name in arr:
    name = name.strip().capitalize()
    type = await get_place_type(name)
    log(f"Name: {name} - Type: {type}")
    if type:
      result.append({ type: name })
  return result

async def get_place_type(name: str) -> str|None:
  fuzzy = FuzzySearch()
  loc_map = await get_locations_map()
  keys_order = [
    PLACE_TYPE_STATE,
    PLACE_TYPE_CITY,
    PLACE_TYPE_BOROUGH,
    PLACE_TYPE_TOWN,
    PLACE_TYPE_VILLAGE,
    PLACE_TYPE_HAMLET
  ]
  for type in keys_order:
    fuzzy.add(type, loc_map[type])
  results = fuzzy.search(name)
  if len(results) > 0:
    return results[0]['type']
  else:
    return None

def get_location_queries(tagged_locations: dict) -> list[str]:
  """ This function will return a list of queries like "city, state" or "town, state" for all tagged locations."""
  state_loc_queries = []
  states = [loc['state'] for loc in tagged_locations if 'state' in loc]
  for loc_type in ['city', 'town', 'borough', 'village', 'hamlet']:
    state_loc = [loc[loc_type] for loc in tagged_locations if loc_type in loc]
    state_loc_queries += [f"{loc}, {state}" for state in states for loc in state_loc]
  return list(set(state_loc_queries))

async def parse_response(response_str):
  locations = []
  parent_locations = []
  try:
    ner_locations = extract_locations_from_ner(response_str)
    ner_labels = [value for d in ner_locations for value in d.values()]
    tagged_locations = await tag_locations(ner_labels)
    log(f'Tagged Locations: {tagged_locations}')
    location_queries = get_location_queries(tagged_locations)
    log(f'Location Queries: {location_queries}')
    for query in location_queries:
      results = await search_location(query)
      if not results.empty:
        debug(f'Results for "{query}": {results}')
        geo_location = await geo_location_from_results(results)
        debug(f'Location found for "{query}": {geo_location}')
        locations.extend([geo_location])
      else:
        warn(f'No results found for query: {query}')
    for location in locations:
      parent_loc = await extract_related_locations(location)
      parent_locations.extend(parent_loc)
  except Exception as e:
    error('Error parsing response', e)
    pass
  locations = deduplicate_locations(locations + parent_locations)
  locations = filter_locations_between_rank(locations, MIN_LOCATION_RANK, MAX_LOCATION_RANK)
  return locations
