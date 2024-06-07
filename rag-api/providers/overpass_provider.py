import json
from typing import List, Dict
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
PLACE_TYPE_COUNTRY = 'country'
PLACE_TYPE_STATE = 'state'
PLACE_TYPE_CITY = 'city'
PLACE_TYPE_BOROUGH = 'borough'
PLACE_TYPE_TOWN = 'town'
PLACE_TYPE_VILLAGE = 'village'
PLACE_TYPE_HAMLET = 'hamlet'

def get_place_ranks() -> List[Dict]:
  """ See
      https://nominatim.org/release-docs/develop/customize/Ranking/#search-rank
      https://nominatim.org/release-docs/develop/api/Output/#addressdetails
  """
  return [
    { 'rank_from': 1, 'rank_to': 3, 'values': ['continent', 'ocean'] },
    { 'rank_from': 4, 'rank_to': 4, 'values': ['country'] },
    { 'rank_from': 5, 'rank_to': 9, 'values': ['state', 'region', 'province'] },
    { 'rank_from': 10, 'rank_to': 12, 'values': ['county'] },
    { 'rank_from': 13, 'rank_to': 16, 'values': ['city', 'municipality', 'island'] },
    { 'rank_from': 17, 'rank_to': 18, 'values': ['town', 'borough'] },
    { 'rank_from': 19, 'rank_to': 19, 'values': ['village', 'suburb'] },
    { 'rank_from': 20, 'rank_to': 20, 'values': ['hamlet', 'farm', 'neighbourhood'] },
    { 'rank_from': 21, 'rank_to': 25, 'values': ['isolated_dwelling', 'city_block'] }
  ]

def all_rank_place_types(reversed: bool = False) -> List[str]:
  ranks = get_place_ranks()
  if reversed:
    ranks.reverse()
  return [place for rank in ranks for place in rank['values']]

def is_type_rank_greater_than(place_left: str, place_right: str) -> bool:
  ranks = get_place_ranks()
  rank_left = next((rank for rank in ranks if place_left in rank['values']), None)
  rank_right = next((rank for rank in ranks if place_right in rank['values']), None)
  if not rank_left or not rank_right:
    return False
  return rank_left['rank_from'] > rank_right['rank_from']

def get_ranked_place_types(rank_from: int, rank_to: int) -> List[str]:
  ranks = get_place_ranks()
  result = []
  for rank in ranks:
    if rank['rank_from'] >= rank_from and rank['rank_to'] <= rank_to:
      result += rank['values']
  return result

def higher_ranked_place_types(place_type: str) -> List[str]:
  ranks = get_place_ranks()
  place_rank = next((rank for rank in ranks if place_type in rank['values']), None)
  if not place_rank:
    return []
  return get_ranked_place_types(0, place_rank['rank_from'] - 1)

def lower_ranked_place_types(place_type: str) -> List[str]:
  ranks = get_place_ranks()
  place_rank = next((rank for rank in ranks if place_type in rank['values']), None)
  if not place_rank:
    return []
  return get_ranked_place_types(place_rank['rank_to'] + 1, sys.maxsize)

async def get_locations_by_place(code_id: str, place: str) -> List[str]:
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
    elements.append(tags.get('name', ''))
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
    elements.append(tags.get('name', ''))
  return elements