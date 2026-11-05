from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, trim_messages
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools import HERRAMIENTAS

# Mensajes recientes que recibe el LLM. El checkpoint conserva el historial completo.
MAX_MENSAJES = 20

SYSTEM_PROMPT = SystemMessage(
    "Eres un asistente que consulta clientes y pedidos. Responde solo con datos "
    "obtenidos de las herramientas; nunca los inventes. Si una herramienta devuelve "
    "ERROR con una sugerencia, vuelve a intentarlo con el valor sugerido. Si no hay "
    "sugerencia, pide al usuario que aclare el dato."
)


class AgentState(MessagesState):
    """Estado del agente: el historial de mensajes, con el reducer add_messages."""


def crear_grafo(llm: BaseChatModel) -> StateGraph:
    """Define el ciclo ReAct: modelo -> (¿tool_calls?) -> herramientas -> modelo."""
    llm_con_herramientas = llm.bind_tools(HERRAMIENTAS)

    async def nodo_modelo(state: AgentState) -> dict[str, list[Any]]:
        # start_on="human" evita cortar un tool_call separado de su resultado.
        recientes = trim_messages(
            state["messages"],
            strategy="last",
            token_counter=len,
            max_tokens=MAX_MENSAJES,
            start_on="human",
        )
        respuesta = await llm_con_herramientas.ainvoke([SYSTEM_PROMPT, *recientes])
        return {"messages": [respuesta]}

    grafo = StateGraph(AgentState)
    grafo.add_node("modelo", nodo_modelo)
    grafo.add_node("herramientas", ToolNode(HERRAMIENTAS, handle_tool_errors=True))

    grafo.add_edge(START, "modelo")
    grafo.add_conditional_edges(
        "modelo",
        tools_condition,
        {"tools": "herramientas", END: END},
    )
    grafo.add_edge("herramientas", "modelo")  # El ciclo: el modelo observa el resultado.
    return grafo
