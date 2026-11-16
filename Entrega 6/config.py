from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
COLLECTION_NAME = "knowledge_base"

MODELO = "gpt-4o-mini"
TOP_K = 3

# Decisiones máximas del supervisor antes de forzar la síntesis.
MAX_PASOS = 6
# Límite de pasos internos (modelo + herramientas) de cada especialista ReAct.
RECURSION_LIMIT_ESPECIALISTA = 10
