import os
from chromadb import HttpClient
from langchain_community.llms.ollama import Ollama
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

def get_ollama():
  ollama_port = os.environ.get("OLLAMA_PORT")
  return Ollama(base_url=f"http://ollama:{ollama_port}", model='llama3', temperature=0)

def get_ollama_embedding_fn():
  ollama_port = os.environ.get("OLLAMA_PORT")
  return OllamaEmbeddingFunction(url=f"http://ollama:{ollama_port}/api/embeddings", model_name='llama3')

def get_chroma():
  chroma_port = os.environ.get("CHROMA_PORT")
  return HttpClient("chroma", port=chroma_port)