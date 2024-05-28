### RAG-LLM

## Projects components:
- [Chroma](https://github.com/chroma-core/chroma) as Embedding Database (chroma)
- [LangChain](https://www.langchain.com/) as Builder (container: rag-api)
- [Ollama](https://ollama.com/) as the LLM Model Loader (container: ollama)
- [Nominatim](https://nominatim.org/) as the Geocoder (container: nominatim)

## Setup
Install docker and run:
```bash
docker compose up
```

Then pull the Ollama models:
```bash
chmod +x pull-models.sh && ./pull-models.sh
```

## Explore de API
The `rag-api` container is the one serving the API endpoint meant to be consumed externally. Additionally, the Chroma remote service is being forwarded too.
