from collections.abc import Callable, Coroutine
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from config import RECURSION_LIMIT_ESPECIALISTA
from state import Especialista, OrchestratorState


def formatear_contribuciones(state: OrchestratorState, agente: Especialista | None = None) -> str:
    contribuciones = [c for c in state["contribuciones"] if agente is None or c["agente"] == agente]
    if not contribuciones:
        return "(sin contribuciones todavía)"
    return "\n\n".join(
        f"[Paso {c['paso']} · {c['agente']}] Instrucción: {c['instruccion']}\n{c['contenido']}"
        for c in contribuciones
    )


def ejecutar_especialista(
    nombre: Especialista, agente: CompiledStateGraph
) -> Callable[[OrchestratorState], Coroutine[Any, Any, dict[str, Any]]]:
    """Envuelve un agente ReAct como nodo del grafo padre.

    Para evitar la contaminación de contexto, el especialista NO recibe el historial
    completo: solo la solicitud original, la instrucción del supervisor y, si es el
    analista, los hechos que aportó el investigador. Su respuesta vuelve al estado
    como una Contribucion.
    """

    async def nodo(state: OrchestratorState) -> dict[str, Any]:
        solicitud = next(m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
        # La solicitud va siempre: sin ella, una instrucción vaga o vacía deja al especialista adivinando.
        tarea = f"SOLICITUD ORIGINAL DEL USUARIO:\n{solicitud}\n\nTU TAREA:\n{state['instruccion'] or 'Resuelve tu parte de la solicitud.'}"
        if nombre == "analista":
            tarea += "\n\nHECHOS DEL INVESTIGADOR:\n" + formatear_contribuciones(state, "investigador")

        resultado = await agente.ainvoke(
            {"messages": [HumanMessage(tarea)]},
            config={"recursion_limit": RECURSION_LIMIT_ESPECIALISTA},
        )
        mensajes = resultado["messages"]
        contenido = mensajes[-1].content
        herramientas = [m.name for m in mensajes if isinstance(m, ToolMessage)]

        return {
            "contribuciones": [
                {
                    "paso": state["pasos"],
                    "agente": nombre,
                    "instruccion": state["instruccion"],
                    "contenido": contenido,
                    "herramientas": herramientas,
                }
            ],
            "messages": [AIMessage(contenido, name=nombre)],
        }

    return nodo
