import os
import json
from base.logger import log
from base.request import get_url
from scraper.overpass_provider import get_locations_by_place
from scraper.overpass_provider import MEXICO_AREA_CODE
from scraper.overpass_provider import PLACE_TYPE_TOWN
from scraper.overpass_provider import PLACE_TYPE_VILLAGE

NOMINATIM_PORT = os.environ.get("NOMINATIM", "8080")
NOMINATIM_PAGE_URL = 'http://nominatim:{port}/reverse?lat={lat}&lon={lon}&format=json'

async def reverse_lookup(lat, lon):
  """ Makes a reverse lookup using nomatim for a given latitude and longitude. """
  url = NOMINATIM_PAGE_URL.format(port=NOMINATIM_PORT, lat=lat, lon=lon)
  content = await get_url(url)
  json_content = json.loads(content)
  return json_content

async def get_locations():
  villages = await get_locations_by_place(MEXICO_AREA_CODE, PLACE_TYPE_VILLAGE)
  towns = await get_locations_by_place(MEXICO_AREA_CODE, PLACE_TYPE_TOWN)
  locations = towns + villages
  result = []
  for location in locations:
    lat = location.get('lat')
    lon = location.get('lon')
    lookup = await reverse_lookup(lat, lon)
    address = lookup.get('address', [])

    result.append({
      'id': location.get('id'),
      'title': location.get('name'),
      'description': location.get('description'),
      'geo_info': {
        'name': location.get('name'),
        'state': address.get('state', None),
        'municipality': address.get('county', None),
        'village': address.get('village', None),
        'city': address.get('city', None),
        'town': address.get('town', address.get('borough', None)),
        'country': address.get('country', None),
        'lat': lat,
        'lng': lon
      }
    })
  return result