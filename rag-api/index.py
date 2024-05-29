from flask import Flask
from flask import json
from flask import request
from flask import Response
from base.logger import log
from base.profile import profile_function
from server_process import kill_previous_instance
from langchain_community.retrievers import WikipediaRetriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from base.services import get_ollama
from prompts.article_geo_location import build_prompt as article_geo_location_prompt
from prompts.article_geo_location import parse_response as parse_geo_location_response
from database import query_location
from database import import_locations

# TODO: maybe use https://github.com/openvenues/libpostal
# read more @ https://medium.com/@albarrentine/statistical-nlp-on-openstreetmap-b9d573e6cc86

app = Flask(__name__)

@profile_function
def load_wikipedia_llm():
  retriever = WikipediaRetriever(
    lang="es",
    load_max_docs=1,
    top_k_results=1,
    doc_content_chars_max=4000
  )
  # docs = retriever.invoke('Morelia, Michoacan, Mexico')
  # log(docs)
  qa_system_prompt = """Eres un buscador de informacion publica que responde preguntas. \
  Si no sabes la respuesta, no la inventes. \
  Responde solamente con la informacion requerida.\
  No agregues saludos, preguntas o resumenes.
  Manten la respuesta corta.\
  Responde es ESPAÑOL siempre.\
  {context}"""
  qa_prompt = ChatPromptTemplate.from_messages(
      [
          ("system", qa_system_prompt),
          MessagesPlaceholder("chat_history"),
          ("human", "{input}"),
      ]
  )
  model = get_ollama()
  question_answer_chain = create_stuff_documents_chain(model, qa_prompt)
  wikipedia_chain = create_retrieval_chain(
    retriever,
    question_answer_chain
  )
  return wikipedia_chain

@app.route("/wikipedia_llm", methods=["POST"])
def wikipedia_llm():
  query = request.form.get('query')
  llm = load_wikipedia_llm()
  resp = llm.invoke({ "input": query, "chat_history": [] })
  json_str = json.dumps(resp['answer'], ensure_ascii=False)
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

@app.route("/chroma_llm", methods=["POST"])
def chroma_llm():
  query = request.form.get('query')
  results = query_location(query)
  json_str = json.dumps(results, ensure_ascii=False)
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

@app.route("/geo_locate_article", methods=["POST"])
async def geo_locate_article():
  title = request.form.get('title')
  content = request.form.get('content')
  prompt = article_geo_location_prompt(title, content)
  model = get_ollama()
  resp = model.invoke(prompt)
  log(f"Trying to parse response: {resp}")
  locations = await parse_geo_location_response(resp)
  log(f"Locations parsed: {locations}")
  json_str = json.dumps(locations, ensure_ascii=False)
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

if __name__ == '__main__':
  kill_previous_instance()
  # from scraper.wiki_locations import generate_locations_data
  # loop = asyncio.get_event_loop()
  # loop.run_until_complete(import_locations(True))
  # loop = asyncio.get_event_loop()
  # loop.run_until_complete(import_locations(False))
  app.run(host="0.0.0.0", port=80)
