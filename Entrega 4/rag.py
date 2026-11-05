import re

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from config import TOP_K
from ingest import get_vector_store, load_chunks


def tokenizar(texto: str) -> list[str]:
    return re.findall(r"\w+", texto.lower())


class RAGSystem:
    """Combina búsqueda léxica (BM25) y semántica (Pinecone) con un EnsembleRetriever."""

    def __init__(self) -> None:
        self.bm25 = BM25Retriever.from_documents(
            load_chunks(), preprocess_func=tokenizar, k=TOP_K
        )
        self.vectorial = get_vector_store().as_retriever(search_kwargs={"k": TOP_K})
        self.ensemble = EnsembleRetriever(
            retrievers=[self.bm25, self.vectorial], weights=[0.5, 0.5]
        )

    def retrieve(self, query: str) -> list[Document]:
        return self.ensemble.invoke(query)[:TOP_K]


if __name__ == "__main__":
    rag = RAGSystem()
    for consulta in ["¿Qué es HTTPException?", "¿Cómo ejecuto algo después de responder?"]:
        print(f"\n{consulta}")
        for doc in rag.retrieve(consulta):
            print(f"- {doc.metadata['source']} (fragmento {int(doc.metadata['chunk_index'])})")
