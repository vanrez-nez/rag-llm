from curses import meta
from base.logger import log
from base.services import get_chroma
from base.services import get_ollama
from base.services import get_ollama_embedding_fn
from scraper.wiki_locations import generate_locations_data

WIKIS_COLLECTION_NAME = "wiki_locations"

async def import_wiki_locations():
  locations = await generate_locations_data()
  client = get_chroma()
  collection = client.get_or_create_collection(WIKIS_COLLECTION_NAME)
  for location in locations:
    log(f"Processing location: {location['title']}")
    geo = location['geo_info']
    collection.upsert(
      documents=[f"{location['title']}: {location['description']}"],
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
  chroma_client = get_chroma()
  # ollama_client = get_ollama()
  # ollama_client("Hola, soy un bot de prueba. ¿En qué puedo ayudarte hoy?")
  # embed_fn = get_ollama_embedding_fn()
  # chroma_client.delete_collection("news")
  # chroma_client.reset()
  # collection = chroma_client.create_collection(
  #   "news",
  #   embedding_function=embed_fn,
  #   # metadata={"hnsw:space": "ip"} # l2 is the default
  # )
  collection = chroma_client.get_or_create_collection(WIKIS_COLLECTION_NAME)
  # results = collection.peek(limit = 10)
  results = collection.query(query_texts=[query], n_results=10)
  return results