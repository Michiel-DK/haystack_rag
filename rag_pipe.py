import os
import warnings

warnings.filterwarnings('ignore')

from haystack import Pipeline
from haystack.utils.auth import Secret
from haystack.components.builders import PromptBuilder
from haystack.components.converters import HTMLToDocument
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore

from haystack_integrations.components.embedders.cohere import CohereDocumentEmbedder, CohereTextEmbedder

from haystack_integrations.components.generators.ollama import OllamaGenerator


def setup_pipe():
    
    document_store = InMemoryDocumentStore()

    fetcher = LinkContentFetcher()
    converter = HTMLToDocument()
    embedder = CohereDocumentEmbedder(model="embed-english-v3.0", api_base_url=os.getenv("CO_API_URL"))
    writer = DocumentWriter(document_store=document_store)

    indexing = Pipeline()
    indexing.add_component("fetcher", fetcher)
    indexing.add_component("converter", converter)
    indexing.add_component("embedder", embedder)
    indexing.add_component("writer", writer)

    indexing.connect("fetcher.streams", "converter.sources")
    indexing.connect("converter", "embedder")
    indexing.connect("embedder", "writer")
    
    indexing.run(
    {
        "fetcher": {
            "urls": [
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-01",
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-02",
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-03",
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-04",
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-05",
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-06",
                "https://www.bikeraceinfo.com/stageraces/ParisNice/2024-paris-nice.html#stage-07",
                
            ]
        }
    }
)
    
    prompt = """
        Answer the question based on the provided context.
        Context:
        {% for doc in documents %}
        {{ doc.content }} 
        {% endfor %}
        Question: {{ query }}
        """
        
    query_embedder = CohereTextEmbedder(model="embed-english-v3.0", api_base_url=os.getenv("CO_API_URL"))
    retriever = InMemoryEmbeddingRetriever(document_store=document_store)
    prompt_builder = PromptBuilder(template=prompt)
    
    generator = OllamaGenerator(model="llama3.1:latest",
                            url = "http://localhost:11434",
                            generation_kwargs={
                              #"num_predict": 100,
                             # "temperature": 0.9,
                              })

    rag = Pipeline()
    rag.add_component("query_embedder", query_embedder)
    rag.add_component("retriever", retriever)
    rag.add_component("prompt", prompt_builder)
    rag.add_component("generator", generator)

    rag.connect("query_embedder.embedding", "retriever.query_embedding")
    rag.connect("retriever.documents", "prompt.documents")
    rag.connect("prompt", "generator")
    
    question = "Who performed the best in the last races?"

    result = rag.run(
        {
            "query_embedder": {"text": question},
            "retriever": {"top_k": 10},
            "prompt": {"query": question},
        }
    )

    print(result["generator"]["replies"][0])
    
if __name__ == '__main__':
    setup_pipe()