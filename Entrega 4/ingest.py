import tiktoken
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DATA_DIR,
    EMBEDDING_MODEL,
    INDEX_NAME,
    NAMESPACE,
    PINECONE_API_KEY,
)

tokenizer = tiktoken.get_encoding("cl100k_base")


def contar_tokens(texto: str) -> int:
    return len(tokenizer.encode(texto))


splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=contar_tokens,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def get_vector_store() -> PineconeVectorStore:
    """Indexación y consulta usan esta función, y por lo tanto el mismo modelo de embeddings."""
    return PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        namespace=NAMESPACE,
        pinecone_api_key=PINECONE_API_KEY,
    )


def load_chunks() -> list[Document]:
    """Fragmenta los archivos de data/. La ingesta y BM25 parten de estos mismos fragmentos."""
    chunks = []
    for ruta in sorted(DATA_DIR.rglob("*.md")):
        source = ruta.relative_to(DATA_DIR).as_posix()
        for i, texto in enumerate(splitter.split_text(ruta.read_text(encoding="utf-8"))):
            chunks.append(
                Document(
                    page_content=texto,
                    metadata={
                        "source": source,
                        "category": ruta.parent.name,
                        "page": 1,
                        "chunk_index": i,
                    },
                )
            )
    return chunks


def ingest_documents() -> None:
    """Sube los fragmentos a Pinecone en lotes."""
    chunks = load_chunks()
    ids = [f"{c.metadata['source']}-{c.metadata['chunk_index']}" for c in chunks]
    get_vector_store().add_documents(chunks, ids=ids, batch_size=100)
    print(f"Enviados {len(chunks)} fragmentos al namespace {NAMESPACE}.")

    # Las estadísticas pueden tardar unos segundos en reflejar la carga.
    stats = Pinecone(api_key=PINECONE_API_KEY).Index(INDEX_NAME).describe_index_stats()
    print(stats)


if __name__ == "__main__":
    ingest_documents()
