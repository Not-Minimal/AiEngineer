from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register

from app.config import PHOENIX_COLLECTOR_ENDPOINT, PHOENIX_PROJECT_NAME

_instrumentado = False


def init_tracing() -> None:
    """Envía a Arize Phoenix un span por cada nodo del grafo, llamada al LLM y herramienta.

    LangChainInstrumentor engancha los callbacks de LangChain/LangGraph, así que no hace
    falta decorar cada función: supervisor, especialistas, sintetizador y las llamadas a
    OpenAI quedan como spans anidados, con tokens de entrada/salida (Phoenix calcula el
    costo a partir de ellos). La búsqueda en Chroma tiene un span manual en knowledge_base.
    """
    global _instrumentado
    if _instrumentado:
        return
    # batch=True: los spans se exportan en segundo plano y no frenan al agente.
    tracer_provider = register(
        endpoint=PHOENIX_COLLECTOR_ENDPOINT,
        project_name=PHOENIX_PROJECT_NAME,
        batch=True,
        verbose=False,
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    _instrumentado = True
