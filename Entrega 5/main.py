import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.errors import GraphRecursionError

from graph import crear_grafo

BASE_DIR = Path(__file__).parent
CHECKPOINTS = BASE_DIR / "checkpoints.sqlite"
TRAZA = BASE_DIR / "traza_ejecucion.json"
MODELO = "gpt-4o-mini"
RECURSION_LIMIT = 10


def serializar_turno(mensajes: list[AnyMessage]) -> list[dict[str, Any]]:
    """Convierte el último turno (desde el último HumanMessage) a pasos ReAct."""
    inicio = max(i for i, m in enumerate(mensajes) if isinstance(m, HumanMessage))
    pasos: list[dict[str, Any]] = []
    for mensaje in mensajes[inicio:]:
        if isinstance(mensaje, HumanMessage):
            pasos.append({"tipo": "usuario", "contenido": mensaje.content})
        elif isinstance(mensaje, ToolMessage):
            pasos.append({"tipo": "observacion", "herramienta": mensaje.name, "contenido": mensaje.content})
        elif isinstance(mensaje, AIMessage) and mensaje.tool_calls:
            for llamada in mensaje.tool_calls:
                pasos.append({"tipo": "accion", "herramienta": llamada["name"], "argumentos": llamada["args"]})
        elif isinstance(mensaje, AIMessage):
            pasos.append({"tipo": "respuesta", "contenido": mensaje.content})
    return pasos


async def consultar(llm: BaseChatModel, pregunta: str, thread_id: str) -> dict[str, Any]:
    """Ejecuta un turno. Cada turno abre el SQLite de nuevo: la memoria viene del disco."""
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}

    async with AsyncSqliteSaver.from_conn_string(str(CHECKPOINTS)) as checkpointer:
        app = crear_grafo(llm).compile(checkpointer=checkpointer)
        try:
            resultado = await app.ainvoke({"messages": [HumanMessage(pregunta)]}, config=config)
        except GraphRecursionError:
            return {
                "thread_id": thread_id,
                "pregunta": pregunta,
                "error": f"Se alcanzó el recursion_limit de {RECURSION_LIMIT}.",
                "pasos": [],
                "llamadas_a_herramientas": 0,
            }

    pasos = serializar_turno(resultado["messages"])
    return {
        "thread_id": thread_id,
        "pregunta": pregunta,
        "pasos": pasos,
        "llamadas_a_herramientas": sum(p["tipo"] == "accion" for p in pasos),
    }


def imprimir(titulo: str, turno: dict[str, Any]) -> None:
    print(f"\n=== {titulo} (thread_id={turno['thread_id']}) ===")
    print(f"Usuario: {turno['pregunta']}")
    if "error" in turno:
        print(f"Error: {turno['error']}")
    for paso in turno["pasos"]:
        if paso["tipo"] == "accion":
            print(f"-> Acción: {paso['herramienta']}({paso['argumentos']})")
        elif paso["tipo"] == "observacion":
            print(f"<- Observación: {paso['contenido']}")
        elif paso["tipo"] == "respuesta":
            print(f"Respuesta: {paso['contenido']}")
    print(f"Llamadas a herramientas: {turno['llamadas_a_herramientas']}")


async def ejecutar_demo(llm: BaseChatModel, sufijo: str) -> dict[str, dict[str, Any]]:
    """Corre los escenarios de la entrega. El sufijo evita reutilizar hilos de otra ejecución."""
    hilo_memoria = f"memoria-{sufijo}"
    escenarios = [
        ("multi_paso", "Razonamiento multi-paso", "¿Cuántos pedidos tuvo Ana García y cuál fue el total?", hilo_memoria),
        ("memoria_mismo_hilo", "Memoria: mismo thread_id", "¿Y Juan Pérez?", hilo_memoria),
        ("memoria_comparacion", "Memoria: turnos anteriores", "¿Quién de los dos gastó más?", hilo_memoria),
        ("control_otro_hilo", "Control: otro thread_id", "¿Quién de los dos gastó más?", f"control-{sufijo}"),
        ("reintento", "Ciclo de retorno: reintento", "¿Cuánto gastó en total Maria Lopes?", f"reintento-{sufijo}"),
        ("aclaracion", "Ciclo de retorno: aclaración", "¿Cuántos pedidos tuvo Roberto Sánchez?", f"aclaracion-{sufijo}"),
    ]

    traza: dict[str, dict[str, Any]] = {}
    for clave, titulo, pregunta, thread_id in escenarios:
        traza[clave] = await consultar(llm, pregunta, thread_id)
        imprimir(titulo, traza[clave])
    return traza


async def main() -> None:
    load_dotenv()
    llm = ChatOpenAI(model=MODELO, temperature=0)

    traza = await ejecutar_demo(llm, datetime.now().strftime("%Y%m%d-%H%M%S"))

    TRAZA.write_text(json.dumps(traza, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nTraza guardada en {TRAZA.name}")


if __name__ == "__main__":
    asyncio.run(main())
