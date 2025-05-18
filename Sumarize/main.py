from fastapi import FastAPI, HTTPException
from models import Resumo
from typing import List

app = FastAPI()

resumos: List[Resumo] = []

@app.post("/resumir/", response_model=Resumo)
def create_resumo(resumo: Resumo):
    if not resumo.texto:
        raise  HTTPException(status_code=400, detail="O texto anexado não pode ser vazio!!" )
    
    if len(resumo.texto) > 3000: 
        raise HTTPException(status_code= 400, detail= "Texto muito longo, reduza a quantidade de caracteres para 4000")
    
    resumos.append(resumo)
    return resumo

@app.get("/resumos/", response_model=List[Resumo])
def listar_resumos():
    return resumos