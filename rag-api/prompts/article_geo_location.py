import json
from operator import le
from string import Template
from base.json_parse import try_parse_json
from base.logger import log
from scraper.nominatim_provider import search_location, search_location_params
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

def map_location_from_results(results):
  try:
    _json = JSONSearch(json.dumps(results))
    return {
      'id': _json.search('[0].place_id'),
      'country': _json.search('[0].address.country'),
      'city': _json.search('[0].address.city'),
      'state': _json.search('[0].address.state'),
      'state_district': _json.search('[0].address.state_district'),
      'county': _json.search('[0].address.county'),
      'town': _json.search('[0].address.town'),
      'lat': _json.search('[0].lat'),
      'lon': _json.search('[0].lon'),
    }
  except Exception as e:
    log('Error mapping location', e)
    return None

async def is_state_relation_valid(state, relation):
  if not state or not relation:
    return False
  results = await search_location_params({ 'state': state, 'city': relation })
  if len(results) == 0:
    results = await search_location_params({ 'state': state, 'county': relation })
  return len(results) > 0

def comma_join(values):
  return ', '.join([v for v in values if v])

async def get_location_queries(obj):
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
    if location not in unique_locations:
      unique_locations.append(location)
  return unique_locations

async def parse_response(response_str):
  locations = []
  try:
    json_obj = try_parse_json(response_str)
    # while trying to parse the json, we might get a list or a dict depending
    # on the structure of the response
    if isinstance(json_obj, dict):
      json_obj = [json_obj]
    log(f'Parsed JSON: {json_obj}')
    for obj in json_obj:
      queries = await get_location_queries(obj)
      log(f'Location Queries: {queries}')
      for query in queries:
        results = await search_location(query)
        log(f'Results for "{query}": {results}')
        if len(results) > 0:
          location = map_location_from_results(results)
          locations.append(location)
          break
      if not locations:
        log(f'No results found for query: {query}')
  except Exception as e:
    log('Error parsing response', e)
    pass
  return deduplicate_locations(locations)
