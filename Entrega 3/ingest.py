from pathlib import Path

import chromadb
import tiktoken
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = Path("data")
VECTORSTORE_DIR = "vectorstore"
COLLECTION_NAME = "knowledge_base"

tokenizer = tiktoken.get_encoding("cl100k_base")


def contar_tokens(texto: str) -> int:
    return len(tokenizer.encode(texto))


splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=contar_tokens,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def get_collection():
    """Indexación y consulta usan esta función, y por lo tanto el mismo modelo de embeddings."""
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )


def ingest_documents():
    """Fragmenta los archivos de data/ y los guarda, salvo que la colección ya tenga datos."""
    collection = get_collection()
    if collection.count() > 0:
        print(
            f"Base ya indexada: {collection.count()} fragmentos. Se omite la ingesta."
        )
        return collection

        return collection

    ids, documentos, metadatos = [], [], []
    rutas = sorted(list(DATA_DIR.glob("*.md")) + list(DATA_DIR.glob("*.txt")))
    for ruta in rutas:
        for i, chunk in enumerate(
            splitter.split_text(ruta.read_text(encoding="utf-8"))
        ):
            ids.append(f"{ruta.name}-{i}")
            documentos.append(chunk)
            metadatos.append({"source": ruta.name, "chunk": i})

    collection.upsert(ids=ids, documents=documentos, metadatas=metadatos)
    print(f"Indexados {len(ids)} fragmentos de {len(rutas)} archivos.")
    return collection


if __name__ == "__main__":
    ingest_documents()
