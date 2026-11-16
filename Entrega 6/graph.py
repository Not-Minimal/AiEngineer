from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents import crear_analista, crear_investigador, crear_sintetizador, crear_supervisor, ejecutar_especialista
from agents.supervisor import enrutar
from state import OrchestratorState


def crear_grafo(llm: BaseChatModel) -> CompiledStateGraph:
    """Topología jerárquica: el supervisor es el único que decide; los especialistas siempre le devuelven el control."""
    grafo = StateGraph(OrchestratorState)
    grafo.add_node("supervisor", crear_supervisor(llm))
    grafo.add_node("investigador", ejecutar_especialista("investigador", crear_investigador(llm)))
    grafo.add_node("analista", ejecutar_especialista("analista", crear_analista(llm)))
    grafo.add_node("sintetizador", crear_sintetizador(llm))

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges("supervisor", enrutar, ["investigador", "analista", "sintetizador"])
    grafo.add_edge("investigador", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_edge("sintetizador", END)
    return grafo.compile()
