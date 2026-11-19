import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
COLLECTION_NAME = "knowledge_base"

MODELO = "gpt-4o-mini"
TOP_K = 3

# Decisiones máximas del supervisor antes de forzar la síntesis.
MAX_PASOS = 6
# Límite de pasos internos (modelo + herramientas) de cada especialista ReAct.
RECURSION_LIMIT_ESPECIALISTA = 10

# --- Pre-entrega 7: infraestructura (se sobreescribe con variables de entorno) ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = "agente:cola"
JOB_PREFIX = "agente:job:"
# Salida del nodo con efectos secundarios: solo se escribe si un humano aprobó.
OUTBOX_NAME = "agente:informes_publicados"
# Cuántos grafos corre el worker a la vez; cada uno espera casi todo el tiempo al LLM.
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "5"))

PHOENIX_COLLECTOR_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006/v1/traces")
PHOENIX_PROJECT_NAME = os.getenv("PHOENIX_PROJECT_NAME", "pre-entrega-7")
# Se registra en cada traza: si cambia un prompt, se ve qué versión produjo qué respuesta.
PROMPT_VERSION = "m6-supervisor-v2"
