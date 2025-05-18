from pydantic import BaseModel 

class Resumo(BaseModel):
    texto: str
    
class TextoEntrada(BaseModel):
    texto: str
