from typing import List, Tuple, Dict
from base.logger import log
from base.logger import debug
from base.logger import error
from base.logger import warn
from providers.nominatim_provider import search_location
from providers.nominatim_provider import search_location_params
from providers.nominatim_provider import search_location_details
from base.json_search import JSONSearch
from entities.article_location import ArticleLocation
from prompts.gliner_geo_tag import extract_locations_from_content
from providers.overpass_provider import lower_ranked_place_types
from entities.location_relation import LocationRelation

MIN_LOCATION_RANK = 4
MAX_LOCATION_RANK = 20

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

def relations_from_parent(locations: dict, parent_type: str) -> List[LocationRelation]:
  relations = []
  parent_locs = [loc for loc in locations if parent_type in loc]
  for loc_type in lower_ranked_place_types(parent_type):
    child_locs = [loc for loc in locations if loc_type in loc]
    for parent in parent_locs:
      for child in child_locs:
        p_tuple = next(iter(parent.items()))
        c_tuple = next(iter(child.items()))
        relations.append(LocationRelation(p_tuple, c_tuple))
  # deduplicate list
  relations = set(relations)
  return relations

async def filter_invalid_relations(relations: List[LocationRelation]) -> List[LocationRelation]:
  log(f"Fitering invalid relations: {relations}")
  for relation in relations:
    params = { relation.parent_type: relation.parent_name, relation.child_type: relation.child_name }
    results = await search_location_params(params)
    if results.empty:
      relations.remove(relation)
  return relations

async def get_location_queries(tagged_locations: dict) -> list[str]:
  """
    This function will return a list of queries like "city, {parent}" or "town, {parent}"
    for all tagged locations. Where parent can be a state or a country.
  """
  queries = []
  relations = []
  relations += relations_from_parent(tagged_locations, 'country')
  relations += relations_from_parent(tagged_locations, 'state')
  relations = await filter_invalid_relations(relations)
  # deduplicate list of relations
  relations = set(relations)
  for relation in relations:
    queries.append(str(relation))
  # if not queries:
  #   queries += [loc['city'] for loc in tagged_locations if 'city' in loc]
  #   queries += [loc['state'] for loc in tagged_locations if 'state' in loc]
  return queries

async def parse_content(content: str, default_state: str = None, default_country: str = None):
  locations = []
  parent_locations = []
  try:
    tagged_locations = await extract_locations_from_content(content)
    if default_country and not any('country' in loc for loc in tagged_locations):
      tagged_locations.append({ 'country': default_country })
    if default_state and not any('state' in loc for loc in tagged_locations):
      tagged_locations.append({ 'state': default_state })
    log(f'Tagged Locations: {tagged_locations}')
    location_queries = await get_location_queries(tagged_locations)
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
