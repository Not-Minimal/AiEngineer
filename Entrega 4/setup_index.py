from pinecone import Pinecone, ServerlessSpec

from config import DIMENSION, INDEX_NAME, PINECONE_API_KEY


def setup_index() -> None:
    """Crea el índice si no existe y verifica que su dimensión sea la esperada."""
    pc = Pinecone(api_key=PINECONE_API_KEY)

    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"Índice creado: {INDEX_NAME}")
    else:
        print(f"El índice ya existe: {INDEX_NAME}")

    dimension = pc.describe_index(INDEX_NAME).dimension
    if dimension != DIMENSION:
        raise SystemExit(
            f"El índice tiene dimensión {dimension}, pero se esperaba {DIMENSION}."
        )


if __name__ == "__main__":
    setup_index()
