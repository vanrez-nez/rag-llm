from flask import Flask
from flask import json
from flask import request
from flask import Response
from base.logger import log
from server_process import kill_previous_instance
from base.services import get_ollama
from prompts.article_geo_location import parse_content as parse_geo_location_content
from prompts.location_mapper import generate_all
# TODO: maybe use https://github.com/openvenues/libpostal
# read more @ https://medium.com/@albarrentine/statistical-nlp-on-openstreetmap-b9d573e6cc86

app = Flask(__name__)

@app.route("/geo_locate_article", methods=["POST"])
async def geo_locate_article():
  title = request.form.get('title')
  content = request.form.get('content')
  default_contry = request.form.get('default_country', None)
  default_state = request.form.get('default_state', None)
  content = "\n".join([title, content])
  locations = await parse_geo_location_content(content, default_state, default_contry)
  log(f"Locations parsed: {locations}")
  json_str = json.dumps(locations, ensure_ascii=False)
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

@app.route("/generate_locations", methods=["POST"])
async def generate_locations():
  await generate_all()
  return Response('ok', content_type='application/json; charset=utf-8')

if __name__ == '__main__':
  kill_previous_instance()
  app.run(host="0.0.0.0", port=80)
