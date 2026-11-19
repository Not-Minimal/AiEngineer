"""Lee de Phoenix las mismas métricas que muestra el dashboard: costo por ejecución y latencia p95.

Uso: .venv/bin/python scripts/metricas_phoenix.py [URL_PHOENIX]

Sirve para verificar las capturas. Phoenix calcula el costo a partir de los tokens de
entrada y salida de cada span LLM y de su tabla de precios por modelo.
"""

import os
import sys

import httpx

PHOENIX = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:6006"
PROYECTO = os.getenv("PHOENIX_PROJECT_NAME", "pre-entrega-7")

CONSULTA = """
query ($primeros: Int!) {
  projects { edges { node {
    name
    traceCount
    p50: latencyMsQuantile(probability: 0.5)
    p95: latencyMsQuantile(probability: 0.95)
    costSummary { prompt { cost tokens } completion { cost tokens } total { cost tokens } }
    spans(first: $primeros, filterCondition: "parent_id is None", sort: {col: startTime, dir: desc}) {
      edges { node {
        name
        latencyMs
        statusCode
        trace { traceId costSummary { total { cost tokens } } }
      } }
    }
  } } }
}
"""


def main() -> None:
    respuesta = httpx.post(f"{PHOENIX}/graphql", json={"query": CONSULTA, "variables": {"primeros": 50}}, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()
    if "errors" in datos:
        sys.exit(datos["errors"])
    proyecto = next((e["node"] for e in datos["data"]["projects"]["edges"] if e["node"]["name"] == PROYECTO), None)
    if proyecto is None:
        sys.exit(f"No existe el proyecto {PROYECTO} en Phoenix")

    print(f"{'traza (raíz)':<24} {'estado':<7} {'latencia (s)':>12} {'tokens':>8} {'costo (USD)':>12}")
    for borde in proyecto["spans"]["edges"]:
        span = borde["node"]
        total = span["trace"]["costSummary"]["total"]
        costo = f"{total['cost']:.6f}" if total["cost"] is not None else "-"
        print(f"{span['name']:<24} {span['statusCode']:<7} {span['latencyMs'] / 1000:>12.1f} {total['tokens'] or 0:>8} {costo:>12}")

    resumen = proyecto["costSummary"]
    n = proyecto["traceCount"]
    costo_total = resumen["total"]["cost"] or 0
    print(
        f"\n{n} trazas · latencia p50={proyecto['p50'] / 1000:.1f}s p95={proyecto['p95'] / 1000:.1f}s"
        f"\nTokens: {resumen['prompt']['tokens'] or 0} entrada + {resumen['completion']['tokens'] or 0} salida"
        f"\nCosto total: {costo_total:.6f} USD · promedio por traza: {costo_total / max(n, 1):.6f} USD"
    )


if __name__ == "__main__":
    main()
