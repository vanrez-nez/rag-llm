from base.logger import log
from base.logger import error
from string import Template
from base.json_parse import try_parse_json
from base.services import get_ollama
from entities.location_tags import LocationTags

def build_prompt_country(content):
  t = Template("""
      ```
      $content
      ```
      Del articulo arriba extrae el pais y responde en formato JSON:
      ```
      { "pais": "Nombre de Pais" }
      ```
  """)
  return t.substitute(content=content)

def build_prompt_administrative(content, admin_name, country):
  t = Template("""
      ```
      $content
      ```
      Del articulo arriba extrae el $admin_name de $country y responde en formato JSON:
      ```
      { "$admin_name": "Nombre de $admin_name" }
      ```
  """)
  return t.substitute(content=content, admin_name=admin_name, country=country)

async def geo_tag_content(content: str) -> LocationTags:
  try:
    model = get_ollama()
    prompt = build_prompt_country(content)
    response = model.invoke(prompt)
    country_json = try_parse_json(response)
    prompt = build_prompt_administrative(content, 'estado', 'Mexico')
    response = model.invoke(prompt)
    state_json = try_parse_json(response)
    return LocationTags([country_json, state_json])
  except Exception as e:
    error(e)
    return {}