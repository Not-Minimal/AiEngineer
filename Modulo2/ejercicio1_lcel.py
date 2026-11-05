import asyncio

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

PREGUNTA = "¿Qué es la entropía?"


def crear_cadena():
    """Compone el flujo completo con LCEL: prompt -> modelo -> texto plano."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Eres un profesor que explica conceptos en un párrafo breve."),
            ("human", "{pregunta}"),
        ]
    )
    modelo = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    return prompt | modelo | StrOutputParser()


async def main() -> None:
    load_dotenv()

    chain = crear_cadena()
    respuesta = await chain.ainvoke({"pregunta": PREGUNTA})
    print(respuesta)


if __name__ == "__main__":
    asyncio.run(main())
