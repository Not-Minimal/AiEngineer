import asyncio

from dotenv import load_dotenv

from ingest import ingest_documents
from rag import get_rag_response

PREGUNTAS = [
    "¿Cuánto baja la latencia la caché de Tallertrack?",
    "¿Qué cuestionarios clínicos incluye VertiTrack?",
    "¿Cuántos usuarios activos tiene VertiTrack?",  # trampa: no está en los documentos
    "¿Cuál es la tarifa por hora de Saúl?",  # trampa: no está en los documentos
    "¿Cuál es la capital de Francia?",  # trampa: el modelo lo sabe, pero no está en el contexto
]


async def main() -> None:
    load_dotenv()
    ingest_documents()

    for pregunta in PREGUNTAS:
        print(f"\nPregunta: {pregunta}")
        respuesta = await get_rag_response(pregunta)
        print(respuesta.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
