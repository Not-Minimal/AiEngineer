from collections.abc import Callable, Coroutine
from typing import Any, Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agents.specialist import formatear_contribuciones
from config import MAX_PASOS
from state import OrchestratorState

PROMPT_SUPERVISOR = """Eres el SUPERVISOR de un equipo de análisis e investigación.
Dada la solicitud del usuario y las contribuciones registradas, decide quién interviene ahora
o si es momento de finalizar.

Especialistas:
- investigador: busca hechos y cifras en la base de conocimiento. No calcula.
- analista: hace cálculos y análisis SOLO con los hechos del investigador. No busca.

Flujo esperado: primero investigador, luego analista (si la solicitud pide cálculos o análisis),
y FINISH cuando la rúbrica se cumple.

RÚBRICA DE VALIDACIÓN (revísala antes de elegir FINISH):
1. Cobertura: cada parte de la solicitud tiene un hecho con fuente o un cálculo que responde
   EXACTAMENTE lo pedido (por ejemplo, si se pide "por taller", un cálculo "por orden" no sirve).
2. Trazabilidad: cada cifra que usa el analista aparece en los hechos del investigador.
3. Cálculos: el analista mostró las operaciones hechas con herramientas, no solo resultados.
4. Honestidad: los datos que no existen están marcados como NO ENCONTRADO y no se inventaron.

Si un criterio falla y el especialista responsable puede corregirlo, devuélvele la tarea con una
instrucción concreta de qué refinar. Si el investigador ya marcó un dato como NO ENCONTRADO,
volver a buscarlo no sirve: elige FINISH y la síntesis lo informará.
La instruccion debe ser autocontenida: el especialista no ve la conversación, solo lo que escribas.
"""


class DecisionSupervisor(BaseModel):
    siguiente: Literal["investigador", "analista", "FINISH"]
    instruccion: str = Field(
        description="Obligatoria si eliges un especialista: qué buscar o calcular, con los datos concretos. Vacía si FINISH."
    )
    razon: str = Field(description="Por qué eliges esta opción, citando el criterio de la rúbrica si aplica.")


PROMPT_SINTESIS = (
    "Eres el SINTETIZADOR. Redacta la respuesta final al usuario en español usando solo las "
    "contribuciones del equipo. Incluye las cifras con su fuente y los resultados del analista. "
    "Si algún dato quedó como NO ENCONTRADO, dilo claramente. No agregues información propia."
)


def crear_supervisor(llm: BaseChatModel) -> Callable[[OrchestratorState], Coroutine[Any, Any, dict[str, Any]]]:
    decisor = llm.with_structured_output(DecisionSupervisor)

    async def supervisor(state: OrchestratorState) -> dict[str, Any]:
        pasos = state.get("pasos", 0) + 1
        solicitud = next(m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage))

        # El supervisor ve la solicitud y las contribuciones, no los mensajes internos de herramientas.
        decision = await decisor.ainvoke(
            [
                SystemMessage(PROMPT_SUPERVISOR),
                HumanMessage(
                    f"SOLICITUD DEL USUARIO:\n{solicitud}\n\n"
                    f"CONTRIBUCIONES REGISTRADAS:\n{formatear_contribuciones(state)}\n\n"
                    f"Decisión {pasos} de {MAX_PASOS}."
                ),
            ]
        )
        return {
            "pasos": pasos,
            "next_agent": decision.siguiente,
            "instruccion": decision.instruccion,
            "task_completed": decision.siguiente == "FINISH",
            "messages": [AIMessage(f"[{decision.siguiente}] {decision.razon}", name="supervisor")],
        }

    return supervisor


def enrutar(state: OrchestratorState) -> Literal["investigador", "analista", "sintetizador"]:
    """Arista condicional. Además de la decisión del modelo, aplica una parada dura por pasos."""
    if state["task_completed"] or state["pasos"] >= MAX_PASOS:
        return "sintetizador"
    return state["next_agent"]


def crear_sintetizador(llm: BaseChatModel) -> Callable[[OrchestratorState], Coroutine[Any, Any, dict[str, Any]]]:
    async def sintetizador(state: OrchestratorState) -> dict[str, Any]:
        solicitud = next(m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
        aviso = ""
        if not state["task_completed"]:
            aviso = f"\n\nNOTA: se alcanzó el límite de {MAX_PASOS} decisiones sin validar la rúbrica completa."
        respuesta = await llm.ainvoke(
            [
                SystemMessage(PROMPT_SINTESIS),
                HumanMessage(
                    f"SOLICITUD:\n{solicitud}\n\nCONTRIBUCIONES:\n{formatear_contribuciones(state)}{aviso}"
                ),
            ]
        )
        return {"messages": [AIMessage(respuesta.content, name="sintetizador")]}

    return sintetizador
