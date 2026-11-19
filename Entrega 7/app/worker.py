"""Worker: saca mensajes de la cola de Redis y ejecuta el grafo, fuera del proceso de la API.

Se corre como proceso aparte (`python -m app.worker`) y se puede escalar a varias
instancias: todas leen de la misma cola y comparten los checkpoints en Redis, así que
un job pausado por una instancia lo puede reanudar otra.
"""

import asyncio
import json
import logging
import time
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from openinference.instrumentation import using_session
from redis import asyncio as aioredis

from app.config import MODELO, PROMPT_VERSION, QUEUE_NAME, REDIS_URL, WORKER_CONCURRENCY
from app.graph import crear_grafo
from app.jobs import JobStatus, actualizar_job, ahora, leer_job
from app.knowledge_base import get_collection
from app.observability import init_tracing

log = logging.getLogger("worker")


def estado_inicial(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [HumanMessage(job["query"])],
        "contribuciones": [],
        "pasos": 0,
        "task_completed": False,
        "publicar": job["publicar"],
        "respuesta": "",
        "aprobacion": "no_requerida",
        "comentario_revisor": "",
        "entrega": "",
    }


async def procesar(graph: CompiledStateGraph, redis: aioredis.Redis, mensaje: dict[str, Any]) -> None:
    job_id = mensaje["job_id"]
    inicio = time.perf_counter()
    try:
        job = await leer_job(redis, job_id)
        if job is None:
            log.warning("Mensaje para un job inexistente: %s", job_id)
            return
        await actualizar_job(redis, job_id, status=JobStatus.RUNNING)

        if mensaje["tipo"] == "start":
            entrada = estado_inicial(job)
        else:
            # Command(resume=...) continúa el mismo thread_id: el valor es lo que devuelve interrupt().
            entrada = Command(resume=mensaje["decision"])

        config = {
            "configurable": {"thread_id": job_id},
            "run_name": f"orquestador:{mensaje['tipo']}",
            "metadata": {"job_id": job_id, "prompt_version": PROMPT_VERSION, "publicar": job["publicar"]},
            "tags": ["pre-entrega-7", mensaje["tipo"]],
        }
        if job.get("simular_fallo"):
            # Fallo real de LangGraph (GraphRecursionError) para comprobar el paso a FAILED y verlo en la traza.
            config["recursion_limit"] = 2

        # using_session agrupa en Phoenix las trazas de un mismo job (la inicial y la de reanudación).
        with using_session(job_id):
            await graph.ainvoke(entrada, config)

        tramo = {"tipo": mensaje["tipo"], "segundos": round(time.perf_counter() - inicio, 2)}
        snapshot = await graph.aget_state(config)
        if snapshot.interrupts:
            await actualizar_job(
                redis,
                job_id,
                status=JobStatus.WAITING_APPROVAL,
                aprobacion=snapshot.interrupts[0].value,
                tramos=[*job.get("tramos", []), tramo],
            )
            log.info("Job %s esperando aprobación", job_id)
            return

        valores = snapshot.values
        await actualizar_job(
            redis,
            job_id,
            status=JobStatus.DONE,
            finished_at=ahora(),
            tramos=[*job.get("tramos", []), tramo],
            result={
                "respuesta": valores["respuesta"],
                "aprobacion": valores["aprobacion"],
                "comentario_revisor": valores["comentario_revisor"],
                "entrega": valores["entrega"],
                "pasos_supervisor": valores["pasos"],
                "agentes": [c["agente"] for c in valores["contribuciones"]],
            },
        )
        log.info("Job %s terminado en %.1fs", job_id, tramo["segundos"])
    except Exception as error:
        # Sin esto, el cliente quedaría haciendo polling para siempre sobre un job RUNNING.
        log.exception("Job %s falló", job_id)
        try:
            await actualizar_job(
                redis, job_id, status=JobStatus.FAILED, finished_at=ahora(), error=f"{type(error).__name__}: {error}"
            )
        except Exception:
            log.exception("No se pudo registrar el fallo del job %s en Redis", job_id)


async def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    init_tracing()

    redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    # Chroma es síncrono e indexa la primera vez: se prepara en un hilo antes de aceptar trabajo.
    # La consulta de calentamiento carga el modelo ONNX de embeddings, que Chroma carga
    # recién en el primer query. Sin ella, en la prueba de carga las 10 primeras búsquedas
    # concurrentes tardaron 39-65 s cada una (visto en los spans chroma.query de Phoenix).
    # Va directo a la colección, sin pasar por buscar(), para no dejar una traza suelta.
    await asyncio.to_thread(lambda: get_collection().query(query_texts=["calentamiento"], n_results=1))

    async with AsyncRedisSaver.from_conn_string(REDIS_URL) as checkpointer:
        await checkpointer.asetup()
        graph = crear_grafo(ChatOpenAI(model=MODELO, temperature=0), checkpointer, redis)

        limite = asyncio.Semaphore(WORKER_CONCURRENCY)
        en_curso: set[asyncio.Task] = set()

        def liberar(tarea: asyncio.Task) -> None:
            en_curso.discard(tarea)
            limite.release()

        log.info("Worker listo: hasta %d jobs en paralelo, cola %s", WORKER_CONCURRENCY, QUEUE_NAME)
        while True:
            # Se toma el cupo ANTES de sacar de la cola: si este worker está lleno, el
            # mensaje queda en Redis para otra instancia en vez de esperar aquí.
            await limite.acquire()
            # Espera corta y se repite: redis-py 8 corta cualquier lectura a los 5 s
            # (socket_timeout por defecto), así que un BLPOP infinito lanzaría TimeoutError.
            item = await redis.blpop(QUEUE_NAME, timeout=2)
            if item is None:
                limite.release()
                continue
            tarea = asyncio.create_task(procesar(graph, redis, json.loads(item[1])))
            en_curso.add(tarea)
            tarea.add_done_callback(liberar)


if __name__ == "__main__":
    asyncio.run(main())
