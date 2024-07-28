from typing import List, Tuple, Dict
from base.logger import log
from base.utils import str_in_text
from prompts.location_mapper import get_locations_map
from base.fuzzy_search import FuzzySearch
from providers.overpass_provider import PLACE_TYPE_STATE
from providers.overpass_provider import PLACE_TYPE_CITY
from providers.overpass_provider import PLACE_TYPE_BOROUGH
from providers.overpass_provider import PLACE_TYPE_TOWN
from providers.overpass_provider import PLACE_TYPE_VILLAGE
from providers.overpass_provider import PLACE_TYPE_HAMLET
from providers.overpass_provider import PLACE_TYPE_COUNTRY

FuzzyLocations = FuzzySearch()
async def init_fuzzy_search():
  if len(FuzzyLocations.collections) > 0:
    return
  loc_map = await get_locations_map()
  keys_order = [
    PLACE_TYPE_COUNTRY,
    PLACE_TYPE_STATE,
    PLACE_TYPE_CITY,
    PLACE_TYPE_BOROUGH,
    PLACE_TYPE_TOWN,
    PLACE_TYPE_VILLAGE,
    PLACE_TYPE_HAMLET
  ]
  for type in keys_order:
    FuzzyLocations.add(type, loc_map[type])

class LocationTags:
  def __init__(self, tags: List[Dict]) -> None:
    self._tags = tags

  async def get_tags(self) -> List[Dict]:
    values = [tag.values() for tag in self._tags]
    values = [item for sublist in values for item in sublist]
    return await self.tag_locations(values)

  def with_text(self, text: str) -> List[Dict]:
    results = []
    for tag in self._tags:
      if str_in_text(' '.join(tag.values()), text) > 0:
        results += tag
    return results

  async def tag_locations(self, arr: List[str]) -> Dict:
    # deduplicate arr
    arr = list(set(arr))
    result = []
    for name in arr:
      name = name.strip().capitalize()
      type = await self.get_place_type(name)
      log(f"Name: {name} - Type: {type}")
      if type:
        result.append({ type: name })
    return result

  async def get_place_type(self, name: str) -> str|None:
    await init_fuzzy_search()
    results = FuzzyLocations.search(name)
    if len(results) > 0:
      return results[0]['type']
    else:
      return None