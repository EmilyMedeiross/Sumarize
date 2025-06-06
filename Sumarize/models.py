from pydantic import BaseModel, validator 
from typing import List, Optional

class Resumo(BaseModel):
    texto: str
    
class TextoEntrada(BaseModel):
    texto: str

class PalavrasChave(BaseModel):
    palavras:List[str]

@validator('texto')
def validar_texto(cls, value):
    if not value.strip():
        raise ValueError("O texto não pode estar vazio.")
    return value

