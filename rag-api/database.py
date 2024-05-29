from base.logger import log
from base.services import get_chroma
# from base.services import get_ollama
# from base.services import get_ollama_embedding_fn
from base.services import get_default_embedding_fn
from scraper.locations import get_wiki_locations
from scraper.locations import get_nominatim_locations

LOCATIONS_COLLECTION_NAME = "geo_locations"

async def import_nominatim_locations(regenerate):
  locations = await get_nominatim_locations(regenerate)
  log(locations[0])
  return []

async def import_locations(regenerate):
  await import_wiki_locations(regenerate)
  # await import_nominatim_locations(regenerate)

async def import_wiki_locations(regenerate):
  locations = await get_wiki_locations(regenerate)
  # locations = locations[:50]
  client = get_chroma()
  client.reset()
  collection = client.get_or_create_collection(
    LOCATIONS_COLLECTION_NAME,
    embedding_function=get_default_embedding_fn(),
    metadata={ "hnsw:space": "l2" }
  )
  for location in locations:
    pass
    # log(f"Processing location: {location.title}")
    # log(location)
    # geo = location['geo_info']
    # aliases = f"Tambien conocido como: {geo['aliases']}." if geo['aliases'] else ""
    # indexable_items = [location.get('title'), geo.get('state'), aliases]
    # # filter out empty values
    # indexable_items = [item for item in indexable_items if item]
    # collection.upsert(
    #   documents=['. '.join(indexable_items)],
    #   metadatas=[{
    #     'description': location.get('description', ''),
    #     'name': geo.get('name', ''),
    #     'aliases': geo.get('aliases', '') or '',
    #     'country': geo.get('country', ''),
    #     'state': geo.get('state', '') or '',
    #     'capital_city': geo.get('capital_city', '') or '',
    #     'borders': geo.get('borders', '') or '',
    #     'lat': geo.get('lat', 0) or 0,
    #     'lng': geo.get('lng', 0) or 0,
    #     'type': geo.get('type', ''),
    #     'url': location.get('url', ''),
    #   }],
    #   ids=[geo['id']]
    # )
  log(f"Locations imported: {len(locations)}")

def format_results(results):
  items = []
  size = len(results['documents'])
  for i in range(size):
    items.append({
      'id': results['ids'][i][0],
      'distance': results['distances'][i][0],
      'document': results['documents'][i][0],
      'metadata': results['metadatas'][i][0]
    })
  return items

def query_location(query: str):
  client = get_chroma()
  collection = client.get_or_create_collection(
    LOCATIONS_COLLECTION_NAME,
    embedding_function=get_default_embedding_fn(),
    metadata={ "hnsw:space": "l2" } # l2 is the default
  )

  results = collection.query(query_texts=[query], n_results=1)
  results = format_results(results)
  # filter results with distance > 0.5
  # results = [result for result in results if result['distance'] < 0.75]

  if len(results) == 0:
    return []

  first = results[0]

  # try extracting its state if it's not one
  if (not first['metadata']['is_state']):
    state_name = first['metadata']['state']
    state = collection.query(query_texts=[state_name], n_results=1, where={'is_state': True})
    results.append(format_results(state))

  return results