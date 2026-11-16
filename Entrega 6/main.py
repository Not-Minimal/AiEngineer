import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from config import MODELO
from graph import crear_grafo

BASE_DIR = Path(__file__).parent
TRAZA = BASE_DIR / "traza_ejecucion.json"

ESCENARIOS = {
    "investigar_y_analizar": (
        "¿Cuántas órdenes de trabajo y cuántos pesos en transacciones registra Tallertrack "
        "en promedio por taller activo?"
    ),
    "dato_inexistente": "¿Cuántos usuarios activos tiene VertiTrack y cuál es su ingreso mensual por usuario?",
}


async def consultar(app: Any, pregunta: str) -> dict[str, Any]:
    """Ejecuta una solicitud y registra, en orden, cada nodo que intervino y su salida."""
    recorrido: list[dict[str, Any]] = []
    respuesta = ""
    async for evento in app.astream(
        {"messages": [HumanMessage(pregunta)], "contribuciones": [], "pasos": 0, "task_completed": False},
        stream_mode="updates",
    ):
        for nodo, salida in evento.items():
            texto = salida["messages"][-1].content
            if nodo == "supervisor":
                recorrido.append({"nodo": nodo, "paso": salida["pasos"], "decision": salida["next_agent"],
                                  "instruccion": salida["instruccion"], "razon": texto})
            elif nodo == "sintetizador":
                respuesta = texto
                recorrido.append({"nodo": nodo})
            else:
                contribucion = salida["contribuciones"][0]
                recorrido.append({"nodo": nodo, "herramientas": contribucion["herramientas"], "contenido": texto})
    return {"pregunta": pregunta, "recorrido": recorrido, "respuesta_final": respuesta}


def imprimir(clave: str, turno: dict[str, Any]) -> None:
    print(f"\n=== {clave} ===\nUsuario: {turno['pregunta']}")
    for paso in turno["recorrido"]:
        if paso["nodo"] == "supervisor":
            print(f"\n[supervisor #{paso['paso']}] -> {paso['decision']}\n  {paso['razon']}")
            if paso["instruccion"]:
                print(f"  Instrucción: {paso['instruccion']}")
        elif paso["nodo"] in ("investigador", "analista"):
            print(f"\n[{paso['nodo']}] herramientas: {paso['herramientas']}\n{paso['contenido']}")
    print(f"\n[sintetizador] Respuesta final:\n{turno['respuesta_final']}")


async def main() -> None:
    load_dotenv()
    app = crear_grafo(ChatOpenAI(model=MODELO, temperature=0))

    if len(sys.argv) > 1:
        imprimir("consulta", await consultar(app, " ".join(sys.argv[1:])))
        return

    traza = {}
    for clave, pregunta in ESCENARIOS.items():
        traza[clave] = await consultar(app, pregunta)
        imprimir(clave, traza[clave])

    TRAZA.write_text(json.dumps(traza, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nTraza guardada en {TRAZA.name}")


if __name__ == "__main__":
    asyncio.run(main())
