import asyncio
import uuid
import json
from fastapi import FastAPI, HTTPException
from redis import asyncio as aioredis
from pydantic import BaseModel

# Configuración de Redis
REDIS_URL = "redis://localhost:6379"
QUEUE_NAME = "tasks_queue"
STATUS_PREFIX = "status:"

app = FastAPI()
# socket_timeout=None: desde redis-py 8 el valor por defecto es 5 s, y un
# blpop(timeout=0) que espera más que eso lanzaría TimeoutError y mataría al worker.
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True, socket_timeout=None)

class TaskRequest(BaseModel):
    query: str


async def save_status(job_id: str, status: str, query: str, result=None):
    """Guarda el estado del job como JSON en la clave status:<job_id>."""
    data = {"status": status, "query": query, "result": result}
    await redis_client.set(f"{STATUS_PREFIX}{job_id}", json.dumps(data))


@app.post("/process")
async def create_task(request: TaskRequest):
    """
    1. Generar un job_id único.
    2. Guardar en Redis el estado inicial (status: pending).
    3. Poner el job_id en la lista (cola) de Redis para que el worker lo vea.
    4. Retornar el job_id al cliente inmediatamente.
    """
    job_id = str(uuid.uuid4())

    # Primero el estado y DESPUÉS encolar: si el worker fuera más rápido que
    # la escritura de "pending", el cliente podría recibir un 404.
    await save_status(job_id, "pending", request.query)
    await redis_client.rpush(QUEUE_NAME, job_id)

    return {"job_id": job_id, "status": "pending"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Consulta el estado y resultado del job_id en Redis."""
    raw = await redis_client.get(f"{STATUS_PREFIX}{job_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return {"job_id": job_id, **json.loads(raw)}


async def task_worker():
    """
    Bucle infinito que:
    1. Extrae job_ids de la cola usando blpop.
    2. Simula el procesamiento de LangGraph (asyncio.sleep).
    3. Actualiza el estado en Redis a 'completed' con el resultado final.
    """
    print("Worker iniciado...")
    while True:
        # blpop bloquea (sin consumir CPU) hasta que haya algo en la cola.
        # Devuelve una tupla (nombre_de_la_cola, valor).
        _, job_id = await redis_client.blpop(QUEUE_NAME, timeout=0)

        raw = await redis_client.get(f"{STATUS_PREFIX}{job_id}")
        query = json.loads(raw)["query"] if raw else ""

        try:
            await save_status(job_id, "processing", query)
            print(f"Procesando {job_id}...")

            # Acá iría: result = await graph.ainvoke({"messages": [...]}, config)
            await asyncio.sleep(5)
            result = f"Respuesta simulada para la consulta: '{query}'"

            await save_status(job_id, "completed", query, result)
            print(f"Job {job_id} completado")
        except Exception as e:
            # Si el grafo falla, el cliente lo ve en /status en vez de quedar en "processing" para siempre.
            await save_status(job_id, "failed", query, str(e))
            print(f"Job {job_id} falló: {e}")

# El worker arranca junto con la API, en el mismo event loop que usa uvicorn
@app.on_event("startup")
async def start_worker():
    asyncio.create_task(task_worker())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
