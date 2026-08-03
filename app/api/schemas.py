from pydantic import BaseModel, Field
from typing import List, Optional

class NotaCompetencia(BaseModel):
    nota: int
    pontos_fortes: List[str]
    pontos_melhorar: List[str]
    reescrita_sugerida: Optional[str] = None
    elementos_identificados: Optional[List[str]] = None

class NotasDetalhadas(BaseModel):
    C1: NotaCompetencia
    C2: NotaCompetencia
    C3: NotaCompetencia
    C4: NotaCompetencia
    C5: NotaCompetencia

class RedacaoRequest(BaseModel):
    tema: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="Tema oficial da redação (ex: Desafios da IA no Brasil)"
    )
    texto_redacao: str = Field(
        ...,
        min_length=1,
        max_length=15000,
        description="O texto integral da redação do aluno (máx. ~15000 caracteres, "
                     "muito acima do esperado para uma redação ENEM real)"
    )

class RedacaoResponse(BaseModel):
    nota_total: int
    fuga_tema: bool
    condicao_anulacao: str
    analise_geral: str
    notas: NotasDetalhadas
    prioridade_estudo: str

class FotoCorrecaoResponse(BaseModel):
    texto_reconhecido: str
    correcao: RedacaoResponse
