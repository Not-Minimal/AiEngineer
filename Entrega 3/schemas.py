from typing import List

from pydantic import BaseModel, Field


class RagResponse(BaseModel):
    respuesta: str = Field(
        description="Respuesta basada solo en el contexto, o 'No lo sé'"
    )
    referencias: List[str] = Field(
        description="Archivos del contexto usados; lista vacía si la respuesta es 'No lo sé'"
    )
