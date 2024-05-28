from curses import meta
from operator import index
from base.logger import log
from base.services import get_chroma
# from base.services import get_ollama
# from base.services import get_ollama_embedding_fn
from base.services import get_default_embedding_fn
from scraper.wiki_locations import generate_locations_data

WIKIS_LOCATIONS_COLLECTION_NAME = "wiki_locations"

async def import_wiki_locations():
  locations = await generate_locations_data()
  # locations = locations[:50]
  client = get_chroma()
  client.reset()
  collection = client.get_or_create_collection(
    WIKIS_LOCATIONS_COLLECTION_NAME,
    embedding_function=get_default_embedding_fn(),
    metadata={ "hnsw:space": "l2" }
  )
  for location in locations:
    log(f"Processing location: {location['title']}")
    geo = location['geo_info']
    aliases = f"Tambien conocido como: {geo['aliases']}." if geo['aliases'] else ""
    indexable_items = [location['title'], geo['state'], aliases]
    # filter out empty values
    indexable_items = [item for item in indexable_items if item]
    collection.upsert(
      documents=['. '.join(indexable_items)],
      metadatas=[{
        'description': location['description'],
        'name': geo['name'],
        'aliases': geo['aliases'] or '',
        'country': geo['country'],
        'state': geo['state'] or '',
        'capital_city': geo['capital_city'] or '',
        'borders': geo['borders'],
        'latitud': geo['lat'] or 0,
        'longitud': geo['lng'] or 0,
        'is_country': geo['is_country'],
        'is_city': geo['is_city'],
        'is_municipality': geo['is_municipality'],
        'is_state': geo['is_state'],
        'url': location['url'],
      }],
      ids=[geo['id']]
    )

  log(len(locations))

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
    WIKIS_LOCATIONS_COLLECTION_NAME,
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