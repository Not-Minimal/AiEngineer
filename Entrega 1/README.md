Archivo Readme para explicar como se ejecuta el script.

# Unified Async LLM Client

Cliente asíncrono con una interfaz común para OpenAI y Anthropic, con streaming,
validación con Pydantic y manejo de errores.

## Estructura

- `schemas.py`: modelos Pydantic (`ChatMessage`, `LLMConfig`, `ModelResponse`).
- `clients.py`: `BaseLLMClient`, `OpenAIClient`, `AnthropicClient` y `create_client`.
- `main.py`: script de validación, en modo normal y streaming.

## Instalación (Python 3.12)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Luego completa tus claves en `.env`. Si falta una, ese proveedor se omite.

## Ejecución

```bash
python main.py
```

Modelos opcionales: `OPENAI_MODEL` (por defecto `gpt-4o-mini`) y
`ANTHROPIC_MODEL` (por defecto `claude-haiku-5-5`).

## Manejo de errores

- Los SDK reintentan hasta 3 veces los errores temporales.
- `generate` devuelve un `ModelResponse` con el campo `error`.
- `generate_stream` emite un aviso de error y termina, sin lanzar la excepción.

## Limitaciones

- `temperature` solo se aplica en OpenAI: `anthropic` 2.5.0 no acepta ese parámetro.
- `AnthropicClient` se probó contra la API real.
- `OpenAIClient` no se probó contra los servidores de OpenAI, por no contar con una clave.
  Se comprobó con un servidor local que imita sus respuestas, y su manejo de errores
  con un error real (402) del endpoint de Google compatible con OpenAI.
  intente
  # Unified Async LLM Client

Cliente asíncrono con una interfaz común para OpenAI y Anthropic, con streaming,
validación con Pydantic y manejo de errores.

## Estructura

- `schemas.py`: modelos Pydantic (`ChatMessage`, `LLMConfig`, `ModelResponse`).
- `clients.py`: `BaseLLMClient`, `OpenAIClient`, `AnthropicClient` y `create_client`.
- `main.py`: script de validación, en modo normal y streaming.

## Instalación (Python 3.12)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Luego completa tus claves en `.env`. Si falta una, ese proveedor se omite.

## Ejecución

```bash
python main.py
```

Modelos opcionales: `OPENAI_MODEL` (por defecto `gpt-4o-mini`) y
`ANTHROPIC_MODEL` (por defecto `claude-haiku-5-5`).

## Manejo de errores

- Los SDK reintentan hasta 3 veces los errores temporales.
- `generate` devuelve un `ModelResponse` con el campo `error`.
- `generate_stream` emite un aviso de error y termina, sin lanzar la excepción.

## Limitaciones

- `temperature` solo se aplica en OpenAI: `anthropic` 2.5.0 no acepta ese parámetro.
- `AnthropicClient` se probó contra la API real.
- `OpenAIClient` no se probó contra los servidores de OpenAI, por no contar con una clave.
  Se comprobó con un servidor local que imita sus respuestas, y su manejo de errores
  con un error real (402) del endpoint de Google compatible con OpenAI.
  Intente hasta con gpt-oss 120b
