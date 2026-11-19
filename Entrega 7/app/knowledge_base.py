from functools import cache
from threading import Lock

import chromadb
from chromadb.utils import embedding_functions
from openinference.instrumentation.langchain import get_current_span
from opentelemetry import trace

from app.config import COLLECTION_NAME, DATA_DIR, TOP_K, VECTORSTORE_DIR

# El ToolNode ejecuta búsquedas paralelas en hilos distintos, y Chroma falla si varios
# hilos crean un PersistentClient a la vez. Se crea una sola vez, protegido por un lock.
_lock = Lock()
_tracer = trace.get_tracer(__name__)


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
    # Chroma no tiene instrumentador de OpenInference: sin este span, el tiempo de
    # embedding + búsqueda quedaría escondido dentro del span de la herramienta.
    # El instrumentador de LangChain no marca su span como "actual" en OpenTelemetry,
    # así que el padre (la herramienta que llamó) se toma con get_current_span().
    padre = get_current_span()
    contexto = trace.set_span_in_context(padre) if padre else None
    with _tracer.start_as_current_span("chroma.query", context=contexto) as span:
        span.set_attribute("openinference.span.kind", "RETRIEVER")
        span.set_attribute("input.value", consulta)
        resultados = get_collection().query(query_texts=[consulta], n_results=k)
        documentos = [
            {"source": metadato["source"], "texto": documento, "distancia": distancia}
            for documento, metadato, distancia in zip(
                resultados["documents"][0], resultados["metadatas"][0], resultados["distances"][0]
            )
        ]
        for i, d in enumerate(documentos):
            span.set_attribute(f"retrieval.documents.{i}.document.id", d["source"])
            span.set_attribute(f"retrieval.documents.{i}.document.content", d["texto"])
            span.set_attribute(f"retrieval.documents.{i}.document.score", d["distancia"])
    return documentos


if __name__ == "__main__":
    print(f"Fragmentos indexados: {get_collection().count()}")
    for r in buscar("¿Cuántas órdenes de trabajo registra Tallertrack?"):
        print(f"- [{r['source']}] {r['texto'][:80]}...")
