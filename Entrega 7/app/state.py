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
    - publicar: el usuario pidió publicar el informe (acción con efectos secundarios).
    - respuesta: el texto del sintetizador, antes de pasar por la revisión humana.
    - aprobacion / comentario_revisor: lo que resolvió el nodo de aprobación humana.
    - entrega: qué pasó finalmente con el informe (publicado, solo devuelto o rechazado).
    """

    contribuciones: Annotated[list[Contribucion], operator.add]
    next_agent: str
    instruccion: str
    pasos: int
    task_completed: bool
    publicar: bool
    respuesta: str
    aprobacion: Literal["no_requerida", "aprobada", "rechazada"]
    comentario_revisor: str
    entrega: str
