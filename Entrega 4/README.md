# Sistema RAG escalable con Pinecone

Recupera fragmentos de la documentación de FastAPI combinando búsqueda semántica
(Pinecone) y léxica (BM25), y mide la calidad con Precision@5 y Recall@5.

## Replicar el índice (Python 3.12)

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env              # completar PINECONE_API_KEY y OPENAI_API_KEY
.venv/bin/python descargar_docs.py
.venv/bin/python setup_index.py   # índice serverless, 1536 dimensiones, coseno
.venv/bin/python ingest.py
.venv/bin/python evaluate.py
```

## Metadatos

| Campo | Contenido |
|---|---|
| `text` | Texto original del fragmento |
| `source` | Ruta relativa del archivo |
| `category` | `tutorial` o `advanced` |
| `page` | Siempre 1: Markdown no tiene páginas |
| `chunk_index` | Posición del fragmento en el archivo |

## Resultados

| Recuperador | Recall@5 | Precision@5 |
|---|---|---|
| Híbrido | 1.00 | 0.56 |
| Solo vectorial | 1.00 | 0.76 |
| Solo BM25 | 0.80 | 0.40 |

El híbrido encuentra el documento esperado en las 5 preguntas y supera a BM25, que falla
en una pregunta conceptual. En este golden set no supera a la búsqueda vectorial: empata
en Recall@5 y baja en Precision@5, porque con pesos 0.5/0.5 BM25 también ocupa lugares del
top 5 con fragmentos de otros documentos. Precision@5 solo cuenta como útiles los
fragmentos del documento esperado, y con 5 preguntas estas diferencias son orientativas.

## Limitaciones

- El golden set tiene solo 5 preguntas: sirve de muestra, no como evaluación completa.
- BM25 se reconstruye en memoria al iniciar; no escala tan bien como Pinecone.
- Cada pregunta espera un solo documento, aunque otros también puedan ser útiles.

Dataset: documentación de [FastAPI](https://github.com/fastapi/fastapi), licencia MIT.
