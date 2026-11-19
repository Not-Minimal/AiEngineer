"""Prueba de carga: 5 peticiones concurrentes contra la API, con polling hasta que terminen.

Uso: .venv/bin/python scripts/carga_concurrente.py [URL_API]

Mide la latencia de punta a punta que ve el cliente (encolado + espera + ejecución).
El costo por ejecución y la latencia p95 del grafo se leen en Phoenix (ver README).
"""

import asyncio
import statistics
import sys
import time

import httpx

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
TERMINALES = {"DONE", "FAILED", "WAITING_APPROVAL"}

CONSULTAS = [
    "¿Cuántas órdenes de trabajo y cuántos pesos en transacciones registra Tallertrack en promedio por taller activo?",
    "¿Cuántas horas manuales por semana ahorró Saúl en Autotruck Diesel y cuántas serían en un año de 52 semanas?",
    "¿Cuántas líneas de código tiene Aura por cada test?",
    "En Forestal Kupal, ¿cuántos productos y vehículos gestionaban sus sistemas y qué porcentajes de reducción lograron en promedio?",
    "¿Cuántos usuarios activos tiene VertiTrack y cuál es su ingreso mensual por usuario?",
]


async def ejecutar(cliente: httpx.AsyncClient, consulta: str) -> dict:
    inicio = time.perf_counter()
    respuesta = await cliente.post(f"{API}/tasks", json={"query": consulta})
    respuesta.raise_for_status()
    job = respuesta.json()
    encolado_ms = (time.perf_counter() - inicio) * 1000

    while job["status"] not in TERMINALES:
        await asyncio.sleep(1)
        job = (await cliente.get(f"{API}/tasks/{job['job_id']}")).json()

    return {**job, "encolado_ms": encolado_ms, "total_s": time.perf_counter() - inicio}


def percentil(valores: list[float], p: int) -> float:
    # Interpolación lineal entre las muestras (método "inclusive"), igual que numpy por defecto.
    return statistics.quantiles(valores, n=100, method="inclusive")[p - 1]


async def esperar_api(cliente: httpx.AsyncClient, segundos: int = 60) -> None:
    """Justo después de `docker compose up` el contenedor existe pero uvicorn aún no escucha."""
    for _ in range(segundos):
        try:
            if (await cliente.get(f"{API}/health")).status_code == 200:
                return
        except httpx.TransportError:
            pass
        await asyncio.sleep(1)
    sys.exit(f"La API no respondió en {API}/health después de {segundos}s")


async def main() -> None:
    async with httpx.AsyncClient(timeout=30) as cliente:
        await esperar_api(cliente)
        resultados = await asyncio.gather(*(ejecutar(cliente, c) for c in CONSULTAS))

    print(f"{'job_id':<38} {'estado':<17} {'POST (ms)':>9} {'total (s)':>9}  consulta")
    for r in resultados:
        print(f"{r['job_id']:<38} {r['status']:<17} {r['encolado_ms']:>9.1f} {r['total_s']:>9.1f}  {r['query'][:50]}")
        if r["status"] == "FAILED":
            print(f"    error: {r['error']}")

    totales = [r["total_s"] for r in resultados]
    print(
        f"\nLatencia cliente: p50={percentil(totales, 50):.1f}s  p95={percentil(totales, 95):.1f}s  "
        f"máx={max(totales):.1f}s · POST más lento: {max(r['encolado_ms'] for r in resultados):.1f} ms"
    )


if __name__ == "__main__":
    asyncio.run(main())
