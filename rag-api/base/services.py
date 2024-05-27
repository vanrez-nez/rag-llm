import os
from chromadb import HttpClient
from langchain_community.llms.ollama import Ollama
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pymilvus import MilvusClient

def get_ollama():
  ollama_port = os.environ.get("OLLAMA_PORT")
  return Ollama(base_url=f"http://ollama:{ollama_port}", model='llama3', temperature=0)

def get_milvus():
  milvus_port = os.environ.get("MILVUS_PORT")
  return MilvusClient(uri=f"http://milvus:{milvus_port}")

def get_ollama_embedding_fn():
  ollama_port = os.environ.get("OLLAMA_PORT")
  return OllamaEmbeddingFunction(url=f"http://ollama:{ollama_port}/api/embeddings", model_name='llama3')

def get_default_embedding_fn():
  # Default Models in Chroma https://www.sbert.net/docs/pretrained_models.html
  # paraphrase-multilingual-mpnet-base-v2
  # multi-qa-MiniLM-L6-cos-v1
  return SentenceTransformerEmbeddingFunction(normalize_embeddings=True, model_name='multi-qa-MiniLM-L6-cos-v1')

def get_chroma():
  chroma_port = os.environ.get("CHROMA_PORT")
  return HttpClient("chroma", port=chroma_port)