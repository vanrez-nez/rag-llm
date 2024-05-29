import json
import re
import sys
from base.request import get_url
from base.logger import log
"""
  Get Countries with area codes:
  https://overpass-turbo.eu/#

  [out:csv(::id, "name:es", "wikipedia")];
  area["admin_level"="2"][boundary=administrative][type!=multilinestring];
  out;
"""
API_URL = 'https://overpass-api.de/api/interpreter'
MEXICO_AREA_CODE = 3600114686
ADMIN_LEVEL_COUNTRY = 2
ADMIN_LEVEL_STATE = 4
ADMIN_LEVEL_CITY = 6
PLACE_TYPE_TOWN = 'town'
PLACE_TYPE_VILLAGE = 'village'
PLACE_TYPE_HAMLET = 'hamlet'

async def get_locations_by_place(code_id: str, place: str):
  """ See https://wiki.openstreetmap.org/wiki/Key:place for place types."""
  data = f"""
    [out:json];
    area({code_id})->.searchArea;
    node(area.searchArea)["place"="{place}"];
    out;
  """
  req_url = f"{API_URL}?data={data}"
  content = await get_url(req_url, sys.maxsize, 'json')
  data = json.loads(content)
  elements = []
  for element in data['elements']:
    tags = element.get('tags', {})
    elements.append({
      'id': element.get('id'),
      'lat': element.get('lat'),
      'lon': element.get('lon'),
      'name': tags.get('name', ''),
      'wikidata': tags.get('wikidata', '')
    })
  return elements

async def get_locations_by_admin_level(code_id: int, admin_level: int):
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
    wikipedia = tags.get('wikipedia', '')
    # removes es:, en:, etc prefix
    slug = wikipedia.split(':')[-1].replace(' ', '_')
    # if slug contains commas invalidate the whole slug
    if ',' in slug:
      slug = ''
    elements.append({
      'id': element.get('id'),
      'name': tags.get('name', ''),
      'wikidata': tags.get('wikidata', ''),
      'wikipedia': wikipedia,
      'slug': slug,
    })
  return elements