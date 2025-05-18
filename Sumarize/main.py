from fastapi import FastAPI, HTTPException
from typing import List
from pydantic import BaseModel, validator
from models import Resumo

app = FastAPI()

resumos: List[Resumo] = []

class TextoEntrada(BaseModel):
    texto: str

    @validator("texto")
    def validar_markdown(cls, value):
        if not value.strip():
            raise ValueError("O texto não pode estar vazio.")
        if not any(md in value for md in ["#", "*", "-", "[", "]", "(", ")"]):
            raise ValueError("O texto deve conter pelo menos um elemento de Markdown.")
        return value

@app.post("/resumir/", response_model=Resumo)
def create_resumo(resumo: TextoEntrada):
    if len(resumo.texto) > 3000:
        raise HTTPException(status_code=400, detail="Texto muito longo, reduza a quantidade de caracteres para 3000")

    novo_resumo = Resumo(texto=resumo.texto)
    resumos.append(novo_resumo)
    return novo_resumo

@app.get("/resumos/", response_model=List[Resumo])
def listar_resumos():
    return resumos
