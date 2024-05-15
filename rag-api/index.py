import os
from flask import Flask
from flask import json
from flask import request
from flask import Response
from base.logger import log
from server_process import create_lock_file
from server_process import kill_previous_instance

from langchain_community.retrievers import WikipediaRetriever
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_community.llms import Ollama


app = Flask(__name__)

retriever = WikipediaRetriever(lang="es", load_max_docs=10)
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

ollama_port = os.environ.get("OLLAMA_PORT")
model = Ollama(base_url=f"http://ollama:{ollama_port}", model='llama3')
question_answer_chain = create_stuff_documents_chain(model, qa_prompt)
qa = create_retrieval_chain(
  retriever,
  question_answer_chain
)

@app.route("/wikipedia_llm", methods=["POST"])
def wikipedia_llm():
  query = request.form.get('query')
  resp = qa.invoke({ "input": query, "chat_history": [] })
  json_str = json.dumps(resp['answer'], ensure_ascii=False)
  response = Response(json_str, content_type='application/json; charset=utf-8')
  return response

if __name__ == '__main__':
  kill_previous_instance()
  create_lock_file(os.getpid())
  app.run(host="0.0.0.0", port=80)
