from email.policy import default
import json
from aiopath import AsyncPath
from aiofiles import open as aio_open
from scraper.wiki_provider import get_wiki_pages, scrape_wiki_pages
from scraper.nominatim_provider import get_locations as get_nomi_locations
from scraper.location import Location
# from base.utils import fix_punctuation_spaces
from base.logger import log
from base.logger import warn
from base.logger import error
from base.utils import replace_unicode_escapes

WIKI_LOCATIONS_FILE = 'storage/wiki_locations.json'
NOMINATIM_LOCATIONS_FILE = 'storage/nominatim_locations.json'

async def get_from_cache(path: str):
  path = AsyncPath(path)
  if not await path.exists():
    return None
  async with aio_open(path, 'r', encoding='utf-8') as f:
    data = json.loads(await f.read())
    data = [Location(fields=entry) for entry in data]
    return data

async def write_to_cache(path: str, data: dict):
  # write to json file using aiofiles
  async with aio_open(path, 'w', encoding='utf-8') as f:
    # entries object to json string
    data = [entry.__dict__ for entry in data]
    json_contents = replace_unicode_escapes(json.dumps(data))
    json_contents = json_contents
    await f.write(json_contents)
  log(f"Locations data generated in {path} with {len(data)} entries")

async def get_wiki_locations(force_generation=False):
  # return from cache if a previous generation exists
  if not force_generation:
    wiki_locations = await get_from_cache(WIKI_LOCATIONS_FILE)
    if wiki_locations:
      return wiki_locations
  pages = await get_wiki_pages()
  entries =  await scrape_wiki_pages(pages)
  await write_to_cache(WIKI_LOCATIONS_FILE, entries)
  return entries

async def get_nominatim_locations(force_generation=False):
  # return from cache if a previous generation exists
  if not force_generation:
    nominatim_locations = await get_from_cache(NOMINATIM_LOCATIONS_FILE)
    if nominatim_locations:
      return nominatim_locations
  locations = await get_nomi_locations()
  await write_to_cache(NOMINATIM_LOCATIONS_FILE, locations)
  return locations