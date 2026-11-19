from app.agents.analyst_agent import crear_analista
from app.agents.research_agent import crear_investigador
from app.agents.specialist import ejecutar_especialista
from app.agents.supervisor import crear_supervisor, crear_sintetizador

__all__ = [
    "crear_analista",
    "crear_investigador",
    "crear_sintetizador",
    "crear_supervisor",
    "ejecutar_especialista",
]
