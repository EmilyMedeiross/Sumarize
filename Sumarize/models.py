from pydantic import BaseModel, validator 
from typing import List

class Resumo(BaseModel):
    texto: str
    
class TextoEntrada(BaseModel):
    texto: str

class PalavrasChave(BaseModel):
    palavras:List[str]

@validator('texto')
def validar_markdown(cls, value):
    if not value.strip():
        raise ValueError("O texto não pode estar vazio.")
    if not any(md in value for md in ["#", "*", "-", "[", "]", "(", ")"]):
        raise ValueError("O texto deve conter pelo menos um elemento de Markdown.")
    return value

