from difflib import get_close_matches

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

# Dos tablas separadas: el agente recibe nombres y debe obtener el ID antes de consultar pedidos.
CLIENTES_DB: dict[str, int] = {
    "ana garcía": 102,
    "juan pérez": 205,
    "maría lópez": 310,
}

PEDIDOS_DB: dict[int, dict[str, int]] = {
    102: {"pedidos": 3, "total": 14500},
    205: {"pedidos": 1, "total": 3200},
    310: {"pedidos": 5, "total": 27800},
}


class BuscarClienteInput(BaseModel):
    nombre: str = Field(description="Nombre completo del cliente, por ejemplo 'Ana García'")


class BuscarPedidosInput(BaseModel):
    cliente_id: int = Field(ge=1, description="ID numérico del cliente, por ejemplo 102")


@tool(args_schema=BuscarClienteInput)
async def buscar_cliente_por_nombre(nombre: str) -> str:
    """Busca el cliente_id de un cliente a partir de su nombre completo.

    Úsala siempre que el usuario mencione a un cliente por su nombre, porque
    buscar_pedidos solo acepta el ID numérico. Devuelve el cliente_id, o un texto
    que empieza con ERROR si el nombre no coincide. Si el error incluye una
    sugerencia, vuelve a llamarla con el nombre sugerido.
    """
    clave = nombre.strip().lower()
    if clave in CLIENTES_DB:
        return f"Cliente encontrado: '{nombre}' -> cliente_id={CLIENTES_DB[clave]}"

    parecidos = get_close_matches(clave, CLIENTES_DB, n=1, cutoff=0.7)
    if parecidos:
        return f"ERROR: no existe el cliente '{nombre}'. Sugerencia: '{parecidos[0]}'."
    return f"ERROR: no existe el cliente '{nombre}' y no hay nombres parecidos."


@tool(args_schema=BuscarPedidosInput)
async def buscar_pedidos(cliente_id: int) -> str:
    """Busca la cantidad de pedidos y el monto total gastado por un cliente.

    Recibe el cliente_id numérico, no el nombre: si solo conoces el nombre, usa
    primero buscar_cliente_por_nombre. Devuelve la cantidad de pedidos y el total
    en pesos, o un texto que empieza con ERROR si el cliente_id no existe.
    """
    if cliente_id not in PEDIDOS_DB:
        return f"ERROR: no existe ningún cliente con cliente_id={cliente_id}."
    datos = PEDIDOS_DB[cliente_id]
    return f"pedidos={datos['pedidos']}, total=${datos['total']}"


HERRAMIENTAS: list[BaseTool] = [buscar_cliente_por_nombre, buscar_pedidos]
