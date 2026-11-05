import os
from getpass import getpass

if not os.environ.get("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = getpass("🔑 ANTHROPIC_API_KEY: ").strip()

if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass(
        "🔑 Ingresá tu GOOGLE_API_KEY (gratis en aistudio.google.com/apikey): "
    ).strip()

print("🟢 Streaming OpenAI:")
async for chunk in manager_openai.generate_stream(pregunta):
    print(chunk, end="", flush=True)

print("\n\n🟣 Streaming Anthropic:")
async for chunk in manager_anthropic.generate_stream(pregunta):
    print(chunk, end="", flush=True)
