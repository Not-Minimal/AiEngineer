from functools import cache
from threading import Lock

import chromadb
from chromadb.utils import embedding_functions

from config import COLLECTION_NAME, DATA_DIR, TOP_K, VECTORSTORE_DIR

# El ToolNode ejecuta búsquedas paralelas en hilos distintos, y Chroma falla si varios
# hilos crean un PersistentClient a la vez. Se crea una sola vez, protegido por un lock.
_lock = Lock()


def get_collection() -> chromadb.Collection:
    with _lock:
        return _crear_collection()


@cache
def _crear_collection() -> chromadb.Collection:
    """La misma base Chroma de la Entrega 3. Si está vacía, indexa data/ por sección."""
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
    )
    if collection.count() == 0:
        ids, documentos, metadatos = [], [], []
        for ruta in sorted(DATA_DIR.glob("*.md")):
            # Los documentos son cortos: cada sección "## " es un fragmento con sentido propio.
            secciones = ruta.read_text(encoding="utf-8").split("\n## ")
            for i, seccion in enumerate(s.strip() for s in secciones[1:]):
                ids.append(f"{ruta.name}-{i}")
                documentos.append(seccion)
                metadatos.append({"source": ruta.name, "chunk": i})
        collection.upsert(ids=ids, documents=documentos, metadatas=metadatos)
    return collection


def buscar(consulta: str, k: int = TOP_K) -> list[dict[str, str]]:
    resultados = get_collection().query(query_texts=[consulta], n_results=k)
    return [
        {"source": metadato["source"], "texto": documento}
        for documento, metadato in zip(resultados["documents"][0], resultados["metadatas"][0])
    ]


if __name__ == "__main__":
    print(f"Fragmentos indexados: {get_collection().count()}")
    for r in buscar("¿Cuántas órdenes de trabajo registra Tallertrack?"):
        print(f"- [{r['source']}] {r['texto'][:80]}...")
