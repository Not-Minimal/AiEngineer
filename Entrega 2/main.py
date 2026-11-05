import asyncio
import logging
import os

from chain import process_text
from dotenv import load_dotenv

TEXTO_EJEMPLO = (
    "Nuestra API en FastAPI está devolviendo timeouts intermitentes. El caché en Redis "
    "parece saturarse en picos de tráfico y las conexiones a PostgreSQL se agotan "
    "porque el pool está mal dimensionado. Esto está afectando a usuarios en producción."
)
TEXTO_AMBIGUO = "El sistema anda medio raro últimamente, no sé bien qué está pasando."

PROVEEDORES = [("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")]


async def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    for provider, variable_clave in PROVEEDORES:
        print(f"\n===== {provider} =====")

        if not os.getenv(variable_clave):
            print(f"Se omite: falta {variable_clave} en el .env")
            continue

        for texto in (TEXTO_EJEMPLO, TEXTO_AMBIGUO):
            try:
                resultado = await process_text(texto, provider)
                print(resultado.model_dump_json(indent=2))
            except Exception as e:
                print(f"⚠️ No se pudo procesar ({type(e).__name__}): {e}")


if __name__ == "__main__":
    asyncio.run(main())
