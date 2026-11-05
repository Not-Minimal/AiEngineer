import asyncio
from typing import List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, InternalServerError, RateLimitError
from pydantic import BaseModel, Field, ValidationError

# Solo los errores de transporte se reintentan: repetir un error de formato gasta dinero sin arreglarlo.
ERRORES_TRANSITORIOS = (APIConnectionError, RateLimitError, InternalServerError)


class EntityExtraction(BaseModel):
    topic: str = Field(description="Tema principal del texto")
    entities: List[str] = Field(
        description="Entidades mencionadas en el texto, como productos, personas u organizaciones"
    )
    sentiment_score: float = Field(
        ge=0,
        le=1,
        description="Sentimiento del texto: 0 es muy negativo, 0.5 neutro y 1 muy positivo",
    )


async def run_validated_chain(text: str) -> None:
    # max_retries=0 deja los reintentos solo en with_retry; si no, se multiplican con los del SDK.
    llm = ChatOpenAI(model="gpt-4o", temperature=0, max_retries=0)

    structured_llm = llm.with_structured_output(EntityExtraction)

    resilient_llm = structured_llm.with_retry(
        retry_if_exception_type=ERRORES_TRANSITORIOS,
        stop_after_attempt=3,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Analiza el texto y extrae las entidades."),
            ("human", "{input}"),
        ]
    )

    chain = prompt | resilient_llm

    try:
        result = await chain.ainvoke({"input": text})
        print(result.model_dump_json(indent=2))
    except ValidationError as e:
        print(f"Error de validación ({type(e).__name__}): {e}")
    except ERRORES_TRANSITORIOS as e:
        print(f"Fallo transitorio tras 3 intentos ({type(e).__name__}): {e}")
    except Exception as e:
        print(f"Error ({type(e).__name__}): {e}")


if __name__ == "__main__":
    load_dotenv()
    sample_text = "LangGraph es una extensión de LangChain para agentes cíclicos."
    asyncio.run(run_validated_chain(sample_text))
