import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import MessagesState

Especialista = Literal["investigador", "analista"]


class Contribucion(TypedDict):
    """Lo que entregó un especialista en un turno: quién, qué se le pidió y qué respondió."""

    paso: int
    agente: Especialista
    instruccion: str
    contenido: str
    herramientas: list[str]


class OrchestratorState(MessagesState):
    """Estado compartido del orquestador.

    - messages: la conversación con el usuario (reducer add_messages de MessagesState).
    - contribuciones: registro acumulativo de cada especialista; operator.add agrega
      sin pisar lo anterior, así se sabe qué aportó cada agente y en qué paso.
    - next_agent / instruccion: la última decisión del supervisor.
    - pasos: cuántas veces decidió el supervisor; es el freno contra el bucle infinito.
    - task_completed: lo marca el supervisor cuando la rúbrica se cumple.
    """

    contribuciones: Annotated[list[Contribucion], operator.add]
    next_agent: str
    instruccion: str
    pasos: int
    task_completed: bool
