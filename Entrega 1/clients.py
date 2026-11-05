from abc import ABC, abstractmethod
from typing import AsyncGenerator, List

from anthropic import APIConnectionError as AnthropicConnectionError
from anthropic import APIError as AnthropicAPIError
from anthropic import AsyncAnthropic
from anthropic import RateLimitError as AnthropicRateLimitError
from openai import APIConnectionError as OpenAIConnectionError
from openai import APIError as OpenAIAPIError
from openai import AsyncOpenAI
from openai import RateLimitError as OpenAIRateLimitError

from schemas import ChatMessage, ModelResponse, Provider


class BaseLLMClient(ABC):
    """Contrato que todo cliente de LLM debe cumplir, sin importar el proveedor real detrás."""

    @abstractmethod
    async def generate(self, messages: List[ChatMessage]) -> ModelResponse:
        """Genera una respuesta completa (modo normal, no streaming)."""
        raise NotImplementedError

    @abstractmethod
    async def generate_stream(
        self, messages: List[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        """Genera la respuesta token a token (modo streaming)."""
        raise NotImplementedError
        yield  # nunca se ejecuta; solo le indica a Python que este método es un generador


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self._client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _preparar_parametros(self, messages: List[ChatMessage]) -> dict:
        """Arma los parámetros de la API, separando los mensajes system del resto."""
        system = "\n".join(m.content for m in messages if m.role == "system")
        conversacion = [m.model_dump() for m in messages if m.role != "system"]

        parametros = {
            "model": self.model,
            "max_tokens": self.max_tokens,  # obligatorio en Anthropic, a diferencia de OpenAI
            "temperature": self.temperature,
            "messages": conversacion,
        }
        if system:
            parametros["system"] = system
        return parametros

    async def generate(self, messages: List[ChatMessage]) -> ModelResponse:
        try:
            response = await self._client.messages.create(
                **self._preparar_parametros(messages)
            )
            return ModelResponse(
                provider=Provider.ANTHROPIC,
                model=self.model,
                content=response.content[0].text,
            )
        except AnthropicRateLimitError as e:
            return ModelResponse(
                provider=Provider.ANTHROPIC,
                model=self.model,
                content="",
                error=f"Límite de cuota excedido: {e}",
            )
        except AnthropicConnectionError as e:
            return ModelResponse(
                provider=Provider.ANTHROPIC,
                model=self.model,
                content="",
                error=f"Error de conexión: {e}",
            )
        except AnthropicAPIError as e:
            return ModelResponse(
                provider=Provider.ANTHROPIC,
                model=self.model,
                content="",
                error=f"Error de la API de Anthropic: {e}",
            )

    async def generate_stream(
        self, messages: List[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        try:
            async with self._client.messages.stream(
                **self._preparar_parametros(messages)
            ) as stream:
                async for texto in stream.text_stream:
                    yield texto
        except (
            AnthropicRateLimitError,
            AnthropicConnectionError,
            AnthropicAPIError,
        ) as e:
            yield f"\n[⚠️ Error durante el streaming: {e}]"


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        self._client = AsyncOpenAI(api_key=api_key, max_retries=3)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _preparar_parametros(self, messages: List[ChatMessage]) -> dict:
        """OpenAI acepta los mensajes system dentro de la lista, no hay que separarlos."""
        return {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [m.model_dump() for m in messages],
        }

    async def generate(self, messages: List[ChatMessage]) -> ModelResponse:
        try:
            response = await self._client.chat.completions.create(
                **self._preparar_parametros(messages)
            )
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content=response.choices[0].message.content or "",
            )
        except OpenAIRateLimitError as e:
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content="",
                error=f"Límite de cuota excedido: {e}",
            )
        except OpenAIConnectionError as e:
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content="",
                error=f"Error de conexión: {e}",
            )
        except OpenAIAPIError as e:
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content="",
                error=f"Error de la API de OpenAI: {e}",
            )

        except OpenAIRateLimitError as e:
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content="",
                error=f"Límite de cuota excedido: {e}",
            )
        except OpenAIConnectionError as e:
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content="",
                error=f"Error de conexión: {e}",
            )
        except OpenAIAPIError as e:
            return ModelResponse(
                provider=Provider.OPENAI,
                model=self.model,
                content="",
                error=f"Error de la API de OpenAI: {e}",
            )

    async def generate_stream(
        self, messages: List[ChatMessage]
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self._client.chat.completions.create(
                **self._preparar_parametros(messages),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except (
            OpenAIRateLimitError,
            OpenAIConnectionError,
            OpenAIAPIError,
        ) as e:
            yield f"\n[⚠️ Error durante el streaming: {e}]"
