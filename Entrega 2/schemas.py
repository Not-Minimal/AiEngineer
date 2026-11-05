from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator


class NivelCriticidad(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class EntidadesTecnicas(BaseModel):
    tecnologias: List[str] = Field(
        description="Tecnologías, frameworks o herramientas mencionadas en el texto"
    )
    nivel_de_criticidad: NivelCriticidad = Field(
        description="Gravedad del problema o relevancia de la arquitectura descrita"
    )
    resumen_tecnico: str = Field(
        description="Resumen técnico de 1 o 2 oraciones sobre el texto"
    )

    @field_validator("tecnologias")
    @classmethod
    def tecnologias_validas(cls, v: List[str]) -> List[str]:
        limpias = [t.strip() for t in v if t.strip()]
        if not limpias:
            raise ValueError("tecnologias debe incluir al menos una tecnología")
        return list(dict.fromkeys(limpias))

    @field_validator("resumen_tecnico")
    @classmethod
    def resumen_valido(cls, v: str) -> str:
        limpio = v.strip()
        if len(limpio) < 10:
            raise ValueError("resumen_tecnico debe tener al menos 10 caracteres")
        return limpio
