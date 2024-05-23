import os
import asyncio
from flask import Flask
from flask import json
from flask import request
from flask import Response
from base.logger import log
from base.profile import profile_function
from server_process import kill_previous_instance
from database import test_chroma
from database import import_wiki_locations
from langchain_community.retrievers import WikipediaRetriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from base.services import get_ollama
from prompts.article_geo_location import build_prompt as article_geo_location_prompt
from prompts.default import build_prompt as default_prompt
app = Flask(__name__)

def get_prompt(prompt_type, *args, **kwargs):
  if prompt_type == 'article_geo_location':
    return article_geo_location_prompt(*args, **kwargs)
  return default_prompt(*args, **kwargs)

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
  results = test_chroma(query)
  # log(results)
  json_str = json.dumps(results, ensure_ascii=False)
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

@app.route("/ollama_llm", methods=["POST"])
def ollama_llm():
  # query = request.form.get('query')
  prompt_vars = {key.replace('prompt_', ''): value for key, value in request.form.items() if key.startswith('prompt_')}
  prompt_vars.pop('type', None)
  prompt = get_prompt(request.form.get('prompt_type'), **prompt_vars)
  model = get_ollama()
  resp = model.invoke(prompt)
  json_str = json.dumps(resp, ensure_ascii=False)
  # json_str = ''
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

if __name__ == '__main__':
  kill_previous_instance()
  # from scraper.wiki_locations import generate_locations_data
  # loop = asyncio.get_event_loop()
  # loop.run_until_complete(generate_locations_data(True))
  # loop = asyncio.get_event_loop()
  # loop.run_until_complete(import_wiki_locations())
  app.run(host="0.0.0.0", port=80)
