"""Human-in-the-loop: el grafo se detiene antes de una acción crítica hasta que una persona decide.

Una tarea es crítica cuando cumple alguna de estas reglas (las evalúa el sistema, no el modelo):
1. Efecto secundario: se pidió publicar el informe, que se escribe en una salida externa
   (la lista OUTBOX_NAME de Redis, que haría las veces de un canal de Slack o un correo).
2. Respuesta no validada: el supervisor llegó a MAX_PASOS sin aprobar la rúbrica, así que
   la respuesta salió del freno de seguridad y no de una validación.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from langgraph.types import interrupt
from pydantic import BaseModel, Field
from redis import asyncio as aioredis

from app.config import OUTBOX_NAME
from app.jobs import JobStatus, actualizar_job, ahora, encolar, leer_job
from app.state import OrchestratorState


def motivos_criticos(state: OrchestratorState) -> list[str]:
    motivos = []
    if state.get("publicar"):
        motivos.append("La tarea publica el informe en un canal externo (efecto secundario).")
    if not state.get("task_completed"):
        motivos.append("El supervisor alcanzó el límite de pasos sin validar la rúbrica.")
    return motivos


async def aprobacion_humana(state: OrchestratorState) -> dict[str, Any]:
    motivos = motivos_criticos(state)
    if not motivos:
        return {"aprobacion": "no_requerida"}

    # interrupt() guarda el estado en el checkpointer (Redis) y corta la ejecución.
    # Al reanudar con Command(resume=...), este nodo se vuelve a ejecutar desde el
    # principio y interrupt() devuelve la decisión. Por eso aquí no hay efectos: van
    # en el nodo siguiente.
    decision = interrupt(
        {
            "pregunta": "¿Apruebas entregar este informe?",
            "motivos": motivos,
            "borrador": state["respuesta"],
        }
    )
    return {
        "aprobacion": "aprobada" if decision["aprobado"] else "rechazada",
        "comentario_revisor": decision.get("comentario", ""),
    }


def crear_nodo_entrega(redis: aioredis.Redis):
    async def entregar(state: OrchestratorState) -> dict[str, Any]:
        if state["aprobacion"] == "rechazada":
            return {"entrega": "rechazado por el revisor: no se entregó ni publicó"}
        if state.get("publicar"):
            await redis.rpush(OUTBOX_NAME, state["respuesta"])
            return {"entrega": f"publicado en {OUTBOX_NAME}"}
        return {"entrega": "devuelto al usuario"}

    return entregar


# --- Endpoint de aprobación ---

router = APIRouter()


class Decision(BaseModel):
    aprobado: bool
    comentario: str = Field(default="", description="Opcional: queda registrado en el estado del grafo.")


@router.post("/tasks/{job_id}/approve", status_code=202)
async def aprobar(job_id: str, decision: Decision, request: Request) -> dict[str, Any]:
    """Registra la decisión y encola la reanudación. No ejecuta el grafo: eso lo hace el worker."""
    redis: aioredis.Redis = request.app.state.redis
    job = await leer_job(redis, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if job["status"] != JobStatus.WAITING_APPROVAL:
        raise HTTPException(status_code=409, detail=f"El job no espera aprobación (estado {job['status']})")

    # Se cambia el estado antes de encolar, igual que al crear el job: así una segunda
    # aprobación recibe 409 y el polling nunca ve un estado viejo.
    await actualizar_job(
        redis, job_id, status=JobStatus.PENDING, decision={**decision.model_dump(), "decidido_at": ahora()}
    )
    await encolar(redis, {"job_id": job_id, "tipo": "resume", "decision": decision.model_dump()})
    return {"job_id": job_id, "status": JobStatus.PENDING}
