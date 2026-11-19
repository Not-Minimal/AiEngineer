"""API REST: recibe la tarea, la registra en Redis, la encola y responde en milisegundos.

La API nunca ejecuta el grafo: eso lo hace el worker (app/worker.py). Todas las llamadas
a Redis usan el cliente async, así que ningún endpoint bloquea el event loop.
"""

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from redis import asyncio as aioredis

from app.config import QUEUE_NAME, REDIS_URL
from app.hitl import router as hitl_router
from app.jobs import JobStatus, ahora, encolar, guardar_job, leer_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    yield
    await app.state.redis.aclose()


app = FastAPI(title="Orquestador multi-agente: Pre-entrega 7", lifespan=lifespan)
app.include_router(hitl_router)


class TaskRequest(BaseModel):
    query: str = Field(min_length=1, description="Pregunta para el equipo de agentes")
    publicar: bool = Field(
        default=False, description="Publicar el informe en el canal externo. Es crítico: requiere aprobación humana."
    )
    simular_fallo: bool = Field(default=False, description="Solo para pruebas: fuerza un error en el grafo.")


@app.post("/tasks", status_code=202)
async def crear_tarea(tarea: TaskRequest, request: Request) -> dict[str, Any]:
    redis: aioredis.Redis = request.app.state.redis
    job_id = str(uuid.uuid4())
    # El estado se escribe ANTES de encolar: si el worker fuera más rápido, el
    # polling no puede recibir un 404 de un job que sí existe.
    await guardar_job(
        redis,
        {"job_id": job_id, "status": JobStatus.PENDING, "created_at": ahora(), **tarea.model_dump()},
    )
    await encolar(redis, {"job_id": job_id, "tipo": "start"})
    return {"job_id": job_id, "status": JobStatus.PENDING}


@app.get("/tasks/{job_id}")
async def estado_tarea(job_id: str, request: Request) -> dict[str, Any]:
    job = await leer_job(request.app.state.redis, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


@app.get("/health")
async def health(request: Request) -> dict[str, Any]:
    redis: aioredis.Redis = request.app.state.redis
    return {"redis": await redis.ping(), "en_cola": await redis.llen(QUEUE_NAME)}
