import asyncio
import os

from dotenv import load_dotenv

from clients import BaseLLMClient, create_client
from schemas import ChatMessage, LLMConfig, Provider

PREGUNTA = "¿Qué es la entropía?"


async def probar_cliente(client: BaseLLMClient, messages: list[ChatMessage]) -> None:
    print("\nModo normal:")
    respuesta = await client.generate(messages)
    if respuesta.error:
        print(f"⚠️ {respuesta.error}")
    else:
        print(respuesta.content)

    print("\nModo streaming:")
    async for token in client.generate_stream(messages):
        print(token, end="", flush=True)
    print()


async def main() -> None:
    load_dotenv()

    proveedores = [
        (Provider.OPENAI, "OPENAI_API_KEY", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        (
            Provider.ANTHROPIC,
            "ANTHROPIC_API_KEY",
            os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"),
        ),
    ]
    messages = [ChatMessage(role="user", content=PREGUNTA)]

    for provider, variable_clave, model in proveedores:
        print(f"\n===== {provider.value} ({model}) =====")

        api_key = os.getenv(variable_clave)
        if not api_key:
            print(f"Se omite: falta {variable_clave} en el .env")
            continue

        config = LLMConfig(provider=provider, model=model, api_key=api_key)
        await probar_cliente(create_client(config), messages)


if __name__ == "__main__":
    asyncio.run(main())
