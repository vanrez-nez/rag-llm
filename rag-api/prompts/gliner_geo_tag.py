from base.logger import log
from base.logger import warn
from gliner import GLiNER
from entities.location_tags import LocationTags
from base.utils import str_in_text
from base.utils import split_text

Cached_Model = None

LOCATION_LABELS = ["Pais", "Estado", "Municipio", "Ciudad", "Comunidad", "Pueblo", "Colonia", "Sitio"]
OTHER_LABELS = ["Organizacion", "Evento", "Persona", "Cargo"]
# Uses https://github.com/urchade/GLiNER to label locations in the text using a NER Model

async def geo_tag_content(content: str) -> LocationTags:
  chunks = split_text(content, 1500)
  log(f"Split text into {len(chunks)} chunks")
  tags = []
  for chunk in chunks:
    log(f"Extracting Locations from chunk: {chunk}")
    ner_locations = extract_locations_from_ner(chunk)
    tags += ner_locations
  return LocationTags(tags)

def extract_locations_from_ner(response_str):
  locations = []
  model = get_gliner_model()
  labels = LOCATION_LABELS + OTHER_LABELS
  entities = model.predict_entities(response_str, labels, threshold=0.4)
  for entity in entities:
    if entity['label'] in OTHER_LABELS:
      continue
    # NER will sometimes put the type of location in the text. We ignore it.
    if (entity['text'].lower() in ['municipio', 'ciudad', 'estado']):
      continue
    if str_in_text(entity['text'], response_str) > 0:
      locations.append({ entity["label"]: entity["text"] })
    else:
      warn(f"Ignoring NER label/value: {entity['label']}:\"{entity['text']}\" not found in text")
  log(f"Extracted Locations from NER: {locations}")
  return locations

def get_gliner_model():
  global Cached_Model
  if not Cached_Model:
    Cached_Model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
    Cached_Model.eval()
  return Cached_Model