import os
import json
from base.logger import debug
from base.request import get_url
from base.json_search import JSONSearch

NOMINATIM_PORT = os.environ.get("NOMINATIM", "8080")
NOMINATIM_REVERSE_URL = 'http://nominatim:{port}/reverse?lat={lat}&lon={lon}&format=json'
NOMINATIM_SEARCH_URL = 'http://nominatim:{port}/search?q={query}&addressdetails=1&limit=1'
NOMINATIM_SEARCH_PARAMS_URL = 'http://nominatim:{port}/search?{params}&format=json&limit=1'
NOMINATIM_DETAILS_URL = 'http://nominatim:{port}/details?place_id={place_id}&addressdetails=1&format=json'
NOMINATIM_LOOKUP_URL = 'http://nominatim:{port}/lookup?osm_ids={osm_ids}&format=json'

def unwrap_single_result(content: str) -> str:
  json_content = json.loads(content)
  if len(json_content) == 1:
    content = json.dumps(json_content[0])
  return content

async def reverse_lookup(lat, lon) -> dict:
  """ Makes a reverse lookup using nomatim for a given latitude and longitude. """
  url = NOMINATIM_REVERSE_URL.format(port=NOMINATIM_PORT, lat=lat, lon=lon)
  content = await get_url(url)
  return json.loads(content)

async def address_lookup(osm_id) -> JSONSearch:
  """ Searches an address by osm_id. """
  url = NOMINATIM_LOOKUP_URL.format(port=NOMINATIM_PORT, osm_ids=osm_id)
  content = await get_url(url)
  content = unwrap_single_result(content)
  debug(f"@address_lookup(osm_id={osm_id}) -> {content}")
  return JSONSearch(content)

async def search_location(query) -> JSONSearch:
  """ Searches a location by name. """
  url = NOMINATIM_SEARCH_URL.format(port=NOMINATIM_PORT, query=query)
  content = await get_url(url)
  content = unwrap_single_result(content)
  debug(f"@search_location(query={query}) -> {content}")
  return JSONSearch(content)

async def search_location_details(location_id) -> JSONSearch:
  url = NOMINATIM_DETAILS_URL.format(port=NOMINATIM_PORT, place_id=location_id)
  content = await get_url(url)
  content = unwrap_single_result(content)
  debug(f"@search_location_details(location_id={location_id}) -> {content}")
  return JSONSearch(content)

async def search_location_params(params) -> JSONSearch:
  """ Searches a location by params. """
  # remove empty params
  params = {k: v for k, v in params.items() if v}
  # merge params dict as URL params key=value and merge them with &
  params = '&'.join([f'{k}={v}' for k, v in params.items()])
  url = NOMINATIM_SEARCH_PARAMS_URL.format(port=NOMINATIM_PORT, params=params)
  content = await get_url(url)
  content = unwrap_single_result(content)
  debug(f"@search_location_params(params={params}) -> {content}")
  return JSONSearch(content)
