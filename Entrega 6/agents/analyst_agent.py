import ast
import operator
import statistics

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

PROMPT = (
    "Eres el agente ANALISTA. Recibes una tarea y los hechos que reunió el investigador. "
    "Trabaja SOLO con esos hechos: si falta un dato, dilo explícitamente en vez de "
    "suponerlo. Toda operación numérica, por simple que sea, se hace con la herramienta "
    "calcular o estadisticas; nunca calcules de cabeza. Responde con: (1) los datos de "
    "entrada que usaste, (2) cada cálculo con su resultado y (3) una conclusión breve."
)

_OPERADORES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _evaluar(nodo: ast.AST) -> float:
    """Evalúa solo aritmética. Nada de eval(): un nombre o una llamada lanzan ValueError."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, int | float):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.left), _evaluar(nodo.right))
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    raise ValueError(f"expresión no permitida: {ast.dump(nodo)}")


class CalcularInput(BaseModel):
    expresion: str = Field(
        description="Expresión aritmética con números sin separador de miles, por ejemplo '99954 / 15'"
    )


class EstadisticasInput(BaseModel):
    valores: list[float] = Field(min_length=1, description="Lista de números, por ejemplo [4200, 89]")


@tool(args_schema=CalcularInput)
def calcular(expresion: str) -> str:
    """Calcula una expresión aritmética (+, -, *, /, **, %, paréntesis).

    Úsala para cualquier cálculo: promedios por unidad, porcentajes, diferencias.
    Devuelve el resultado o un texto que empieza con ERROR si la expresión no es válida.
    """
    try:
        resultado = _evaluar(ast.parse(expresion, mode="eval").body)
    except (SyntaxError, ValueError, ZeroDivisionError) as error:
        return f"ERROR: {error}. Usa solo números y operadores, sin puntos de miles."
    return f"{expresion} = {round(resultado, 4)}"


@tool(args_schema=EstadisticasInput)
def estadisticas(valores: list[float]) -> str:
    """Devuelve cantidad, suma, promedio, mínimo y máximo de una lista de números."""
    return (
        f"n={len(valores)}, suma={sum(valores)}, promedio={round(statistics.mean(valores), 4)}, "
        f"min={min(valores)}, max={max(valores)}"
    )


def crear_analista(llm: BaseChatModel):
    return create_react_agent(llm, [calcular, estadisticas], prompt=PROMPT, name="analista")
