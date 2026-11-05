# Sistema de recuperación semántica local (RAG)

Responde preguntas sobre el perfil profesional y los proyectos de Saúl Muñoz Pedreros
usando solo documentos locales. Si la respuesta no está en ellos, dice "No lo
sé".

## Estructura

- `data/`: dataset de ejemplo (4 archivos `.md`).
- `ingest.py`: fragmenta los documentos y los guarda en ChromaDB. - `schemas.py`: modelo de salida `RagResponse` (respuesta y referencias).
- `rag.py`: prompt, recuperación, cadena LCEL y `get_rag_response()`. - `main.py`: ejecuta la ingesta y las preguntas de prueba. ## Instalación (Python 3.12)
  ```bash
  python3.12 -m venv .venv source .venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env

````
                                                                             Luego completa `ANTHROPIC_API_KEY` en `.env`.
                                                                              ## Ejecución

```bash                                                                      python main.py
````

También puedes ejecutar solo la ingesta con `python ingest.py`.

La primera ejecución crea la base en `vectorstore/`. Las siguientes omiten la
ingesta si
la colección ya tiene datos. Si cambias `data/`, borra `vectorstore/` y vuelv
a ejecutar.

## Flujo

1. **Ingesta:** `RecursiveCharacterTextSplitter`, medido en tokens con
   `tiktoken` (`chunk_size=500`, `chunk_overlap=50`), y persistencia en ChromaDB.
2. **Recuperación:** búsqueda por similitud de los 3 fragmentos más cercanos.
   Indexación
   y consulta usan el mismo modelo de embeddings, a través de
   `get_collection()`.
3. **Generación:** cadena LCEL asíncrona, `contexto | prompt | modelo |
PydanticOutputParser`,
   con hasta 3 intentos si la salida no se puede parsear.

## Pruebas

Salida real con `claude-haiku-5-5`.
**Preguntas con respuesta en los documentos:**

```json
{
  "respuesta": "La caché distribuida de Tallertrack, implementada con Redis 7
baja la latencia más de un 60 %, con degradación gradual.",
  "referencias": ["02_productos_principales.md"]                             }
```

```json {
  "respuesta": "VertiTrack incluye los cuestionarios clínicos DHI y ABC.",
  "referencias": ["02_productos_principales.md"]
}
```

**Preguntas trampa:** "¿Cuántos usuarios activos tiene VertiTrack?", "¿Cuál ela tarifa
por hora de Saúl?" y "¿Cuál es la capital de Francia?". Las tres dieron:

````json
{
  "respuesta": "No lo sé",                                                     "referencias": []
}                                                                            ```
                                                                             ## Limitaciones
                                                                             - **Tamaño de los fragmentos:** `chunk_size=500` es un máximo. Los 7
fragmentos actuales
  tienen entre 276 y 484 tokens.                                             - **Embeddings:** se usa el modelo por defecto de ChromaDB, local y sin clave
de API, pensado
  principalmente para inglés. Por eso, las consultas sobre los frameworks de `asjk` no
  recuperan el fragmento correcto dentro del top 3, y el sistema no puede responderlas bien.
- **Detección de preguntas sin respuesta:** depende del prompt, no de la distancia vectorial,
  porque una pregunta sin relación puede quedar tan cerca como una válida.
- **Referencias:** las indica el modelo y no se comprueban contra los fragmentos recuperados.
- **Alcance de las pruebas:** son 5 preguntas de ejemplo, no una evaluación completa.
````
