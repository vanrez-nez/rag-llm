import json
import sys
from base.request import get_url
from base.logger import log
from aiofiles import open as aio_open
from providers.overpass_provider import get_locations_by_place
from providers.overpass_provider import get_locations_by_admin_level
from providers.overpass_provider import PLACE_TYPE_BOROUGH
from providers.overpass_provider import PLACE_TYPE_CITY
from providers.overpass_provider import PLACE_TYPE_HAMLET
from providers.overpass_provider import PLACE_TYPE_TOWN
from providers.overpass_provider import PLACE_TYPE_VILLAGE
from providers.overpass_provider import MEXICO_AREA_CODE
from providers.overpass_provider import ADMIN_LEVEL_CITY
from providers.overpass_provider import ADMIN_LEVEL_STATE

CACHE_FILE = 'storage/locations_map.json'

async def get_locations_map() -> dict:
  try:
    async with aio_open(CACHE_FILE, 'r', encoding='utf-8') as file:
      contents = await file.read()
      return json.loads(contents)
  except Exception as e:
    return {}

async def generate_all():
  locs_dict = {}
  for type in [PLACE_TYPE_CITY, PLACE_TYPE_BOROUGH, PLACE_TYPE_TOWN, PLACE_TYPE_VILLAGE, PLACE_TYPE_HAMLET]:
    locs_dict[type] = await get_locations_by_place(MEXICO_AREA_CODE, type)
  for level in [ADMIN_LEVEL_STATE, ADMIN_LEVEL_CITY]:
    levels_to_type = { '4': 'state', '6': 'city' }
    type = levels_to_type[str(level)]
    locs_dict.setdefault(type, [])
    locs_dict[type] += await get_locations_by_admin_level(MEXICO_AREA_CODE, level)
  # deduplicate values on each key
  for key in locs_dict.keys():
    locs_dict[key] = list(set(locs_dict[key]))
  async with aio_open(CACHE_FILE, 'w', encoding='utf-8') as file:
    locs_dict_str = json.dumps(locs_dict, ensure_ascii=False)
    await file.write(locs_dict_str)
