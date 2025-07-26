from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

#Tabela intermediária que representa o relacionamento N:N entre o resumo e as palavras-chave, coloquei essa tabela separada porque um resumo pode ter várias palavras-chave

class ResumoPalavra(SQLModel, table=True):
    __tablename__ = "resumopalavra"

    resumo_id: Optional[int] = Field(default=None, foreign_key="resumo.id", primary_key=True)
    palavra_id: Optional[int] = Field(default=None, foreign_key="palavrachave.id", primary_key=True)
    frequencia: Optional[int] = Field(default=1)

#Tabela que armazena as palavras chaves de forma individual
class PalavraChave(SQLModel, table=True):
    __tablename__ = "palavrachave"

    id: Optional[int] = Field(default=None, primary_key=True)
    termo: str 
    #Relacionamento com palavras-chave 
    resumos: List["Resumo"] = Relationship(back_populates="palavras_chave", link_model=ResumoPalavra)


class Resumo(SQLModel, table=True):
    __tablename__ = "resumo"

    id: Optional[int] = Field(default=None, primary_key=True)
    texto: str
    palavras_chave: List[PalavraChave] = Relationship(back_populates="resumos", link_model=ResumoPalavra)

#Não é uma tabela no banco, só serve pra entrada de dados. É um auxiliar pra receber texto de entrada na API 
class TextoEntrada(SQLModel):
    texto: str

#Auxiliar pra retornar a lista de palavras-chave, também não é uma tabela
class PalavrasChaveResposta(SQLModel):
    palavras: List[str]
