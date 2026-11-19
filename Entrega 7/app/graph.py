from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from redis import asyncio as aioredis

from app.agents import crear_analista, crear_investigador, crear_sintetizador, crear_supervisor, ejecutar_especialista
from app.agents.supervisor import enrutar
from app.hitl import aprobacion_humana, crear_nodo_entrega
from app.state import OrchestratorState


def crear_grafo(llm: BaseChatModel, checkpointer: BaseCheckpointSaver, redis: aioredis.Redis) -> CompiledStateGraph:
    """El orquestador jerárquico del Módulo 6, más la revisión humana antes de entregar.

    supervisor ⇄ especialistas → sintetizador → aprobacion_humana → entregar
    El checkpointer (AsyncRedisSaver) guarda el estado después de cada nodo, bajo el
    thread_id del job: es lo que permite pausar en aprobacion_humana y reanudar horas
    después, incluso en otro proceso del worker.
    """
    grafo = StateGraph(OrchestratorState)
    grafo.add_node("supervisor", crear_supervisor(llm))
    grafo.add_node("investigador", ejecutar_especialista("investigador", crear_investigador(llm)))
    grafo.add_node("analista", ejecutar_especialista("analista", crear_analista(llm)))
    grafo.add_node("sintetizador", crear_sintetizador(llm))
    grafo.add_node("aprobacion_humana", aprobacion_humana)
    grafo.add_node("entregar", crear_nodo_entrega(redis))

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges("supervisor", enrutar, ["investigador", "analista", "sintetizador"])
    grafo.add_edge("investigador", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_edge("sintetizador", "aprobacion_humana")
    grafo.add_edge("aprobacion_humana", "entregar")
    grafo.add_edge("entregar", END)
    return grafo.compile(checkpointer=checkpointer)
