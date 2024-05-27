from curses import meta
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
    metadata={ "hnsw:space": "cosine" }
  )
  for location in locations:
    log(f"Processing location: {location['title']}")
    geo = location['geo_info']
    borders = f"Fronteras: {geo['borders']}." if geo['borders'] else ''
    aliases = f"Tambien conocido como: {geo['aliases']}." if geo['aliases'] else ""
    collection.upsert(
      documents=[f"{location['title']}: {location['description']}. {aliases} {borders}"],
      metadatas=[{
        'nombre': geo['name'],
        'aliases': geo['aliases'] or '',
        'pais': geo['country'],
        'estado': geo['state'] or '',
        'capital': geo['capital_city'] or '',
        'fronteras': geo['borders'],
        'latitud': geo['lat'] or 0,
        'longitud': geo['lng'] or 0,
        'es_pais': geo['is_country'],
        'es_ciudad': geo['is_city'],
        'es_municipio': geo['is_municipality'],
        'es_estado': geo['is_state'],
        'url': location['url'],
      }],
      ids=[geo['id']]
    )

  log(len(locations))

def test_chroma(query: str):
  client = get_chroma()
  collection = client.get_or_create_collection(
    WIKIS_LOCATIONS_COLLECTION_NAME,
    embedding_function=get_default_embedding_fn(),
    metadata={ "hnsw:space": "cosine"} # l2 is the default
  )

  # results = collection.peek(limit = 10)
  results = collection.query(query_texts=[query], n_results=10, )
  return results