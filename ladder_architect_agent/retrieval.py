# retrieval.py
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)

reader = SimpleDirectoryReader("syllabi/")
documents = reader.load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=3)

def retrieve_curriculum(skill: str, query: str) -> list[str]:
    results = query_engine.query(f"{skill}: {query}")
    return [node.text for node in results.source_nodes]
