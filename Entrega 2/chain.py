import logging

from anthropic import APIConnectionError as AnthropicConnectionError
from anthropic import InternalServerError as AnthropicServerError
from anthropic import RateLimitError as AnthropicRateLimitError
from langchain_anthropic import ChatAnthropic
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import APIConnectionError as OpenAIConnectionError
from openai import InternalServerError as OpenAIServerError
from openai import LengthFinishReasonError
from openai import RateLimitError as OpenAIRateLimitError
from pydantic import ValidationError
from schemas import EntidadesTecnicas

logger = logging.getLogger("pipeline_extraccion")

INSTRUCCIONES_FORMATO = (
    "Incluye solo tecnologías mencionadas en el texto, sin inventar ninguna. "
    "Clasifica la criticidad como baja, media o alta. "
    "Escribe el resumen técnico en 1 o 2 oraciones."
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un analista técnico que extrae información de textos.\n{instrucciones_formato}",
        ),
        ("human", "{texto}"),
    ]
)
