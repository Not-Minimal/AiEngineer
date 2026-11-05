# Pipeline de Extracción de Entidades Técnicas

Recibe un texto técnico sin procesar, como un log de error o una descripción de
arquitectura, y devuelve un objeto validado con Pydantic.

## Estructura

- `schemas.py`: contrato de salida (`NivelCriticidad`, `EntidadesTecnicas`).
- `chain.py`: prompt, modelos, cadena LCEL, reintentos y `process_text()`.
- `main.py`: mini-script de prueba asíncrono.

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

## Cadena LCEL

```python
(prompt | model.with_structured_output(EntidadesTecnicas, include_raw=True) | validar_salida).with_retry(
    retry_if_exception_type=debe_reintentar,
    stop_after_attempt=3,
)
```

- `include_raw=True` da acceso a la respuesta cruda para`.
- `validar_salida` detecta respuestas cortadas y relanza los errores de parseo, para
  que `with_retry` pueda actuar sobre ellos.

## Resiliencia

Se hacen hasta 3 intentos y cada fallo queda registrado

- **Se reintenta:** JSON mal formado o incompleto, respuestas cortadas por límite de
  tokens, errores de conexión, 429 y 5xx.
- **No se reintenta:** errores permanentes, como una clave inválida (401).
- `max_retries=0` evita que los reintentos del SDK se muh_retry`.

## Ejemplo de salida

Salida real con Anthropic (`claude-haiku-5-5`). El texto de entrada describe timeouts
en una API con FastAPI, Redis y PostgreSQL:

```json
{
  "tecnologias": ["FastAPI", "Redis", "PostgreSQL"],
  "nivel_de_criticidad": "alta",
  "resumen_tecnico": "Una API desarrollada con FastAPI presenta timeouts intermitentes por saturación de la caché en Redis durante picos de tráfico y por agotamiento de conexiones a PostgreSQL debido a un pool mal dimensionado. El problema afecta a usuarios en producción."
}
```

## Prueba de estrés

Texto ambiguo: "El sistema anda medio raro últimamente, o."

El modelo no inventó tecnologías y devolvió una lista vazó,
se agotaron los 3 intentos y el script informó el error sin caerse:

```text
WARNING:pipeline_extraccion:Intento fallido (ValidationError), reintentable: True
WARNING:pipeline_extraccion:Intento fallido (ValidationE
WARNING:pipeline_extraccion:Intento fallido (ValidationE
ERROR:pipeline_extraccion:[anthropic] Falló (ValidationError): 1 validation error for EntidadesTecnicas
```

Se prefiere un error explícito antes que un dato inventado.

## Limitaciones

- La rama de Anthropic se probó contra la API real.
- La rama de OpenAI no se probó contra sus servidores, por no contar con una clave. Se
  comprobó con respuestas simuladas: reintentos, respuestas cortadas y errores 401, 429 y 500.
- La detección de respuestas cortadas en Anthropic no se probó en una ejecución real.
- Un texto sin tecnologías consume 3 llamadas al modelo antes de fallar.
- `temperature` solo se configura en OpenAI: la versión instalada lo descarta para `claude-haiku-5-5`.
