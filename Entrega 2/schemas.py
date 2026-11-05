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
