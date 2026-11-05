# Agente ReAct con memoria persistente

Agente asíncrono en LangGraph que consulta clientes y pedidos en una base simulada. El
modelo decide en cada paso si usa una herramienta o si ya puede responder, y recuerda la
conversación por `thread_id` gracias a un checkpoint en SQLite.

## Levantar el entorno (Python 3.12)

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env    # completar OPENAI_API_KEY
.venv/bin/python main.py
```

`main.py` imprime el ciclo de cada escenario y escribe `traza_ejecucion.json`. Las
conversaciones quedan en `checkpoints.sqlite`, que no se sube al repositorio.

## Estructura

- `tools.py`: las herramientas `buscar_cliente_por_nombre` y `buscar_pedidos`, con
  validación Pydantic y la base simulada.
- `graph.py`: `AgentState` (hereda de `MessagesState`) y el `StateGraph`.
- `main.py`: checkpointer, `recursion_limit`, escenarios de prueba y generación de la traza.
- `traza_ejecucion.json`: traza ReAct de una ejecución real.

## Grafo

```
START -> modelo -> (tools_condition) -> herramientas -> modelo
                         |
                         +-> END, cuando el modelo responde sin tool_calls
```

## Cómo se cumple cada criterio

| Criterio | Implementación |
|---|---|
| Autonomía | El modelo elige las herramientas con `bind_tools` y sus docstrings; no hay rutas `if/else` |
| Ciclo de retorno | Las herramientas devuelven `ERROR` como texto y `ToolNode` convierte los argumentos inválidos en un mensaje de error. El modelo reintenta si hay una sugerencia, o pide aclaración |
| Resiliencia de estado | `AsyncSqliteSaver` con `thread_id`. Cada turno abre el SQLite de nuevo, así que la memoria viene del disco |
| Límite de pasos | `recursion_limit=10`; si se alcanza, el turno termina con un error controlado |
| Estado sucio | El checkpoint guarda todo, pero el modelo recibe como máximo los últimos 20 mensajes |

Se usa `AsyncSqliteSaver`, la variante asíncrona de `SqliteSaver`, porque el grafo se
ejecuta con `asyncio`.

## Escenarios de la traza

| Clave | Qué demuestra |
|---|---|
| `multi_paso` | Dos herramientas para una sola pregunta: primero el ID, luego los pedidos |
| `memoria_mismo_hilo` | Segundo turno del mismo hilo: "¿Y Juan Pérez?" |
| `memoria_comparacion` | "¿Quién de los dos gastó más?" se responde con el historial, sin usar herramientas |
| `control_otro_hilo` | La misma pregunta en otro `thread_id`: sin historial, el agente pide los nombres |
| `reintento` | Nombre mal escrito: error con sugerencia y segundo intento |
| `aclaracion` | Cliente inexistente: el agente pide verificar el nombre |

"¿Y Juan Pérez?" no sirve por sí sola como prueba de memoria: en una ejecución con otro
`thread_id`, el modelo también consultó sus pedidos sin contexto. Por eso la comprobación
es `memoria_comparacion` frente a `control_otro_hilo`.

Extracto de `traza_ejecucion.json`, resumido, de una ejecución real con `gpt-4o-mini`:

```
Usuario: ¿Cuántos pedidos tuvo Ana García y cuál fue el total?
-> Acción: buscar_cliente_por_nombre({'nombre': 'Ana García'})
<- Observación: Cliente encontrado: 'Ana García' -> cliente_id=102
-> Acción: buscar_pedidos({'cliente_id': 102})
<- Observación: pedidos=3, total=$14500
Respuesta: Ana García tuvo 3 pedidos y el total gastado fue de $14,500.
```

## Limitaciones

- La base de datos es simulada y solo tiene 3 clientes.
- Cada ejecución crea hilos nuevos, para que la traza no dependa de una ejecución anterior.
- Las decisiones las toma el modelo, así que el texto y los pasos pueden variar entre ejecuciones.
