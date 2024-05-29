import os
import json
from base.logger import log
from base.request import get_url
from scraper.overpass_provider import get_locations_by_place
from scraper.overpass_provider import MEXICO_AREA_CODE
from scraper.overpass_provider import PLACE_TYPE_TOWN
from scraper.overpass_provider import PLACE_TYPE_VILLAGE
from scraper.overpass_provider import PLACE_TYPE_HAMLET
from scraper.location import Location

NOMINATIM_PORT = os.environ.get("NOMINATIM", "8080")
NOMINATIM_REVERSE_URL = 'http://nominatim:{port}/reverse?lat={lat}&lon={lon}&format=json'
NOMINATIM_SEARCH_URL = 'http://nominatim:{port}/search?q={query}&format=json&addressdetails=1&limit=1'
NOMINATIM_SEARCH_PARAMS_URL = 'http://nominatim:{port}/search?{params}&addressdetails=1&format=json&limit=1'

async def reverse_lookup(lat, lon):
  """ Makes a reverse lookup using nomatim for a given latitude and longitude. """
  url = NOMINATIM_REVERSE_URL.format(port=NOMINATIM_PORT, lat=lat, lon=lon)
  content = await get_url(url)
  json_content = json.loads(content)
  return json_content

async def search_location(query):
  """ Searches a location by name. """
  url = NOMINATIM_SEARCH_URL.format(port=NOMINATIM_PORT, query=query)
  content = await get_url(url)
  json_content = json.loads(content)
  return json_content

async def search_location_params(params):
  """ Searches a location by params. """
  # merge params dict as URL params key=value and merge them with &
  params = '&'.join([f'{k}={v}' for k, v in params.items()])
  url = NOMINATIM_SEARCH_PARAMS_URL.format(port=NOMINATIM_PORT, params=params)
  content = await get_url(url)
  json_content = json.loads(content)
  return json_content

async def get_locations():
  villages = await get_locations_by_place(MEXICO_AREA_CODE, PLACE_TYPE_VILLAGE)
  towns = await get_locations_by_place(MEXICO_AREA_CODE, PLACE_TYPE_TOWN)
  hamlets = await get_locations_by_place(MEXICO_AREA_CODE, PLACE_TYPE_HAMLET)
  locations = towns + villages + hamlets
  # locations = locations[:50]
  result = []
  for location in locations:
    lat = location.get('lat')
    lon = location.get('lon')
    lookup = await reverse_lookup(lat, lon)
    address = lookup.get('address', [])
    result.append(Location(fields={
      'id': location.get('id'),
      'title': location.get('name'),
      'description': location.get('description', ''),
      'name': location.get('name', ''),
      'country': address.get('country', ''),
      'state': address.get('state', ''),
      'municipality': address.get('county', ''),
      'city': address.get('city', ''),
      'village': address.get('village', ''),
      'hamlet': address.get('hamlet', ''),
      'town': address.get('town', ''),
      'lat': lat,
      'lon': lon
    }))
  return result