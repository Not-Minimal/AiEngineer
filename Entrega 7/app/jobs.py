"""Estado de cada job en Redis. Lo comparten la API, el worker y el endpoint de aprobación."""

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from redis import asyncio as aioredis

from app.config import JOB_PREFIX, QUEUE_NAME


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    DONE = "DONE"
    FAILED = "FAILED"


def ahora() -> str:
    return datetime.now(UTC).isoformat()


async def leer_job(redis: aioredis.Redis, job_id: str) -> dict[str, Any] | None:
    raw = await redis.get(f"{JOB_PREFIX}{job_id}")
    return json.loads(raw) if raw else None


async def guardar_job(redis: aioredis.Redis, job: dict[str, Any]) -> None:
    job["updated_at"] = ahora()
    await redis.set(f"{JOB_PREFIX}{job['job_id']}", json.dumps(job, ensure_ascii=False))


async def actualizar_job(redis: aioredis.Redis, job_id: str, **cambios: Any) -> dict[str, Any]:
    job = await leer_job(redis, job_id) or {"job_id": job_id}
    job.update(cambios)
    await guardar_job(redis, job)
    return job


async def encolar(redis: aioredis.Redis, mensaje: dict[str, Any]) -> None:
    """La cola lleva mensajes {"job_id", "tipo": "start" | "resume", ...}; el estado vive aparte."""
    await redis.rpush(QUEUE_NAME, json.dumps(mensaje, ensure_ascii=False))
