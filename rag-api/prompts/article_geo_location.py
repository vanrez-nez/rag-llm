import json
from operator import le
from string import Template
from base.json_parse import try_parse_json
from base.logger import log
from base.logger import debug
from base.logger import error
from base.logger import warn
from scraper.nominatim_provider import search_location
from scraper.nominatim_provider import search_location_params
from scraper.nominatim_provider import search_location_details
from scraper.nominatim_provider import address_lookup
from base.json_search import JSONSearch

def build_prompt(title, content):
  t = Template("""
      Del articulo abajo:
      - Extrae la ubicacion geografica de ciudades, estados, municipios, comunidades y localidades que se mencionan.
      - Si se mencionan ubicaciones diferentes crea un objecto por cada ubicacion.
      - Omite colonias, nombres propios, nombres de universidades, empresas, etc.
      - Todos los valores deben ser cadenas de texto. Deja los valores vacios si no se mencionan.
      - NO agregues informacion adicional como notas o comentarios.

      ```
      Titulo: $title
      Contenido: $content
      ```

      Ejemplo de respuesta:
      ```
      [
        { "ciudad": "Ciudad 1", "municipio": "Municipio, comunidad, localidad", "estado": "Estado 1"},
        { "ciudad": "Ciudad 2", "municipio": "Municipio, comunidad, localidad", "estado": "Estado 2"}
        { "ciudad": "Ciudad 3", "municipio": "Municipio, comunidad, localidad" "estado": "Estado 3"},
      ]
      ```

  """)
  return t.substitute(title=title, content=content)


class GeoLocation:
  def __init__(self, fields = {}) -> None:
    self.place_id = fields.get('place_id', '')
    self.osm_type = fields.get('osm_type', '')
    self.osm_id = fields.get('osm_id', '')
    self.country = fields.get('country', '')
    self.city = fields.get('city', '')
    self.state = fields.get('state', '')
    self.state_district = fields.get('state_district', '')
    self.county = fields.get('county', '')
    self.town = fields.get('town', '')
    self.rank_address = fields.get('rank_address', '')
    self.lat = fields.get('lat', '')
    self.lon = fields.get('lon', '')

  @property
  def id(self):
    """
      place_id is nominatim's unique identifier for a location but can't be used externally as it changes each time
      database is rebuilt. Instead we use osm_type and osm_id for form a unique id. osm_id cannot be used alone
      as it is not unique across osm_types.
    """
    return f"{self.osm_type}-{self.osm_id}"

  def __str__(self) -> str:
    return json.dumps(self.__dict__)

async def extract_related_locations(location: GeoLocation):
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
    # _details = JSONSearch(json.dumps(details))
    # log(f'Details: {details}')
    return GeoLocation({
      'place_id': place_id,
      'osm_type': results.search('osm_type'),
      'osm_id': results.search('osm_id'),
      'country': results.search('address.country') or default_fields.get('country', None),
      'city': results.search('address.city') or default_fields.get('city', None),
      'state': results.search('address.state') or default_fields.get('state', None),
      'state_district': results.search('address.state_district'),
      'county': results.search('address.county') or default_fields.get('county', None),
      'town': results.search('address.town') or default_fields.get('town', None),
      'rank_address': details.search('rank_address'),
      'lat': results.search('lat'),
      'lon': results.search('lon'),
    })
  except Exception as e:
    error('Error mapping location', e)
    return None

async def is_state_relation_valid(state, relation):
  if not state or not relation:
    return False
  results = await search_location_params({ 'state': state, 'city': relation })
  if results.empty:
    results = await search_location_params({ 'state': state, 'county': relation })
  return results.empty == False

def comma_join(values):
  return ', '.join([v for v in values if v])

async def get_location_queries(obj):
  """
    Based on the parsed JSON object, constructs a list of queries to search per location.
    This is done to ensure a location is assigned to the article. First trying to search
    the more specific location, then the state, and finally the country. Relations to a
    state are validated to ensure the location is within the state, LLM will sometimes
    miscategorize names inside state or city fields.
  """
  state = obj.get('estado', '')
  municipality = obj.get('municipio', '')
  is_valid_municipality = await is_state_relation_valid(state, municipality)
  if not is_valid_municipality:
    municipality = ''
    obj['municipio'] = ''

  city = obj.get('ciudad', '')
  is_valid_city = await is_state_relation_valid(state, city)
  if not is_valid_city:
    obj['ciudad'] = ''
    city = ''

  comma_values = comma_join(obj.values())
  country = obj.get('pais', 'México')
  municipality_state = comma_join([municipality, state])
  city_state = comma_join([city, state])
  queries = [
    comma_values,
    municipality_state,
    city_state,
    state,
    country
  ]
  # remove empty values
  queries = [q for q in queries if q]
  # remove duplicates
  queries = list(dict.fromkeys(queries))
  return queries

def deduplicate_locations(locations):
  unique_locations = []
  for location in locations:
    if not any(loc.id == location.id for loc in unique_locations):
      unique_locations.append(location)
  return unique_locations

def filter_locations_between_rank(locations, rank_from: int, rank_to: int):
  """
      Both LLM and Nominatim are not perfect with high rank locations (such as streets or new neighbourhoods).
      Maybe in the future we can increase the range.
  """
  return [location for location in locations if location.rank_address >= rank_from and location.rank_address <= rank_to]

async def parse_response(response_str):
  locations = []
  parent_locations = []
  try:
    json_obj = try_parse_json(response_str)
    # while trying to parse the json, we might get a list or a dict depending
    # on the structure of the response
    if isinstance(json_obj, dict):
      json_obj = [json_obj]
    debug(f'Parsed JSON: {json_obj}')
    for obj in json_obj:
      queries = await get_location_queries(obj)
      log(f'Location Queries: {queries}')
      for query in queries:
        results = await search_location(query)
        if not results.empty:
          debug(f'Results for "{query}": {results}')
          geo_location = await geo_location_from_results(results)
          debug(f'Location found for "{query}": {geo_location}')
          locations.extend([geo_location])
          break
        else:
          warn(f'No results found for query: {query}')
    for location in locations:
      parent_loc = await extract_related_locations(location)
      parent_locations.extend(parent_loc)
  except Exception as e:
    error('Error parsing response', e)
    pass
  locations = deduplicate_locations(locations + parent_locations)
  locations = filter_locations_between_rank(locations, 4, 16)
  locations = [location.__dict__ for location in locations]
  return locations
