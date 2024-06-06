from base.logger import log
from base.logger import warn
from gliner import GLiNER
from base.fuzzy_search import FuzzySearch
from providers.overpass_provider import PLACE_TYPE_STATE
from providers.overpass_provider import PLACE_TYPE_CITY
from providers.overpass_provider import PLACE_TYPE_BOROUGH
from providers.overpass_provider import PLACE_TYPE_TOWN
from providers.overpass_provider import PLACE_TYPE_VILLAGE
from providers.overpass_provider import PLACE_TYPE_HAMLET
from location_mapper import get_locations_map
from base.utils import str_in_text

Cached_Model = None

# Uses https://github.com/urchade/GLiNER to label locations in the text using a NER Model

async def extract_locations_from_content(content: str) -> dict:
  ner_locations = extract_locations_from_ner(content)
  ner_labels = [value for d in ner_locations for value in d.values()]
  return await tag_locations(ner_labels)

def extract_locations_from_ner(response_str):
  locations = []
  model = get_gliner_model()
  labels = ["Estado", "Municipio", "Ciudad"]
  entities = model.predict_entities(response_str, labels, threshold=0.4)
  for entity in entities:
    # NER will somethings put the type of location in the text. We ignore it.
    if (entity['text'].lower() in ['municipio', 'ciudad', 'estado']):
      continue
    if str_in_text(entity['text'], response_str) > 0:
      locations.append({ entity["label"]: entity["text"] })
    else:
      warn(f"Ignoring NER label/value: {entity['label']}:\"{entity['text']}\" not found in text")
  log(f"Extracted Locations from NER: {locations}")
  return locations

async def tag_locations(arr: list[str]) -> dict:
  # deduplicate arr
  arr = list(set(arr))
  result = []
  for name in arr:
    name = name.strip().capitalize()
    type = await get_place_type(name)
    log(f"Name: {name} - Type: {type}")
    if type:
      result.append({ type: name })
  return result

async def get_place_type(name: str) -> str|None:
  fuzzy = FuzzySearch()
  loc_map = await get_locations_map()
  keys_order = [
    PLACE_TYPE_STATE,
    PLACE_TYPE_CITY,
    PLACE_TYPE_BOROUGH,
    PLACE_TYPE_TOWN,
    PLACE_TYPE_VILLAGE,
    PLACE_TYPE_HAMLET
  ]
  for type in keys_order:
    fuzzy.add(type, loc_map[type])
  results = fuzzy.search(name)
  if len(results) > 0:
    return results[0]['type']
  else:
    return None

def get_gliner_model():
  global Cached_Model
  if not Cached_Model:
    Cached_Model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
    Cached_Model.eval()
  return Cached_Model